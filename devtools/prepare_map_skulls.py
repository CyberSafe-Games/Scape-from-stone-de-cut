"""Gera as caveiras que marcam chefes concluídos no mapa.

Uso: python -B devtools/prepare_map_skulls.py

Lê docs/icones_mapa/fonte_caveiras.png (duas caveiras em pixel art ampliada, já
com fundo transparente) e grava em assets/ui/map_markers/:

- miniboss_skull.png   -> caveira branca (esquerda)
- final_boss_skull.png -> caveira vermelha com chifres (direita)

Cada bloco da arte original (~36 px) vira 2 px, sem suavização: a cor de cada
pixel é a mediana do miolo da célula correspondente. As sprites saem no tamanho
exato em que o mapa as desenha, então o jogo não precisa reescalar.

Requer Pillow e NumPy (requirements-dev.txt).
"""
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "docs", "icones_mapa", "fonte_caveiras.png")
OUTPUT_DIR = os.path.join(ROOT, "assets", "ui", "map_markers")

SOURCE_PIXELS_PER_OUTPUT_PIXEL = 18.2  # bloco original (~36,4 px) / 2
# arquivo -> faixa horizontal (início, fim) da caveira na imagem de origem
SKULLS = {
    "miniboss_skull.png": (0, 880),
    "final_boss_skull.png": (880, None),
}


def shrink(region):
    """Recorta a área opaca e reduz por amostragem de células, sem interpolar."""
    alpha = region[..., 3]
    ys, xs = np.nonzero(alpha > 128)
    region = region[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    height, width = region.shape[:2]
    out_w = round(width / SOURCE_PIXELS_PER_OUTPUT_PIXEL)
    out_h = round(height / SOURCE_PIXELS_PER_OUTPUT_PIXEL)
    result = np.zeros((out_h, out_w, 4), dtype=np.uint8)
    for row in range(out_h):
        for col in range(out_w):
            # Miolo da célula: ignora a borda suavizada entre blocos vizinhos.
            y0, y1 = (row + 0.25) * height / out_h, (row + 0.75) * height / out_h
            x0, x1 = (col + 0.25) * width / out_w, (col + 0.75) * width / out_w
            cell = region[int(y0):max(int(y1), int(y0) + 1), int(x0):max(int(x1), int(x0) + 1)]
            cell = cell.reshape(-1, 4)
            if np.median(cell[:, 3]) > 128:
                result[row, col, :3] = np.median(cell[cell[:, 3] > 128, :3], axis=0)
                result[row, col, 3] = 255
    return Image.fromarray(result, "RGBA")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    source = np.asarray(Image.open(SOURCE).convert("RGBA"))
    for filename, (start, end) in SKULLS.items():
        sprite = shrink(source[:, start:end])
        path = os.path.join(OUTPUT_DIR, filename)
        sprite.save(path, optimize=True)
        print(f"{filename}: {sprite.size[0]}x{sprite.size[1]} -> {os.path.relpath(path, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
