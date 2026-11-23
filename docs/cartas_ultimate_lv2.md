# Cartas Ultimate no molde LV2

> Referência vigente — auditoria de 23/11/2026. [Estado atual](estado_atual.md). Relatos de validações datadas abaixo representam somente aquela execução.

Atualização de 19/11/2026, autorizada pelo usuário.

As três cartas usam a dimensão real da Esfera Protetora LV2 (316 × 489), a mesma
posição do losango (53, 52), o mesmo tamanho de glifo e painéis equivalentes de
arte, título e descrição. A moldura dourada é compartilhada, com filigranas e
brasas discretas; o exterior é transparente. As ilustrações foram recriadas no
ImageGen a partir das três artes que já estavam no projeto, pois a mensagem
não trouxe um novo anexo visível. O protagonista mantém silhueta esguia.

## Regras canônicas

Todas exigem 20 de carga e **2 de energia**, debitados antes do efeito. A carga
continua começando em zero em cada batalha. Falta de energia não consome carga.

- **Mana Ancestral:** Restaura sua energia para 8 e remove todos os seus efeitos negativos.
  Preserva buffs, escudo e Força; também remove restrições ofensivas pendentes.
- **Forças Ancestrais:** Ganhe 12 de força ate o fim do combate e 40 de escudo por 2 turnos
  Força usa o reset normal de combate; Escudo usa as camadas de duração existentes.
- **Rugido da Floresta:** Destrua o escudo inimigo, cause 60 de dano e aplique Fraqueza por 3 turnos.
  Remove o bloqueio antes do ataque; mantém modificadores globais de ataque e
  proteções existentes. Fraqueza também é registrada em statuses para HUD/limpeza.

Rodapé: `ULTIMATE - 2 ENERGIA`. O losango é recomposto dentro do contorno
ilustrado pelo mesmo renderizador das cartas regulares, lendo energy_cost real;
o rodapé também muda se o custo mudar. Não sobrepor badges/faixas na batalha.
Mochila e combate usam a carta completa com ajuste proporcional dentro do slot.

## Preparação e origem

`devtools/prepare_ultimate_cards.py --sources <ultimate_sources.json>` aceita um
JSON externo com `sources: {frame, mana, forcas, rugido}`, apontando para os
originais gerados. Não sobrescreve esses originais. `--font` permite indicar uma
fonte serifada local (Georgia no preparo atual). Textos são compostos no PNG e
validados contra as definições do modelo; mudanças posteriores são recompostas
na UI. O manifesto guarda SHA-256 de cada fonte, dimensões e contorno do custo.

As três artes `_art_v2.png` anteriores estão no arquivo local ignorado
`_arquivos_antigos_para_deletar/ultimates_antes_padrao_lv2/`. Não são carregadas.

## Prompts de ilustração usados no ImageGen

### Mana

Recreate the reference illustration for the MANA ANCESTRAL Ultimate in a detailed pixel-art dark fantasy forest deckbuilder. Keep the invocation pose with both hands raised, blue cyan magical orbs, spectral jaguar eagle and serpent, ancient mossy ruins and warm gold jewelry. Correct the young indigenous shaman's face and anatomy: clean balanced facial features, coherent eyes and jaw, natural hands with five fingers, slim wiry protagonist rather than bulky bodybuilder, black shoulder-length hair, red headband and white/red feathers, brown and red rustic clothing. Medium close view from waist up so the face is clearly readable and the blue animals/orbs fill the upper background. Landscape illustration framed for a card's upper art window approximately 1.25:1, main character centered, both raised hands fully in frame. Strong rich blue magic and dark forest shadows, expressive believable human anatomy, crisp handcrafted pixel art, same earthy and gold game palette. NO text, NO frame, NO borders, NO UI. Use reference for color, effects and pose.

### Forcas

Recreate the reference illustration for FORÇAS ANCESTRAIS Ultimate in a detailed pixel-art dark fantasy forest deckbuilder. Keep the confident shaman pose with clenched fists apart, imposing ancestral golden masked guardian spirit behind him, radiant amber gold protective aura, floating stones, ancient mossy ruins. Correct the young indigenous shaman's face and anatomy: balanced coherent facial features, symmetrical eyes and jaw, natural five-finger hands, slim wiry protagonist with slender shoulders and arms, black shoulder-length hair, red headband and white/red feathers, brown/red rustic clothes and gold bracelets. Medium close view waist up, face clearly readable, both fists fully in frame, tall luminous ancestral mask/spirit above and behind. Landscape illustration for a card upper art window approximately 1.25:1. Gold and warm amber magic, deep moss-green shadows, crisp handcrafted pixel art, no text, no frame, no UI. Maintain reference colors, magical effects and pose.

### Rugido

Recreate the reference illustration for RUGIDO DA FLORESTA Ultimate in a detailed pixel-art dark fantasy forest deckbuilder. Keep the roaring shaman pose fists at his sides, huge emerald spectral jaguar head roaring above and behind him, green magical shockwaves and gold sparks breaking stones in mossy ancient forest ruins. Correct the young indigenous protagonist's face and anatomy: expressive natural open mouth, coherent eyes jaw teeth, balanced handsome youthful face, slim wiry body and slender arms rather than bulky muscles, natural five-finger hands, black shoulder-length hair, red headband white/red feathers, brown and red rustic garments, gold jewelry. Medium close view waist up for a card illustration upper window approximately 1.25:1, protagonist centered with both fists visible, jaguar fills upper background. Rich emerald green magic and gold accents, warm brown skin, dark forest shadows, crisp handcrafted pixel art, preserve reference colors and magic. NO text, NO borders, NO UI, NO card frame.

### Moldura compartilhada

Referência: Esfera Protetora LV2. Preservar exatamente geometria e proporção,
vazado superior, faixa de título, painel inferior e losango; trocar prata por
ouro nobre ornamentado, filigranas e brasas discretas; painéis verde-musgo quase
pretos; sem palavras/números; vazado da arte e exterior transparentes.

## Conferência

Testes: tests.test_ultimate_cards_lv2, tests.test_ultimates,
tests.test_backpack_ultimates, tests.test_ultimate_animations,
tests.test_player_card_art e regressões de combate/status.
Preview com saves temporários: devtools/preview_roguelite.py --smoke --output <pasta>.
Conferir no jogo a aba de Ultimates na Mochila e a carta na mão ao atingir 20/20.

## Arquivos desta implementação

Criados:
- assets/ultimates/mana_ancestral.png
- assets/ultimates/forcas_ancestrais.png
- assets/ultimates/rugido_da_floresta.png
- assets/ultimates/art_manifest.json
- devtools/prepare_ultimate_cards.py
- tests/test_ultimate_cards_lv2.py
- docs/cartas_ultimate_lv2.md

Alterados:
- src/models/effects/ultimate_effect.py
- src/models/entity.py
- src/core/asset_manager.py
- src/ui/ultimate_card_art.py
- src/scenes/backpack_scene.py
- src/scenes/battle_scene.py
- devtools/preview_roguelite.py
- tests/test_ultimates.py
- tests/test_backpack_ultimates.py
- README.md
- AGENTS.md

Movidos de assets/ultimates para o arquivo local ignorado:
- mana_ancestral_art_v2.png
- forcas_ancestrais_art_v2.png
- rugido_da_floresta_art_v2.png

Validação concluída: **149 testes em 12 módulos aprovados**, mais o smoke da
interface com saves temporários. Galeria, aba Ultimates da Mochila e carta
na mão em combate renderizadas e inspecionadas. Isso não substitui playtest
de balanceamento nem uma campanha humana completa.
