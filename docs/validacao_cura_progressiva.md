# Cura progressiva da loja — 17/11/2026

> **Registro histórico — não é especificação vigente.** Valores, caminhos, comandos e resultados abaixo pertencem à etapa original. Não restaurar regras/arte antigas nem executar preparadores sobre kits atuais. Consulte o [estado atual](estado_atual.md).

Implementada na branch `feature/balanceamento-roguelite`, sem commit, push ou merge.

## Regra aprovada

- Até três compras por run, por **30, 45 e 60 ouro**, respectivamente.
- Cada compra recupera até **20 de vida atual**, limitada à vida máxima.
- Vida cheia, saldo insuficiente e falha ao gravar não cobram nem consomem uma compra.
- A quarta compra fica bloqueada mesmo depois de receber mais dano.
- Contador e próximo preço persistem ao reabrir o save; uma nova run zera o contador.
- Aumento permanente de vida máxima continua separado, com fragmentos.

O save passa à versão 14. Saves v13 recebem contador zero porque a versão anterior não registrava quantas curas tinham sido compradas. HP, ouro e perfil são preservados; o original fica em `.v13.bak`. A migração não tenta deduzir gastos antigos.

## Verificação

Testes direcionados cobrem preços, limite, cura parcial, vida cheia, saldo insuficiente, rollback de gravação, reload, isolamento entre slots, nova run e migração v13. A validação consolidada reúne **656 testes aprovados em 68 módulos**, em `validacao_balanceamento_por_modulo.json`; 26 módulos relacionados a saves e loja foram executados novamente, reutilizando os resultados anteriores dos demais módulos.

O smoke de interface passou com saves temporários. As imagens da segunda e terceira ofertas e da oferta esgotada foram conferidas em `tools/roguelite-qa/`. Nenhum save real foi usado nas simulações ou no preview.

## Efeito observado no bot

Nova amostra: 420 tentativas de campanha, sete decks, três configurações de Ultimate, dois modos de aquisição e duas políticas do bot. Cada grupo contém cinco sementes por política: dez casos, não dez sementes independentes. Todos os decks desta comparação excluem cartas de cura; as evoluções LV2 ficam limitadas a três por run.

| Deck e Ultimate | Modo | Cura ilimitada a 30 ouro (histórico) | Três curas a 30/45/60 ouro |
| --- | --- | --- | --- |
| Híbrido/controle + Mana Ancestral | Aquisição real | 5/10 | 0/10 |
| Defesa/controle + Rugido da Floresta | Aquisição real | 8/10 | 4/10 |
| Defesa/controle + Rugido da Floresta | Deck pronto desde o início | 7/10 | 2/10 |

Na amostra nova, os outros grupos não completaram campanhas. Isso inclui dano puro direto e dano por efeitos. Deck exclusivamente defensivo sem uma fonte ofensiva tem casos encerrados por ausência de via de dano; esses casos não representam mortes jogadas até o fim.

O limite aumenta a dificuldade e reduz a recuperação disponível. Os resultados sugerem que o equilíbrio entre estratégias ainda precisa de avaliação; não demonstram impossibilidade para um jogador humano. Nenhum outro valor de combate foi ajustado para compensar essa mudança.

Relatórios brutos:

- `comparacao_decks_cura_limitada_sem_ultimate.json`
- `comparacao_decks_cura_limitada_mana.json`
- `comparacao_decks_cura_limitada_rugido.json`

O resumo `comparacao_decks_sem_cura.md` distingue a regra histórica ilimitada da regra atual limitada.
