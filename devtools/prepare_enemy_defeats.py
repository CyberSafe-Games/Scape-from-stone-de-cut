"""Exporta poses finais dos atlas de derrota, no enquadramento de cada kit."""

import argparse
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUTPUT = ASSETS / "enemies" / "defeat"
SHEETS = {"guardiao_da_pedra", "corpo_seco", "carrasco_da_vigilia"}
GROUPS = {
    "bosses": ("guardiao_da_pedra", "goblin_nerd", "gordofera", "corpo_seco",
               "carrasco_da_vigilia", "alvaro_tex_phase2"),
    "comuns-a": ("viniurgo", "macaco", "guerreiro_mata", "golem", "lagarto", "putrefato"),
    "comuns-b": ("crocodilo", "esqueleto", "morcego", "centauro", "lutador", "mago"),
}


def idle_sprite(group, slug):
    if slug in SHEETS:
        path = ASSETS / "bosses" / "sheets_eight" / slug / "idle.png"
        return Image.open(path).convert("RGBA").crop((0, 0, 448, 320))
    category = "bosses" if group == "bosses" else "enemies"
    path = ASSETS / category / "eight_frames" / slug / "idle_1.png"
    return Image.open(path).convert("RGBA")


def align(cell, idle, slug):
    cell.putalpha(cell.getchannel("A").point(lambda alpha: alpha if alpha >= 32 else 0))
    bounds = cell.getbbox()
    if not bounds:
        raise ValueError(f"Quadro de derrota vazio: {slug}")
    cell = cell.crop(bounds)
    left, top, right, floor = idle.getbbox()
    width, height = right - left, floor - top
    scale = (width * 1.12 / cell.width if slug == "morcego" else
             min(height * .80 / cell.height, width * 1.5 / cell.width))
    canvas = Image.new("RGBA", idle.size)
    if slug == "morcego":
        floor = canvas.height - 2
    cell = cell.resize((round(cell.width * scale), round(cell.height * scale)),
                       Image.Resampling.LANCZOS)
    canvas.alpha_composite(cell, (round((left + right - cell.width) / 2),
                                  floor - cell.height))
    return canvas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("group", choices=GROUPS)
    parser.add_argument("atlas", type=Path)
    args = parser.parse_args()
    atlas = Image.open(args.atlas).convert("RGBA")
    width, height = atlas.size
    OUTPUT.mkdir(exist_ok=True)
    for index, slug in enumerate(GROUPS[args.group]):
        row, col = divmod(index, 3)
        cell = atlas.crop((col * width // 3, row * height // 2,
                           (col + 1) * width // 3, (row + 1) * height // 2))
        align(cell, idle_sprite(args.group, slug), slug).save(OUTPUT / f"{slug}.png")


if __name__ == "__main__":
    main()
