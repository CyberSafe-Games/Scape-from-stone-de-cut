# AGENTS.md — Scape From Stone de Cut

> Referência vigente — auditoria de 23/11/2026. [Estado atual](docs/estado_atual.md). Relatos de validações datadas abaixo representam somente aquela execução.

Referência vigente, auditada em 23/11/2026 contra o código. Regras completas:
[estado atual](docs/estado_atual.md), [catálogo LV1/LV2](docs/cartas_e_estados.md)
e [auditoria de documentação/testes](docs/auditoria_documentacao_testes.md).
Relatórios marcados como históricos registram etapas anteriores; não definem
custos, caminhos ou comportamento atual.

## 1. Projeto e ambiente

Roguelite/deckbuilder por turnos em Python 3.12+ e Pygame. Textos, comentários e
documentação em pt-BR; código em inglês e indentação de quatro espaços.
Jaum Manel defende a tribo Stone The Cut do Clã Moskar. Interface dark fantasy
rústica, pixel art, verde-musgo, couro/madeira/pedra e ouro envelhecido.

- Trabalhe no checkout ativo confirmado pelo usuário. Não imponha caminhos
  absolutos de computadores de outros integrantes nem versões locais de Python.
- Dependências de execução: requirements.txt (pygame>=2.6.0). Pillow e NumPy
  são dependências de desenvolvimento em requirements-dev.txt.
- Canvas interno 1920×1080, janela inicial 1280×720, 60 FPS; F11/F10 alternam
  os modos. Converta mouse com map_to_virtual/get_virtual_mouse_pos.
- Mouse deve permitir toda a navegação. ESC e atalhos são complementares.

## 2. Arquitetura e persistência

- src/config: resolução, layout, tipografia, nomes de exibição, trilha e preços.
- src/systems: regras sem interface; não introduzir Pygame nas transações.
- src/models: entidades, cartas, ações e efeitos.
- src/scenes e src/ui: eventos, composição e animações. BaseScene/SceneManager
  administram cenas e modais. Áudio via scene_manager.audio_manager.
- src/settings.py e src/game.py são shims; não colocar regras novas neles.
- Saves v15: perfil permanente separado de run; progresso é o alias em memória.
  SaveManager valida/migra, usa revisão otimista e gravação atômica.
- Mudanças de schema exigem SAVE_VERSION e migração compatível. Não incrementar
  a versão por mudança visual/documental.
- Transações falhas restauram o documento completo. Preservar rascunho de deck,
  rollback, isolamento entre slots e semântica exclusiva de modo_teste.
- Derrota encerra a run, mantendo perfil/fragmentos; nova run refaz estado
  temporário. Há snapshot de combate para retomar uma luta viva; isso não
  equivale a recuperar uma run morta. Epílogo após Zanzara já está implementado.
- Preservar alterações preexistentes; não usar add global, stash, reset, restore
  ou descarte sem autorização. Commit, publicação e merge exigem autorização
  do usuário. Não publicar como parte de uma simples auditoria.

## 3. Campanha, nomes e IDs

Dois encontros comuns antes de cada chefe, sete territórios. IDs legados
permanecem estáveis em saves, áudio, sprites, retratos e regras.

| Nome interno | Nome exibido |
|---|---|
| Guardião da Pedra | Octav, o lobisomem |
| Álvaro e Tex | Alvar & Tekks, Rastreadores |
| Álvaro e Tex · Pequeno | Tekks |
| Goblin Nerd | Jozephino, o Inventor |
| Gordofera | Sir Thomas, a Besta Fera |
| Corpo Seco | Jan-Pietro, o Imortal |
| Carrasco da Vigília | Labrro, o Carrasco |
| Zanzara | Zanzara, Líder do Clã Moskar |

Use boss_display_name em src/config/boss_names.py; não renomeie Enemy.name,
boss_id, boss_key ou slugs para acompanhar mudanças narrativas.
O ZIP BossesNovasSprites usa Boss1=Octav, Boss5=Jan-Pietro e Boss6=Labrro.
Jozephino é goblin nerd, mesmo quando mensagens informais o chamarem Boss6.
Consulte o código/nome e esclareça divergências sem trocar personagens.

## 4. Combate e estados

- Energia inicial 2, teto 8 e crescimento por turno; melhorias permanentes podem
  alterar o início. Mão inicial 3, limite 5, cartas restantes ficam na mão.
- Deck: 6–18 cartas, três cópias por tipo. Pode haver rascunho vazio, mas só deck
  válido é promovido/salvo; não sobrescrever o último válido ao fechar.
- Cemitério: descarte por uma energia e uma troca grátis por turno.
- Intenções: uma ação comum, duas de chefe; executar o plano já anunciado.
- Revanche não gera ouro, cartas ou materiais; recompensas têm identificação
  idempotente por run/encontro. Não permitir farm por repetir etapa.
- Ultimate começa em ultimate_charge=0 em toda nova batalha, threshold=20.
  Não herdar carga de outra batalha nem do campo legado carga_ultimate.
  Retomar o snapshot da mesma luta viva restaura a carga daquela luta; a
  segunda fase da dupla também conserva o estado por ser a mesma batalha.
- Limpar debuffs, durações, contadores, Força e bônus temporários ao iniciar/
  encerrar combate; preservar somente os campos de progressão previstos.
- Veneno: 1–2 stacks por aplicação, máximo 5, poison_turns=2 renovado inclusive
  no teto. Fim do turno: 5*poison_stacks direto, sem Escudo; decrementar duração,
  zerar stacks ao expirar.
