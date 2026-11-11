# Retratos dos personagens

Os retratos fornecidos em `boses.zip` e `inimigos.zip` são usados na moldura
da HUD, no lugar do recorte automático das animações. Os arquivos originais
estão preservados em `assets/portraits/source`; `manifest.json` registra os
nomes originais nos pacotes. A correspondência e os recortes ficam em
`src/systems/character_portraits.py`.

Foram integrados os sete bosses e onze inimigos comuns. A dupla Álvaro e Tex
usa a composição com os dois personagens; a segunda fase usa um recorte do
pequeno. Os recortes respeitam a proporção original, sem esticar os rostos.

Slime, Macaco Selvagem e protagonista mantêm o retrato anterior, pois os
pacotes não continham novas imagens para eles. As animações não foram
alteradas. Imagens são carregadas sob demanda e reutilizadas em cache.
