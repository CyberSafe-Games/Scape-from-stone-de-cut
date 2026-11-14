# Retratos dos personagens

Os retratos personalizados da HUD ficam em `assets/portraits/source`.
O `manifest.json` registra os nomes originais dos retratos comuns vindos de
`inimigos.zip`. A correspondência e os recortes ficam em
`src/systems/character_portraits.py`.

Álvaro e Tex têm retratos próprios para cada fase. Zanzara usa a arte da
versão necromante com a moldura do protagonista.

Slime e Macaco Selvagem usam retratos derivados dos sprites. As imagens
são carregadas sob demanda e reutilizadas em cache.
