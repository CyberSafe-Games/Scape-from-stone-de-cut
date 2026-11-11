# AGENTS.md — Scape From Stone de Cut

Roguelite/deckbuilder por turnos em Pygame. Leia este arquivo antes de alterar o código.
Onde o contexto original (design) diverge do código, o item está marcado com **TODO/Verificar**.

## 1. Visão geral do jogo

- **Nome:** Scape From Stone de Cut. **Gênero:** estratégia, roguelike, RPG de turno, deckbuilding.
- **Plataforma:** PC. **Classificação:** a partir de 10 anos.
- **Equipe:** CyberGames — projeto acadêmico, Barbacena, 2026.
- **Repositório:** https://github.com/CyberSafe-Games/Scape-from-stone-de-cut.git
- **Slogan:** "A floresta resiste. Escreva sua estratégia. Defenda sua terra."
- **História:** Jaum Manel, jovem indígena, tem a tribo Stone The Cut invadida pelo Clã Moskar e a tribo capturada pelo líder Zanzara. Ele atravessa o território invadido vencendo combates por turno, monta seu baralho ao longo da run e derrota o chefe final para libertar a tribo. Há introdução em quadrinhos e encerramento ao vencer o boss final (**TODO/Verificar** — telas de quadrinhos/encerramento não encontradas no código).
- **Controles:** exclusivamente point-and-click. Botão esquerdo seleciona cartas, habilidades e menus. Esc cancela/volta nos menus (implementado em várias telas). Botão direito como cancelar está no contexto, mas **TODO/Verificar** — não foi encontrado tratamento de `button == 3` no código.

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

- Neste workspace não existe `python`, apenas `python3`.
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
- Turno do jogador: a energia é restaurada e **+1 de energia máxima por turno** (começa em 2, limite 8); a mão é completada (`refill_hand`, mão inicial 3, cresce até **5**); jogar cartas gasta energia; ao encerrar, a mão é descartada.
- Turno do inimigo: pausa ~800 ms (`windup_ms`; 270 ms em follow-up de combo), executa a ação (ataque ou defesa) e escolhe a próxima intenção. A intenção é exibida na HUD (`EnemyIntentView`).
- Bloqueio (Escudo) é consumido antes da vida. Vida dos inimigos e o valor das ações sobem com o andar (`create_enemy(level, ...)`).
- Baralho com três pilhas (compra/mão/descarte); ao esvaziar a compra, o descarte é reembaralhado (`DeckManager.draw_cards`).

**Cemitério (confirmado no código):** no turno do jogador, descartar uma carta da mão custa **1 de energia** (sem comprar outra). Por turno, há **1 troca grátis** (troca carta da mão por carta do descarte). Abre pelo botão na UI ("Cemitério (1 E.)") ou tecla **C**; é um modal (`CemeteryModal`). Não é expulsão permanente do deck.

**Ultimate (confirmado):** barra na HUD mostrando "Carga x/20" (`ultimate_threshold = 20`) e botão de ativar. A carga acumula proporcionalmente à energia gasta em cartas. São 3 ultimates: **Mana Ancestral** (padrão), **Forças Ancestrais** e **Rugido da Floresta**. Desbloqueadas persistem no save; a equipada é selecionada na Mochila.

**Fim de run:** ao zerar a vida do herói, a cena de batalha mostra "VOCÊ MORREU" com o andar alcançado; tecla **R** reinicia a batalha **retomando o último checkpoint do save**; ESC permite voltar ao mapa/menu. **TODO/Verificar** — o contexto descreve *permadeath* com reset total da run; o código mantém o checkpoint (não apaga progresso).

**Vitória no combate:** inimigos com vida 0 → tela "VITÓRIA!"; se não for revanche (`is_replay`), o jogador escolhe **1 carta entre até 3 opções sorteadas entre as que ainda não possui** ou pula; recompensas são adicionadas à coleção (não ao deck equipado).

**Vitória na run:** completar os 7 territórios e derrotar Zanzara abre a sequência de encerramento (**TODO/Verificar** — tela/sequência de encerramento não encontrada no código).

