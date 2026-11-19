# AGENTS.md — Scape From Stone de Cut

**Atualização de 17/11/2026:** na branch `feature/balanceamento-roguelite`, a seção 11 prevalece sobre as descrições anteriores de morte, recompensas, economia, níveis de cartas e saves.

Roguelite/deckbuilder por turnos em Pygame. Leia este arquivo antes de alterar o código.
Onde o contexto original (design) diverge do código, o item está marcado com **TODO/Verificar**.

## 1. Visão geral do jogo

- **Nome:** Scape From Stone de Cut. **Gênero:** estratégia, roguelike, RPG de turno, deckbuilding.
- **Plataforma:** PC. **Classificação:** a partir de 10 anos.
- **Equipe:** CyberGames — projeto acadêmico, Barbacena, 2026.
- **Repositório:** https://github.com/CyberSafe-Games/Scape-from-stone-de-cut.git
- **Slogan:** "A floresta resiste. Escreva sua estratégia. Defenda sua terra."
- **História:** Jaum Manel atravessa sete territórios para libertar a tribo Stone The Cut, capturada por Zanzara, Líder do Clã Moskar. O jogo tem cutscenes de introdução e pós-tutorial em `src/config/cutscenes.py`.
- **Controles:** point-and-click com atalhos opcionais. Botão esquerdo seleciona cartas, habilidades e menus. Esc cancela/volta nos menus (implementado em várias telas). Botão direito como cancelar está no contexto, mas **TODO/Verificar** — não foi encontrado tratamento de `button == 3` no código.

## 2. Stack e como rodar

- **Linguagem:** Python 3.12+ (rodando hoje com Python 3.12.3).
- **Framework:** Pygame. O contexto fala em "Pygame-CE" e resolução interna 1280×720; o código renderiza em superfície virtual **1920×1080** (`WIDTH`/`HEIGHT` em `src/config/settings.py`) e abre a janela em **1280×720** (`LEGACY_WINDOW_SIZE`), com F11 (tela cheia/janela) e F10 (maior 16:9 / 1280×720). **TODO/Verificar** a resolução "oficial" do design.
- **60 FPS** (`FPS = 60`). `requirements.txt` declara apenas `pygame>=2.6.0`; este ambiente roda pygame 2.5.2.
- **Sem CI, lint, typecheck ou formatter.** A verificação é a suíte de testes.

```bash
python3 -m pip install -r requirements.txt
python3 main.py

# Teste único / arquivo específico (testes usam stdlib unittest, não pytest)
python3 -m pip install -r requirements-dev.txt
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m unittest tests.test_window_modes -v

# Suíte inteira (pesada por causa dos assets; pode passar de 5 minutos)
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m unittest discover -s tests -t .
```

- Neste computador Windows, usar `.venv\Scripts\python.exe` (Python 3.12.10, pygame 2.6.1). O launcher `py` reconhece a instalação; não depender do PATH global.
- Os testes de sprites e os scripts em `devtools/` usam **Pillow e NumPy**, declarados em `requirements-dev.txt`. Prévias não leem/gravam saves; prepares regeneram assets e docs.
- A suíte é unittest; pytest não está em `requirements.txt` (há uma referência desatualizada a `pytest` em `docs/bosses_oito_frames.md`).
- Saída esperada de ruído: aviso de AVX2 do pygame, "Hello from pygame" e avisos de som ausente — não são falhas.

## 3. Estrutura do projeto (mapeada do código)

```
main.py                 # Entrada: cria Managers, inicia MenuScene, loop (eventos de janela antes de cena)
requirements.txt        # pygame>=2.6.0 (único runtime dep)
src/
  config/               # Fonte canônica: settings.py (resolução, FPS, paths), layout.py (poses/timers), colors.py (paleta)
  settings.py, game.py  # Shims de compatibilidade — não adicionar código novo neles
  core/                 # window.py (superfície 1920x1080 + letterbox), scene_manager.py (cena + pilha de modais),
                        # asset_manager.py (cache de sprites/fontes), audio_manager.py (IDs estáveis de som)
  scenes/               # menu, save_selection, tutorial, map, battle, backpack (mochila), shop (loja),
                        # cemetery_modal, confirmation_modal, base_scene.py (classe base)
  systems/              # Regras puras (sem pygame): combat_engine (motor de combate), card_catalog/card_definitions
                        # (fonte das cartas), deck_loadout, save_manager (saves/migração), territory_map,
                        # campaign_progress, shop_system, enemy_factory, normal_enemy_catalog, animações/kits
  models/               # entity/player/enemy/card/deck, effects/ (TacticalCardEffect, ultimates, efeitos)
  ui/                   # battle_hud, card_view, entity_view, card_fx, theme/dark_fantasy_theme (helpers de desenho)
assets/                 # Sprites, áudio, cartas, efeitos — centenas de MB comitados; não varrer em massa
devtools/               # Scripts de preparo/preview de sprites (Pillow/NumPy)
docs/                   # Specs de animação/arte em pt-BR + prévias geradas (PNGs/GIFs grandes)
tests/                  # unittest; fixtures em tests/fixtures/ (hashes de efeitos de boss)
saves/                  # Saves JSON por slot (gitignored): 3 slots + save especial `modo_teste`
```

