# Comparação de Mana Ancestral e Machados Gêmeos — 18/11/2026

> **Registro histórico — não é especificação vigente.** Valores, caminhos, comandos e resultados abaixo pertencem à etapa original. Não restaurar regras/arte antigas nem executar preparadores sobre kits atuais. Consulte o [estado atual](estado_atual.md).

> Comparação histórica: posteriormente o usuário aprovou devolver a limpeza de efeitos à Mana, mantendo a remoção da compra de cartas. Os resultados abaixo refletem a alternativa anterior sem limpeza.

Proposta implementada localmente para avaliação, sem commit/push/merge nesta rodada. A PR #24 continua com a versão anterior.

## Mudança

- Machados Gêmeos custa **5 de energia** nos dois níveis; dano preservado: LV1 40 e LV2 50.
- Mana Ancestral restaura somente a energia para **8**. Não compra cartas nem remove efeitos negativos. Continua exigindo 20 de carga e 5 de energia para ativar.
- Cartas, tooltip e textos de feedback refletem as novas regras; PNGs originais preservados. A legenda de custo dos especiais também foi corrigida na composição usada fora do combate.
- Nenhuma outra regra de combate, preço em ouro, dano, evolução ou save foi alterada.

Com oito de energia, um Machado consome cinco e deixa três: não cabem dois Machados seguidos nessa reserva. Mana ainda permite combinar outras cartas, e a mudança não impede toda forma de dano explosivo. A limpeza depende agora das cartas próprias para esse efeito.

## Método

140 tentativas: **50 gerais e 20 focadas por versão**. Mesmo script, sementes, estratégias, especiais e política nas duas execuções. Antes foi executado com o código da PR; depois, com a proposta. Hashes de código em cada JSON. Saves temporários independentes, sem acessar saves reais.

Condições: aquisição real a partir dos starters, 60 HP, energia inicial 2, zero melhorias permanentes, cartas de cura permitidas, até três evoluções LV2 e três curas da loja por 30/45/60 ouro. Limite técnico de 400 passos por encontro. A matriz geral repete as 50 runs anteriores; são 18 casos com Mana, 17 com Forças e 15 com Rugido. Os decks gerais não usam Machados: essa parte mede a mudança da Mana, não o custo do Machado.

O foco usa 20 sementes com Mana e prioridades de aquisição de Machados, cura, Protetora, Escudo e limpeza; os starters continuam até a compra. Plano final: três Machados, três curas, três Protetoras, dois Escudos, uma Purificadora e três Socos. Não é reprodução do deck exato do amigo, que não foi registrado. O Machado esteve equipado em parte das runs nas duas versões; a combinação não é concedida gratuitamente desde a primeira luta.

```powershell
.\.venv\Scripts\python.exe -B devtools/compare_mana_axes.py --report docs/comparacao_mana_machados_depois.json
```

Para reproduzir o antes, usar o código do commit `3e465dc` com este script de comparação. Não sobrescrever relatórios históricos. A árvore atual reproduz apenas o depois.

## Resultados

| Amostra | Antes | Proposta |
| --- | --- | --- |
| Geral: campanhas concluídas | 8/50 (16%) | 9/50 (18%) |
| Geral: Mana Ancestral | 2/18 | 3/18 |
| Geral: Forças Ancestrais | 4/17 | 4/17 |
| Geral: Rugido da Floresta | 2/15 | 2/15 |
| Foco Machados + Mana: campanhas concluídas | 1/20 | 0/20 |
| Foco: média de encontros iniciados | 19,85 | 16,80 |

Nas 50 gerais, todas as não conclusões foram mortes. No foco anterior, 19 mortes; no foco proposto, 19 mortes e **um limite técnico**, na semente 18, no terceiro encontro, turno 81, ainda com 46 HP. Esse caso não é uma morte nem prova de impossibilidade; pode refletir a política do bot e a disponibilidade das cartas. Encontros iniciados incluem o encontro em que a tentativa parou.

A matriz geral tem uma vitória a mais apesar da redução de efeitos da Mana. Mudanças na compra e na mão alteram as escolhas da busca heurística; não interpretar esse resultado pequeno como aumento real de poder. As vitórias gerais continuam concentradas em defesa/cura. O foco mostra menor avanço com a proposta, mas não isola a contribuição de cada uma das duas mudanças.

**Decisão:** manter a proposta implementada localmente como alternativa experimental, autorizada pelo usuário. Ela elimina a sequência de dois Machados com apenas oito de energia e remove os efeitos extras da Mana. Ainda exige playtest humano para verificar se a combinação ficou restritiva demais; não afirmar equilíbrio geral ou probabilidade humana a partir dessas amostras. Nenhum outro valor foi ajustado para elevar vitórias do bot.

Relatórios: `comparacao_mana_machados_antes.json` e `comparacao_mana_machados_depois.json`.

## Verificação técnica

**113 testes reexecutados em nove módulos relacionados, todos aprovados.** Consolidado incremental: 659 testes/68 módulos, reutilizando os resultados dos demais módulos. Testes confirmam Mana sem compra/limpeza, pilhas preservadas, efeitos negativos mantidos e Machados LV1/LV2 com custo cinco e dano inalterado. Smoke de interface aprovado; captura `tools/roguelite-qa/mana_machados_custo5.png` conferida. Sem alteração de schema ou migração adicional.
