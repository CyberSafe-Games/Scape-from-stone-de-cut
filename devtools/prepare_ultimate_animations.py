"""Separa as folhas RGBA 4x2 em poses e efeitos para o jogo."""
from pathlib import Path
import numpy as np
import pygame
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]


def extract(image, col, row):
    width, height = image.size
    cell = image.crop((round(col*width/4), round(row*height/2),
                       round((col+1)*width/4), round((row+1)*height/2)))
    pixels = np.array(cell)
    # Preserve the supplied transparency; only discard imperceptible pixels.
    pixels[pixels[:, :, 3] < 10] = 0
    if not row:
        sprite = pygame.image.frombytes(pixels.tobytes(), cell.size, 'RGBA')
        parts = pygame.mask.from_surface(sprite, 50).connected_components(30)
        main = max(parts, key=lambda m: m.count())
        mask = Image.frombytes('RGB', cell.size, pygame.image.tobytes(
            main.to_surface(setcolor='white', unsetcolor='black'), 'RGB')).convert('L')
        keep = np.array(mask.filter(ImageFilter.MaxFilter(5))) > 0
        pixels[~keep] = 0
    # Outer wisps can cross a mathematical cell boundary. Fade just that
    # narrow edge to avoid hard-cut smoke while retaining the whole subject.
    if row:
        sprite = pygame.image.frombytes(pixels.tobytes(), cell.size, 'RGBA')
        parts = pygame.mask.from_surface(sprite, 35).connected_components(3)
        main = max(parts, key=lambda m: m.count())
        bounds = main.get_bounding_rects()[0].inflate(20, 20)
        keep_mask = pygame.mask.Mask(cell.size)
        for part in parts:
            if part is main or bounds.collidepoint(part.get_bounding_rects()[0].center):
                keep_mask.draw(part, (0, 0))
        keep = Image.frombytes('RGB', cell.size, pygame.image.tobytes(
            keep_mask.to_surface(setcolor='white', unsetcolor='black'), 'RGB')).convert('L')
        pixels[np.array(keep.filter(ImageFilter.MaxFilter(3))) == 0] = 0
        for x in range(6):
            pixels[:, x, 3] = (pixels[:, x, 3].astype(float)*x/6).astype('uint8')
            pixels[:, -x-1, 3] = (pixels[:, -x-1, 3].astype(float)*x/6).astype('uint8')
    cell = Image.fromarray(pixels)
    return cell.crop(cell.getbbox())


def main():
    preview = Image.new('RGB', (4*320, 3*430), '#101e1b')
    labels = ImageDraw.Draw(preview)
    for row, uid in enumerate(('mana_ancestral', 'forcas_ancestrais', 'rugido_da_floresta')):
        folder = ROOT/'assets'/'ultimate_effects'/uid
        source = Image.open(folder/'source.png').convert('RGBA')
        casts = [extract(source, col, 0) for col in range(4)]
        effects = [extract(source, col, 1) for col in range(4)]
        body_scale = 130/casts[3].height
        effect_maximum = 175 if uid == 'mana_ancestral' else 270 if uid == 'forcas_ancestrais' else 230
        effect_scale = effect_maximum/max(max(e.size) for e in effects)
        for i, (cast, effect) in enumerate(zip(casts, effects), 1):
            pixels = np.array(cast)
            opaque_y = np.where(pixels[:, :, 3] > 60)[0]
            floor = opaque_y.max()+1
            ys, xs = np.where((pixels[:, :, 3] > 60) &
                              (np.indices(pixels.shape[:2])[0] >= floor*.92))
            anchor_x = float(np.median(xs))
            scaled = cast.resize((round(cast.width*body_scale), round(cast.height*body_scale)), Image.Resampling.LANCZOS)
            frame = Image.new('RGBA', (320, 260))
            frame.alpha_composite(scaled, (round(160-anchor_x*body_scale), 258-round(floor*body_scale)))
            frame.save(folder/f'cast_{i}.png')
            scaled_fx = effect.resize((round(effect.width*effect_scale), round(effect.height*effect_scale)), Image.Resampling.LANCZOS)
            fx = Image.new('RGBA', (384, 320))
            fx.alpha_composite(scaled_fx, (192-scaled_fx.width//2, 160-scaled_fx.height//2))
            fx.save(folder/f'effect_{i}.png')
            preview.paste(frame, ((i-1)*320, row*430-15), frame)
            fx_preview = fx.resize((269, 224), Image.Resampling.LANCZOS)
            preview.paste(fx_preview, ((i-1)*320+25, row*430+205), fx_preview)
        labels.text((12, row*430+7), uid, fill='#e4c78c')
        print(uid, 'body scale', round(body_scale, 3), 'effect scale', round(effect_scale, 3))
    preview.save(ROOT/'docs'/'sprites_ultimates_animacoes.png')


if __name__ == '__main__':
    main()
