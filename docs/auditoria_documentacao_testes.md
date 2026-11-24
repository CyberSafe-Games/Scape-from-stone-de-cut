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
| [docs/build_windows.md](build_windows.md) | Vigente | Preserva build PyInstaller/Inno Setup, instalação e dados locais do executável recebidos na PR #29. |
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

## Integração das PRs #29/#30 — 24/11/2026

O bloqueio da PR #28 vinha de quatro conflitos em README.md, AGENTS.md,
assets/audio/README.md e docs/cartas_e_estados.md. A conciliação mantém a
auditoria e as reações de dano, o instalador, o altar de espólios, as derrotas
e os áudios da main. O guia docs/build_windows.md foi incorporado ao manifesto
de documentação vigente, totalizando 59 documentos.

A regra integrada de Sangramento passou a uma ativação após o primeiro ataque
do turno, mesmo absorvido; debuffs de impacto exigem perda de vida. Essas
alterações da main estão refletidas no contrato e nos guias, sem reverter as
regras trazidas pelo grupo. O primeiro território se chama Stone de Cut.

Nova validação da versão combinada em
[validacao_integracao_pr28.json](validacao_integracao_pr28.json).

Resultado da integração: **753 testes em 79 módulos, zero falhas**,
execução integral nova em 175.32 segundos.

~~~text
Concluído: 753 testes, 0 módulos com falha.
~~~

## HUD e tutoriais de gerenciamento — 24/11/2026

Base conferida antes de editar: main 00b0078, com PRs #28/#29/#30 integradas,
git status limpo e os dez commits recentes revisados. Preservados instalador,
áudio, derrotas, altar de espólios e regras atuais de combate.

Implementação: MENU central e painéis de vida simétricos; molduras externas
compartilhadas com cantos proporcionais; guias independentes de Loja, Mochila
e Altar. Schema v15 e flags permanentes por slot com migração, rollback e
reabertura manual. README, AGENTS e guias vigentes atualizados. Nenhum PNG
aprovado foi substituído, portanto não há asset obsoleto novo para arquivar.

Testes novos em test_management_guides: primeira visita, migração v14→v15,
persistência entre runs/slots, captura de cliques e mouse escalado, rollback,
layout dos passos e geometria das molduras/HUD. Fixtures dos testes de fluxos
anteriores indicam guias já vistos, preservando suas asserções de negócio.

Resultado integral novo: **764 testes em 80 módulos, zero falhas**,
em 181.13 segundos. [Relatório completo](validacao_guias_hud.json).
Preview dos dez passos e das três telas, além do combate em 1920×1080 e
1280×720, renderizado por preview_management_guides.py com saves temporários.
Conferência de imagens não equivale a jogar uma campanha completa.

~~~text
Concluído: 764 testes, 0 módulos com falha.
~~~

## Retratos comuns e Santuário dos Ajustes — 24/11/2026

Preservada integralmente a etapa local anterior de HUD/guias. Os comuns usam
agora a moldura do protagonista pelo mesmo compositor de Zanzara, com faces
originais e fallback de sprites. A moldura anterior foi removida do loader;
a batalha não depende mais daquele asset para habilitar a HUD.

Configurações e pausa usam pedra/pergaminho e ouro, cenário ilustrado próprio,
controles texturizados e realce rúnico. Preferências, defaults e aplicação
imediata são mantidos. Retorno direto fecha Opções+pausa sem recriar a batalha;
consulta dos guias não altera o slot. Saída pede confirmação e preserva o
save, impedindo falhas de gravação e recompensas/transições pendentes.

Nova arte por image_gen integrado: prompt completo em
[opcoes_arte_prompt.txt](opcoes_arte_prompt.txt), hash e procedência no
[manifesto da arte](../assets/ui/options/art_manifest.json). Previews das
quatro abas, biblioteca, pausa, HUD e 14 retratos usam somente dados temporários.
Conferência das imagens não equivale a jogar uma campanha completa.

### Arquivos desta etapa (além das mudanças locais da etapa anterior)

| Situação | Arquivo |
|---|---|
| Criado | assets/ui/options/sanctuary_background.png |
| Criado | assets/ui/options/art_manifest.json |
| Criado | src/ui/options_sanctuary_view.py |
| Criado | src/scenes/guide_library_scene.py |
| Criado | devtools/preview_options_sanctuary.py |
| Criado | tests/test_options_sanctuary.py |
| Criado | docs/opcoes_arte_prompt.txt |
| Criado | docs/validacao_opcoes_retratos.json |
| Alterado | src/core/asset_manager.py |
| Alterado | src/systems/character_portraits.py |
| Alterado | src/ui/battle_hud.py |
| Alterado | src/scenes/battle_scene.py |
| Alterado | src/scenes/options_scene.py |
| Alterado | src/scenes/pause_menu_modal.py |
| Alterado | src/config/options_layout.py |
| Alterado | tests/test_character_portraits.py |
| Alterado | tests/test_options_menu.py |
| Alterado | tests/test_audio_options.py |
| Alterado | README.md |
| Alterado | AGENTS.md |
| Alterado | docs/estado_atual.md |
| Alterado | docs/retratos_personagens.md |
| Alterado | docs/auditoria_documentacao_testes.md |
| Alterado | docs/auditoria_documentacao.json |
| Alterado | docs/inventario_testes.json |
| Arquivado, fora do Git | assets/ui/hud_portrait.png → _arquivos_antigos_para_deletar/assets/ui/hud_portrait.png |

