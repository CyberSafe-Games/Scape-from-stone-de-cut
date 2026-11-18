"""Gera tabelas auditáveis da comparação estrita de decks."""
from collections import defaultdict
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    reports = []
    for path in sorted((ROOT / 'docs').glob('comparacao_decks_*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        reports.append((path, data))
    lines = ['# Comparação de decks sem cartas de cura', '',
        'Teste automatizado, sem alterar regras do jogo ou saves reais. Referência LV1 e controle com até três LV2; 60 HP, '
        'energia inicial 2 e zero melhorias permanentes. A cura normal de 30% após chefes é preservada.', '',
        '**LV1 usa dez sementes por política; o controle LV2 usa cinco. Cada célula agrupa duas políticas '
        'do bot (conservadora/agressiva): 20 ou 10 casos, não sementes independentes adicionais.** '
        'Limite de 40 turnos por confronto; limite não é contado como morte.', '',
        'Na campanha controlada o deck completo está pronto desde o começo; na aquisição real, '
        'o jogo começa obrigatoriamente com Socos e Protetoras. O JSON marca `restricao_atendida` '
        'em cada encontro para não apresentar o deck inicial híbrido como dano ou defesa puros. '
        'Com LV2 habilitado, o controle recebe o deck final pronto; a aquisição real precisa pagar os materiais/evoluções.', '',
        '## Composições', '']
    decks = {}
    for _, data in reports:
        decks.update(data['decks'])
    for name, cards in decks.items():
        lines.append(f"- **{name}**: " + ', '.join(f'{count}× {card}' for card, count in cards.items()) + '.')
    lines += ['', 'Todas as composições têm nove cópias e máximo de três por tipo. '
        'Defesa pura usa Escudo/Totem; defesa_controle acrescenta limpeza LV1. Nenhuma possui cura, reflexo ou efeito ofensivo.', '',
        '## Campanhas completas', '', '| Relatório | Ultimate | Cura na loja | LV2 | Deck | Modo | Vitórias/casos |',
        '|---|---|---|---|---|---|---:|']
    attempt_count, isolated_count = 0, 0
    for path, data in reports:
        grouped = defaultdict(list)
        for run in data['campanhas']:
            grouped[(run['deck'], run['modo'])].append(run)
        attempt_count += len(data['campanhas'])
        isolated_count += len(data['chefes_isolados'])
        for (deck, mode), runs in grouped.items():
            wins = sum(bool(r['venceu']) for r in runs)
            shop = 'Não'
            if data.get('cura_loja_habilitada', False):
                prices = data.get('cura_loja_precos')
                shop = ('3 curas: ' + '/'.join(map(str, prices)) + ' ouro') if prices else '30 ouro, ilimitada (histórico)'
            lv2 = 'Até 3' if data.get('evolucoes_habilitadas', False) else 'Não'
            lines.append(f'| [{path.stem}]({path.name}) | {data["ultimate"]} | {shop} | {lv2} | {deck} | {mode} | {wins}/{len(runs)} |')
    lines += ['', '## Chefes isolados com vida cheia', '',
        'O personagem reinicia com 60 HP em cada caso: essa tabela não mede desgaste entre encontros. '
        'Alvar/Tekks inclui as duas fases no mesmo combate.', '',
        '| Ultimate | Deck | Chefe/território | Vitórias/casos |', '|---|---|---|---:|']
    for _, data in reports:
        grouped = defaultdict(list)
        for case in data['chefes_isolados']:
            grouped[(case['deck_tipo'], case['territorio'])].append(case)
        for (deck, level), cases in grouped.items():
            wins = sum(c['resultado'] == 'victory' for c in cases)
            lines.append(f'| {data["ultimate"]} | {deck} | {level} | {wins}/{len(cases)} |')
    lines += ['', '## Limites de interpretação', '',
        '- Defesa pura sem Ultimate ofensiva não tem via de dano nas regras atuais. '
        '`sem_via_de_dano` é uma impossibilidade estrutural dessa composição, não uma derrota simulada.',
        '- Com Rugido, um deck de defesa pode matar, mas o dano vem da Ultimate. '
        'Mana Ancestral não causa dano diretamente; Forças Ancestrais também precisaria de um ataque para aproveitar sua Força.',
        '- Vitórias com cura da loja demonstram ausência de carta de cura, não ausência de recuperação de vida.',
        '- Uma composição não representa toda a família de estratégias. '
        'Foram incluídas variações de dano direto e de ataques com Veneno/Sangramento para reduzir essa limitação.',
        '- Busca curta, compras predefinidas, composições/planos LV2 fixos e limite de turnos restringem o bot. '
        'Falhar aqui não prova que pessoas não possam vencer. As políticas podem divergir em sorteios e economia.',
        '- Não usar uma vitória com deck já pronto como prova de que a mesma composição é obtida cedo e vence na progressão real.',
        '', f'Total registrado: **{attempt_count} tentativas de campanha** e **{isolated_count} casos de chefes isolados**. '
        'Tentativas interrompidas e provas sem via de dano não são campanhas jogadas até o fim.', '']
    path = ROOT / 'docs/comparacao_decks_sem_cura.md'
    path.write_text('\n'.join(lines), encoding='utf-8')
    print(f'{attempt_count} tentativas / {isolated_count} casos isolados -> {path.name}')


if __name__ == '__main__':
    main()