- Fluxo de telas: **Menu → Seleção de Save → (Tutorial, só em save novo) → Mapa de territórios → Batalha**. Mochila e Loja são cenas próprias; Cemitério e Confirmação são modais sobre a pilha do `SceneManager`.
- Entrada `main.py` trata F11/F10 e redimensionamento antes de delegar eventos à cena; ao sair, chama `save_on_exit()` da cena ativa.
- Efeito imediato: cenas desenham na superfície virtual passada ao `draw()`; mouse deve ser convertido com `window_manager.map_to_virtual()` / `get_virtual_mouse_pos()` (nunca usar `event.pos` direto).

## 4. Regras e mecânicas do jogo

**Combate (por turno, Jaum Manel vs 1 inimigo por cena):**
- Turno do jogador: a energia é restaurada e **+1 de energia máxima por turno** (começa em 2, limite 8); a mão é completada (`refill_hand`, mão inicial 3, cresce até **5**); jogar cartas gasta energia e as cartas restantes ficam na mão ao encerrar o turno.
- Turno do inimigo: pausa ~800 ms (`windup_ms`; 270 ms em follow-up de combo), executa a ação (ataque ou defesa) e escolhe a próxima intenção. A intenção é exibida na HUD (`EnemyIntentView`).
- Bloqueio (Escudo) é consumido antes da vida. Vida dos inimigos e o valor das ações sobem com o andar (`create_enemy(level, ...)`).
- Baralho com três pilhas (compra/mão/descarte); ao esvaziar a compra, o descarte é reembaralhado (`DeckManager.draw_cards`).

**Cemitério (confirmado no código):** no turno do jogador, descartar uma carta da mão custa **1 de energia** (sem comprar outra). Por turno, há **1 troca grátis** (troca carta da mão por carta do descarte). Abre pelo botão na UI ("Cemitério (1 E.)") ou tecla **C**; é um modal (`CemeteryModal`). Não é expulsão permanente do deck.

**Ultimate:** `ultimate_threshold = 20`. No início de toda batalha, o motor define `ultimate_charge = 0`. A carga cresce conforme a energia gasta em cartas e existe apenas durante a batalha. Preserve as Ultimates desbloqueadas e a escolha equipada no save. `SaveManager._normalize()` descarta o campo legado `carga_ultimate`. A transição para Tekks é a segunda fase do mesmo combate e conserva a carga do jogador.

**Estado e debuffs** — `src/models/entity.py` e `src/systems/combat_engine.py`

- **Veneno:** aplique 1 ou 2 stacks por ação, limitado a `0 <= poison_stacks <= 5`. Toda aplicação renova `poison_turns = 2`, inclusive com 5 stacks ativos. Ao fim do turno da entidade afetada, aplique `5 * poison_stacks` de dano direto que ignora Escudo e reduza `poison_turns` em 1. Ao chegar a 0, zere os stacks.
- **Sangramento:** aplique 1 ou 2 stacks por ação, limitado a `0 <= bleed_stacks <= 5`. Toda aplicação renova `bleed_turns = 2`, inclusive no teto. Após uma ação ofensiva que tire vida do alvo, aplique `3 * bleed_stacks` de dano direto à entidade afetada se `bleed_triggers_this_turn < 2` e incremente o contador. Um ataque com vários golpes conta como uma ação. Zere o contador no início do turno da entidade. No fim do turno, reduza `bleed_turns` em 1 e zere os stacks se chegar a 0.
- **Choque:** exclusivo de inimigos. A habilidade comum de Jozephino aplica 1 stack e sua Ultimate aplica 2. Os stacks se somam e duram 1 turno. Após restaurar a energia no início do próximo turno do jogador, aplique `max(0, energia - stacks)` e remova todos os stacks imediatamente.
- **Ciclo da batalha:** inicialize `ultimate_charge = 0` e limpe todos os efeitos de combate na entrada. Na vitória ou derrota, o motor limpa Veneno e Sangramento de ambas as entidades, zerando stacks, durações e contador de Sangramento. Os demais efeitos e a carga são estado local do encontro e ficam fora do save. A troca de fase do chefe mantém o estado do jogador no mesmo combate.
- **HUD de status:** mostre stacks, turnos restantes e dano por gatilho em Veneno e Sangramento. Mantenha os textos das cartas e habilidades em pt-BR, incluindo a quantidade aplicada e a duração.

**Fim de run:** ao zerar a vida do herói, a cena de batalha mostra "VOCÊ MORREU" com o andar alcançado; tecla **R** reinicia a batalha **retomando o último checkpoint do save**; ESC permite voltar ao mapa/menu. **TODO/Verificar** — o contexto descreve *permadeath* com reset total da run; o código mantém o checkpoint (não apaga progresso).

**Vitória no combate:** inimigos com vida 0 → tela "VITÓRIA!"; se não for revanche (`is_replay`), o jogador escolhe **1 carta entre até 3 opções sorteadas entre as que ainda não possui** ou pula; recompensas são adicionadas à coleção (não ao deck equipado).

**Vitória na run:** derrote Zanzara, Líder do Clã Moskar, no Santuário de Pedra para concluir a campanha.

**Moedas:** ganhas em combate (acumuladas no HUD e coletadas na vitória); usadas na Loja.

## 5. Progressão e conteúdo

**Campanha (7 territórios)** — `src/systems/territory_map.py`, desbloqueio progressivo (só libera o próximo ao concluir o atual):

