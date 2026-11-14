"""Recorta os ícones de território do mapa a partir das artes originais.

Uso: python -B devtools/prepare_map_icons.py

Lê as fontes preservadas em docs/icones_mapa/ (spritesheet 3x2 dos minibosses e
arte do boss final) e grava um PNG transparente por território em
assets/ui/map_icons/<id_do_territorio>.png. Cada PNG é quadrado e centrado no
losango do ícone, de modo que o centro da imagem coincide com o ponto do mapa.

O fundo preto externo é removido por preenchimento a partir das bordas; o disco
interno (também escuro) é protegido e permanece opaco. As artes não são
redesenhadas: só o fundo conectado à borda vira transparência.

Requer Pillow e NumPy (requirements-dev.txt).
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIR = os.path.join(ROOT, "docs", "icones_mapa")
OUTPUT_DIR = os.path.join(ROOT, "assets", "ui", "map_icons")

SHEET = "fonte_minibosses.webp"
FINAL_BOSS = "fonte_zanzara.webp"
CELL = 512

# id do território -> (arquivo, célula (coluna, linha) ou None, centro do losango,
#                      raio protegido do disco, metade do lado do recorte)
ICONS = {
    "stone_the_cut": (SHEET, (2, 1), (1272, 741), 140, 250),      # urso espiritual azul
    "mata_sombria": (SHEET, (0, 0), (258, 243), 140, 250),        # fumaça verde e shurikens
    "ruinas_ancestrais": (SHEET, (0, 1), (263, 740), 140, 250),   # raios azuis
    "pantano_abissal": (SHEET, (1, 1), (760, 740), 140, 250),     # garras marrons
    "fortaleza_caida": (SHEET, (2, 0), (1272, 243), 140, 250),    # facas cinzas
    "pico_da_vigilia": (SHEET, (1, 0), (760, 243), 140, 250),     # machado vermelho
    "santuario_de_pedra": (FINAL_BOSS, None, (627, 605), 500, 650),  # necromante com foice
}

DARK_FLOOR = 6    # abaixo disso o pixel é preto de fundo (o fundo das fontes é 0)
DARK_LIMIT = 40   # na borda externa, brilho até aqui esmaece gradualmente
CLOSE_SIZE = 9    # janela (px, ímpar) do fechamento que protege contornos escuros


def cut_icon(source, cell, center, guard_radius, half):
    """Devolve o ícone RGBA quadrado, centrado em `center`."""
    cx, cy = center
    canvas = Image.new("RGB", (half * 2, half * 2), (0, 0, 0))
    box = (cx - half, cy - half, cx + half, cy + half)
    if cell is not None:  # nunca invade o ícone vizinho da spritesheet
        col, row = cell
        box = (max(box[0], col * CELL), max(box[1], row * CELL),
               min(box[2], (col + 1) * CELL), min(box[3], (row + 1) * CELL))
    box = (max(box[0], 0), max(box[1], 0), min(box[2], source.width), min(box[3], source.height))
    canvas.paste(source.crop(box), (box[0] - (cx - half), box[1] - (cy - half)))

    rgb = np.asarray(canvas)
    brightness = rgb.max(axis=2).astype(np.float32)
    yy, xx = np.mgrid[0:half * 2, 0:half * 2]
    guarded = (xx - half) ** 2 + (yy - half) ** 2 <= guard_radius ** 2
    content = (brightness >= DARK_FLOOR) | guarded

    # Fechamento morfológico: contornos e sombras quase pretos dentro da arte
    # continuam fazendo parte dela, em vez de abrir caminho para o fundo.
    pad = CLOSE_SIZE
    padded = np.pad(content, pad, constant_values=False).astype(np.uint8) * 255
    # frombytes cria uma imagem gravável (fromarray compartilha memória só de leitura).
    solid = Image.frombytes("L", padded.shape[::-1], padded.tobytes())
    solid = solid.filter(ImageFilter.MaxFilter(CLOSE_SIZE)).filter(ImageFilter.MinFilter(CLOSE_SIZE))
    ImageDraw.floodfill(solid, (0, 0), 128)  # só o preto ligado à borda vira fundo
    reached = solid.point(lambda value: 255 if value == 128 else 0)
    background = np.asarray(reached)[pad:-pad, pad:-pad] == 255
    near_edge = np.asarray(reached.filter(ImageFilter.MaxFilter(5)))[pad:-pad, pad:-pad] == 255

    # Opaco por padrão; na borda externa o brilho fraco esmaece em vez de virar halo.
    alpha = np.full(brightness.shape, 255.0, dtype=np.float32)
    ramp = np.clip((brightness - DARK_FLOOR) / (DARK_LIMIT - DARK_FLOOR), 0.0, 1.0) * 255.0
    fringe = near_edge & ~background & ~guarded
    alpha[fringe] = ramp[fringe]
    alpha[background] = 0
    rgba = np.dstack([rgb, alpha.round().astype(np.uint8)])
    rgba[alpha == 0] = 0
    return Image.fromarray(rgba, "RGBA")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    sources = {}
    for territory_id, (filename, cell, center, guard, half) in ICONS.items():
        if filename not in sources:
            sources[filename] = Image.open(os.path.join(SOURCE_DIR, filename)).convert("RGB")
        icon = cut_icon(sources[filename], cell, center, guard, half)
        path = os.path.join(OUTPUT_DIR, territory_id + ".png")
        icon.save(path, optimize=True)
        print(f"{territory_id}: {icon.size[0]}x{icon.size[1]} -> {os.path.relpath(path, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
