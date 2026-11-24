# Cem runs com decks variados — 18/11/2026

> **Registro histórico — não é especificação vigente.** Valores, caminhos, comandos e resultados abaixo pertencem à etapa original. Não restaurar regras/arte antigas nem executar preparadores sobre kits atuais. Consulte o [estado atual](estado_atual.md).

> Registro histórico da alternativa sem limpeza. Depois desta amostra, o usuário aprovou Mana restaurando energia **e limpando efeitos negativos**, sem compra de cartas. A taxa abaixo não mede essa revisão posterior.

**11 campanhas completas, 89 mortes e nenhum limite técnico atingido. Taxa do bot nesta matriz: 11%.** Todas as vitórias passaram pelos 21 encontros, incluindo Zanzara, sem morrer na run. Isso não estima a chance de um jogador iniciante vencer.

## Condições

- Dez planos de deck, dez tentativas por plano, sementes distintas 1000–1099.
- Começo real com starters; compras, recompensas e materiais adquiridos durante a run. O plano indica prioridades, não um deck concedido pronto.
- 60 HP, energia inicial 2 e zero melhorias permanentes; perfil independente em cada tentativa.
- Até três evoluções LV2 e três curas da loja por 30/45/60 ouro. Cura normal após chefe preservada.
- Três especiais em rodízio: 34 Mana Ancestral, 33 Forças Ancestrais, 33 Rugido da Floresta; cada deck recebeu três ou quatro casos de cada especial.
- Proposta local atual: Machados custa cinco, dano 40/50; Mana somente restaura energia para oito, sem comprar cartas ou limpar efeitos. Especiais exigem 20 de carga e cinco de energia.
- Mesma política heurística preparada, sem alterações de regras do jogo nesta rodada. Limite de segurança de 400 passos por encontro, não atingido nas cem tentativas.

Os planos cobrem os **20 tipos disponíveis**, mas não enumeram todas as combinações de cartas, níveis e aquisição. Não se presume que todos os tipos do plano tenham sido comprados antes da derrota. Os dez estilos têm peso igual na amostra; isso não representa a frequência de escolhas de pessoas. Resultados anteriores com outros decks/sementes não são comparação pareada com esta matriz.

## Resultados por plano

| Plano | Campanhas completas |
| --- | --- |
| Dano com Aura | 0/10 |
| Híbrido de defesa/cura | 4/10 |
| Veneno + sangramento | 0/10 |
| Híbrido com Machados | 0/10 |
| Dano direto | 0/10 |
| Arco com controle e limpeza, sem cartas de cura | 0/10 |
| Fogo híbrido | 0/10 |
| Veneno híbrido | 0/10 |
| Sangramento híbrido | 0/10 |
| Sustentação com Máscara Ancestral | 7/10 |

O plano de Máscara inclui dois exemplares da Máscara, três Arcos, três Protetoras, um Totem, um Surto de Energia, uma Purificadora e duas curas. O híbrido de defesa/cura usa Arcos, curas, Escudo, Protetoras, Aura e limpeza. Ambos dependem de adquirir os tipos durante a campanha.

| Especial | Campanhas completas |
| --- | --- |
| Mana Ancestral | 4/34 |
| Forças Ancestrais | 4/33 |
| Rugido da Floresta | 3/33 |

Os números por especial misturam decks e sementes diferentes; não servem para ordenar o poder dos especiais.

Das 89 mortes, 4 ocorreram no território 2, 28 no 3, 13 no 4, 11 no 5, 14 no 6 e 19 no último combate da campanha. Esses valores indicam onde a tentativa terminou, não uma taxa de mortalidade condicional de cada chefe. O terceiro território e a sustentação entre lutas merecem atenção no playtest humano.

## Interpretação

A campanha permanece exigente para esta política. As vitórias concentraram-se em dois planos com recuperação de vida e proteção; esta amostra não demonstra diversidade de estratégias vencedoras. O bot pode planejar mal certos efeitos e composições, portanto zero vitórias em dez tentativas não prova impossibilidade humana.

O plano de sustentação com Máscara merece ser observado pelo grupo: 7/10 sugere uma rota consistente para o bot, sem demonstrar sozinho que a carta está forte demais. A amostra não reproduz o deck exato dos amigos nem o aprendizado de um iniciante. Não ajustar automaticamente o jogo para atingir uma porcentagem de vitórias do bot.

Para medir sucesso na primeira experiência humana, registrar a primeira tentativa de cada pessoa em perfil novo, separada das seguintes e das tentativas com dicas. A taxa agregada de 11% não deve ser apresentada como probabilidade de vitória de uma pessoa.

## Reprodução e verificação

```powershell
.\.venv\Scripts\python.exe -B devtools/simulate_diverse_100.py --check
.\.venv\Scripts\python.exe -B devtools/simulate_diverse_100.py
```

Matriz validada para limites de cópias/espaços e cobertura do catálogo. Relatório completo com planos, encontros e hashes: `simulacao_decks_variados_100.json`. Todos os saves usados foram temporários. Nove testes dos especiais foram reexecutados e aprovados, concluindo a checagem interrompida na rodada anterior; o consolidado incremental existente continua em 659 testes/68 módulos. Não foi necessário repetir a suíte completa para adicionar apenas a matriz de simulação e documentação.

Mudanças locais; sem commit, push, merge ou atualização da PR #24 nesta rodada. A PR ainda não contém a proposta nova de Mana/Machados.
