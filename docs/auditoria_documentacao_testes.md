# Auditoria da documentação e dos testes — 23/11/2026

> Referência vigente. [Estado atual](estado_atual.md), [contrato extraído do código](contrato_atual.json)
> e [inventário de testes](inventario_testes.json).

## Escopo e decisões

Foram lidos/inventariados os 56 Markdown iniciais e todos os arquivos Python de
tests/. Os dois novos guias totalizam 58 Markdown. Referências vigentes foram
corrigidas; relatórios de simulações, prompts e etapas antigas foram marcados
históricos sem adulterar resultados medidos. Custos de cinco no histórico não
são regras vigentes; Machados Gêmeos continua legitimamente custando cinco.

Correções principais: cura20/preços30-45-60/limite3 (não HP máximo);
saves v14 e fim de run/snapshot; ultimates2 com efeitos atuais; baralho6–18;
catálogo de 20 LV1/LV2 e 75 bloqueadas; duas lutas por bioma; UI ilustrada e
preview de intenção central; famílias de animação mistas e Jozephino distinto
do Boss6 externo de Labrro. Nenhuma regra de jogo foi alterada nesta auditoria.

## Resumo por Markdown

| Arquivo | Natureza | Revisão |
|---|---|---|
| [AGENTS.md](../AGENTS.md) | Vigente | Convenções vigentes reescritas; remove regras conflitantes e caminhos específicos de outro computador. |
| [README.md](../README.md) | Vigente | UI/arte atuais, cura/preços, deck mínimo, morte/run/snapshot, epílogo, pastas e executor isolado. |
| [assets/audio/README.md](../assets/audio/README.md) | Vigente | Remove aviso de áudio ausente; trilha, IDs, canais, volumes e fontes ativos. |
| [docs/alvaro_tex.md](alvaro_tex.md) | Vigente | Duas fases, fumaça de cura/buff, ações12/idle8 e retomada por snapshot. |
| [docs/alvaro_tex_audio_fase1.md](alvaro_tex_audio_fase1.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/alvaro_tex_audio_fase2.md](alvaro_tex_audio_fase2.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/animacoes_ultimates.md](animacoes_ultimates.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/audio_mix_review.md](audio_mix_review.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/audio_polimento_final.md](audio_polimento_final.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/auditoria_documentacao_testes.md](auditoria_documentacao_testes.md) | Vigente | Novo índice completo por documento, cobertura dos testes, comandos e resultado da auditoria. |
| [docs/bestiario_e_biomas.md](bestiario_e_biomas.md) | Vigente | 14 tipos, dois por bioma, duas lutas; Viniurgo e nomes atuais dos chefes. |
| [docs/boss_twelve_frames.md](boss_twelve_frames.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/boss_ultimate_eight_effects.md](boss_ultimate_eight_effects.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/boss_ultimates_e_ruinas.md](boss_ultimates_e_ruinas.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/bosses_oito_frames.md](bosses_oito_frames.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/bosses_spritesheets_oito.md](bosses_spritesheets_oito.md) | Vigente | Cadência distinta de Jan-Pietro, fontes8 e reação segura em560 ms. |
| [docs/carrasco_audio_piloto.md](carrasco_audio_piloto.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/carrasco_da_vigilia.md](carrasco_da_vigilia.md) | Vigente | Labrro: HP140, danos/buff reais, folhas4×2; preserva prompt do cenário. |
| [docs/cartas_e_estados.md](cartas_e_estados.md) | Vigente | Tabela real dos 20 tipos LV1/LV2, 75 bloqueadas, stacks, dispel e evolução. |
| [docs/cartas_packs_lv1_lv2.md](cartas_packs_lv1_lv2.md) | Vigente | Renderização real da cópia na Mochila, em vez de coleção sempre LV1. |
| [docs/cartas_ultimate_lv2.md](cartas_ultimate_lv2.md) | Vigente | Referência conferida; vínculo canônico e validações datadas distinguidas. |
| [docs/common_eight_frames.md](common_eight_frames.md) | Vigente | 14 comuns/56 grupos/448 fontes, reação filtrada e fase de voo. |
| [docs/comparacao_decks_sem_cura.md](comparacao_decks_sem_cura.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/comparacao_main_etapa3.md](comparacao_main_etapa3.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/comparacao_mana_machados.md](comparacao_mana_machados.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/corpo_seco_audio_piloto.md](corpo_seco_audio_piloto.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/diagnostico_balanceamento_roguelite.md](diagnostico_balanceamento_roguelite.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/estado_atual.md](estado_atual.md) | Vigente | Nova referência canônica com regras, UI, famílias de animação e comandos atuais. |
| [docs/etapa3_audio_validacao_final.md](etapa3_audio_validacao_final.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/etapa4_trilha_sonora.md](etapa4_trilha_sonora.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/fechamento_balanceamento_roguelite.md](fechamento_balanceamento_roguelite.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/goblin_nerd_audio_piloto.md](goblin_nerd_audio_piloto.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/gordofera.md](gordofera.md) | Vigente | Sir Thomas: nome, Sangramento por stacks, ações12/idle8 e valores da fábrica. |
| [docs/gordofera_audio_piloto.md](gordofera_audio_piloto.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/guardiao_audio_piloto.md](guardiao_audio_piloto.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/guardiao_e_biomas.md](guardiao_e_biomas.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/implementacao_balanceamento_roguelite.md](implementacao_balanceamento_roguelite.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/intencoes_dos_inimigos.md](intencoes_dos_inimigos.md) | Vigente | Duas ações de chefe; carta inteira em x central/y43%, sem painel lateral. |
| [docs/jan_pietro_alinhamento.md](jan_pietro_alinhamento.md) | Vigente | Distingue idle já preparado do registro/filtro global de dano. |
| [docs/laboratorio_de_testes.md](laboratorio_de_testes.md) | Vigente | 14 encontros, mínimo seis, 75 bloqueadas, ultimates e isolamento dos saves. |
| [docs/loja_altar_visual.md](loja_altar_visual.md) | Vigente | Cura30/45/60, materiais15, limite3 evoluções e padding/custo único. |
| [docs/mapa_e_encontros.md](mapa_e_encontros.md) | Vigente | Revanche sem drops, cura pós-chefe, snapshot/run e epílogo. |
| [docs/mochila_e_ultimates.md](mochila_e_ultimates.md) | Vigente | Mínimo seis, rascunho, filtros, preview, cartas douradas, custo 2 e sem herança de carga. |
| [docs/mochila_visual.md](mochila_visual.md) | Vigente | Referência conferida; vínculo canônico e validações datadas distinguidas. |
| [docs/player_twelve_frames.md](player_twelve_frames.md) | Vigente | Referência conferida; vínculo canônico e validações datadas distinguidas. |
| [docs/playtest_balanceamento_grupo.md](playtest_balanceamento_grupo.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/playtest_refino_cartas.md](playtest_refino_cartas.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/pr_audio_final.md](pr_audio_final.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/prompts_ultimates_v2.md](prompts_ultimates_v2.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/protagonista_oito_frames.md](protagonista_oito_frames.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/reacoes_dano.md](reacoes_dano.md) | Vigente | Referência conferida; vínculo canônico e validações datadas distinguidas. |
| [docs/resultado_decks_dano_hibrido_defesa.md](resultado_decks_dano_hibrido_defesa.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/resultado_decks_variados_100.md](resultado_decks_variados_100.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/retratos_personagens.md](retratos_personagens.md) | Vigente | Referência conferida; vínculo canônico e validações datadas distinguidas. |
| [docs/revisao_cartas_balanceamento.md](revisao_cartas_balanceamento.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/validacao_cura_progressiva.md](validacao_cura_progressiva.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/validacao_especiais_custo5.md](validacao_especiais_custo5.md) | Histórico | Marcado histórico; preserva resultados, prompts e fontes sem tratar regras/caminhos antigos como vigentes. |
| [docs/zanzara.md](zanzara.md) | Vigente | Necromante atual; HP175, kit e efeitos reais, renderizador e epílogo. |

