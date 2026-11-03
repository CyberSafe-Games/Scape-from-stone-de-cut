"""Prepara as folhas originais de Álvaro e Tex sem redesenhar os personagens.

python devtools/prepare_alvaro_tex.py
Ataques: 4 colunas x 2 linhas; idle/dano: 4 colunas.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from PIL import Image, ImageDraw
import pygame
from devtools.prepare_normal_enemies import clean, components, mask_array

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'assets/bosses/alvaro_tex'


def extract(path, rows=2, content_height=None, projectile=False):
    original = Image.open(path).convert('RGBA')
    pixels = np.array(original)
    # Genuine alpha sheets have faint residual background; keep smoke translucency.
    if pixels[:, :, 3].min() < 10:
        pixels[pixels[:, :, 3] < 45] = 0
        sheet = Image.fromarray(pixels)
    else:
        sheet = clean(original)
    w, h = sheet.size
    h = content_height or h
    cells = []
    for row in range(rows):
        for col in range(4):
            cell = sheet.crop((round(col*w/4), round(row*h/rows),
                               round((col+1)*w/4), round((row+1)*h/rows)))
            arr = np.array(cell)
            parts = components((arr[:, :, 3] > 55).astype('uint8')*255)
            body = max(parts, key=lambda p: p.count())
            box = body.get_bounding_rects()[0]
            mask = pygame.mask.Mask(cell.size)
            for part in parts:
                r = part.get_bounding_rects()[0]
                if part.count() < 8:
                    continue
                # The grey target in the demonstration sheet is not an enemy sprite.
                if projectile and part is not body:
                    continue
                if not box.inflate(45, 45).colliderect(r):
                    continue
                if part is not body and (r.left == 0 or r.right == cell.width):
                    continue
                mask.draw(part, (0, 0))
            arr[~mask_array(mask)] = 0
            cell = Image.fromarray(arr)
            # Anchor to the body, not the detached projectile or sparks.
            floor = box.bottom
            bottom = mask_array(body)
            yy, xx = np.where(bottom & (np.indices(bottom.shape)[0] >= floor-12))
            anchor = float(np.median(xx)) if len(xx) else box.centerx
            cells.append((cell, anchor, floor, box.height))
    return cells


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    preview = Image.new('RGB', (8*224, 14*155), '#172520')
    pen = ImageDraw.Draw(preview)
    line = 0
    for phase in (1, 2):
        source = FOLDER / 'source' / ('fase 2' if phase == 2 else '')
        out = FOLDER / f'phase{phase}'
        out.mkdir(parents=True, exist_ok=True)
        groups = [('idle', 'idle.png', 1), ('dano', 'tomando dano.png', 1)]
        groups += [(f'atk{i}', f'atk {i}.png', 2) for i in range(1, 5)]
        if phase == 1:
            groups.append(('transition', 'Morte.png', 2))
        for group, filename, rows in groups:
            cells = extract(source / filename, rows,
                            790 if phase == 2 and group == 'atk4' else None,
                            projectile=(phase == 1 and group == 'atk2') or (phase == 2 and group == 'atk4'))
            scale = (190 if phase == 1 else 102) / cells[0][3]
            for i, (cell, ax, ay, _) in enumerate(cells):
                box = cell.getbbox()
                frame = Image.new('RGBA', (448, 250))
                crop = cell.crop(box).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                crop = crop.resize((max(1, round(crop.width*scale)), max(1, round(crop.height*scale))), Image.Resampling.NEAREST)
                x = round(224 - (box[2]-ax)*scale)
                y = round(246 - (ay-box[1])*scale)
                frame.alpha_composite(crop, (x, y))
                frame.save(out / f'{group}_{i+1}.png')
                small = frame.resize((224,125), Image.Resampling.NEAREST)
                preview.paste(small, (224*i,155*line+25), small)
            pen.text((5,155*line+5), f'Fase {phase} - {group}', fill='white')
            line += 1
    # Separate throwing star from the supplied bonus drawing (no invented character).
    star = clean(Image.open(FOLDER / 'source/fase 2/atk 4.png').crop((620,800,900,1024)))
    star = star.crop(star.getbbox()).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    star.thumbnail((36,36), Image.Resampling.NEAREST)
    star.save(FOLDER / 'shuriken.png')
    (ROOT/'docs').mkdir(exist_ok=True)
    preview.crop((0,0,1792,line*155)).save(ROOT/'docs/alvaro_tex_sprites.png')
    pygame.quit()


if __name__ == '__main__':
    main()