**Moedas:** ganhas em combate (acumuladas no HUD e coletadas na vitória); usadas na Loja.

## 5. Progressão e conteúdo

**Campanha (7 territórios)** — `src/systems/territory_map.py`, desbloqueio progressivo (só libera o próximo ao concluir o atual):

| # | Território | Nível | Chefe |
|---|------------|-------|-------|
| 1 | Pedra do Corte | 1 | Guardião da Pedra |
| 2 | Mata Sombria | 2 | Álvaro e Tex (boss dual, 2 fases) |
| 3 | Ruínas Ancestrais | 3 | Goblin Nerd |
| 4 | Pântano Abissal | 4 | Gordofera |
| 5 | Fortaleza Caída | 5 | Corpo Seco |
| 6 | Pico da Vigília | 6 | Carrasco da Vigília |
| 7 | Santuário de Pedra | 7 | Zanzara (boss final, `is_final_boss`) |

Cada território tem **2 encontros comuns** (`ROAD_FIGHTS = 2`, inimigos de bioma de `normal_enemy_catalog.py`) antes do chefe; minibosses são genéricos e procedurais (`create_enemy`/`is_miniboss_level`) nos primeiros andares, mas os chefes de território são nomeados e pintados à mão (`enemy_factory.py`). O contexto cita "Golenks" — no código há **Golem das Ruínas** (bioma 3) e o **Guardião da Pedra** (boss 1): **TODO/Verificar** qual é o "Golenks" do design.

**Tutorial:** primeiro acesso a um save inicia `TutorialScene` (batalha guiada com balões/caixas de texto e recompensa fixa de +30 moedas). Conclusão libera o mapa (`tutorial_concluido` no save).

**Cartas (20)** — fonte da verdade: `CARD_SPECS` em `src/systems/card_definitions.py`. O contexto cita Golpe/Defesa/Investida/Fortalecer/Fúria/Golpe Duplo; esses nomes foram **substituídos/renomeados** (migração em `LEGACY_CARD_NAMES`: Golpe→Soco Simples, Defesa→Esfera Protetora, Fortalecer→Esfera Escudo, Fúria→Aura Rubra, Golpe Duplo→Machados Gêmeos). O catálogo completo hoje: Esfera Protetora, Soco Simples, Investida, Aura Rubra, Poção Fragilizante, Poção Purificadora, Totem Protetor, Zarabatana Venenosa, Disparo de Arco, Esfera Escudo, Machado Quebra-Escudo, Amuleto Dissipador, Adaga Sangrenta, Máscara Ancestral, Machados Gêmeos, Lança Perfurante, Bola de Fogo, Poção de Cura, Surto de Energia, Poção Venenosa.

**Mochila/Deck:** até 6 tipos de carta equipados, 3 cópias de cada (`deck_loadout.py`); desbloqueio pertence à run; coleção persiste no save.

**Loja ("Mercado Silencioso")** — `shop_system.py`, persistida no save:
- Cura +15 HP por **50 moedas**, limite **3 por run** (não por território), vida máxima 60.
- Cartas do catálogo por **25 + 15 × custo de energia**; cada compra adiciona o tipo à coleção (equipe na Mochila).
- **TODO/Verificar** — compra de upgrades de vida e energia máxima prevista no contexto não existe no código.

**Saves:** um JSON por slot em `saves/` (gitignored), 3 slots + `modo_teste` (Laboratório de Testes, acesso em `[T]` na tela de seleção, invulnerável). `SAVE_VERSION = 8`; `SaveManager._normalize()` valida e migra saves antigos — ao mudar o schema, incremente `SAVE_VERSION` e estenda `_normalize()`.

**Moedas por inimigo:** cada vitória concede moedas do inimigo derrotado (acumuladas e coletadas na vitória). Progresso por vitória: `record_victory` / `record_road_victory` em `campaign_progress.py` gravam e liberam o próximo território.

## 6. Estado atual de implementação

