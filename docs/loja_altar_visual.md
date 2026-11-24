# Loja e altar ancestral

> Referência vigente — auditoria de 23/11/2026. [Estado atual](estado_atual.md). Relatos de validações datadas abaixo representam somente aquela execução.

Redesign local de 19/11/2026, baseado na main fe7284b.

## Composição

A loja usa o Mercado Silencioso ilustrado, com mercador, bancada, lanternas e ruínas. Exibe quatro cartas por página, preços em ouro, estado de compra, preview central ampliado e feedback de aquisição e cura.

O altar apresenta a coleção em páginas de cinco tipos, seleção das cópias individuais, comparação LV1 → LV2 calculada com `instance_card()`, materiais necessários e preço. As runas giram e a confirmação do upgrade produz brilho e partículas. Cópias já LV2 continuam selecionáveis para consulta.

Cura até 20 HP atual por 30/45/60 ouro, três compras/run; vida cheia não cobra. Evolução individual custa três materiais e ouro, limite três/run; material custa 15, reserva nove. Preservar padding e artes LV1/LV2 com custo dinâmico único.

As regras são executadas pelas transações existentes de `shop_system.py` e `roguelite.py`. O fluxo de preparação entre runs continua na mesma cena.

## Assets ativos

- `assets/ui/shop/market_background.png`
- `assets/ui/shop/offer_frame.png` — moldura ornamental reutilizada também nas cartas do altar.
- `assets/ui/workshop/altar_background.png`
- `assets/ui/workshop/rune_ring.png`

Os quatro assets foram gerados com a ferramenta integrada de imagens. Os originais da geração foram preservados. Os fundos compartilhados do jogo continuam referenciados pelas outras telas.

## Prompts finais de geração

### Mercado

Create a production game background asset, 16:9 landscape, for Scape From Stone dark fantasy pixel-art deckbuilder. Ancient ruined forest market. Hand-crafted detailed pixel art matching aged gold ornamental frames, deep near-black moss green shadows, weathered sandstone, worn brown wood, amber firelight. Composition must support overlay UI: mysterious hooded ancestral merchant with charismatic weathered face seated at FAR LEFT occupying only leftmost 24%, old gold necklaces and dark moss cloak; behind merchant carved ancient arch and lanterns; lower foreground broad stone and timber counter with dark cloth; center and right 70% calm dark stone wall and shelves, sparse detail so 6 vertical card UI overlays can be read. Strong atmospheric depth, warm candles, jungle roots and subtle jade glints, restrained contrast, no text, no cards drawn, no interface, no buttons. Finished illustrated raster game environment, richly textured yet clearly pixel art, not photograph, not 3D. Wide landscape.

### Altar

Production environment background asset for Scape From Stone dark fantasy pixel-art deckbuilder, landscape 16:9. An ancient forest enchantment workshop inside ruined stone temple: central broad dark stone altar low foreground, intricately carved worn gold trim, circular green jade rune engraved in floor, low amber braziers on left and right, faint upward gold embers, roots, mossy crumbling pillars, ritual tools and bones at edges. Detailed handcrafted pixel art matching aged gold ornamented cards, earthy browns, near-black green shadows, weathered sandstone and warm torchlight with subtle emerald glow. Main interactive card overlays will occupy center and right: keep middle 70% dark uncluttered usable negative space behind cards, altar platform across bottom third. NO text, no cards, no UI, no buttons, no people. Immersive atmospheric game scenario, pixel art not photorealistic, not 3D, restrained illumination so overlaid cards stay readable. Wide landscape.

### Moldura

Production UI sprite for dark fantasy pixel art deckbuilder Scape From Stone. ONE tall rectangular hollow ornamental aged GOLD AND BRONZE FRAME, portrait 2:3 shape, perfectly front facing, straight aligned horizontal and vertical sides, thin weathered carved ancient gold border, tiny moss accents, carved serpent and foliage corner pieces. Entire center completely empty and transparent, entire surrounding background transparent. Frame occupies image edges with slight outer margin; the border only about 4 percent of width, leaving maximum open interior for a playing card. Real transparent alpha. Rich detailed handcrafted pixel art, near-black shadows and restrained amber gold highlights matching ancient forest ruin game. No text, no words, no card, no illustration inside, no checkerboard, no glow filling the hole.

### Runas

Single isolated magical rune ring VFX sprite for dark fantasy pixel-art roguelike card enchantment altar. Perfect circular ancient gold ring with small angular geometric invented runes, subtle emerald jade glow and tiny gold sparks, ornate worn bronze and gold detailed pixel art, hollow transparent center and transparent outside, front facing flat circle. Delicate lines, sparse effect, moderately dim luminosity, no text, no letters, no card, no background, no checkerboard. Intended as a slowly rotating ring behind before-after card comparison.

## Validação

Testes direcionados de loja, coleção, roguelite, áudio de interface e seleção de cópias. O piloto `devtools/preview_roguelite.py --smoke` usa saves temporários. Os testes novos verificam seleção da segunda cópia, persistência, clique repetido, rollback de falha de gravação, limite de materiais, todas as cartas LV1/LV2, coleção vazia e compra com hover aberto.

Para conferir visualmente, abra a Loja no mapa e o Altar de Aprimoramento pelo botão inferior esquerdo. Selecione o tipo e a cópia, confira a comparação e confirme a evolução. O hover da loja é exclusivamente visual e mantém o destino dos cliques na oferta.
