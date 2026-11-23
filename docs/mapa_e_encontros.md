# Mapa e encontros

> Referência vigente — auditoria de 23/11/2026. [Estado atual](estado_atual.md). Relatos de validações datadas abaixo representam somente aquela execução.

Campanha linear de sete territórios, dois encontros comuns antes de cada chefe.
Chefe concluído libera a próxima região. Fontes: territory_map.py,
campaign_progress.py, combat_engine.py e save_manager.py.

Repetir encontro concluído é revanche: não dá ouro, carta ou material, nem avança
a rota novamente. Recompensas inéditas têm registro idempotente por run/encontro.
Na vitória, escolher tipo ainda não adquirido ou material conforme as regras;
cartas entram na coleção, não automaticamente no deck equipado.

Vida atual persiste. Vitória inédita sobre chefe recupera 30% da vida máxima,
limitada ao teto. Loja cura HP atual. Ultimate começa com carga zero em cada
nova batalha. A dupla passa para Tekks na mesma luta, sem recompensa intermediária.

Saves v14 podem retomar combate vivo por snapshot. Derrota encerra a run; nova
jornada refaz temporários e mantém perfil/fragmentos. Vitória final abre epílogo,
retornando depois ao mapa. No laboratório, pode ser revisto.
[Distribuição dos biomas](bestiario_e_biomas.md) · [Estado atual](estado_atual.md).
