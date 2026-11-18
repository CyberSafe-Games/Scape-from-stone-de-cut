"""Campanhas determinísticas com compras/recompensas reais e perfil sem bônus.

Uma política heurística é evidência limitada: falhar aqui não prova que uma
campanha seja impossível para uma pessoa. Não mede animação ou áudio.
"""
import argparse
from copy import deepcopy
from collections import Counter
import json
import hashlib
from pathlib import Path
import random
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.systems.save_manager import SaveManager
from src.systems.combat_engine import CombatEngine
from src.systems.deck_loadout import commit_deck
from src.systems.shop_system import purchase_card, purchase_heal, next_heal_price
from src.systems.save_manager import player_max_hp
from src.systems.roguelite import purchase_material, upgrade_copy, UPGRADE_PRICES, MATERIAL_PRICE, normalize_inventory
from src.systems.campaign_progress import record_victory, record_road_victory

STRATEGIES = {
    'dano_aura': ('Aura Rubra', 'Disparo de Arco', 'Poção de Cura', 'Esfera Protetora',
                  'Soco Simples', 'Poção Purificadora'),
    'defesa_cura': ('Poção de Cura', 'Disparo de Arco', 'Esfera Escudo', 'Esfera Protetora',
                    'Aura Rubra', 'Poção Purificadora'),
    'veneno_sangramento': ('Poção Venenosa', 'Adaga Sangrenta', 'Poção de Cura',
                          'Esfera Protetora', 'Zarabatana Venenosa', 'Poção Purificadora'),
}

# Não preencher três cópias de toda habilidade de suporte: mão é persistente.
DECK_PLANS = {
    'dano_aura': {'Disparo de Arco': 3, 'Aura Rubra': 1, 'Poção de Cura': 2,
                 'Esfera Protetora': 3, 'Soco Simples': 3, 'Poção Purificadora': 1},
    'defesa_cura': {'Disparo de Arco': 3, 'Poção de Cura': 3, 'Esfera Escudo': 2,
                   'Esfera Protetora': 3, 'Aura Rubra': 1, 'Poção Purificadora': 1},
    'veneno_sangramento': {'Poção Venenosa': 3, 'Adaga Sangrenta': 2, 'Poção de Cura': 2,
                          'Esfera Protetora': 3, 'Zarabatana Venenosa': 2, 'Poção Purificadora': 1},
}


def prepared_slots(progress, strategy):
    """Monta um deck válido com o que foi realmente adquirido."""
    from src.systems.card_catalog import CARD_BY_NAME
    counts = {name: count for name, count in DECK_PLANS[strategy].items()
              if name in progress['cartas_colecao']}
    if not any(CARD_BY_NAME[n].card_type == 'attack' or n == 'Poção Venenosa' for n in counts):
        counts['Soco Simples'] = 3
    slots = [name for name, count in counts.items() for _ in range(count)]
    # Nunca ignorar a falha de commit e acabar testando um deck anterior por acidente.
    if len(slots) < 6:
        slots = ['Soco Simples'] * 3 + ['Esfera Protetora'] * 3
    return slots + [None] * (18 - len(slots))


def upgrade_targets(progress, strategy):
    """Só propõe cópias que o bot realmente pretende equipar."""
    draft = deepcopy(progress)
    draft['deck_slots'] = prepared_slots(progress, strategy)
    normalize_inventory(draft)
    equipped = set(draft['copy_slots'])
    targets = []
    for name in STRATEGIES[strategy]:
        target = next((c for c in progress['copies'] if c['id'] in equipped
                       and c['name'] == name and c['level'] == 1), None)
        if target:
            targets.append(target)
    counts = Counter(c['name'] for c in progress['copies'] if c['level'] == 2)
    return sorted(targets, key=lambda c: counts[c['name']])