| # | Território | Nome interno | Nome de exibição |
|---|---|---|---|
| 1 | Pedra do Corte | `Guardião da Pedra` | Octav, o lobisomem |
| 2 | Mata Sombria | `Álvaro e Tex` | Alvar & Tekks, Rastreadores |
| 3 | Ruínas Ancestrais | `Goblin Nerd` | Jozephino, o Inventor |
| 4 | Pântano Abissal | `Gordofera` | Sir Thomas, a Besta Fera |
| 5 | Fortaleza Caída | `Corpo Seco` | Jan-Pietro, o Imortal |
| 6 | Pico da Vigília | `Carrasco da Vigília` | Labrro, o Carrasco |
| 7 | Santuário de Pedra | `Zanzara` | Zanzara, Líder do Clã Moskar |

`Álvaro e Tex · Pequeno` é exibido como **Tekks** na segunda fase. Resolva os nomes visíveis com `boss_display_name()` de `src/config/boss_names.py` no HUD, mapa, diálogos e anúncios. Preserve `Enemy.name`, `boss_id`, `Territory.boss_key`, slugs e chaves de sprites, retratos, cartas de intenção, áudio e lógica de combate. A função normaliza maiúsculas e acentos para consultar o mapeamento.

Cada território tem **2 encontros comuns** (`ROAD_FIGHTS = 2`) antes do chefe. `normal_enemy_catalog.py` define os inimigos comuns por bioma e `enemy_factory.py` cria os chefes.

**Tutorial:** primeiro acesso a um save inicia `TutorialScene` (batalha guiada com balões/caixas de texto e recompensa fixa de +30 moedas). Conclusão libera o mapa (`tutorial_concluido` no save).

**Cartas:** `CARD_SPECS` em `src/systems/card_definitions.py` define as 20 cartas jogáveis. O mesmo arquivo lista as 75 em desenvolvimento em `ADDITIONAL_CARD_SPECS`. O catálogo filtra as indisponíveis de recompensas, loja e montagem do deck. `LEGACY_CARD_NAMES` preserva a migração dos nomes usados em saves antigos.

**Mochila/Deck:** deck por **espaços individuais** (um espaço por cópia); limite na constante `DECK_SLOT_LIMIT` (hoje 18), máximo de 3 cópias da mesma carta; clique na coleção adiciona 1 cópia ao próximo espaço livre; clique num espaço preenchido remove só aquela cópia; deck inicial preenche com até 3 cópias de cada carta inicial (`deck_loadout.py`); desbloqueio pertence à run; coleção persiste no save.

**Loja ("Mercado Silencioso")** — `shop_system.py`, persistida no save:
- Aumento de **15 de vida máxima** por **50 moedas**, limite de **3 por run**. A vida atual persiste entre encontros comuns e a vitória sobre chefe de território recupera 30% da vida máxima.
- Cartas do catálogo por **25 + 15 × custo de energia**; cada compra adiciona o tipo à coleção (adicione cópias na Mochila).

**Saves:** um JSON por slot em `saves/` (gitignored), 3 slots + `modo_teste` (Laboratório de Testes, acesso em `[T]` na tela de seleção, invulnerável). `SAVE_VERSION = 12`; `SaveManager._normalize()` valida e migra saves antigos — ao mudar o schema, incremente `SAVE_VERSION` e estenda `_normalize()`. Saves v8 (6 espaços de tipos × 3 cópias) migram em `normalize_collection_and_slots()` para 18 espaços individuais.

**Moedas por inimigo:** cada vitória concede moedas do inimigo derrotado (acumuladas e coletadas na vitória). Progresso por vitória: `record_victory` / `record_road_victory` em `campaign_progress.py` gravam e liberam o próximo território.

## 6. Estado atual de implementação

**Implementado:** campanha completa de sete territórios, cutscenes de introdução e pós-tutorial, diálogos de chefes, menu de configurações, trilha por contexto, efeitos sonoros, deck por espaços individuais, recompensas, loja, tutorial e Laboratório de Testes. Animações de espera e dano do jogador e dos chefes usam 8 quadros. Os kits também têm ações com 12 quadros. Os inimigos comuns usam 8 quadros.

**Pendente no design:** permadeath com reset total da run. O jogo atual retoma o último checkpoint após a derrota.

**Cronograma da equipe (contexto):** sprints semanais de 23/09 a 24/11; apresentação parcial em 28/10 e final em 25/11. Loja e minibosses nas primeiras sprints; boss final e recompensas na sprint 6; balanceamento/testes na 7; bugs e polimento nas 8–9.

## 7. Convenções de código e boas práticas para agentes

**Regras para agentes:**
- Ler o código existente antes de propor mudanças e seguir o estilo já usado.
- Não mudar regras de combate já finalizadas sem pedido explícito.
- Manter compatibilidade com 1280×720/60 FPS (**TODO/Verificar** — ver divergência de resolução na seção 2).
- Manter o jogo 100% jogável com mouse.
- Textos de interface e documentação em português (pt-BR).
- Não adicionar dependências sem necessidade e sem avisar.
- Ao terminar uma tarefa, informar o que mudou e como testar.

