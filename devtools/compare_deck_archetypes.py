"""Compara decks estritos sem cura, sem alterar o jogo ou os saves reais.

Separa encontros controlados (deck pronto/HP cheio), campanha controlada
(deck pronto/HP persistente) e aquisição real (começa com os starters).
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from devtools.simulate_roguelite_balance import play_turn, evaluate
from src.models.deck import DeckManager
from src.systems.card_catalog import CARD_BY_NAME
from src.systems.combat_engine import CombatEngine
from src.systems.enemy_factory import create_point_enemy, create_road_enemy, choose_next_action
from src.systems.save_manager import SaveManager
from src.systems.shop_system import purchase_card, purchase_heal, next_heal_price, HEAL_PRICES, HEAL_LIMIT
from src.systems.deck_loadout import commit_deck
from src.systems.campaign_progress import record_victory, record_road_victory
from src.systems.roguelite import instance_card, purchase_material, upgrade_copy, UPGRADE_PRICES, MATERIAL_PRICE

DECKS = {
    'somente_dano': {'Soco Simples': 3, 'Disparo de Arco': 3, 'Lança Perfurante': 3},
    'hibrido': {'Soco Simples': 2, 'Disparo de Arco': 2,
                'Esfera Protetora': 3, 'Esfera Escudo': 2},
    'somente_defesa': {'Esfera Protetora': 3, 'Esfera Escudo': 3, 'Totem Protetor': 3},
    'dano_efeitos': {'Soco Simples': 3, 'Adaga Sangrenta': 3, 'Zarabatana Venenosa': 3},
    'hibrido_efeitos': {'Adaga Sangrenta': 2, 'Zarabatana Venenosa': 2,
                       'Esfera Protetora': 3, 'Totem Protetor': 2},
    'hibrido_controle': {'Disparo de Arco': 3, 'Esfera Protetora': 3,
                        'Esfera Escudo': 2, 'Poção Purificadora': 1},
    'defesa_controle': {'Esfera Protetora': 3, 'Esfera Escudo': 3,
                       'Totem Protetor': 2, 'Poção Purificadora': 1},
}
UPGRADES = {
    'somente_dano': {'Disparo de Arco': 3},
    'hibrido': {'Disparo de Arco': 2, 'Esfera Protetora': 1},
    'somente_defesa': {'Esfera Escudo': 3},
    'dano_efeitos': {'Adaga Sangrenta': 3},
    'hibrido_efeitos': {'Adaga Sangrenta': 2, 'Esfera Protetora': 1},
    'hibrido_controle': {'Disparo de Arco': 3},
    'defesa_controle': {'Esfera Escudo': 3},
}


def aggressive_score(engine):
    """Contraponto à política original, que pesa mais a preservação de vida."""
    p, enemy = engine.player, engine.enemy
    if not p.is_alive():
        return -10000
    if engine.state in ('victory', 'phase_complete'):
        return 10000 + p.hp
    return (p.hp - enemy.hp * 2 + min(45, p.block) * .3
            + enemy.poison_stacks * 7 + enemy.bleed_stacks * 5
            + p.attack_bonus * 2 - p.poison_stacks * 8 - p.bleed_stacks * 5
            + p.ultimate_charge * .4 + p.energy)


def slots_for(archetype, owned=None):
    names = [name for name, count in DECKS[archetype].items()
             if owned is None or name in owned for _ in range(count)]
    if owned is not None and len(names) < 6:
        names = ['Soco Simples'] * 3 + ['Esfera Protetora'] * 3
    return names + [None] * (18 - len(names))


def has_damage_route(engine, ultimate):
    return any(card.card_type == 'attack' for card in engine.deck) or ultimate == 'rugido_da_floresta'


def fight(engine, ultimate, policy, max_turns=40):
    """Sem cura de loja ou carta; cura normal pós-chefe é aplicada pelo chamador."""
    engine.on_event = lambda *args, **kwargs: None
    if ultimate != 'nenhuma':
        engine.equip_ultimate(ultimate)
    # Prova estrutural: Escudo/Totem sem ataque/efeito ofensivo não reduzem HP inimigo.
    if not has_damage_route(engine, ultimate):
        return 'sem_via_de_dano'
    score = aggressive_score if policy == 'agressiva' else evaluate
    for _ in range(max_turns * 8):
        if engine.player.turn_count > max_turns:
            return 'limite_de_turnos'
        if engine.state == 'player_turn':
            play_turn(engine, score_fn=score, allow_ultimate=ultimate != 'nenhuma')
        elif engine.state == 'enemy_turn':
            engine.enemy_turn()
        elif engine.state == 'enemy_resolving':
            engine.finish_enemy_turn()
        elif engine.state == 'boss_transition':
            engine.finish_boss_transition()
        else:
            return engine.state
    return 'limite_de_turnos'


def controlled_engine(archetype, level, encounter, seed, hp=60, upgrades=False):
    engine = CombatEngine(map_mode=True)
    # Remove a influência do sorteio genérico do construtor nos pares controlados.
    random.seed(seed * 100 + level * 3 + (2 if encounter is None else encounter))
    engine.level = level
    engine.encounter_kind = 'point' if encounter is None else 'road'
    engine.encounter_index = encounter
    engine.enemy = create_point_enemy(level) if encounter is None else create_road_enemy(level)
    engine.deck_manager = DeckManager([
        instance_card({'id': f'{name}-{i}', 'name': name,
                       'level': 2 if upgrades and i < UPGRADES[archetype].get(name, 0) else 1})
        for name, count in DECKS[archetype].items() for i in range(count)])
    engine.player.hp = hp
    choose_next_action(engine.enemy)
    engine.start_combat()
    return engine


def record(engine, result, archetype):
    actual = Counter(c.name for c in engine.deck)
    pure = all(name in DECKS[archetype] for name in actual)
    return {'territorio': engine.level, 'encontro': engine.encounter_index,
            'inimigo': engine.enemy.name, 'resultado': result,
            'vida_saida': engine.player.hp, 'vida_inimigo': engine.enemy.hp,
            'turnos': engine.player.turn_count, 'deck': dict(actual), 'restricao_atendida': pure,
            'copias_lv2': dict(Counter(c.name for c in engine.deck if c.level == 2))}


def buy_heals(manager, data, before_boss=False):
    """Compra recuperação existente, sem introduzir carta de cura no deck."""
    p = data['progresso']
    purchases = []
    while 60 - p['vida'] >= 15 or p['vida'] < 25 or (before_boss and p['vida'] < 60):
        price = next_heal_price(p)
        if price is None or p['moedas'] < price:
            break
        before = p['moedas']
        result = purchase_heal(manager, data)
        if not result.success:
            break
        purchases.append({'vida': result.amount, 'ouro': before - p['moedas']})
    return purchases


def controlled_campaign(archetype, seed, ultimate, policy, shop_healing=False, upgrades=False):
    hp, gold, encounters = 60, 30, []
    with tempfile.TemporaryDirectory() as folder:
        manager = SaveManager(folder)
        data = manager.create_save('controlled')
        for level in range(1, 8):
            for index in (0, 1, None):
                data['progresso'].update(vida=hp, moedas=gold)
                cures = buy_heals(manager, data, index is None) if shop_healing else []
                hp, gold = data['progresso']['vida'], data['progresso']['moedas']
                engine = controlled_engine(archetype, level, index, seed, hp, upgrades)
                engine.player.coins = gold
                entry = hp
                result = fight(engine, ultimate, policy)
                item = record(engine, result, archetype)
                item.update(vida_entrada=entry, curas_loja=cures, ouro=engine.player.coins)
                encounters.append(item)
                if result != 'victory':
                    return {'venceu': False, 'encontros': encounters}
                engine.finish_map_phase()
                hp, gold = engine.player.hp, engine.player.coins
    return {'venceu': True, 'encontros': encounters}


def planned_upgrade_targets(progress, archetype):
    targets = []
    for name, limit in UPGRADES[archetype].items():
        copies = [c for c in progress['copies'] if c['name'] == name]
        needed = limit - sum(c['level'] == 2 for c in copies)
        targets.extend([c for c in copies if c['level'] == 1][:max(0, needed)])
    return targets


def real_campaign(archetype, seed, ultimate, policy, shop_healing=False, upgrades=False):
    random.seed(seed)
    encounters = []
    with tempfile.TemporaryDirectory() as folder:
        manager = SaveManager(folder)
        data = manager.create_save('comparison')
        p = data['progresso']
        p.update(moedas=30, tutorial_concluido=True)
        if ultimate != 'nenhuma':
            p['ultimate_equipada'] = ultimate
        for level in range(1, 8):
            for index in (0, 1, None):
                p = data['progresso']
                cures = buy_heals(manager, data, index is None) if shop_healing else []
                for name in DECKS[archetype]:
                    if name not in p['cartas_colecao']:
                        purchase_card(manager, data, name)
                if upgrades:
                    for target in planned_upgrade_targets(p, archetype):
                        name = target['name']
                        missing = max(0, 3 - p['materials'].get(name, 0))
                        if p['upgrades_purchased'] >= 3 or p['moedas'] < UPGRADE_PRICES[name] + missing * MATERIAL_PRICE:
                            continue
                        for _ in range(missing):
                            ok, message = purchase_material(manager, data, name)
                            if not ok:
                                raise ValueError(message)
                        ok, message = upgrade_copy(manager, data, target['id'])
                        if not ok:
                            raise ValueError(message)
                ok, message = commit_deck(manager, data, slots_for(archetype, p['cartas_colecao']))
                if not ok:
                    raise ValueError(message)
                engine = CombatEngine(map_mode=True)
                engine.resume_from_save(data, manager, level=level,
                    encounter_kind='point' if index is None else 'road', encounter_index=index)
                entry = engine.player.hp
                result = fight(engine, ultimate, policy)
                item = record(engine, result, archetype)
                item.update(vida_entrada=entry, ouro=engine.player.coins, curas_loja=cures)
                encounters.append(item)
                if result != 'victory':
                    return {'venceu': False, 'encontros': encounters}
                reward = next((i for name in DECKS[archetype]
                               for i, c in enumerate(engine.reward_cards) if c.name == name), None)
                if reward is not None:
                    engine.choose_reward(reward)
                elif upgrades and p['upgrades_purchased'] < 3 and planned_upgrade_targets(p, archetype):
                    amount = 3 if engine.enemy.is_miniboss else 1
                    name = planned_upgrade_targets(p, archetype)[0]['name']
                    if p['materials'].get(name, 0) + amount <= 9:
                        if not engine.choose_material(name):
                            raise ValueError('Falha na seleção de materiais.')
                    else:
                        engine.skip_reward()
                else:
                    engine.skip_reward()
                recorder = record_victory if index is None else record_road_victory
                recorder(manager, data, engine, lambda: None)
    return {'venceu': True, 'encontros': encounters}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--ultimate', choices=('nenhuma', 'mana_ancestral', 'rugido_da_floresta'), default='nenhuma')
    parser.add_argument('--report', required=True)
    parser.add_argument('--shop-healing', action='store_true', help='Permite comprar cura com ouro, sem cartas de cura.')
    parser.add_argument('--decks', nargs='+', choices=tuple(DECKS), default=list(DECKS))
    parser.add_argument('--upgrades', action='store_true')
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error('--seeds deve ser positivo.')
    runs, bosses = [], []
    for archetype in args.decks:
        for policy in ('conservadora', 'agressiva'):
            for seed in range(args.seeds):
                for mode, simulator in (('controlada', controlled_campaign), ('aquisicao_real', real_campaign)):
                    run = simulator(archetype, seed, args.ultimate, policy,
                                    shop_healing=args.shop_healing, upgrades=args.upgrades)
                    run.update(deck=archetype, politica=policy, seed=seed, modo=mode)
                    runs.append(run)
                for level in (() if args.shop_healing else range(1, 8)):
                    engine = controlled_engine(archetype, level, None, seed, upgrades=args.upgrades)
                    result = fight(engine, args.ultimate, policy)
                    item = record(engine, result, archetype)
                    item.update(deck_tipo=archetype, politica=policy, seed=seed)
                    bosses.append(item)
            print(f'{archetype} / {policy}: concluido', flush=True)
    script = Path(__file__).read_bytes()
    report = {'script_sha256': hashlib.sha256(script).hexdigest(),
              'bot_sha256': hashlib.sha256((ROOT / 'devtools/simulate_roguelite_balance.py').read_bytes()).hexdigest(),
              'ultimate': args.ultimate, 'seeds': args.seeds,
              'cura_loja_habilitada': args.shop_healing,
              'cura_loja_precos': HEAL_PRICES,
              'cura_loja_limite': HEAL_LIMIT,
              'evolucoes_habilitadas': args.upgrades,
              'plano_lv2': {key: UPGRADES[key] for key in args.decks} if args.upgrades else {},
              'parametros': '60 HP, energia 2 inicial, zero melhorias permanentes; '
                'sem cartas de cura. Cura normal pos-chefe preservada. Limite 40 turnos por combate. '
                'Deck pronto na controlada; starters obrigatorios na aquisicao real. '
                'Flag cura_loja_habilitada determina se ouro pode pagar recuperacao entre encontros.',
              'decks': {key: DECKS[key] for key in args.decks}, 'campanhas': runs, 'chefes_isolados': bosses}
    (ROOT / args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
