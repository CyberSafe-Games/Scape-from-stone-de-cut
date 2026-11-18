"""Executa 50 campanhas com aquisição real e custo dos especiais vigente."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from devtools.simulate_roguelite_balance import campaign, STRATEGIES
from src.models.effects.ultimate_effect import known_ultimate_ids, UltimateAbility


def main():
    runs = []
    strategies = list(STRATEGIES)
    ultimates = known_ultimate_ids()
    for index in range(50):
        strategy = strategies[index % 3]
        ultimate = ultimates[(index // 3) % 3]
        run = campaign(index, strategy, policy='prepared', upgrades=True, ultimate=ultimate)
        run['ultimate'] = ultimate
        runs.append(run)
        print(f"{index + 1}/50 {strategy} / {ultimate}: "
              f"{'venceu' if run['venceu'] else 'parou'} ({len(run['encontros'])}/21)", flush=True)
    paths = ['devtools/simulate_ultimate_cost.py', 'devtools/simulate_roguelite_balance.py',
             'src/systems/combat_engine.py', 'src/models/effects/ultimate_effect.py']
    report = {
        'custo_especial': UltimateAbility.energy_cost,
        'carga_exigida': UltimateAbility.charge_requirement,
        'total': len(runs), 'vitorias': sum(r['venceu'] for r in runs),
        'condicoes': '50 sementes distintas; aquisição real; 60 HP; energia inicial 2; '
            'sem melhorias permanentes; cartas de cura permitidas; três evoluções LV2; '
            'três curas da loja por 30/45/60 ouro. Três estratégias e três especiais '
            'distribuídos em rodízio. Limite técnico de 400 passos por encontro.',
        'sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        'runs': runs,
    }
    path = ROOT / 'docs/simulacao_especiais_custo5_50runs.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Concluído: {report['vitorias']}/50 campanhas.", flush=True)


if __name__ == '__main__':
    main()