**Práticas do repositório:**
- Código em inglês; strings, docstrings, UI e docs em pt-BR. Indentação de 4 espaços.
- Regras em `src/systems/` **sem importar pygame** (`combat_engine`, `save_manager`, `territory_map`...). Renderização em `src/scenes/` e `src/ui/`. Configuração canônica em `src/config/`.
- Testes com `unittest` (não pytest). Rode módulos específicos; a suíte completa é asset- pesada e pode exceder 5 minutos.
- Assets: não regerar sprites "na mão"; use `python3 -B devtools/prepare_<alvo>.py` após conferir `docs/<alvo>.md`. Testes de hash/pixel (`tests/fixtures/boss_ultimate_effect_hashes.json`, pixel-identity) falham ao trocar arte — atualize fixture e arte juntos, e só com mudança intencional.
- Adicionar/alterar carta: edite `CARD_SPECS` e forneça `assets/cards/<id>.png`, `assets/card_effects/<id>_1..4.png` e `assets/player/twelve_frames/<id>_1..12.png` — há testes que cobram todos esses arquivos.
- Adicionar/alterar save: incremente `SAVE_VERSION`, estenda `_normalize()`, preserve a semântica de `modo_teste`.
- Commits seguem Conventional Commits pt-BR (`feat:`, `fix:`...). `saves/` e `_arquivos_antigos_para_deletar/` ficam fora do Git.
- `assets/` e `docs/` somam centenas de MB de binários comitados: localize arquivos específicos por nome, não varra o disco.

**Fluxo da equipe (contexto):**
- Tarefas divididas por membro e organizadas no Trello.
- Toda mecânica nova deve ser testada (funciona + não conflita com as finalizadas) antes de ir ao GitHub.
- Mudanças pequenas, focadas e não quebrantes.
- Decisões de escopo, identidade visual e mecânicas são **humanas**; a IA é apenas apoio.

**Cartas de intenção e enquadramento**

- `src/ui/enemy_intent_view.py` encaixa e centraliza a carta inteira no espaço da miniatura, com proporção preservada. Reserve espaço separado para ordem e valor. Os ícones ficam acima do inimigo, no canto superior direito.
- O hover é determinado pelo retângulo do ícone. Com arte de carta completa, mostre apenas a carta ampliada, sem painel lateral de texto. O centro horizontal fica no meio da arena e o centro vertical em 43% da altura. Respeite os limites da superfície virtual e deixe margem para o HUD e a mão. Desenhe o preview sobre a arena e o HUD, sem área interativa própria. Quando faltar uma carta completa, use o tooltip compacto.
- Use `assets/intent_art/<slug>/` para as artes de intenções e `assets/cards/` para as cartas jogáveis. Mantenha os valores e efeitos impressos sincronizados com o código. Um recurso `ultimate.png` pode distinguir a carta de Ultimate mesmo quando ela compartilha a animação de outra ação.

## 8. Identidade visual e narrativa

- **Pixel art** com materiais orgânicos; atmosfera de invasão e contraste entre facções.
- **Tribo/Jogador (Stone The Cut):** marrom, ocre, verde-musgo, vermelho-fogo; madeira, osso, penas, totens.
- **Clã Moskar (invasores):** cinza-metal, azul-aço, preto; armaduras, armas de fogo, bandeiras de guerra. (Obs.: no jogo há outros chefes/inimigos com paletas próprias, p.ex. Zanzara em azul escuro e faixa branca.)
- **Cartas:** ataque com moldura vermelha, defesa/habilidade com moldura azul (o código usa `RED` para attack, `BLUE` para skill e `GOLD` para power); seguir o padrão por tipo.
- **Jaum Manel:** magricela, penas, roupas e paleta aprovadas; mantém silhueta e pivô dos pés.
- **Chefe final:** Zanzara, Líder do Clã Moskar, é um necromante de kimono preto com foice e efeitos verdes. Seu kit usa Foice Sombria, Passo do Barqueiro, Grilhões das Almas e Travessia Final.
- Sprites gerados com auxílio de IA; há fallback visual desenhado proceduralmente no `AssetManager.get_fallback_sprite()` para sprites ausentes.
- **Slogan:** "A floresta resiste. Escreva sua estratégia. Defenda sua terra." **Narrativa:** Jaum Manel salva a tribo da Stone The Cut das mãos de Zanzara e do Clã Moskar; o mapa de 7 territórios conta essa jornada.

## 9. Histórico de integração — 11/11/2026

As seções 9 e 10 registram o ambiente e as decisões das etapas de áudio anteriores. Consulte as seções 3 a 8 para o estado atual do projeto.

Estas decisões atualizam as descrições históricas de Zanzara e áudio acima:

