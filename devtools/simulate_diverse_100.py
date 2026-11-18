"""Amostra de 100 campanhas em dez planos de deck, sem bônus permanentes."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from devtools.simulate_roguelite_balance import campaign, STRATEGIES, DECK_PLANS
from src.models.effects.ultimate_effect import known_ultimate_ids, ManaAncestralUltimate
from src.systems.card_catalog import AVAILABLE_CARD_NAMES, CARD_BY_NAME


def plans():
    result = {key: dict(DECK_PLANS[key]) for key in STRATEGIES}
    result.update({
        'machados_hibrido': {'Machados Gêmeos': 3, 'Poção de Cura': 3,
            'Esfera Protetora': 3, 'Esfera Escudo': 2, 'Poção Purificadora': 1, 'Soco Simples': 3},
        'dano_direto': {'Disparo de Arco': 3, 'Lança Perfurante': 3,
            'Machados Gêmeos': 3, 'Investida': 3, 'Soco Simples': 3},
        'arco_controle': {'Disparo de Arco': 3, 'Esfera Protetora': 3,
            'Esfera Escudo': 2, 'Poção Purificadora': 1, 'Amuleto Dissipador': 1,
            'Machado Quebra-Escudo': 1},
        'fogo_hibrido': {'Bola de Fogo': 3, 'Disparo de Arco': 3,
            'Esfera Protetora': 3, 'Poção de Cura': 2, 'Poção Purificadora': 1},
        'veneno_hibrido': {'Poção Venenosa': 3, 'Zarabatana Venenosa': 3,
            'Esfera Protetora': 3, 'Poção de Cura': 2, 'Poção Purificadora': 1},
        'sangramento_hibrido': {'Adaga Sangrenta': 3, 'Poção Fragilizante': 1,
            'Disparo de Arco': 3, 'Esfera Protetora': 3,
            'Poção de Cura': 2, 'Poção Purificadora': 1},
        'sustentacao_mascara': {'Máscara Ancestral': 2, 'Disparo de Arco': 3,
            'Esfera Protetora': 3, 'Totem Protetor': 1, 'Surto de Energia': 1,
            'Poção Purificadora': 1, 'Poção de Cura': 2},
    })
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    matrix = plans()
    assert len(matrix) == 10
    assert set().union(*(set(p) for p in matrix.values())) == AVAILABLE_CARD_NAMES
    for plan in matrix.values():
        assert 6 <= sum(plan.values()) <= 18
        assert all(1 <= count <= 3 for count in plan.values())
    if args.check:
        print('Matriz válida: dez planos, dez runs por plano, 20 tipos disponíveis cobertos.')
        return
    STRATEGIES.update({key: tuple(plan) for key, plan in matrix.items()
                       if key not in STRATEGIES})
    DECK_PLANS.update(matrix)
    paths = ['devtools/simulate_diverse_100.py', 'devtools/simulate_roguelite_balance.py',
        'src/models/effects/ultimate_effect.py', 'src/systems/card_definitions.py',
        'src/systems/combat_engine.py', 'src/systems/roguelite.py']
    report = {'concluido': False, 'runs': [], 'planos': matrix,
        'sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        'custo_machados': CARD_BY_NAME['Machados Gêmeos'].cost,
        'mana_descricao': ManaAncestralUltimate.description,
        'condicoes': '100 sementes distintas (1000–1099), dez runs por plano. '
            'Especiais em rodízio (34 Mana/33 Forças/33 Rugido). Aquisição real '
            'a partir dos starters; 60 HP; energia inicial 2; zero bônus permanentes; '
            'até três evoluções LV2; três curas da loja 30/45/60; cura pós-chefe normal. '
            'Mesma heurística preparada. Limite técnico 400 passos por encontro. '
            'Planos são prioridades, não decks concedidos prontos; não enumera todas as combinações.'}
    path = ROOT / 'docs/simulacao_decks_variados_100.json'
    ultimates = known_ultimate_ids()
    for deck_index, strategy in enumerate(matrix):
        for sample in range(10):
            index = deck_index * 10 + sample
            ultimate = ultimates[index % 3]
            run = campaign(1000 + index, strategy, policy='prepared', upgrades=True, ultimate=ultimate)
            last = run['encontros'][-1]
            outcome = 'vitoria' if run['venceu'] else (
                'morte' if last['resultado'] == 'game_over' else 'limite_tecnico')
            run.update(ultimate=ultimate, desfecho=outcome)
            report['runs'].append(run)
            report['resumo'] = dict(Counter(r['desfecho'] for r in report['runs']))
            report['concluido'] = index == 99
            path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f"{index+1}/100 {strategy}/{ultimate}: {outcome} "
                  f"({len(run['encontros'])}/21 encontros)", flush=True)
    print(json.dumps(report['resumo']), flush=True)


if __name__ == '__main__':
    main()