- Sangramento: 1–2 stacks, máximo 5, bleed_turns=2 renovado. Após o primeiro ataque
  de cada turno: 3*bleed_stacks direto, mesmo se o alvo bloquear todo o golpe;
  limite bleed_triggers_this_turn<1.
  Multigolpe conta uma ação. Resetar contador no início; reduzir duração no fim
  sem dano extra. Zerar stacks quando expirar.
- Choque: somente inimigos aplicam ao jogador. Cada stack tira uma energia no
  próximo início de turno, mínimo zero; consumir/remover todos imediatamente.
  Jozephino aplica um na descarga comum e dois no especial.
- HUD/tooltips mostram stacks, dano por gatilho e duração. Não tratar números
  antigos de Veneno/Sangramento como dano fixo.

## 5. Cartas, ultimates e evolução

Catálogo com 20 cartas disponíveis e 75 bloqueadas. CARD_SPECS/CARD_POOL são a
fonte; unavailable não entra em compra, recompensa nem equipamento.

- Arte LV1: assets/cards/<id>.png; LV2 prateada: assets/cards/lv2/<id>.png.
  assets/cards/art_manifest.json registra recortes, dimensões, contorno e
  centroide do losango de cada uma das 40 artes.
- Propagar level, cost e description da cópia real via instance_card para
  get_card_image. Cache por nível/custo/descrição. Não presumir redução de custo
  no LV2: usar as regras reais de roguelite.py.
- with_player_rules recompõe somente o interior do losango da arte: um custo
  dinâmico, sem badge duplicado. Não deslocar o contorno por coordenada global
  fixa. with_rules permanece para intenções/consumidores legados.
- Recortes regulares têm dimensões individuais registradas no manifesto;
  não presumir que as 40 imagens tenham a dimensão da Ultimate.
- Desenhar a carta inteira proporcionalmente; preservar transparência e padding
  entre carta e moldura externa, desenhando o ornamento por último.
- Ultimates: PNGs individuais completos 316×489, moldura dourada, exterior
  transparente, geometria da Esfera Protetora LV2. Manifesto assets/ultimates/art_manifest.json.
  Custo e rodapé são dinâmicos. Carga 20 e custo 2 para as três:
  Mana restaura energia para 8 e limpa negativos, sem comprar cartas;
  Forças concede +12 Força até o fim da luta e 40 Escudo/2 turnos;
  Rugido destrói Escudo antes de 60 de dano base e aplica Fraqueza/3 turnos,
  respeitando modificadores e proteções existentes.
- Evolução individual LV1→LV2: três materiais do tipo e preço UPGRADE_PRICES,
  limite de três upgrades por run. Material custa 15, reserva máxima 9.
  Não evoluir automaticamente todas as cópias.
- Preços das cartas em CARD_PRICES. Loja cura até 20 HP atual por 30/45/60 ouro,
  até três compras/run; não aumenta vida máxima. Vida cheia não cobra nem conta.
  Melhorias permanentes de vida/energia/preparação usam fragmentos entre runs.

## 6. Telas e interação

- Mercado Silencioso: cenário/mercador ilustrados, quatro cartas por página,
  preços, compra, cura e feedback. Altar: seleção da cópia, Antes LV1/Depois LV2,
  comparação calculada, materiais/preço e confirmação com efeitos.
- Mochila Ancestral: cenário de expedição, 18 compartimentos de couro, reserva
  em páginas de seis tipos, filtros e aba de ultimates. Preview fixo à direita,
  fora dos botões; hover nunca equipa/consome recursos.
- Filtros de custo/nível da Mochila acompanham a próxima cópia livre, priorizando
  LV2 como a regra existente. Recalcular após mutações do deck.
- Compartilhar composição MerchantWorkshopView/BackpackView; não duplicar
  transações de shop_system/roguelite/deck_loadout na UI.
- Intenção com arte: somente carta ampliada, sem painel lateral redundante,
  centralizada horizontalmente em y≈43% e limitada às bordas da tela.
  Ícones ficam no canto superior direito. Sem arte, usar ficha textual única.
  Preview é visual, desenhado acima da arena, sem capturar cliques.

## 7. Famílias de animação e personagens

O jogo tem kits mistos; não padronizar tudo em 4×2 ou doze quadros por engano.

- Octav/Jan-Pietro/Labrro: seis folhas RGBA nativas 4×2, oito frames row-major,
  células 448×320, em assets/bosses/sheets_eight/<slug>/, com paleta/manifesto.
  Carregamento AssetManager._load_boss_sheet_kit; aliases em boss_sheet_kits.py.
  Preparo canônico prepare_boss_sheet_update.py; não executar preparadores
  históricos de oito/doze poses para sobrescrever estes kits.
- Outros chefes legados: ações de doze poses; idle/fontes de dano de oito.
  Efeitos independentes de Ultimate podem ter doze frames; não confundir corpo,
  carta e camada de magia. A dupla mantém suas duas fases.
- Inimigos comuns: 14 tipos, oito frames, canvas 448×260. Não confundir o
  Golem das Ruínas com Octav.
- Protagonista esguio: ações/cartas/ultimates com doze poses, idle/dano com oito;
  preservar desenho, equipamentos, paleta e pivô.
- Jan-Pietro: apoio (224,318), botas pixel-idênticas no idle, 160 ms/pose, ciclo
  de respiração em jan_pietro_animation.py; não aplicar outro align_stance.
- Jozephino: oito respirações derivadas da guarda íntegra, botas fixas,
  160 ms/pose (6,25 FPS), ping-pong; não restaurar poses que encolhem 18%.
- Dano inimigo: enemy_reactions.py registra apoio e filtra poses incompatíveis,
  560 ms totais, hold visual ≈90 ms, recuo só horizontal até 12 px internos e
  pulso curto. Preservar fase de idle e esperar reação antes da ação seguinte.
  Não girar/achatar/redimensionar nem forçar poses inválidas por contagem.
