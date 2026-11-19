"""Compõe os derivados ImageGen no molde LV2, sem redesenhar a ilustração.

Uso: python -B devtools/prepare_ultimate_cards.py --sources <ultimate_sources.json>
O JSON externo informa frame, mana, forcas e rugido em sources; originais preservados.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def centered_text(image, text, box, size, color, font_path):
    draw = ImageDraw.Draw(image)
    x, y, w, h = box
    while True:
        font = ImageFont.truetype(str(font_path), size)
        lines = []
        line = ''
        for word in text.split():
            trial = (line + ' ' + word).strip()
            if line and draw.textlength(trial, font=font) > w:
                lines.append(line)
                line = word
            else:
                line = trial
        lines.append(line)
        step = size + 4
        if len(lines) * step <= h or size <= 10:
            break
        size -= 1
    top = y + (h - len(lines) * step) // 2
    for i, line in enumerate(lines):
        draw.text((x + w / 2, top + i * step), line, font=font, fill=color, anchor='mt')


def prepare(sources_file, output, font_path):
    from src.models.effects.ultimate_effect import ULTIMATE_METADATA
    from devtools.prepare_player_card_packs import detect_cost_diamond

    sources = json.loads(sources_file.read_text(encoding='utf-8'))['sources']
    reference = Image.open(ROOT / 'assets/cards/lv2/esfera_protetora.png')
    frame = Image.open(sources['frame']).convert('RGBA').resize(reference.size, Image.Resampling.LANCZOS)
    layout = detect_cost_diamond(frame)
    regular = json.loads((ROOT / 'assets/cards/art_manifest.json').read_text(encoding='utf-8'))
    layout['cost_radius'] = regular['cards']['esfera_protetora:2']['cost_radius']
    manifest = {'version': 1, 'reference': 'cards/lv2/esfera_protetora.png',
                'size': list(reference.size), 'cards': {}, 'source_sha256': {}}
    for name, path in sources.items():
        manifest['source_sha256'][name] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    output.mkdir(parents=True, exist_ok=True)
    for uid, art_key in [('mana_ancestral', 'mana'), ('forcas_ancestrais', 'forcas'),
                         ('rugido_da_floresta', 'rugido')]:
        meta = ULTIMATE_METADATA[uid]
        card = Image.new('RGBA', reference.size)
        # A ilustração fica atrás da moldura e preenche o vazado sem tocar o exterior.
        art = ImageOps.fit(Image.open(sources[art_key]).convert('RGBA'), (272, 222),
                           method=Image.Resampling.LANCZOS, centering=(.5, .5))
        card.alpha_composite(art, (20, 16))
        card.alpha_composite(frame)
        centered_text(card, meta['name'].upper(), (26, 244, 260, 29), 20,
                      (255, 231, 168), font_path)
        centered_text(card, meta['description'], (35, 302, 242, 119), 19,
                      (245, 231, 196), font_path)
        centered_text(card, f"ULTIMATE - {meta['energy_cost']} ENERGIA", (35, 444, 242, 20),
                      14, (245, 206, 123), font_path)
        draw = ImageDraw.Draw(card)
        center = layout['cost_center']
        font = ImageFont.truetype(str(font_path), 30)
        draw.text(tuple(center), str(meta['energy_cost']), fill=(255, 223, 158),
                  font=font, anchor='mm')
        card.save(output / f'{uid}.png', optimize=True)
        manifest['cards'][uid] = {**layout, 'file': f'{uid}.png',
            'description': meta['description'], 'energy_cost': meta['energy_cost'],
            'text_area': [35 / reference.width, 302 / reference.height,
                          242 / reference.width, 119 / reference.height],
            'size': list(reference.size),
            'footer_rect': [35, 441, 242, 25]}
    (output / 'art_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('3 cartas Ultimate geradas:', reference.size, 'losango:', layout['cost_center'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'assets/ultimates')
    parser.add_argument('--font', type=Path, default=Path('C:/Windows/Fonts/georgia.ttf'))
    args = parser.parse_args()
    prepare(args.sources, args.output, args.font)
