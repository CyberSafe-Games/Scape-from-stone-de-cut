"""Exporta a sequência de derrota de Vinimuth com o pé dianteiro alinhado."""

from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from devtools.prepare_common_eight_frames import pack


def front_foot(image, foot_depth):
    left, _, right, bottom = image.getbbox()
    foot = image.crop((left, bottom - foot_depth, (left + right) // 2, bottom))
    bounds = foot.getbbox()
    if not bounds:
        raise ValueError("Pé dianteiro ausente no quadro.")
    return left + (bounds[0] + bounds[2]) / 2, bottom


def main():
    folder = ROOT / "assets/enemies/eight_frames/vinimuth"
    source = Image.open(folder / "defeat_reference.png").convert("RGBA")
    source.putalpha(source.getchannel("A").point(lambda alpha: alpha if alpha >= 32 else 0))
    width, height = source.size
    scale = 0.28
    idle = Image.open(folder / "idle_1.png").convert("RGBA")
    target_foot, _ = front_foot(idle, 7)
    for index in range(3):
        cell = source.crop((index * width // 3, 0, (index + 1) * width // 3, height))
        foot, floor = front_foot(cell, 24)
        frame = pack(cell, scale, foot + (224 - target_foot) / scale, floor)
        frame.save(folder / f"defeat_{index + 1}.png")


if __name__ == "__main__":
    main()
