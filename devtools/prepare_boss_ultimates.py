"""Exporta poses originais e mantém os efeitos das ultimates aprovadas.

Use --effects apenas para recortar novamente os efeitos das folhas geradas.
Os personagens dessas folhas não são usados: o corpo vem dos assets originais.
"""
import os
import sys
from pathlib import Path
import numpy as np
import pygame
from PIL import Image, ImageFilter, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.systems.boss_ultimate_animations import BOSS_ULTIMATE_ANIMATIONS
from src.core.asset_manager import AssetManager


def extract(source, column, effects=False, asset_id=''):
    w, h = source.size
    # The body is extracted from an extended cell so claws, daggers and feet
    # crossing a mathematical gutter remain complete. Other actors are masked.
    box = ((round(column*w/4), round(h*.51), round((column+1)*w/4), h) if effects else
           (max(0, round(column*w/4-70)), 0, min(w, round((column+1)*w/4+70)), round(h*.56)))
    if effects:
        # Large spectral heads and blade rings cross the equal-width gutters.
        # Bounds follow each illustration, preserving the snout/front arc.
        ranges = {
            'guardiao_da_pedra': ((0, 350), (350, 860), (790, 1380), (1350, 1774)),
            'goblin_nerd': ((0, 390), (425, 875), (850, 1370), (1370, 1774)),
            'corpo_seco': ((0, 365), (350, 880), (805, 1435), (1410, 1774)),
            'carrasco_da_vigilia': ((0, 405), (415, 890), (855, 1355), (1330, 1774)),
        }
        left, right = ranges[asset_id][column]
        box = (round(left*w/1774), round(h*.51), round(right*w/1774), h)
    cell = source.crop(box)
    pixels = np.array(cell)
    pixels[pixels[:, :, 3] < 12] = 0
    sprite = pygame.image.frombytes(pixels.tobytes(), cell.size, 'RGBA')
    parts = pygame.mask.from_surface(sprite, 40).connected_components(4)
    if not effects:
        # Upper silhouettes only; reject large blue/red FX entering from below.
        candidates = [p for p in parts if p.get_bounding_rects()[0].centery < h*.42]
        main = max(candidates, key=lambda p: p.count())
        keep = main
    else:
        main = max(parts, key=lambda p: p.count())
        bounds = main.get_bounding_rects()[0].inflate(18, 18)
        keep = pygame.mask.Mask(cell.size)
        for part in parts:
            if bounds.collidepoint(part.get_bounding_rects()[0].center):
                keep.draw(part, (0, 0))
    mask = Image.frombytes('RGB', cell.size, pygame.image.tobytes(
        keep.to_surface(setcolor='white', unsetcolor='black'), 'RGB')).convert('L')
    pixels[np.array(mask.filter(ImageFilter.MaxFilter(5))) == 0] = 0
    if effects:
        for x in range(24):
            pixels[:, x, 3] = (pixels[:, x, 3].astype(float)*x/24).astype('uint8')
            pixels[:, -1-x, 3] = (pixels[:, -1-x, 3].astype(float)*x/24).astype('uint8')
    image = Image.fromarray(pixels)
    return image.crop(image.getbbox())


def main():
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    pygame.init()
    pygame.display.set_mode((1, 1))
    assets = AssetManager()
    preview = Image.new('RGB', (4*384, 4*470), '#101e1b')
    labels = ImageDraw.Draw(preview)
    for row, (name, spec) in enumerate(BOSS_ULTIMATE_ANIMATIONS.items()):
        folder = ROOT/'assets'/'boss_ultimate_effects'/spec.asset_id
        if '--effects' in sys.argv:
            source = Image.open(folder/'source.png').convert('RGBA')
            effects = [extract(source, i, True, spec.asset_id) for i in range(4)]
            scale = 280/max(max(image.size) for image in effects)
            for i, effect in enumerate(effects, 1):
                resized = effect.resize((round(effect.width*scale), round(effect.height*scale)), Image.Resampling.LANCZOS)
                fx = Image.new('RGBA', (384, 320))
                fx.alpha_composite(resized, (192-resized.width//2, 160-resized.height//2))
                fx.save(folder/f'effect_{i}.png')
        for i, cast in enumerate(assets.get_boss_ultimate_sprites(name), 1):
            pygame.image.save(cast, str(folder/f'cast_{i}.png'))
            frame = Image.frombytes('RGBA', cast.get_size(), pygame.image.tobytes(cast, 'RGBA'))
            fx = Image.open(folder/f'effect_{i}.png').convert('RGBA')
            preview.paste(frame, ((i-1)*384-32, row*470-40), frame)
            thumb = fx.resize((307, 256), Image.Resampling.LANCZOS)
            preview.paste(thumb, ((i-1)*384+38, row*470+215), thumb)
        labels.text((12, row*470+8), name, fill='#e4c78c')
        print(spec.asset_id, 'design original restaurado')
    preview.save(ROOT/'docs'/'boss_ultimates_sprites.png')
    pygame.quit()


if __name__ == '__main__':
    main()