### Validação

**773 testes em 81 módulos, zero falhas no resultado consolidado.** A execução
integral encontrou somente uma fixture antiga de áudio sem o novo serviço de
assets; após corrigi-la, os sete testes desse módulo foram repetidos e passaram.
O relatório final marca retomado=true: não é anunciado como nova execução
integral. [Resultado completo](validacao_opcoes_retratos.json).

~~~text
6/81 tests.test_audio_options: OK (7 tests)
Concluído: 773 testes, 0 módulos com falha.
~~~

Testes dedicados cobrem bordas pixel-idênticas nos 14 comuns, cache, quatro
abas, sliders com mouse escalado, preferências, falha de gravação, pilha modal,
consulta dos guias, saída confirmada e proteção de recompensas pendentes.

## Auditoria de enquadramento dos retratos — 24/11/2026

A composição anterior usava cover e crop percentual único, causando perdas
nas laterais; Slime/Macaco vinham de recortes do idle. Agora os 14 dos biomas
usam recortes individuais, framed-contain e margem interna. O gerador comum
legado registra também Goblin/Guarda Sombrio: ambos foram incluídos, totalizando
16 tipos comuns. Artes/composição de chefes e minibosses ficam preservadas.

Recriados: Slime, Macaco Selvagem, Goblin e Guarda Sombrio, em
assets/portraits/source/dedicated/. Prompts completos, ferramenta integrada e
hashes em [art_manifest.json](../assets/portraits/source/dedicated/art_manifest.json).
Reenquadrados: Viniurgo, Guerreiro da Mata, Golem das Ruínas, Lagarto Couraçado,
Putrefato do Pântano, Crocodilo Abissal, Esqueleto Saqueador, Morcego Sombrio,
Centauro Vigia, Lutador Mascarado, Vinimuth e Mago do Santuário.

Não havia retratos dedicados antigos dos quatro novos para arquivar. Os onze
PNGs fornecidos continuam em uso; sprites de Slime/Macaco continuam ativos no
combate e foram preservados. Nenhuma animação foi removida nesta correção.

### Arquivos

- Criados: dedicated/slime.png, dedicated/macaco_selvagem.png,
  dedicated/goblin.png, dedicated/guarda_sombrio.png e art_manifest.json na
  pasta assets/portraits/source/; docs/validacao_enquadramento_retratos.json.
- Alterados: src/core/asset_manager.py, src/systems/character_portraits.py,
  tests/test_character_portraits.py e devtools/preview_options_sanctuary.py.
- Documentação/inventário: README.md, AGENTS.md, docs/retratos_personagens.md,
  docs/estado_atual.md, docs/inventario_testes.json, este relatório e a
  auditoria estática docs/auditoria_documentacao.json.

### Validação

**776 testes em 81 módulos, zero falhas**, execução completa sem retomada.
Após registrar os dois tipos comuns legados, houve rechecagem de retratos e
contrato documental: **16 testes aprovados**. O [relatório](validacao_enquadramento_retratos.json)
registra ambas as etapas sem confundir a rechecagem com nova execução integral.

Testes garantem bordas pixel-idênticas, cobertura de ambos os catálogos,
carregamento de todas as fontes sem fallback para sprites e preservação de
quatro cantos em artes altas/largas/quadradas. Previews de todos os comuns
foram conferidos na HUD de 1920×1080 e na redução 1280×720. Esta conferência
visual de retratos não equivale a jogar uma campanha completa.

## Fechamento e publicação das melhorias de UI — 24/11/2026

O canal de HP agora usa a abertura real da arte com águias, sem os antigos
insets de 18%/64%. Máscara e moldura usam a mesma escala em faixas; o vermelho
fica restrito à abertura, ocupa as duas pontas em HP máximo e diminui em
proporção exata da largura. A correção vale para jogador, comuns e chefes.

Configuração: src/config/combat_header.py. Renderização compartilhada:
BattleHUD.health_window/health_bar em src/ui/battle_hud.py. Novo módulo de
teste: tests/test_health_bar.py, com cinco casos para HP máximo/parcial/zero,
limites, ausência da arte, simetria e preservação dos ornamentos.

Preview: Jaum Manel e Alvar/Tekks em 60/60–76/76, 30/60–38/76 e 0/60–0/76,
conferidos em 1920 pixels e na redução 1280. Não houve edição do PNG da barra.

Fechamento do conjunto acumulado: HUD/MENU, molduras, guias, saves v15,
Santuário dos Ajustes, biblioteca de tutoriais e retratos dos 16 comuns.
Fontes aprovadas foram preservadas e a pasta de descarte permanece fora do Git.

**Execução integral nova: 781 testes em 82 módulos, zero falhas**,
em 183.13 segundos, sem retomada. [Relatório final](validacao_ui_final.json).

~~~text
Concluído: 781 testes, 0 módulos com falha.
~~~