def prepare_shop(manager, data, strategy, level, upgrades):
    """Usa ouro de verdade para recuperar vida, adquirir tipos e evoluir cópias."""
    p = data['progresso']
    purchases = []
    while player_max_hp(p) - p['vida'] >= 15 or p['vida'] < 25:
        price = next_heal_price(p)
        if price is None or p['moedas'] < price:
            break
        result = purchase_heal(manager, data)
        if not result.success:
            break
        purchases.append({'tipo': 'cura', 'valor': result.amount, 'ouro': price})
    priorities = list(STRATEGIES[strategy])
    if strategy == 'dano_aura':
        priorities = ['Disparo de Arco', 'Aura Rubra', 'Poção de Cura', 'Poção Purificadora']
    if level >= 3:
        priorities = ['Poção Purificadora'] + priorities
    for name in dict.fromkeys(priorities):
        if name not in p['cartas_colecao']:
            before = p['moedas']
            result = purchase_card(manager, data, name)
            if result.success:
                purchases.append({'tipo': 'carta', 'nome': name, 'ouro': before - p['moedas']})
    if upgrades and p['upgrades_purchased'] < 3:
        for target in upgrade_targets(p, strategy):
            name = target['name']
            if p['upgrades_purchased'] >= 3:
                continue
            missing = max(0, 3 - p['materials'].get(name, 0))
            cost = UPGRADE_PRICES[name] + missing * MATERIAL_PRICE
            if p['moedas'] < cost:
                continue
            for _ in range(missing):
                ok, message = purchase_material(manager, data, name)
                if not ok:
                    raise ValueError(message)
            ok, message = upgrade_copy(manager, data, target['id'])
            if not ok:
                raise ValueError(message)
            purchases.append({'tipo': 'evolucao', 'nome': name, 'ouro': cost})
    return purchases


def evaluate(engine):
    p, enemy = engine.player, engine.enemy
    if not p.is_alive():
        return -10000
    if engine.state in ('victory', 'phase_complete'):
        return 10000 + p.hp * 3
    return (p.hp * 3 - enemy.hp + min(45, p.block) * .8
            + enemy.poison_stacks * 7 + enemy.bleed_stacks * 5
            + p.attack_bonus * 2 - p.poison_stacks * 12 - p.bleed_stacks * 8
            + p.ultimate_charge * .4 + p.energy * 1.5)


def play_turn(engine, score_fn=evaluate, *, allow_ultimate=True):
    """Busca curta por sequências de cartas; resolve a intenção já anunciada."""
    if engine.state != 'player_turn':
        return
    rng = random.getstate()
    candidates = [(engine, ())]
    best = (-float('inf'), ())
    for _ in range(8):
        expanded = []
        for current, moves in candidates:
            ended = deepcopy(current)
            ended.on_event = lambda *a, **k: None
            ended.end_turn()
            while ended.state in ('enemy_turn', 'enemy_resolving', 'boss_transition'):
                if ended.state == 'boss_transition':
                    ended.finish_boss_transition()
                    break
                if ended.state == 'enemy_turn':
                    ended.enemy_turn()
                else:
                    ended.finish_enemy_turn()
            score = score_fn(ended)
            if score > best[0]:
                best = score, moves
            options = [i for i, card in enumerate(current.hand) if card.cost <= current.energy]
            if (allow_ultimate and current.ultimate_ready
                    and current.energy >= current.ultimate.energy_cost):
                options.append('ultimate')
            for i in options:
                if i == 'ultimate' or current.hand[i].cost <= current.energy:
                    trial = deepcopy(current)
                    trial.on_event = lambda *a, **k: None
                    if (trial.activate_ultimate() if i == 'ultimate' else trial.play_card(i)):
                        sequence = moves + (i,)
                        if trial.state in ('victory', 'boss_transition'):
                            value = score_fn(trial) + (1000 if trial.state == 'boss_transition' else 0)
                            if value > best[0]:
                                best = value, sequence
                        elif trial.state == 'player_turn':
                            expanded.append((trial, sequence))
        candidates = sorted(expanded, key=lambda pair: score_fn(pair[0]), reverse=True)[:4]
        if not candidates:
            break
    random.setstate(rng)
    for index in best[1]:
        if engine.state == 'player_turn':
            if index == 'ultimate':
                engine.activate_ultimate()
            else:
                engine.play_card(index)
    if engine.state == 'player_turn':
        if not best[1] and engine.can_swap_cemetery():
            # Libera uma mão retida sem benefício imediato, como curas em vida cheia.
            for index, card in enumerate(engine.hand):
                if card.card_type != 'attack':
                    engine.swap_cemetery(index)
                    break
        engine.end_turn()


