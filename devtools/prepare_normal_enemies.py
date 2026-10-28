"""Recorta as 11 folhas fornecidas: python devtools/prepare_normal_enemies.py PASTA.

Pillow, NumPy e Pygame são usados apenas na preparação, nunca no jogo.
Mantém escala por personagem, transparência e pivô dos pés em todos os quadros.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from PIL import Image, ImageDraw
import pygame
from src.systems.normal_enemy_catalog import NORMAL_SPRITES

SOURCES = (
    '23e82e90-2dc6-4a0f-8358-f0eee2a3e9f8',
    '11bf999b-b702-4591-80b4-3b16664d6a54',
    'fa674722-04b2-4779-b98e-49c0c61f2117',
    'e1519c60-afbe-4209-aac4-082e442d654f',
    'dd81a560-824d-43b6-a502-42a7d2bdc806',
    '2298b3b5-fc94-4e81-88b4-d29a0fa06877',
    'a47f2757-3c1c-4008-b6dd-4b087a4123be',
    '2ae6695d-b5e8-4f74-8757-bf53d11f1108',
    'e20d34e5-4c60-42fd-91d3-52e1da668226',
    '9064e5c5-f1f3-4c30-8eac-8c0764c50bc4',
    '4df3f048-61a1-4879-b1fc-1d89c3d7f4d3',
)
HEIGHTS = (135, 145, 140, 120, 137, 86, 120, 138, 136, 145, 100)


def components(alpha):
    surf = pygame.image.frombytes(Image.fromarray(alpha).convert('RGBA').tobytes(),
                                  (alpha.shape[1], alpha.shape[0]), 'RGBA')
    # RGB is irrelevant; alpha must hold the binary mask.
    a = pygame.surfarray.pixels_alpha(surf)
    a[:] = alpha.T
    del a
    return pygame.mask.from_surface(surf, 1).connected_components(1)


def mask_array(mask):
    return pygame.surfarray.array3d(mask.to_surface(setcolor='white', unsetcolor='black'))[:, :, 0].T > 0


def clean(image, keep_white=False):
    rgba = np.array(image.convert('RGBA'))
    rgb = rgba[:, :, :3].astype(int)
    neutral = ((rgb.min(2) > 185) & (rgb.max(2) - rgb.min(2) < 32))
    for comp in components(neutral.astype('uint8') * 255):
        rect = comp.get_bounding_rects()[0]
        exterior = rect.left == 0 or rect.top == 0 or rect.right == image.width or rect.bottom == image.height
        if exterior or (comp.count() > 90 and not keep_white):
            rgba[mask_array(comp), 3] = 0
    # A second, two-pixel boundary pass removes pale antialiasing only.
    for _ in range(2):
        transparent = rgba[:, :, 3] == 0
        edge = np.zeros_like(transparent)
        edge[1:] |= transparent[:-1]; edge[:-1] |= transparent[1:]
        edge[:, 1:] |= transparent[:, :-1]; edge[:, :-1] |= transparent[:, 1:]
        pale = (rgb.min(2) > 105) & (rgb.max(2) - rgb.min(2) < 45)
        if not keep_white:
            rgba[edge & pale, 3] = 0
    rgba[rgba[:, :, 3] == 0] = 0
    return Image.fromarray(rgba)


def main(folder):
    pygame.init()
    pygame.display.set_mode((1, 1))
    root = Path(__file__).resolve().parents[1]
    preview = Image.new('RGB', (4 * 320, 11 * 215), '#14231f')
    draw = ImageDraw.Draw(preview)
    for idx, ((name, spec), source) in enumerate(zip(NORMAL_SPRITES.items(), SOURCES)):
        slug, groups, _, _ = spec
        original = Image.open(Path(folder) / f'codex-clipboard-{source}.png')
        w, h = original.size
        sheet = clean(original)
        projection = (np.array(sheet)[:, :, 3] > 0).sum(axis=1)
        cuts = [0]
        for row in range(1, 4):
            center = round(row*h/4)
            lo, hi = center-round(h*.065), center+round(h*.065)
            # Pick the quietest horizontal gutter, not a mathematical quarter:
            # several supplied sheets have feet crossing those quarters.
            score = np.convolve(projection, np.ones(9), mode='same')
            candidates = np.flatnonzero(score[lo:hi] == score[lo:hi].min()) + lo
            cuts.append(int(candidates[np.argmin(abs(candidates-center))]))
        cuts.append(h)
        # Keep whole silhouettes even where a weapon/foot crosses a gutter.
        parts = components(np.array(sheet)[:, :, 3])
        rects = [part.get_bounding_rects()[0] for part in parts]
        owners = {}
        for r in range(4):
            for c in range(4):
                candidates = [i for i, rect in enumerate(rects)
                              if c*w/4 <= rect.centerx < (c+1)*w/4 and cuts[r] <= rect.centery < cuts[r+1]]
                owners[r, c] = max(candidates, key=lambda i: parts[i].count())
        body_ids = set(owners.values())
        cells = []
        for r in range(4):
            row_cells = []
            for c in range(4):
                selected = [owners[r, c]] + [i for i, rect in enumerate(rects)
                    if i not in body_ids and parts[i].count() >= 5
                    and c*w/4 <= rect.centerx < (c+1)*w/4 and cuts[r] <= rect.centery < cuts[r+1]]
                mask = pygame.mask.Mask((w, h))
                for i in selected:
                    mask.draw(parts[i], (0, 0))
                pixels = np.array(sheet)
                pixels[~mask_array(mask)] = 0
                cell = Image.fromarray(pixels)
                row_cells.append(cell.crop(cell.getbbox()))
            cells.append(row_cells)
        if slug == 'macaco':
            cells[2][2] = clean(original.crop((round(2*w/4), cuts[2], round(3*w/4), cuts[3])), keep_white=True)
        boxes = [im.getbbox() for im in cells[0]]
        scale = HEIGHTS[idx] / np.median([b[3]-b[1] for b in boxes])
        out = root / 'assets' / 'enemies' / slug
        out.mkdir(parents=True, exist_ok=True)
        # These reference cells contain a detached projectile, not the actor.
        missing = {(2, 2)} if slug in ('golem', 'putrefato') else {(3, 2)} if slug == 'guerreiro_mata' else set()
        for row, group in enumerate(groups):
            for col in range(4):
                image = cells[row][col]
                if (row, col) in missing:
                    if slug in ('golem', 'putrefato'):
                        projectile = image.crop(image.getbbox()).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                        projectile.thumbnail((100, 85), Image.Resampling.NEAREST)
                        projectile.save(out / f'projectile_{group}.png')
                    image = cells[row][1].copy()
                if slug == 'centauro' and (row, col) == (2, 2):
                    # The arrow travels separately: remove its baked copy.
                    image = image.copy()
                    image.paste((0, 0, 0, 0), (round(image.width*.55), 0, image.width, image.height))
                bbox = image.getbbox()
                body_pixels = np.array(image)[:, :, 3] > 0
                floor = bbox[3]
                ys, xs = np.where(body_pixels & (np.indices(body_pixels.shape)[0] >= floor-max(5, round((floor-bbox[1])*.18))))
                anchor_x = float(np.median(xs))
                anchor_y = floor
                cropped = image.crop(bbox)
                mirrored = not (slug == 'lutador' and row == 0 and col == 3)
                if mirrored:
                    cropped = cropped.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                    ax = bbox[2] - anchor_x
                else:
                    ax = anchor_x - bbox[0]
                ay = anchor_y - bbox[1]
                cropped = cropped.resize((round(cropped.width*scale), round(cropped.height*scale)), Image.Resampling.NEAREST)
                frame = Image.new('RGBA', (448, 220))
                frame.alpha_composite(cropped, (round(224-ax*scale), round(214-ay*scale)))
                if slug == 'centauro' and (row, col) == (2, 2):
                    # The supplied release pose lost its bow. Restore the
                    # wooden limb and relaxed string at the outstretched hand.
                    frame.paste((0, 0, 0, 0), (0, 0, 165, 220))
                    pen = ImageDraw.Draw(frame)
                    curve = [(187, 90), (181, 99), (174, 109), (169, 121),
                             (168, 136), (173, 152), (184, 170), (191, 180)]
                    pen.line(curve, fill=(35, 24, 17, 255), width=5)
                    pen.line(curve, fill=(148, 93, 43, 255), width=3)
                    pen.line([(x-1, y) for x, y in curve], fill=(207, 153, 80, 255), width=1)
                    pen.line([(187, 90), (191, 180)], fill=(161, 157, 133, 255), width=1)
                if slug == 'guerreiro_mata' and (row, col) in missing:
                    impact = cells[row][col].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                    impact.thumbnail((110, 100), Image.Resampling.NEAREST)
                    frame.alpha_composite(impact, (90, 214-impact.height))
                frame.save(out / f'{group}_{col+1}.png')
                if col == 2:
                    preview.paste(frame, (row*320-64, idx*215-5), frame)
            draw.text((row*320+8, idx*215+5), f'{name} / {group}', fill='#ecd5a1')
        print(name, original.size, 'scale', round(scale, 3))
        # Extract the arrow and sonic wave as independent travelling effects.
        if slug in ('centauro', 'morcego'):
            row = 2 if slug == 'centauro' else 3
            effect = cells[row][2]
            # Both references face right: the detached effect is to the right.
            pixels = np.array(effect)
            if slug == 'morcego':
                rgb = pixels[:, :, :3].astype(int)
                blue = (rgb[:, :, 2] > rgb[:, :, 0]*1.25) & (rgb[:, :, 1] > 130) & (pixels[:, :, 3] > 0)
                start = int(np.where(blue)[1].min())
            else:
                start = round(effect.width*.55)
            effect = effect.crop((start, 0, effect.width, effect.height))
            effect = effect.crop(effect.getbbox()).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            effect.thumbnail((105, 65), Image.Resampling.NEAREST)
            effect.save(out / f'projectile_{groups[row]}.png')
        if slug == 'mago':
            for action, color in [('atk1', (255, 71, 35)), ('atk2', (197, 151, 91))]:
                fx = Image.new('RGBA', (90, 56))
                pen = ImageDraw.Draw(fx)
                for radius, alpha in [(23, 45), (16, 100), (10, 230)]:
                    pen.ellipse((26-radius, 28-radius, 26+radius, 28+radius), fill=(*color, alpha))
                pen.polygon([(4, 28), (28, 17), (81, 26), (37, 32), (75, 42), (24, 38)], fill=(*color, 220))
                pen.ellipse((13, 21, 28, 35), fill=(255, 226, 156, 255))
                fx.save(out / f'projectile_{action}.png')
    preview.save(root / 'docs' / 'bestiario_preview.png')
    pygame.quit()


if __name__ == '__main__':
    main(sys.argv[1])