- Ambiente utilizado nessa etapa: `C:\Users\marco\OneDrive\Desktop\Scape-from-stone-de-cut-git`; usar seu Python `.venv\Scripts\python.exe`. Branch usada na integração: `feature/audio-enemies`.
- Etapa 3 de áudio e redesign de Zanzara concluídos e aprovados pelo usuário no estado local anterior à conciliação. Preservar aparência, animações, escala e sons aprovados. Após integrar mudanças externas, repetir as validações pertinentes.
- Zanzara é necromante de kimono preto, foice e efeitos verdes: Foice Sombria, Passo do Barqueiro, Grilhões das Almas e Travessia Final (avatar de Caronte no barco). Não retomar ataques de moedas, maré ou amuleto antigo. Foice e Passo têm som de lâmina e cauda de sangramento; Grilhões têm portal e almas; Travessia usa a risada enviada. O Game Over mantém voz e ambientação, com essa risada entrando aos 2,8 segundos.
- Durante ajustes de um personagem, executar os testes direcionados e abrir apenas o piloto daquele personagem para o usuário avaliar e refinarmos. Esse fluxo faz parte da implementação autorizada; não substituir por listas de players no chat nem pedir confirmação repetida.
- No fechamento da etapa, executar os testes consolidados sem janelas e abrir somente uma instância do `main.py` para o usuário avaliar o jogo completo. Não abrir um piloto de cada personagem nesse momento. Em validações automáticas de pilotos, usar `--smoke` e configurar drivers dummy antes de importar Pygame.
- Preservar originais externos e recursos aprovados; novos derivados de áudio do jogo devem ser OGG, com fontes e composição registradas. Não sobrescrever versões existentes desnecessariamente. Novos arquivos na pasta autorizada podem ser localizados, preparados, integrados e testados automaticamente no escopo pedido.
- Não afirmar escuta crítica, campanha completa jogada ou ausência perceptual de sobreposições com base somente em testes técnicos.
- Preservar alterações preexistentes. Não executar git add global, stash, reset, restore ou descarte sem autorização. Commits, publicação e merge na main exigem autorização; o usuário autorizou trazer a main para esta branch, resolver conflitos e validar, mantendo a main intacta. A revisão combinada das diferenças foi realizada e o usuário autorizou a publicação da PR; não mesclar na main sem aprovação do grupo.
- Manter este arquivo atualizado quando o usuário aprovar decisões persistentes, novos recursos ou ajustes de fluxo. Documentar pendências reais e não reabrir decisões já aprovadas sem necessidade.
- O catálogo agora tem 95 cartas (20 originais e 75 novas ainda bloqueadas por falta de arte/animações). Os chefes seguem usando ações; uso de cartas por chefes não foi implementado na main integrada.
- Atualização da conciliação: main ae383f5 integrada nesta branch com dois conflitos reais resolvidos. Validação posterior: 472 testes aprovados em 51 módulos isolados e auditoria de 79 efeitos aprovada. Usar `devtools/validate_isolated_tests.py` para a suíte completa neste computador, liberando caches entre módulos; a execução monolítica excedeu memória. Ver `docs/comparacao_main_etapa3.md` e `docs/validacao_main_por_modulo.json`.
- Revisão do retrato após conferir a main: preservar `bosses/zanzara-necromante-v8.png` como rosto de Zanzara na HUD; não sobrescrever com o retrato `framed/zanzara.png` recebido do grupo, que não corresponde à aparência aprovada. A main elevou FLASH_DURATION de 220 para 560 ms e trouxe recuo/mesclagem geral; a reação dedicada de Zanzara já foi conciliada para usar essa duração global. O usuário aprovou o resultado no piloto.
- Moldura de Zanzara: reutilizar a moldura do protagonista com o rosto aprovado `bosses/zanzara-necromante-v8.png` composto dentro dela. O modo `framed-content` mantém as bordas do recurso do protagonista sem alterar os PNGs originais. A HUD deve seguir a mesma proporção e dimensão dos demais retratos emoldurados; testes de retrato aprovados após essa composição.
- Retrato e moldura de Zanzara aprovados pelo usuário após conferência no piloto. Refinamento seguinte: a reação de dano agora usa FLASH_DURATION global em vez de 220 ms fixos, distribuindo os oito quadros ao longo dos 560 ms atuais. Sprites, escala, golpes, áudio e reações gerais do grupo preservados. 27 testes direcionados aprovados; fluidez visual desse ajuste conferida e aprovada pelo usuário no piloto. Tecla H permite ver o protagonista acertando Zanzara; teclas 1–4 mostram os ataques contra o protagonista.

## 10. Etapa final — trilha sonora