**Implementado e com testes:** combate por turnos completo (pilhas, mão, energia, intenção, bloqueio), 20 cartas e suas regras (`CARD_SPECS` + `TacticalCardEffect`), Cemitério, 3 ultimates + barra de carga, moedas e recompensa/draft, desbloqueio progressivo dos 7 territórios, 2 lutas comuns + chefes por território, Mochila (deck de 6 tipos/3 cópias), Loja (cura + compra de cartas), Tutorial guiado com caixas de texto, tela de seleção de saves, sistema de saves com migração (v8) e laboratório `modo_teste`, chefes Álvaro e Tex (2 fases), Zanzara como boss final, sprites animados (12 frames p/ jogador e chefes, 8 p/ inimigos comuns), áudio (SFX via `AudioManager`, missing files tolerados; `play_music` disponível mas **nenhuma cena chama** — soundtrack pendente no código).

**TODO/Verificar (incompleto ou ausente no código):**
- Introdução em quadrinhos; tela/sequência de encerramento após Zanzara.
- Comportamento de Zanzara conforme a vida diminui (boss final tem fase/ultimate própria, mas ramificação de IA por % de vida não confirmada).
- Permadeath com reset total da run (hoje: checkpoint do save é mantido).
- Upgrades de vida/energia máxima na loja.
- Música de fundo/soundtrack (só SFX).
- Botão direito (RMB) como cancelar.
- Equivalência "Golenks" (design) × criaturas reais no código.
- Consistência entre "resolução interna 1280×720" do contexto e a superfície virtual 1920×1080 atual.

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
- Commits seguem Conventional Commits pt-BR (`feat:`, `fix:`...). `saves/` e `AGENTS.md` estão no `.gitignore` (se quiser versionar este arquivo, remova a linha correspondente).
- `assets/` e `docs/` somam centenas de MB de binários comitados: localize arquivos específicos por nome, não varra o disco.

**Fluxo da equipe (contexto):**
- Tarefas divididas por membro e organizadas no Trello.
- Toda mecânica nova deve ser testada (funciona + não conflita com as finalizadas) antes de ir ao GitHub.
- Mudanças pequenas, focadas e não quebrantes.
- Decisões de escopo, identidade visual e mecânicas são **humanas**; a IA é apenas apoio.

## 8. Identidade visual e narrativa

- **Pixel art** com materiais orgânicos; atmosfera de invasão e contraste entre facções.
- **Tribo/Jogador (Stone The Cut):** marrom, ocre, verde-musgo, vermelho-fogo; madeira, osso, penas, totens.
- **Clã Moskar (invasores):** cinza-metal, azul-aço, preto; armaduras, armas de fogo, bandeiras de guerra. (Obs.: no jogo há outros chefes/inimigos com paletas próprias, p.ex. Zanzara em azul escuro e faixa branca.)
- **Cartas:** ataque com moldura vermelha, defesa/habilidade com moldura azul (o código usa `RED` para attack, `BLUE` para skill e `GOLD` para power); seguir o padrão por tipo.
- **Jaum Manel:** magricela, penas, roupas e paleta aprovadas; mantém silhueta e pivô dos pés.
- **Boss final Zanzara:** cabelo/olhar "maré", ataques em onda de palma para a esquerda; muda a situação conforme a vida diminui (**TODO/Verificar** no código).
- Sprites gerados com auxílio de IA; há fallback visual desenhado proceduralmente no `AssetManager.get_fallback_sprite()` para sprites ausentes.
- **Slogan:** "A floresta resiste. Escreva sua estratégia. Defenda sua terra." **Narrativa:** Jaum Manel salva a tribo da Stone The Cut das mãos de Zanzara e do Clã Moskar; o mapa de 7 territórios conta essa jornada.

## 9. Decisões aprovadas de integração — 11/11/2026

Estas decisões atualizam as descrições históricas de Zanzara e áudio acima:

- Projeto oficial neste computador: `C:\Users\marco\OneDrive\Desktop\Scape-from-stone-de-cut-git`; usar seu Python `.venv\Scripts\python.exe`. Não desenvolver em cópias antigas. Branch da integração: `feature/audio-enemies`.
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
