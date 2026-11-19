"""Recorta os packs LV1/LV2 autorizados e registra a origem de cada arte."""
import argparse
from collections import deque
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PACKS = {
    1: ("lanca_perfurante", "bola_de_fogo", "pocao_de_cura", "surto_de_energia", "pocao_venenosa"),
    2: ("machado_quebra_escudo", "amuleto_dissipador", "adaga_sangrenta", "mascara_ancestral", "machados_gemeos"),
    3: ("esfera_protetora", "soco_simples", "investida", "aura_rubra", "pocao_fragilizante"),
    4: ("pocao_purificadora", "totem_protetor", "zarabatana_venenosa", "disparo_de_arco", "esfera_escudo"),
}



def remove_outer_background(image):
    """Remove somente cinzas claros conectados ao exterior do recorte."""
    rgb = np.array(image.convert("RGB"), dtype=np.int16)
    low, high = rgb.min(axis=2), rgb.max(axis=2)
    candidates = (low > 135) & (high - low < 30)
    height, width = candidates.shape
    exterior = np.zeros((height, width), dtype=bool)
    queue = deque()
    for x in range(width):
        queue.extend(((x, 0), (x, height - 1)))
    for y in range(height):
        queue.extend(((0, y), (width - 1, y)))
    while queue:
        x, y = queue.popleft()
        if exterior[y, x] or not candidates[y, x]:
            continue
        exterior[y, x] = True
        if x > 0:
            queue.append((x - 1, y))
        if x + 1 < width:
            queue.append((x + 1, y))
        if y > 0:
            queue.append((x, y - 1))
        if y + 1 < height:
            queue.append((x, y + 1))
    rgba = np.array(image.convert("RGBA"))
    rgba[exterior, 3] = 0
    return Image.fromarray(rgba)


def card_component_box(image):
    pixels = np.array(image, dtype=np.int16)
    mask = (pixels.min(axis=2) < 110) | (pixels.max(axis=2) - pixels.min(axis=2) > 35)
    # Une os traços da moldura e separa os pequenos fragmentos das cartas vizinhas.
    mask = np.array(Image.fromarray(mask.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(3))) > 0
    height, width = mask.shape
    cx, cy = width // 2, height // 2
    ys, xs = np.nonzero(mask)
    seed = int(np.argmin((xs - cx) ** 2 + (ys - cy) ** 2))
    queue = deque(((int(xs[seed]), int(ys[seed])),))
    visited = np.zeros_like(mask)
    left, top, right, bottom = width, height, 0, 0
    while queue:
        x, y = queue.popleft()
        if visited[y, x] or not mask[y, x]:
            continue
        visited[y, x] = True
        left, top, right, bottom = min(left, x), min(top, y), max(right, x), max(bottom, y)
        if x > 0:
            queue.append((x - 1, y))
        if x + 1 < width:
            queue.append((x + 1, y))
        if y > 0:
            queue.append((x, y - 1))
        if y + 1 < height:
            queue.append((x, y + 1))
    return (max(0, left - 1), max(0, top - 1),
            min(width, right + 2), min(height, bottom + 2))


def detect_cost_diamond(image):
    """Detecta o interior fechado do losango, independente das margens do recorte."""
    rgba = np.array(image.convert("RGBA"))[:120, :125]
    dark = (rgba[:, :, :3].max(axis=2) < 55) & (rgba[:, :, 3] > 0)
    visited = np.zeros_like(dark)
    candidates = []
    height, width = dark.shape
    for y, x in zip(*np.nonzero(dark)):
        if visited[y, x]:
            continue
        queue = deque(((int(x), int(y)),))
        points = []
        while queue:
            px, py = queue.popleft()
            if visited[py, px] or not dark[py, px]:
                continue
            visited[py, px] = True
            points.append((px, py))
            for nx, ny in ((px - 1, py), (px + 1, py), (px, py - 1), (px, py + 1)):
                if 0 <= nx < width and 0 <= ny < height:
                    queue.append((nx, ny))
        if len(points) < 1000:
            continue
        xs, ys = zip(*points)
        left, top, right, bottom = min(xs), min(ys), max(xs), max(ys)
        if (left > 1 and top > 1 and right < width - 2 and bottom < height - 2
                and 50 < right - left < 105 and 50 < bottom - top < 105):
            candidates.append(points)
    if len(candidates) != 1:
        raise ValueError(f"Esperado um losango fechado, encontrados {len(candidates)}.")

    # O fecho convexo preenche também o número impresso, que é um furo claro.
    def cross(origin, a, b):
        return (a[0] - origin[0]) * (b[1] - origin[1]) - (a[1] - origin[1]) * (b[0] - origin[0])

    points = sorted(set(candidates[0]))
    lower, upper = [], []
    for point in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    for point in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    polygon = lower[:-1] + upper[:-1]
    pairs = list(zip(polygon, polygon[1:] + polygon[:1]))
    factors = [a[0] * b[1] - b[0] * a[1] for a, b in pairs]
    area2 = sum(factors)
    cx = sum((a[0] + b[0]) * factor for (a, b), factor in zip(pairs, factors)) / (3 * area2)
    cy = sum((a[1] + b[1]) * factor for (a, b), factor in zip(pairs, factors)) / (3 * area2)
    xs, ys = zip(*polygon)
    radius = int(min(max(xs) - min(xs), max(ys) - min(ys)) / 2) - 3
    return {
        "cost_center": [round(cx), round(cy)],
        "cost_polygon": [list(point) for point in polygon],
        "cost_radius": radius,
    }


def prepare(source, output):
    from src.systems.card_definitions import CARD_SPECS
    from src.systems.roguelite import instance_card
    names = {spec[0]: spec[1] for spec in CARD_SPECS}
    manifest = {"version": 2, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "cards": {}}
    output.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as archive:
        for pack, ids in PACKS.items():
            for level in (1, 2):
                member = f"Cartas/Cards pack {pack} Lv {level}.png"
                sheet = Image.open(io.BytesIO(archive.read(member))).convert("RGB")
                assert sheet.width == 1600
                # No ZIP recebido, os nomes dos packs 1 e 2 LV2 estão invertidos.
                actual_ids = PACKS[3 - pack] if level == 2 and pack in (1, 2) else ids
                for column, card_id in enumerate(actual_ids):
                    window_left = max(0, column * 320 - 28)
                    window_right = min(sheet.width, (column + 1) * 320 + 28)
                    cell = sheet.crop((window_left, 0, window_right, sheet.height))
                    box = card_component_box(cell)
                    crop = remove_outer_background(cell.crop(box))
                    assert crop.width > 280 and crop.height > 400, (member, card_id, crop.size)
                    relative = f"{card_id}.png" if level == 1 else f"lv2/{card_id}.png"
                    target = output / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    crop.save(target, optimize=True)
                    card = instance_card({"id": "art-preview", "name": names[card_id], "level": level})
                    cost_layout = detect_cost_diamond(crop)
                    manifest["cards"][f"{card_id}:{level}"] = {
                        "file": relative, "sheet": member,
                        "crop": [window_left + box[0], box[1], window_left + box[2], box[3]],
                        "size": list(crop.size),
                        **cost_layout,
                        "description": card.description,
                        "text_area": [.085, .64, .83, .28],
                    }
    assert len(manifest["cards"]) == 40
    (output / "art_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"40 cartas preparadas em {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "assets/cards")
    args = parser.parse_args()
    prepare(args.source, args.output)


if __name__ == "__main__":
    main()