- Branch de trabalho: `feature/trilha-sonora`, criada por solicitação do usuário a partir do estado aprovado de áudio e Zanzara. Manter as novas alterações de trilha nesta branch, separadas de `feature/audio-enemies` e da PR #13.
- Direção aprovada: fantasia sombria com percussão e elementos da floresta.
- Escopo: selecionar e avaliar músicas, integrar reprodução em menus/mapa/combates/chefes, ajustar loops, transições e volumes. As 75 cartas novas estão fora do escopo desta etapa; não implementar seus sons, artes ou regras.
- Os cinco originais baixados e suas fontes estão em `C:\Users\marco\Documents\Codex\2026-11-10\navegador-plugin-browser-openai-bundled-x20-2\outputs\trilha-sonora`. Preservar originais, fontes e efeitos sonoros já aprovados; derivados do jogo em OGG, sem sobrescrever versões anteriores desnecessariamente.
- Avaliação por partes em piloto durante a implementação. Fechamento com testes sem janelas e conferência do jogo completo no `main.py` pelo usuário.
- A PR da trilha será preparada/publicada depois dos ajustes e da aprovação, conforme pedido do usuário. Não enviar alterações novas à PR #13 e não realizar merge na main sem aprovação do grupo. Conferir a base remota e a integração da PR #13 antes de publicar a nova PR.
- Primeiro piloto da trilha preparado: `testar_trilha_sonora.bat` / `devtools/preview_soundtrack.py`. Cinco candidatos em OGG, com originais conferidos por SHA-256; fontes em `docs/trilha_sonora_fontes_v1.json`. Teclas 1–5 escolhem contexto, A/S/D/F disparam golpes, setas ajustam volume, M silencia música, T alterna menu/mapa na faixa 1. Teste `--smoke` aprovado sem janelas. Músicas, volumes e loops ainda aguardam escuta do usuário; troca automática na campanha será feita após essa seleção. Não presumir aprovação por carregamento técnico.
- Avaliação do primeiro piloto musical: faixas 1 (Deep forest) e 2 (The Last Stand) aprovadas pelo usuário. Preservar. A faixa de chefes deve ser revista com a referência de energia do trecho 25–35 s do vídeo de Tarzan enviado (x3u1_181N7g), usando composições independentes e licença registrada. Não copiar gravação, melodia ou arranjo; não alegar escuta desse trecho, que não pôde ser reproduzido nesta sessão. A seleção final foi aprovada posteriormente: Jungle Tribe para Zanzara e Jungle Chase para os demais chefes.
- Piloto musical, rodada 2: teclas 3 (Jungle Tribe) e 6 (Jungle Chase) são novas opções de chefes. Faixas 1 e 2 aprovadas foram conferidas por SHA-256 e permanecem intactas. A Jungle Guerilla anterior está preservada, fora da seleção ativa. Fontes/derivados da rodada 2 em docs/trilha_sonora_fontes_v2.json. O usuário aprovou Jungle Tribe para Zanzara e Jungle Chase para os demais chefes; as alternativas anteriores de Zanzara ficam fora da seleção ativa.
- Seleção final aprovada e integrada na campanha: menu/mapa Deep forest (1), combates comuns The Last Stand (2), todos os demais chefes Jungle Chase (6) e Zanzara Jungle Tribe (3). src/config/music.py é a configuração canônica. MusicDirector/SceneManager trocam o canal musical com saída/entrada gradual, sem reiniciar ao mudar mapa/menu ou a fase do mesmo chefe. Vitória e Game Over retiram a música sem interromper os efeitos. Volume inicial 45%. 102 testes de áudio e 6 testes novos de música aprovados; smoke do piloto com as quatro faixas aprovado. Conferência final das transições e loops no main.py permanece para o usuário, antes de publicar a PR da trilha.

## 11. Balanceamento roguelite — implementação de 17/11/2026

- Publicação posterior autorizada pelo usuário: PR #24 conferida como integrada; main remota `0240b5b` tem árvore idêntica ao commit `3e465dc`. Branch nova `feature/refino-cartas-roguelite` criada a partir de origin/main, preservando todos os ajustes locais aprovados. Publicar esta revisão em nova PR; não fazer merge. Roteiro em `docs/playtest_refino_cartas.md`.
- Investida final aprovada: custo dois, dano **18/24**, depois remove **25% do Escudo restante**, arredondando para baixo; não quebra antes do ataque nem causa dano extra à vida. Totem bloqueia a ação completa. A remoção não renova durações das camadas. Esta regra substitui a proposta intermediária 20/26 de dano simples.
- Validação da nova publicação: **664 testes/68 módulos reexecutados e aprovados**, sem reaproveitamento; `docs/validacao_pr_refino_cartas.json`. Smoke aprovado e cartas finais conferidas. Não reinterpretar os resultados históricos do bot como validação desta revisão.

- Revisão seguinte autorizada: Investida dano 20/26 por duas energias (paridade com Arco, sem efeito novo); Máscara cura 14/18, Escudo 22/28 e custo quatro preservados; Amuleto remove benefícios/Escudo/Força inimigos e preserva debuffs/durações; Surto mostra ganho adicional sob teto e aviso de ganho zero, sem mudar sua mecânica. Previsão do Surto considera energia máxima do próximo turno e bônus já pendente, antes de ações futuras/Choque. 123 testes reexecutados em dez módulos aprovados; consolidado incremental 661/68. Smoke aprovado. Mudanças locais, sem atualizar PR #24; simulações anteriores não medem estes ajustes.

- Revisão mais recente aprovada: Mana Ancestral restaura energia para **8 e limpa efeitos negativos, sem comprar cartas**. Mantém carga 20 e ativação por cinco de energia; Machados mantém custo cinco e dano 40/50. Resultados das 100 runs anteriores correspondem à alternativa sem limpeza e não validam esta revisão. Alteração local, ainda fora da PR #24.
- Verificação da revisão com limpeza: 49 testes reexecutados em quatro módulos, todos aprovados; consolidado incremental 659/68. Smoke da interface aprovado e descrição conferida. Efeitos positivos preservados; mão/pilhas não recebem cartas pela Mana.

- Amostra posterior autorizada de 100 runs variadas na proposta local Mana/Machados: **11 vitórias/89 mortes/zero limites técnicos**; dez planos com dez runs, 20 tipos no conjunto dos planos e especiais 34/33/33. Sustentação com Máscara venceu 7/10 e defesa/cura 4/10; demais planos 0/10. Não enumera todas as combinações nem estima a probabilidade humana. Ver `docs/resultado_decks_variados_100.md` e JSON correspondente. Nenhuma regra adicional alterada; resultados locais, PR #24 não atualizada.

- Revisão experimental local posterior ao playtest de 18/11, autorizada condicionalmente após comparar: Machados Gêmeos custa **5 energia** em LV1/LV2, dano 40/50 preservado. Mana Ancestral **somente restaura para 8**, sem comprar cartas nem limpar efeitos; carga 20 e ativação 5 preservadas. Comparação pareada: gerais 8/50 antes, 9/50 depois; foco Machados/Mana 1/20 antes, 0/20 depois (19 mortes e um limite técnico). Não afirmar equilíbrio final nem taxa humana. 113 testes reexecutados/nove módulos aprovados; consolidado incremental 659/68 e smoke aprovado. Ver `docs/comparacao_mana_machados.md`. Mudanças desta rodada ainda locais, sem atualizar PR #24; publicar somente após avaliação.