- Zanzara: necromante de foice, kimono preto, efeitos verdes, habilidades Foice,
  Passo, Grilhões e Travessia/Caronte. Não restaurar moedas, amuleto ou palma.
  Renderizador e estados próprios; preservar escala, rosto aprovado em
  bosses/zanzara-necromante-v8.png e moldura do protagonista (framed-content).

## 8. Assets, áudio e limpeza

- Reutilizar material aprovado; não sobrescrever originais externos.
  Preparo reproduzível e fontes/prompts em docs/manifestos.
- Ao substituir recurso, verificar referências e mover para
  _arquivos_antigos_para_deletar/ (ignorado) ou remover o ativo obsoleto.
  Não comitar essa pasta, fontes temporárias, saves ou capturas de QA enormes.
- Não remover fundos/ornamentos compartilhados ainda referenciados.
- Caminhos relativos ao projeto, slugs estáveis, transparência real. Ausência
  de arquivo não deve ficar oculta por fallback em testes de integração.
- Arte intencionalmente alterada exige atualizar fixtures de hashes/pixels
  pertinentes; não alterar fixture só para silenciar falha.
- IDs de áudio estáveis via AudioManager; derivados novos em OGG com origem e
  composição registradas, preservando versões aprovadas.
- Trilha canônica em src/config/music.py: Deep forest menu/mapa/serviços,
  The Last Stand combates, Jungle Chase chefes, Jungle Tribe Zanzara.
  Volume inicial 45%, saída 350 ms e entrada 600 ms; canal musical separado.
  Não reiniciar música na mesma região/contexto nem na segunda fase da dupla.
- Não afirmar escuta crítica ou campanha completa jogada com base só em smoke.

## 9. Testes e conferência

Usar unittest, não pytest. Instalar requirements-dev.txt para testes de assets.
O executor por módulos evita acumular caches até faltar memória:

~~~powershell
python -m pip install -r requirements-dev.txt
python -B devtools/validate_isolated_tests.py --report docs/validacao_auditoria_documentacao.json
python -B devtools/audit_project_docs.py --output docs/auditoria_documentacao.json
~~~

Em Unix, usar python3 se necessário. SDL dummy é configurado pelo executor.
Um módulo isolado: configurar SDL_VIDEODRIVER/SDL_AUDIODRIVER=dummy e executar
python -m unittest tests.test_ultimate_cards_lv2 -v.
Resume/recheck são incrementais; não chamá-los de nova suíte integral.

- Rodar testes pertinentes e a suíte solicitada; não reduzir asserts para
  aceitar regressões. Expectativas antigas mudam somente com contrato aprovado.
- Durante ajuste de personagem, usar somente o piloto pertinente; no fechamento
  geral, testes sem janelas e no máximo uma instância do jogo para conferência.
- Pilotos usam --smoke com drivers definidos antes de importar Pygame e saves
  temporários. Não tocar nos três slots reais para QA.
- Atualizar documentação, inventário/contrato e relatório quando o código mudar.
  Ao concluir, informar arquivos, validação e limitações materiais.

## 10. Integração das PRs #29 e #30 — 24/11/2026

- Primeiro território agora se chama Stone de Cut; IDs internos dos chefes permanecem estáveis.
- Sangramento dispara uma vez por turno após o primeiro ataque, mesmo absorvido.
  Dano direto de 3 por stack, teto 5, duração 2 renovável; contador reinicia no turno.
- Debuffs vinculados a golpes só aplicam/renovam quando o golpe tira vida.
  Escudo que absorva todo o dano impede a aplicação; receber Escudo preserva negativos.
- Empacotamento: PyInstaller e Inno Setup em installer/ e workflow build-windows.
  Paths de recursos e dados diferem no executável; preservar a configuração de
  src/config/settings.py e a persistência em LOCALAPPDATA no jogo instalado.
  Ver [build Windows](docs/build_windows.md).

## 17. Altar de espólios pós-combate

- `src/ui/post_combat_reward_view.py` desenha o cenário em `assets/ui/rewards/`, com procedência em `art_manifest.json`. Reutiliza moldura, padding e custo dinâmico da Loja/Altar, preview lateral e moldura prateada para uma cópia LV2 existente.
- Carta Nova desbloqueia o tipo pelas regras da run. Materiais entram na reserva de evolução do tipo, respeitando o limite 9. Mostre a quantidade de cópias existentes e a reserva. Preserve as regras do motor, ouro, fragmentos, revanches e transações de save.
- Brasas no cenário, runas e faíscas no hover, pulso dourado ao confirmar. A cena encaminha a decisão uma única vez após o pulso e conclui a escolha se a janela for fechada durante ele. Pular mantém o ouro conquistado.
- Piloto sem slots reais em `testar_polimento_audio.bat recompensa`. Teste rápido com `--smoke` e testes de seleção, pulo, materiais e fechamento em `tests/test_post_combat_rewards.py`.
- A vitória sobre Zanzara preserva a celebração e segue automaticamente para o epílogo depois de salvar a conclusão da campanha. O altar de espólios fica reservado aos demais encontros.

## 18. Animações de derrota

- Slime derrete e deixa uma poça. Morcego Sombrio cai e solta poeira e som ao tocar o chão. Vinimuth, Zanzara e a transição de Alvar para Tekks têm sequências próprias.
- Os demais kits de campanha usam a reação de dano antes da pose final em `assets/enemies/defeat/`. Bípedes apoiam um joelho. Quadrúpedes cedem de acordo com a anatomia. Procedência em `art_manifest.json` e exportação em `devtools/prepare_enemy_defeats.py`.
- Pilotos `testar_polimento_audio.bat derrotas-comuns` e `testar_polimento_audio.bat derrotas-chefes`. Use as setas para trocar o inimigo, Espaço para o golpe final e R para repetir.

