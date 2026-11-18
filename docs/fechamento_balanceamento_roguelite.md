# Fechamento técnico e roteiro de avaliação

> Atualização posterior: a comparação estrita encontrou campanhas sem cartas de cura. Ver [resultado de dano/híbrido/defesa](resultado_decks_dano_hibrido_defesa.md). As taxas da matriz inicial abaixo continuam como registro histórico, não como conclusão de que cura em cartas seja obrigatória.

Branch: `feature/balanceamento-roguelite`. Esta rodada melhora a ferramenta de avaliação e a documentação; **não altera valores, regras, arte ou áudio do jogo**. Sprite do fragmento permanece uma entrega externa e não bloqueia o trabalho abaixo.

## O que foi corrigido na avaliação

- O bot passou a dosar cópias de suporte, em vez de preencher três de cada tipo indiscriminadamente em uma mão persistente.
- Usa a cura da loja pagando ouro real; não recebe cura gratuita nem atributos permanentes artificiais.
- Considera limpeza e energia perdida na avaliação da rodada. Compra de um tipo inacessível não impede avaliar outras compras possíveis.
- Com LV2 habilitado, escolhe materiais direcionados, compra os faltantes e paga a evolução conforme as regras reais. Cópias que ficarão fora do deck não são alvos de evolução.
- Ultimate passa a integrar a sequência de ações. Isso permite gastar energia antes de usar Mana Ancestral, em vez de desperdiçar sua restauração automaticamente no início do turno.
- A exploração de ações do bot não consome os sorteios futuros do jogo. Quatro testes específicos validam montagem, pagamento, alvos de upgrade e preservação do estado aleatório.
- O runner de testes agora encerra corretamente o relatório mesmo quando o último módulo é reaproveitado por `--resume`.

## Comparação consolidada

60 campanhas: três estratégias, cinco sementes por estratégia, quatro configurações. Todas com perfil sem melhorias permanentes e sem vida máxima temporária; preparação e transações usam saves temporários. Os quatro relatórios têm o mesmo hash de código do bot (`db7dcd0b4e1b…`).

| Configuração | Dano/Aura | Defesa/cura | Veneno/Sangramento |
|---|---:|---:|---:|
| LV1, Forças Ancestrais, cura da loja | 0/5 | 3/5 | 0/5 |
| Até três LV2, Forças Ancestrais, cura da loja | 0/5 | 2/5 | 0/5 |
| Até três LV2, Mana Ancestral, cura da loja | 0/5 | 4/5 | 0/5 |
| Até três LV2, Rugido da Floresta, cura da loja | 0/5 | 1/5 | 0/5 |

Relatórios detalham deck, compras, evoluções, vida de entrada/saída, turno, ouro e recompensa por encontro:

- [LV1 / Forças](simulacao_balanceamento_preparado.json)
- [LV2 / Forças](simulacao_balanceamento_evolucoes.json)
- [LV2 / Mana](simulacao_balanceamento_mana.json)
- [LV2 / Rugido](simulacao_balanceamento_rugido.json)

**Conclusão permitida:** defesa/cura tem campanhas completas reproduzíveis sem melhoria permanente. As demais políticas chegaram mais longe em alguns casos, inclusive ao confronto final, mas não completaram nesta amostra. Ainda não há evidência suficiente de diversidade de estratégias vencedoras.

**Conclusões que a amostra não permite:** afirmar que LV2 piora o jogo, que Mana é universalmente superior ou que dano/efeitos são impossíveis para pessoas. São apenas cinco sementes por configuração; decisões de compra, embaralhamento e combate mudam trajetórias e consumo de sorteios. O bot usa uma busca curta e decks predefinidos, sem explorar todas as cartas, a troca de Ultimate entre encontros ou todas as decisões de Cemitério. Não ajustar números apenas para elevar a taxa deste bot.

## Pontos de balanceamento a conferir no jogo

1. **Jozephino:** duas aplicações de Choque podem reduzir o próximo turno de três para uma energia. Purificadora não devolve energia que o Choque já retirou na abertura do turno; ela continua útil contra Veneno e demais negativos presentes. Não apresentar limpeza como resposta retroativa ao Choque. Verificar se o plano anunciado oferece decisão útil com a mão real.
2. **Labrro e Zanzara:** registrar se a derrota ocorre por falta de defesa/sustentação ou por sequência sem resposta razoável, considerando buffs e debuffs. Intenção perigosa não prova que a resposta seja acessível.
3. **Dependência de cura:** comparar uma cópia adicional de cura contra dano/controle e observar se prolongar lutas para curar vira a única estratégia econômica.
4. **Evoluções:** observar quanto benefício é percebido na cópia escolhida e em que território a primeira/terceira evolução aparece. Não avaliar apenas o número de upgrades comprados; conferir quantos estão equipados.

Nenhum ajuste adicional de dano, stacks, custo ou padrão de chefe foi feito nesta rodada. Os valores atuais continuam experimentais até essas verificações.

## Roteiro curto para avaliação humana

Usar uma única instância do `main.py`. Não apagar nem sobrescrever jornadas para executar este roteiro; para testar dificuldade de base, usar um slot sem melhorias permanentes. Laboratório serve para conferir apresentação, mas sua invulnerabilidade não mede balanceamento.

| Caso | Ação | Resultado esperado |
|---|---|---|
| Loja | Com vida faltante, comprar cura; depois conferir a compra com vida cheia | Recupera até 20 por 30 ouro, máximo não aumenta; cheia não cobra |
| Evolução | Ter três materiais extras e ouro; escolher uma cópia | Só aquela vira LV2; três materiais e ouro saem; outras cópias preservadas |
| Mochila | Retirar e recolocar uma LV2 | Nível preservado, sem material novo nem liberação de uma quarta evolução |
| Continuação | Anotar mão/HP/energia e intenções, sair vivo e retomar | Mesmo estado lógico; sem nova mão, inimigo curado ou novo sorteio de intenção |
| Chefes | Conferir saldo antes/depois da primeira vitória | Fragmentos sobem uma vez; nova confirmação/revanche não duplica |
| Próxima derrota normal | Abrir preparação e iniciar outra run | Recursos temporários reiniciam; fragmentos/melhorias e tutorial permanecem |
| Dificuldade | Registrar chefe, mão, intenção e decisão no turno crítico | Distinguir erro compreensível de falta de resposta viável |

A leitura do painel e a sensação de combate dependem dessa avaliação humana. Não há campanha completa jogada por uma pessoa nesta sessão, nem escuta crítica de áudio.

## Estado para entrega

- Implementação funcional, compra de cura, LV1/LV2, saves e evolução individual disponíveis.
- Consolidação incremental atual: **643 testes aprovados em 67 módulos**, incluindo quatro novos testes do simulador e os testes atualizados da loja. Não é uma nova execução integral de todos os módulos; aprovações anteriores foram preservadas e módulos afetados foram repetidos.
- Relatório: [validação por módulo](validacao_balanceamento_por_modulo.json).
- Pendente interna: playtest focado e eventual rodada de ajustes de balanceamento com evidência dos turnos críticos.
- Dependência externa: sprite do fragmento. Lógica e indicação textual já existem; não bloquear a validação por falta desse recurso.
- Commit/PR/publicação/merge ainda não realizados. Preparação de descrição e organização pode avançar, mas publicar ou integrar depende de autorização.

Reproduzir uma configuração atual:

```powershell
.\.venv\Scripts\python.exe -B devtools/simulate_roguelite_balance.py --seeds 5 --upgrades --ultimate mana_ancestral --report docs/simulacao_balanceamento_mana.json
```