## Suíte de testes e cobertura

O inventário inclui todos os arquivos .py de tests/, seus módulos, classes e
métodos de teste. unittest conta um método por caso, independentemente dos
subtests usados para percorrer cartas, níveis ou personagens.

| Área | Cobertura localizada |
|---|---|
| Ultimate custo/efeitos/energia/carga | test_ultimates, test_ultimate_cards_lv2, test_backpack_ultimates |
| Arte LV1/LV2, losango e cache | test_player_card_art, test_merchant_workshop, test_backpack_visual |
| Evolução individual e rollback | test_roguelite, test_merchant_workshop |
| Loja, cura/preços/limites e persistência | test_shop_and_combat_reset, test_card_collection_pages |
| Deck, mínimo/máximo, rascunho e saves | test_deck_slots, test_deck_clear_and_minimum, test_deck_draft_persistence |
| Sprites/idle/dano | test_boss_sheet_update, test_jan_pietro_stance, test_enemy_reactions |
| Intenções/preview central | test_enemy_intents |
| Vínculo código→documentação | test_documentation_contract |

### Testes criados/atualizados nesta auditoria

- **test_documentation_contract.py (novo):** nove regressões de inventário
  Markdown, links locais, catálogo LV1/LV2, ultimates, economia/deck/save,
  estados/campanha, famílias/IDs, inventário de testes e marcação histórica.
- **test_ultimate_cards_lv2.py:** caso novo para as três ultimates com energia
  exatamente dois, consumo único de carga e recusa de segunda ativação sem
  recarregar, preservando efeitos.
- **test_merchant_workshop.py:** evolução→gravação→reabertura→Mochila/Altar
  usando a cópia LV2 real, enquanto a oferta da Loja continua LV1.

As expectativas de custo2 já estavam corretas nos testes atuais; não foi
necessário substituir valores legítimos de outras cartas. As regressões de
dano e de Zanzara/BossTwelveFrames da tarefa anterior foram preservadas e
incluídas nesta execução completa.

## Reprodução e resultado

~~~powershell
python -B devtools/audit_project_docs.py --output docs/auditoria_documentacao.json
python -B devtools/validate_isolated_tests.py --report docs/validacao_auditoria_documentacao.json
~~~

Executor unittest por módulos isolados, sem janelas, configurando os drivers SDL
dummy. Relatório da execução completa em
[validacao_auditoria_documentacao.json](validacao_auditoria_documentacao.json).
Resume/recheck não devem ser descritos como uma nova execução integral.
A auditoria estática registra documentos/hashes, links e inventário em
[auditoria_documentacao.json](auditoria_documentacao.json).

Execução integral nova, sem retomada: **77 módulos, 732 testes, zero falhas**,
em 182,24 segundos. Saída final do executor:

~~~text
Concluído: 732 testes, 0 módulos com falha.
~~~

Os 58 documentos foram classificados (25 vigentes e 33 históricos). Os
relatórios históricos preservam seus resultados e apontam explicitamente
para as regras vigentes. A auditoria estática também verifica os links locais.