## 19. Áudio dos debuffs — 24/11/2026

- Veneno e Sangramento aprovados no piloto. Veneno usa só a cauda corrosiva da Poção Venenosa. Sangramento usa só o escoamento da Adaga Sangrenta e toca com o aviso do debuff, após o som de contato.
- Fogo e Queimadura usam a cauda de chama da Bola de Fogo, aprovada no piloto `testar_polimento_audio.bat queimadura`. Fonte e recorte em `docs/queimadura_debuff_chama_v2.json`.
- Choque aprovado no piloto. Usa o mesmo OGG da Esfera Protetora, com identificador próprio no grupo de volume de dano e disparo quando a energia é reduzida. Piloto `testar_polimento_audio.bat debuffs`, tecla 3.
- Rugido da Floresta aprovado no piloto com o som da Bola de Fogo no lançamento do avatar e o som comum na ativação. As três cartas especiais usam o feedback padrão ao entrar com o mouse nas cartas da mão.
- Avanço dos diálogos aprovado com `ui.navigate` em volume reduzido. Epílogo aprovado com Jungle Tribe da batalha final até as últimas falas de Zanzara, saída gradual na tela preta e Lost Time, de Kevin MacLeod, a partir da primeira fala de Octav. Fonte, licença e conversão em `assets/audio/README.md`.
- Abertura aprovada no piloto exclusivo `testar_polimento_audio.bat abertura`. The Last Stand toca no primeiro quadro. Jungle Chase entra quando Zanzara aparece no navio, no segundo quadro.
- Guerreiro da Mata aprovado no piloto. Varredura do Mangual e Abalo da Floresta usam o mesmo OGG do Machado Quebra-Escudo, agendado 250 ms antes do contato para alinhar o transiente pesado e preservar a cauda de quebra. No piloto único, pressione 2 e use A ou S para comparar os golpes.
- Game Over e vitória do tutorial aprovados no piloto. O brasão de derrota e o áudio original entram após o golpe fatal. O tutorial usa a fanfarra e o brasão padrão de vitória antes da tela de conclusão. No piloto único, use 6 para Game Over ou 7 e V para a vitória do tutorial.
- Revisão em janela única com `testar_polimento_audio.bat polimento-final`. Teclas 1–8 alternam Rugido, Mangual, diálogos, abertura, epílogo, Game Over, tutorial e recompensa. Usa saves temporários. O teste rápido do piloto valida os disparos pelo mixer e as mudanças de contexto musical. A avaliação de timbre e volume é feita ouvindo o piloto.
- Fechamento técnico de 24/11/2026 nesta branch: suíte completa isolada com 724 testes em 77 módulos, todos aprovados. O mixer dummy iniciou 84 efeitos e cinco trilhas, e a entrada real `main.py` abriu e desenhou o menu no teste automático. A conferência da campanha no jogo aberto é manual.

## 20. HUD, molduras e guias de gerenciamento — 24/11/2026