def campaign(seed, strategy, *, policy='prepared', upgrades=False, ultimate='forcas_ancestrais'):
    random.seed(seed)
    records = []
    with tempfile.TemporaryDirectory() as folder:
        manager = SaveManager(folder)
        data = manager.create_save('simulation')
        p = data['progresso']
        p['moedas'] = 30  # tutorial já contabilizado, sem segundo prêmio
        p['tutorial_concluido'] = True
        p['ultimate_equipada'] = ultimate
        priorities = STRATEGIES[strategy]
        for level in range(1, 8):
            for encounter in (0, 1, None):
                p = data['progresso']
                purchases = []
                if policy == 'prepared':
                    purchases = prepare_shop(manager, data, strategy, level, upgrades)
                    slots = prepared_slots(p, strategy)
                else:
                    for name in priorities:
                        if name not in p['cartas_colecao']:
                            if not purchase_card(manager, data, name).success:
                                break
                    names = [name for name in priorities if name in p['cartas_colecao']]
                    from src.systems.card_catalog import CARD_BY_NAME
                    if not any(CARD_BY_NAME[name].card_type == 'attack'
                               or name == 'Poção Venenosa' for name in names):
                        names.append('Soco Simples')
                    if len(names) < 2:
                        names = ['Soco Simples', 'Esfera Protetora']
                    slots = [name for name in names for _ in range(3)]
                    slots += [None] * (18 - len(slots))
                ok, message = commit_deck(manager, data, slots)
                if not ok:
                    raise ValueError(message)
                engine = CombatEngine(map_mode=True)
                engine.resume_from_save(data, manager, level=level,
                    encounter_kind='road' if encounter is not None else 'point', encounter_index=encounter)
                entry_hp = engine.player.hp
                for _ in range(400):
                    if engine.state == 'player_turn':
                        play_turn(engine)
                    elif engine.state == 'enemy_turn':
                        engine.enemy_turn()
                    elif engine.state == 'enemy_resolving':
                        engine.finish_enemy_turn()
                    elif engine.state == 'boss_transition':
                        engine.finish_boss_transition()
                    else:
                        break
                records.append({'territorio': level, 'encontro': encounter,
                    'vida_entrada': entry_hp, 'vida_saida': engine.player.hp,
                    'turnos': engine.player.turn_count, 'ouro': engine.player.coins,
                    'resultado': engine.state, 'deck': [n for n in slots if n],
                    'evolucoes': p['upgrades_purchased'], 'compras': purchases})
                if engine.state != 'victory':
                    return {'seed': seed, 'estrategia': strategy, 'venceu': False, 'encontros': records}
                best = next((i for name in priorities for i, card in enumerate(engine.reward_cards)
                             if card.name == name), None)
                if best is not None:
                    engine.choose_reward(best)
                    records[-1]['recompensa'] = engine.reward_selection
                elif upgrades and p['upgrades_purchased'] < 3:
                    amount = 3 if engine.enemy.is_miniboss else 1
                    name = next((c['name'] for c in upgrade_targets(p, strategy)
                        if p['materials'].get(c['name'], 0) + amount <= 9), None)
                    if name is not None:
                        if not engine.choose_material(name):
                            raise ValueError('Bot não conseguiu selecionar a recompensa de materiais.')
                        records[-1]['recompensa'] = {'material': name, 'quantidade': amount}
                    else:
                        engine.skip_reward()
                else:
                    engine.skip_reward()
                recorder = record_road_victory if encounter is not None else record_victory
                recorder(manager, data, engine, lambda: None)
        return {'seed': seed, 'estrategia': strategy, 'venceu': True, 'encontros': records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds', type=int, default=3)
    parser.add_argument('--policy', choices=('legacy', 'prepared'), default='prepared')
    parser.add_argument('--upgrades', action='store_true')
    parser.add_argument('--ultimate', choices=('mana_ancestral', 'forcas_ancestrais', 'rugido_da_floresta'),
                        default='forcas_ancestrais')
    parser.add_argument('--report', default='docs/simulacao_balanceamento_preparado.json')
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error('--seeds deve ser positivo.')
    runs = []
    for strategy in STRATEGIES:
        for seed in range(args.seeds):
            run = campaign(seed, strategy, policy=args.policy, upgrades=args.upgrades, ultimate=args.ultimate)
            runs.append(run)
            print(f"{strategy} seed={seed}: {'venceu' if run['venceu'] else 'parou'} "
                  f"({len(run['encontros'])}/21 encontros)", flush=True)
    path = ROOT / args.report
    path.write_text(json.dumps({'versao_bot': 2,
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'limites': 'Heurística sem bônus permanentes '
        'ou melhorias de vida temporárias. Não substitui playtest.', 'politica': args.policy,
        'ultimate': args.ultimate,
        'evolucoes_habilitadas': args.upgrades, 'cura_loja_habilitada': args.policy == 'prepared',
        'runs': runs},
        ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
