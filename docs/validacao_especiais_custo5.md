# Especiais com custo de energia — 18/11/2026

Os três especiais exigem 20 de carga e **5 de energia para ativar por escolha do jogador**. Sem energia suficiente, nada é consumido e a carta continua disponível nos turnos seguintes. O pagamento não gera nova carga. Mana Ancestral paga primeiro e depois restaura a energia para 8. Demais efeitos, dano e regras de recarga foram preservados.

Custo exibido sobre a carta e no tooltip. Clique recusado não dispara o som de ativação. A legenda antiga da arte é encoberta ao renderizar, preservando o PNG original. Não houve mudança de schema de save.

## Testes

Consolidado incremental: **658 testes aprovados em 68 módulos**, com nove módulos relacionados reexecutados e os demais resultados anteriores preservados. Casos cobrem energia insuficiente nos três especiais, carga preservada entre turnos, pagamento exato, energia restante, Mana restaurando após pagamento, carga incompleta, turno incorreto e transição de chefe. Smoke de interface em saves temporários aprovado, incluindo clique sem energia e capturas com 4 e 5 de energia.

## 50 campanhas do bot

Execução: `.venv\Scripts\python.exe -B devtools/simulate_ultimate_cost.py`.

**8 vitórias em 50 runs (16%); 42 derrotas por morte.** Nenhuma foi encerrada pelo limite técnico. Vitória significa superar todos os 21 encontros, incluindo Zanzara.

| Estratégia | Concluiu | Tentativas |
| --- | --- | --- |
| Dano com Aura | 0 | 17 |
| Híbrido de defesa/cura | 8 | 17 |
| Veneno/sangramento | 0 | 16 |

| Especial | Concluiu | Tentativas |
| --- | --- | --- |
| Mana Ancestral | 2 | 18 |
| Forças Ancestrais | 4 | 17 |
| Rugido da Floresta | 2 | 15 |

Condições: 50 sementes distintas; aquisição real a partir dos starters; 60 HP; energia inicial 2; zero melhorias permanentes; cartas de cura permitidas; até três evoluções LV2 e três curas da loja por 30/45/60 ouro. Estratégias e especiais distribuídos em rodízio, sem distribuição exatamente igual. Política heurística preparada, que considera o custo real do especial ao buscar jogadas. Cada run usa um save temporário independente; nenhum save do jogador foi alterado.

Relatório completo e hashes dos arquivos executados: `simulacao_especiais_custo5_50runs.json`.

Os 16% são a taxa desta amostra do bot, não a chance de um jogador iniciante. As vitórias continuam concentradas em defesa/cura. Não é uma comparação pareada antes/depois: esta matriz inclui cartas de cura, enquanto a comparação recente de decks estritos as excluía. Portanto, não atribuir diferenças entre essas amostras somente ao custo dos especiais. Nenhum outro valor foi ajustado para melhorar a taxa do bot.