- Em 18/11 o usuário autorizou commit, push da branch e abertura de PR para o grupo testar o balanceamento completo. Não fazer merge nem habilitar auto-merge; aguardar avaliação humana. Roteiro do grupo em `docs/playtest_balanceamento_grupo.md`. A autorização de publicação substitui a proibição anterior de push nesta etapa.
- Fechamento para publicação: suíte completa reexecutada em processos isolados, **658 testes aprovados nos 68 módulos**, sem reaproveitar resultados. Relatório `docs/validacao_pr_balanceamento.json`. Main/origin/main conferidas em `ad593a5` antes da publicação.

- Atualização aprovada em 18/11: os três especiais exigem **5 de energia na ativação**, além de 20 de carga. Clique sem energia não consome carga nem dispara ativação; carta pronta permanece para próximos turnos. Pagamento não recarrega o especial. Mana paga primeiro e depois restaura para 8. Custo composto sobre arte original, preservando PNGs. Não alterar efeitos/dano automaticamente. Validação: consolidado incremental 658 testes/68 módulos (nove módulos reexecutados), smoke aprovado; 50 campanhas com aquisição real e cartas de cura deram 8 vitórias, todas defesa/cura. Ver `docs/validacao_especiais_custo5.md`; não interpretar 16% como probabilidade humana nem comparar diretamente com matriz sem cartas de cura.

- Revisão mais recente aprovada: **três curas da loja por run**, até 20 HP cada, preços **30 / 45 / 60 ouro**. Contador `curas_loja_run` persistido, reset apenas na nova run; vida cheia/falha não cobra nem consome compra. Save v14; v13 migra com contador zero porque não havia histórico das curas. Backup usa a versão de origem (`.v13.bak`, `.v12.bak` etc.). Resultados antigos com cura ilimitada são históricos e não validam este novo limite.
- Validação da cura progressiva: consolidado de 656 testes aprovados/68 módulos, com 26 módulos relacionados reexecutados e demais resultados anteriores reaproveitados; smoke da interface aprovado. Nas 420 tentativas novas do bot sem cartas de cura, defesa/controle com Rugido concluiu 4/10 no modo aquisição real (antes 8/10 com cura ilimitada); híbrido/controle com Mana caiu de 5/10 para 0/10. Não compensar automaticamente com outras mudanças de combate. Ver `docs/validacao_cura_progressiva.md`.

- Comparação posterior de dano/híbrido/defesa: `docs/resultado_decks_dano_hibrido_defesa.md` demonstrou rotas sem cartas de cura. Com cura paga na loja e até três LV2, híbrido com limpeza/Mana venceu 5/10 casos de aquisição real e defesa com limpeza/Rugido venceu 8/10. Defesa sem fonte ofensiva não tem via de dano. Pureza desde o primeiro encontro só é testada no controle com deck pronto; runs reais começam com Socos/Protetoras. Não generalizar “só defesa/cura vence” a partir da matriz inicial. Consolidação incremental atual: 649 testes em 68 módulos; regras e valores do jogo não foram alterados nessa comparação.

- Continuação da avaliação: ver `docs/fechamento_balanceamento_roguelite.md`. Bot corrigido para usar cura, dosar suporte, evoluir cópias equipadas e planejar a Ultimate. Matriz atual de 60 campanhas mantém zero melhorias permanentes: apenas defesa/cura completou nesta amostra. Não alterar o jogo para satisfazer o bot nem declarar diversidade validada. Consolidação incremental atual: 643 testes em 67 módulos aprovados; falta playtest focado. Sprite do fragmento depende de outros membros e não bloqueia o fechamento técnico.

- Rótulos visíveis de nível das cartas: **LV1/LV2**, conforme preferência posterior do usuário. Referências N1/N2 em diagnósticos anteriores significam os mesmos níveis. Alteração apenas de apresentação; sem novo nível ou regra.
- Ouro compra cura de até 20 de vida atual, sem ultrapassar o máximo, respeitando o limite/preços progressivos acima. Vida máxima é comprada somente com fragmentos entre runs. Não há bônus automático por morrer. Bônus temporários já comprados em saves anteriores são preservados apenas até aquela run terminar; `melhorias_vida_run` é legado somente para leitura, não uma oferta nova.

