"""Registra matriz pareada de 50 runs gerais e 20 focadas em Machado/Mana."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from devtools.simulate_roguelite_balance import campaign, STRATEGIES, DECK_PLANS
from src.models.effects.ultimate_effect import known_ultimate_ids, ManaAncestralUltimate
from src.systems.card_catalog import CARD_BY_NAME


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    strategies = list(STRATEGIES)
    ultimates = known_ultimate_ids()
    cases = [(i, strategies[i % 3], ultimates[(i // 3) % 3], 'geral') for i in range(50)]
    STRATEGIES['machados_mana'] = ('Machados Gêmeos', 'Poção de Cura', 'Esfera Protetora',
                                  'Esfera Escudo', 'Poção Purificadora', 'Soco Simples')
    DECK_PLANS['machados_mana'] = {'Machados Gêmeos': 3, 'Poção de Cura': 3,
        'Esfera Protetora': 3, 'Esfera Escudo': 2, 'Poção Purificadora': 1, 'Soco Simples': 3}
    cases.extend((i, 'machados_mana', 'mana_ancestral', 'focada') for i in range(20))
    runs = []
    for index, (seed, strategy, ultimate, group) in enumerate(cases, 1):
        run = campaign(seed, strategy, policy='prepared', upgrades=True, ultimate=ultimate)
        run.update(ultimate=ultimate, grupo=group)
        runs.append(run)
        print(f"{index}/70 {strategy}/{ultimate}: {'venceu' if run['venceu'] else 'parou'}", flush=True)
    paths = ['devtools/compare_mana_axes.py', 'devtools/simulate_roguelite_balance.py',
             'src/models/effects/ultimate_effect.py', 'src/systems/card_definitions.py',
             'src/systems/combat_engine.py']
    report = {'custo_machados': CARD_BY_NAME['Machados Gêmeos'].cost,
        'mana_descricao': ManaAncestralUltimate.description,
        'condicoes': 'Aquisição real; 60 HP; energia inicial 2; zero melhorias permanentes; '
            'cartas de cura permitidas; três evoluções LV2; curas da loja 30/45/60 ouro; '
            'limite técnico 400 passos/encontro. Mesmos casos e política nas duas versões. '
            'Matriz geral idêntica às 50 runs anteriores; foco inclui Machados e Mana em 20 sementes.',
        'sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        'runs': runs}
    (ROOT / args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Concluído: {sum(r['venceu'] for r in runs)}/70", flush=True)


if __name__ == '__main__':
    main()