- Branch desta implementação: codex/hud-tutoriais-gerenciamento, partindo da
  main 00b0078 (PRs #28, #29 e #30 integradas). Preservar áudio, derrotas,
  altar de espólios, instalador e a regra de Sangramento de uma ativação.
- Geometria da faixa de combate em src/config/combat_header.py: painéis de
  vida espelhados; MENU central em (870,80,180,56); título da arena acima.
  Desenho e eventos usam o mesmo retângulo e coordenadas virtuais.
- Molduras em src/ui/frames.py: nine_slice para cantos proporcionais e faixas
  centrais extensíveis; horizontal_frame conserva extremidades das barras de
  vida; gold_outline compartilha paleta/espessura. MerchantWorkshopView leva
  o mesmo padrão à Loja, Altar, Mochila e Recompensas. Painéis usam theme.panel.
  Não transformar as bordas prateadas LV2 ou douradas de Ultimate em borda base;
  não refazer rostos aprovados. Enquadrar cartas/retratos inteiros e manter padding.
- Guias em src/ui/management_guide.py; regras puras em
  src/systems/management_tutorials.py. Estados shop/backpack/workshop; cada
  tela é independente. Passos consultam retângulos reais, sem deslocar controles.
- O guia intercepta cliques/teclas enquanto ativo; nunca deixar o clique de
  Próximo/Concluir chegar a compra, equipamento ou evolução. Opções de janela
  continuam tratadas antes do guia. AJUDA reabre, Esc/× dispensam com gravação.
- Saves v15: tutoriais_gerenciamento é um dicionário de booleanos por tela em
  PROFILE_FIELDS, persistido no perfil; a migração inicializa faltantes como
  False, preservando o restante do save. Não guardar essas flags apenas na run.
  Gravar via transact e respeitar rollback/revisões. Falha mantém guia aberto
  para repetir; Esc após falha permite sair sem gravar nem marcar como visto.
- Testes de fluxos já conhecidos usam tests.management_fixtures.guides_seen;
  primeira visita, cliques capturados, migração, rollback e persistência são
  cobertos separadamente em test_management_guides. Não remover essas verificações.
- Preview sem slots reais: python -B devtools/preview_management_guides.py
  --smoke --output <pasta-de-QA>. Nenhum asset original foi substituído nesta
  etapa; não mover recursos compartilhados para a pasta de descarte.

## 21. Retratos comuns e Santuário dos Ajustes — 24/11/2026

- Manter as alterações locais da etapa 20. Nenhum rebalanceamento foi feito.
- BattleHUD.portrait sempre pede o retrato completo no tamanho do slot a
  AssetManager.get_character_portrait. Não voltar ao antigo recorte interno
  com hud_portrait por cima. O dispatcher da batalha usa BattleHUD diretamente,
  sem condicionar a HUD à presença da moldura aposentada.
- Os 14 comuns compõem a face dentro de framed/manel.png usando
  _portrait_with_protagonist_frame, o mesmo compositor de Zanzara; preserve
  bordas pixel-idênticas e escala contain. Viniurgo reaproveita só o conteúdo
  do PNG antigo emoldurado; não desenhar duas bordas. Slime/Macaco e encontros
  sem retrato próprio usavam um recorte do idle/fallback; ver a auditoria da seção 22.
- As faces e PNGs aprovados de jogador/chefes permanecem intactos. Crops dos
  comuns estão em character_portraits.py; preservar olhos/focinho no quadro.
- assets/ui/hud_portrait.png foi arquivado em
  _arquivos_antigos_para_deletar/assets/ui/hud_portrait.png e removido do mapa
  de carregamento. Não comitar a pasta de descarte nem reintroduzir referências.
- Nova arte em assets/ui/options/sanctuary_background.png, criada com image_gen
  integrado; prompt em docs/opcoes_arte_prompt.txt e procedência/hash no
  art_manifest.json da pasta. Não guardar referências apenas em .codex.
- OptionsSanctuaryView é o renderizador de pedra/pergaminho, controles rúnicos
  e ornamentos; reutiliza offer_frame.png. Opções, pausa e biblioteca de guias
  compartilham o padrão. Preferências continuam em GamePreferences/AudioManager,
  não duplicar armazenamento na UI nem alterar os padrões de áudio/vídeo.
- MENU → pausa → Opções conserva a pilha modal. Botão Retornar ao Combate fecha
  Opções e a pausa; Esc fecha uma camada. Não recriar a cena/engine ao retomar.
- Rever Tutoriais na aba Jogo abre GuideLibraryScene em leitura: usa somente
  títulos/textos dos passos. Não avaliar targets de spotlight nessa biblioteca,
  marcar flags, liberar cartas, escrever slots ou avançar a batalha.
- Sair para Menu confirma e usa save_on_exit da cena; impedir saída se houver
  falha ou recompensa/transição pendente. Não pular o altar de espólios/epílogo.
- Testes: opções/persistência já existentes, test_options_sanctuary e a auditoria
  pixel da moldura dos comuns em test_character_portraits. Preview:
  python -B devtools/preview_options_sanctuary.py --smoke --output <pasta-QA>.
  Saves e preferências do preview são temporários.

## 22. Enquadramento dos 14 retratos comuns — 24/11/2026

- COMMON_PORTRAIT_SPECS em character_portraits.py cobre exatamente os 14 nomes
  de BIOME_ENEMIES. Todas as entradas apontam para PNGs dedicados ao retrato,
  sem depender de idle, pose, animação ou recorte automático da spritesheet.
- Recortes individuais retiram a borda anterior e o vazio acima da cabeça,
  preservando rosto/orelhas/cristas/focinho. Não voltar ao crop uniforme .28/.28.
- Comuns usam framed-contain: o compositor recebe fit=contain, escala com min
  em 88% da largura/90% da altura e centraliza com margem interna. Não usar
  cover/max nos comuns nem esticar a imagem. A moldura aprovada não foi alterada.
- framed-content/cover continua reservado aos retratos aprovados de Zanzara;
  não alterar o enquadramento do jogador/chefes para corrigir os comuns.
- Slime e Macaco Selvagem receberam arquivos em portraits/source/dedicated/,
  gerados com image_gen integrado; prompts/hashes estão no art_manifest.json.
  Esses dois monstros não devem voltar ao recorte do sprite de combate.
- Os sprites e fontes existentes continuam ativos, portanto não arquivar
  idle_*.png nem os onze PNGs de portraits/source/enemies/. Não havia retratos
  dedicados antigos de Slime/Macaco a substituir.
- Testes verificam cobertura dos 14 nomes, carregamento sem fallback de sprite,
  moldura pixel-idêntica e preservação dos quatro cantos em artes largas,
  altas e quadradas. Revisão visual inclui a HUD real em 1920 e 1280 pixels.

- Cobertura completa dos comuns: 14 dos biomas + Goblin/Guarda Sombrio do pool
  ENEMY_TYPES legado. Os dois adicionais ficam em LEGACY_COMMON_PORTRAIT_SPECS,
  com novas artes dedicadas; não confundi-los com Jozephino/Vinimuth. Testes
  conferem a união dos dois registros. Chefes/minibosses ficam preservados.

## 23. Canal útil de HP — 24/11/2026

- BattleHUD.health_bar usa a máscara de HEALTH_WINDOW_POLYGON, definida na
  referência 733×188 de hud_health.png em src/config/combat_header.py.
- Máscara e moldura passam pelo mesmo horizontal_frame: não restaurar margens
  de 18%/largura de 64%, pois deixam espaços pretos antes das águias.
- Preencher de 0 a 100% do bounding box da abertura, com clipping pela máscara;
  nunca pintar sobre a ornamentação. Jogador/inimigo usam o mesmo método.
  O texto de HP é centralizado na abertura, não no canvas decorativo inteiro.
- test_health_bar cobre pontas no HP máximo, proporção parcial, zero, limites,
  preservação dos ornamentos e simetria dos dois lados. A arte PNG não mudou.

## 24. Prova web — Etapa 1

As restrições desta seção descrevem --poc; a campanha padrão segue a Etapa 4.

- Branch feat/web-mobile-port a partir de b19cfcf. Entradas web/main.py e web/poc.py,
  empacotadas por devtools/build_web.py. Não executar a campanha/saves no navegador.
- Application compartilha um frame: desktop síncrono; web cede com asyncio.sleep(0).
  Não usar sys.exit no caminho web. Não alterar instalador, schema v15 ou layouts mobile.
- AssetManager(preload=False) carrega somente fontes e fundo. ProofAssets prepara
  somente jogador/cartas iniciais/Mana/Slime/HUD em lotes cooperativos.
- O fallback NotoSansSymbols2/OFL é baixado pelo preparador para o build ignorado;
  não incluir fontes do Windows no pacote. Desktop mantém a fonte anterior.
- AudioManager(defer_initialization=True) aguarda gesto e conserva música pendente.
  O construtor padrão desktop continua inicializando imediatamente.
- ProofWindow mantém canvas virtual 1920x1080, saída 1280x720 e CSS proporcional, sem
  alterar a resolução virtual ou sprites. Isso não constitui layout compacto mobile. O cenário estático e os textos usam
  caches exclusivos da prova; o teste de pixels preserva a composição original.
- No piloto `?render=1`, preferências vivem só em memória e nenhum slot real é acessado.
  Bibliotecas/runtime web versionados em requirements-web.txt; ambiente .venv-web separado.
- Veja [prova web](docs/web_poc.md) e [estado atual](docs/estado_atual.md).

## 25. Isolamento de plataforma — Etapa 2

- src/platforms define capacidades e serviços; não introduzir Pygame em caminhos
  ou capacidades. Emscripten é detectado em runtime; não inferir pelo tamanho.
- Resources são separados de user_data_path. Desktop preserva _MEIPASS/
  LOCALAPPDATA. Web tem FS de sessão e capacidade de IndexedDB (disponibilidade validada ao abrir):
  não tratar esse diretório como save durável; usar BrowserStore para persistência.
- Usar SceneManager.request_exit em cenas; não sys.exit/pygame.quit.
  Main conserva encerramento e save desktop; web volta à home_factory.
- WindowManager é o controlador desktop original. create_window_manager
  seleciona WebWindowManager; APIs do browser ficam em web/bridge.js.
- Pausa web por visibilidade/foco: suspender updates/entrada/áudio e descartar
  tempo/eventos acumulados. Conferir a geração de retomada, além do booleano.
- RenderCache usa fontes imutáveis. Não modificar pixels de imagens cacheadas.
  Blit recortado mantém origem e flags; não recortar o canvas das sprites.
- Bandeja RGB é uma otimização exclusiva do Slime na prova, com fallback para
  Ultimates; não aplicar cegamente a bosses/FX que cruzem a mão.
- [Contrato e validação de plataformas](docs/web_platforms.md).


## 26. Persistência web — Etapa 3

- Save JSON permanece v15; IndexedDB v1 tem stores saves e backups. Não incrementar SAVE_VERSION por adicionar backend.
- DiskStore preserva fsync/replace e caminhos nativos. Nunca usar FS virtual web como save durável.
- BrowserSaveManager.run/transact_async executam regras numa candidata isolada; somente oncomplete publica a candidata e confirma UI. Não chamar save síncrono do manager web.
- SceneManager.submit bloqueia entrada duplicada, preservando desenho e cooperação asyncio. Falha descarta candidata; combate restaura snapshot confirmado.
- Revisão e run de origem verificadas dentro do readwrite IndexedDB. Duas abas não podem sobrescrever silenciosamente o mesmo slot.
- JSON na fronteira Python/JavaScript deve usar escapes ASCII nos dois sentidos; textos em português precisam sobreviver intactos a múltiplos commits e importações.
- Preferências leves no localStorage; perfil, run, guias vistos e snapshots no IndexedDB. Mesmas migrações, normalização e validações nativas.
- Checkpoints lógicos e comandos confirmados são a garantia principal; pagehide/visibilitychange são complementares, sem garantia ao fechar a aba.
- Backup .json validado e limitado a 5 MiB; substituição de slot exige confirmação. Preservar originais e instalador.
- Ver [persistência web](docs/web_storage.md) e [estado atual](docs/estado_atual.md). Campanha web completa, mobile e PWA permanecem fora desta etapa.


## 27. Campanha Web PC — Etapa 4

- Checkpoint anterior: 742218f. O build padrão agora usa web/campaign.py e recursos por contexto; --poc preserva a prova anterior.
- src/systems/web_resources.py e devtools/web_asset_packs.py definem propriedade única, dependências, hashes e pacotes estáticos. Não incluir saves, ambientes ou arte de outros contextos no pacote inicial.
- CampaignAssets libera arquivos/superfícies de contextos anteriores; os loaders nativos aceitam filtro opcional de nomes, com default None preservando o carregamento Desktop completo.
- Transições web devem carregar o contexto antes de construir/desenhar cenas que leem imagens. Erros permitem tentar novamente; não prosseguir com arte incompleta silenciosamente.
- web/campaign.py reutiliza cenas/regras nativas, com confirmação IndexedDB para tutorial, flags, recompensas e nova run. Não introduzir regras alternativas de dano/progressão para a web.
- InputRouter conserva event.pos nativo; não substituir por coordenadas virtuais e converter novamente na cena. InspectionController não deve capturar cliques dos ícones ao exibir preview.
- Recursos de mouse, hover, roda, teclado e botões equivalentes continuam no layout desktop proporcional. A camada compacta/touch é isolada conforme a Etapa 5; PWA pertence à Etapa 6.
- QA por checkpoints fica exclusivamente em build/; atributos controlados são explícitos no relatório, nunca aplicados ao jogo normal.
- Ver [campanha web](docs/web_campaign.md) e [estado atual](docs/estado_atual.md).

- Composições web de fundos/painéis ficam em src/ui/composition_cache.py; preservar equivalência de pixels, transparência de previews e limite de memória. Não aplicar a composição de um painel raiz sobre conteúdo dinâmico.
- combat_snapshot.restore deve recuperar também level/kind/index; motores temporários de recompensa não podem permanecer no nível padrão 1. A finalização automática de Zanzara confirma o save antes do epílogo.

## 28. Host compacto e toque — Etapa 5

- Checkpoint da Etapa 4: 62de681. A campanha web instala web/mobile.py; o Desktop não instala esse adaptador.
- responsive_layout.py define os limiares 1000×600 úteis, controles compactos também em tablets com apontador primário touch e o bloqueio em retrato somente nesses dispositivos. Coordenadas lógicas 1920×1080; MobileCanvas físico 1280×720 e DPR 1. Web PC mantém HiDPI até 1920×1080.
- web/index.html é um fragmento do host Pygbag, não outro runtime. Preservar safe areas, 100dvh e orientação/foco na bridge.
- MobileInterface reutiliza cenas, handlers, instâncias reais de cartas e persist_command. Não duplicar regras/transações nos arquivos JavaScript.
- Primeiro toque inspeciona; JOGAR/COMPRAR/EQUIPAR/REMOVER/APRIMORAR/ESCOLHER confirma. Nenhuma inspeção pode gastar recursos.
- Época de composição + geração de orientação invalidam comandos antigos. Bloquear durante commit e consumir confirmação uma vez. Cancelar seleção/arraste no blur, pointercancel, rotação e troca de cena.
- ActiveTimeline afeta apenas o runtime web e congela ticks durante suspensão. Não alterar pygame.time.get_ticks no Desktop.
- Controles compactos têm mínimo 44×44 CSS, contain/padding, texto via textContent e spotlight sobre elementos reais. Preservar identidade e níveis da arte via AssetManager.
- Partículas procedurais são limitadas a três por emissão e 12 por frame no perfil transitório apenas compacto. Caches de imagens do host são limitados e liberados por cena.
- Ver [contrato mobile](docs/web_mobile.md) e [estado atual](docs/estado_atual.md). Emulação não autoriza alegar desempenho em dispositivos físicos.
- Fechamento técnico de 25/11/2026: 889 testes em 87 módulos aprovados; 22 verificações Chromium mobile e 11 Web PC aprovadas. O host deve manter uma única meta viewport no head, com viewport-fit=cover. Também foram conferidos tablet touch 1280×800, rotação e Web PC amplo. Relatório: docs/validacao_web_etapa5.json.

## 29. PWA, offline e distribuição — Etapa 6

- Checkpoint anterior: 4967b58. O build padrão gera dist/web, com release.json e SHA-256 de shell/pacotes. Não alterar o workflow do instalador Windows para hospedar a web.
- web/manifest.webmanifest usa start_url/scope relativos. O id é omitido intencionalmente para derivar a identidade do start_url na subpasta; id "./" resolveria contra a origem e poderia colidir com outro projeto.
- Ícones são exportações técnicas do retrato aprovado de Jaum; preservar a fonte. Web/icons/art_manifest.json registra fonte/hash, tamanhos e área segura maskable.
- web/runtime-lock.json fixa os recursos externos Pygbag/Python/WASM/pygame-ce. Não atualizar hashes automaticamente quando uma origem divergir. O primeiro preparo exige conexão; o teste offline deve desativar cache HTTP.
- Service Worker separa shell/runtime por versão e packs por hash, com namespace por scope. Nunca publicar resposta parcial, opaca ou divergente. CacheStorage não é backend de saves.
- O indicador offline pronto cobre os 29 packs essenciais, não todos os territórios. Pacotes ainda não baixados precisam de conexão; falhas devem permitir retentativa sem interromper o combate atual.
- Atualizações instalam em waiting. skipWaiting somente após confirmação de todas as abas no menu inicial, sem modal ou gravação pendente. Bloquear entrada na aprovação e recarregar apenas depois da ativação coordenada. A primeira ativação não reinicia a partida.
- O manifesto de distribuição deve ser verificado antes de publicar; deploy atômico, HTTPS, index/service-worker com revalidação e packs com cache immutable. Não remover packs de releases ainda em uso.
- A página install.html oferece uma entrada leve de instalação; não carrega nem grava slots. A instalação Chromium é validada em perfil temporário e desinstalada ao final.
- Ver [build web](docs/build_web.md) e [estado atual](docs/estado_atual.md). PWA no Chromium não comprova instalação física iOS/Safari. Etapa 7 cobre fechamento/instalador/push.
- Fechamento técnico de 25/11/2026: 908 testes em 88 módulos e 10 verificações PWA aprovados. Instalação/abertura standalone e atualização entre abas foram testadas em perfil Chromium temporário. Mobile conferido sem sobreposição do indicador. Relatório: docs/validacao_web_etapa6.json.

## 30. Fechamento multiplataforma — Etapa 7

- Preservar os três caminhos: Desktop síncrono/JSON v15, Web PC proporcional e host mobile/PWA. Não importar Pygbag/Playwright no runtime ou instalador nativo.
- PyInstaller 6.11.1 exige Python 3.12/3.13 x64; installer/build_installer.bat prefere .venv-build e rejeita versões incompatíveis. Não elevar dependências nativas apenas para acompanhar ferramentas web.
- main.py --smoke-report é uma verificação opcional de quatro frames do menu, com drivers dummy e preferências isoladas. A entrada normal permanece igual; esse teste não representa uma campanha jogada.
- devtools/validate_windows_build.py usa o batch oficial e verifica assets por SHA-256, portátil, instalação temporária e desinstalação. Não substituir instalação pessoal registrada. /SUPPRESSMSGBOXES preserva dados por padrão; diálogo interativo de remoção permanece.
- build/, dist/, instaladores, ambientes virtuais, bytecode, caches, logs/screenshots de QA e _arquivos_antigos_para_deletar/ não são fontes versionadas. Adicionar explicitamente apenas arquivos revisados.
- Validação final local: 909 testes em 89 módulos, zero falhas. Build Windows com Python 3.12.13/Pygame 2.6.1 sem bibliotecas web; 2.528 assets íntegros. Não alegar validação física iOS/Safari ou sucesso do workflow remoto com base apenas na execução local.
- Ver [arquitetura multiplataforma](docs/arquitetura_multiplataforma.md) e [build web](docs/build_web.md).

Fechamento cruzado: 11 verificações Web PC, 22 mobile e 10 PWA aprovadas.
Resultados e limites no [relatório final](docs/validacao_multiplataforma_final.json).

## Nitidez e áudio na Web — correção posterior à Etapa 7

A bridge informa tamanho CSS e devicePixelRatio. Apenas SDL/Pygame altera o
backing buffer Web PC: CSS × DPR limitado a 2 e à arte nativa 1920×1080;
mobile usa o perfil físico 1280×720/DPR 1 descrito abaixo.
Não atribuir canvas.width/height por JavaScript, pois isso desincroniza SDL e
entrada. Não forçar 960×540 no compacto. O último downscale usa smoothscale;
em 1920×1080 ocorre blit direto, sem redução intermediária. CSS pixelated evita
interpolação borrada quando há ampliação residual. O Desktop mantém WindowManager.

Somente em emscripten, preparar mixer antes dos subsistemas com 44100 Hz,
signed 16-bit, estéreo e buffer 4096. A abertura continua após gesto real;
o backend pode negociar 48000 Hz com o navegador. Quatro canais SFX × ganho
máximo 0,16 e música × 0,25 reservam margem de mix (soma teórica 0,89).
Sliders continuam multiplicativos e desbloqueio/retomada não criam nova trilha
ou ganho master. Não alterar volumes, canais ou inicialização do Desktop.
A medição de PCM no Chromium não substitui escuta em dispositivos físicos.

## Mobile com a arte original

Todas as telas mobile usam as cenas originais, sem HUD/menu/grid HTML paralelo.
A camada de toque oferece apenas inspeção artística e confirmação explícita;
os hits invisíveis são ampliados para 44×44 CSS. O buffer mobile é realmente
1280×720, DPR 1, com coordenadas lógicas originais e caches limitados; Web PC e
Desktop mantêm seus caminhos. Laterais recebem a ambientação e o indicador
offline não rouba espaço da cena. Instalação/atualização continua no menu.
Ver [regras, arquitetura e validação](docs/web_mobile.md).

Não reintroduzir a antiga mobile-header/mobile-grid/mobile-footer em nenhuma
cena. MobileCanvas adapta primitivas só no draw síncrono e restaura o módulo;
nunca alterar globalmente o renderizador nativo. Congelar somente superfícies
imutáveis: LRU de arte 24 MiB, textos 8 MiB. Limpar composições na troca de perfil.
A regra 1280×720 mobile substitui a adoção anterior de backing HiDPI nesse perfil.

Validação desta correção: **931 testes em 91 módulos, zero falhas**; 14 telas e
11 verificações de toque no Chromium. Combate: 46,3 FPS medianos na emulação;
comparação controlada: 24,6 → 44,2 FPS. Não equivale a medição no celular físico.
Veja o [relatório e limites](docs/validacao_mobile_arte_original.json).

Os hits ampliados das Configurações devem considerar somente os controles da
aba ativa; controles ocultos não podem interceptar sliders. Assinaturas de
preview usam digest da imagem cacheada, evitando serializar base64 a cada frame.

## Blindagens Web de memória e hospedagem

- `web/memfs.py` só limpa animações PNG do MEMFS depois dos loaders. Marcar grupos
  incompletos e repor os arquivos antes de carregar novamente. Nunca remover
  OGG em streaming, JSON de manifesto, fontes ou UI/retratos ainda lazy.
- Extração sequencial: hash/tamanho/inventário verificados, arquivos parciais e
  temporário removidos também no erro/cancelamento; liberar bytes JS antes de
  extrair. Não confundir remoção do MEMFS com redução física do heap WASM.
- Preservar EXPORTAR/IMPORTAR da seleção de saves, schema v15 e confirmação de
  substituição. Não criar outro formato de save nem duplicar a lógica no JS.
- Service Worker é opcional. Getter/registro podem falhar em iframe; degradar
  silenciosamente sem esconder falhas de IndexedDB. Persistência solicitada é
  consultiva; sem concessão garantida. Downloads dependem da política do host.
- `devtools/web_hosting.py` audita arquivos reais ao final do build, incluindo
  auxiliares, e avisa sobre Cloudflare Pages/itch.io. Relatório em build/, jamais
  fora do inventário de release em dist/. Atualizar limites com fontes oficiais.
- Ver [contratos e tamanhos medidos](docs/build_web.md).

Blindagens Web de memória/hospedagem validadas: 942 testes, 6 verificações
iframe/backup, 10 PWA/offline e 14 telas mobile. Nenhum limite auditado excedido.
Ver [resultados e restrições](docs/validacao_web_blindagens.json).