- O usuário autorizou implementar a proposta após o diagnóstico. Branch `feature/balanceamento-roguelite`, base main `ad593a5`; sem commit, push ou merge. Não publicar nem integrar na main sem autorização. Ver `docs/implementacao_balanceamento_roguelite.md` e o diagnóstico original para valores e limites.
- Save v14: `perfil` por slot e `run` separados no JSON; `progresso` é projeção em memória para cenas antigas. Preservar backups da migração, revisão de gravação, rejeição de schema futuro e isolamento do laboratório. Morte encerra a run; fechar vivo guarda snapshot lógico. Não retornar ao checkpoint morto nem misturar HP intermediário com inimigo reiniciado.
- Cada tipo cria três instâncias N1 estáveis; nomes dos espaços continuam como projeção, `copy_slots` resolve IDs. Evolução é individual, usa três materiais extras + ouro, só na loja, limite três compras por run. N1/N2 juntos respeitam três por tipo e 18 espaços. Materiais fora do deck, limite nove por tipo; não gerar material ao desequipar.
- Primeira vitória oferece até dois tipos novos OU materiais direcionados (1 comum/3 chefe). Ouro creditado pelo motor; partículas não creditam novamente. Chefes dão fragmentos 1/1/2/2/3/3/5 uma vez por run/encontro; confirmação e recarga não duplicam. Revanches são treino sem persistir dano, cura ou recursos.
- Nova run: 30 ouro, vida cheia, seis starters e preparação permanente escolhida; limpa mapa, ouro antigo, aquisições, materiais, evoluções e vida temporária. Perfil preserva fragmentos, melhorias, flags e Ultimates. Tutorial concede os primeiros 30 sem segundo bônus. Vida permanente +5 por nível (3/5/8 fragmentos), energia inicial 3 por 12, preparação I/II por 4/6. Máximos +15 vida, +1 energia e um tipo extra N1.
- N1/N2/preços e chefes usam valores da proposta. Regras globais de status e Ultimates preservadas. PNGs, sprites e áudio originais intactos; textos numéricos são compostos ao renderizar para manter a arte sincronizada com o código.
- Validação consolidada: 636 testes em 66 módulos, incluindo 18 novos, aprovados; relatório `docs/validacao_balanceamento_por_modulo.json`. Runner suporta `--report`, `--resume` e `--recheck`. Prévia `devtools/preview_roguelite.py --smoke` usa saves temporários. Não sobrescrever relatório histórico da main.
- Balanceamento ainda experimental: 15 campanhas de bot com N1 e zero melhorias permanentes deram 2 vitórias, ambas defesa/cura. Dano/Aura e Veneno/Sangramento não completaram nessa política. Isso não substitui playtest nem prova impossibilidade humana; conferir diversidade, sustentação por cura, Jozephino e chefes finais no jogo. Não alegar campanha humana completa, escuta crítica ou aprovação perceptual automática.


## 12. Loja e altar ilustrados — 19/11/2026

- Redesign autorizado pelo usuário para Loja e Aprimoramento. Cenários e ornamentos em assets/ui/shop/ e assets/ui/workshop/, carregados sob demanda por AssetManager.get_service_image(). A moldura da loja também é usada no altar.
- Loja com quatro cartas por página, preço em ouro, disponibilidade, preview ampliado central sem captura de eventos e efeitos de aquisição/cura. A oficina seleciona uma cópia individual e compara LV1/LV2 a partir de instance_card(), com preço, materiais e limite da run visíveis.
- src/ui/merchant_workshop_view.py compartilha composição e cache. As compras e evoluções usam as transações existentes de shop_system.py e roguelite.py. Preserve a conversão do mouse para coordenadas virtuais e o fluxo de preparação entre runs.
- Fontes das artes, prompts e roteiro de conferência em docs/loja_altar_visual.md. Preview com saves temporários por devtools/preview_roguelite.py --smoke. Cobertura específica em tests/test_merchant_workshop.py.


## 13. Artes de cartas LV1/LV2 — integração de Cartas.zip

- As 20 cartas disponíveis têm PNG LV1 em assets/cards/<id>.png e LV2 prateado em assets/cards/lv2/<id>.png. assets/cards/art_manifest.json registra a identidade e a geometria dos recortes. O ZIP tem os nomes dos packs 1 e 2 LV2 invertidos; o importador os associa pelo conteúdo.
- Encaminhe level, cost e description reais da cópia para AssetManager.get_card_image(). O custo é recomposto no interior do losango original, preservando sua borda. O cache inclui nível, custo e descrição.
- Use with_player_rules para os novos packs. with_rules atende intenções e composição legada. Preserve a moldura prateada ao exibir LV2 e o espaçamento externo da loja/altar.
- Reproduza recortes por devtools/prepare_player_card_packs.py após consultar docs/cartas_packs_lv1_lv2.md. As 20 artes anteriores estão no arquivo local ignorado pelo Git. As regras de combate e os custos continuam definidos no catálogo e na lógica de upgrade.

- Alinhamento revisado dos custos das 40 artes: o manifesto v2 registra cost_polygon e o centroide por imagem. O preparo detecta o interior fechado do losango e o renderizador usa esse contorno, preservando as proporções de cada arte. Centralize a área visível do glifo sobre o centro detectado. A regressão da Aura Rubra e a preservação dos pixels externos têm cobertura em tests/test_player_card_art.py.


## 14. Cartas Ultimate no molde LV2 — 19/11/2026

- Mana, Forças e Rugido custam 2 de energia e 20 de carga. Mana restaura para 8 e limpa todos os negativos; Forças dá +12 Força até o fim da luta e 40 Escudo/2 turnos; Rugido remove Escudo antes de 60 de dano base e aplica Fraqueza/3 turnos. Esta regra substitui os relatos experimentais históricos de custo 5.
- assets/ultimates/<id>.png são cartas completas 316×489, ouro ornamentado e exterior transparente. art_manifest.json registra a mesma posição de custo da Esfera Protetora LV2. get_ultimate_image compõe custo/descrição reais, com cache por regras; não adicionar faixa/badge duplicado no combate.
- Originais substituídos somente no arquivo local ignorado. Preparo reproduzível em devtools/prepare_ultimate_cards.py e fontes/prompts em docs/cartas_ultimate_lv2.md. Preserve animações e sprites de batalha.
