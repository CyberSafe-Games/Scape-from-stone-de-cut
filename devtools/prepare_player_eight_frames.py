"""Recorta arte original em 27 sequências de oito poses com paleta compartilhada."""
import json
import os
import sys
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import pygame
from PIL import Image, ImageDraw
from devtools.polish_boss_sequences import cells, palette_for, grade

FOLDER = ROOT / 'assets/player/eight_frames'


def anchor(im):
    """Usa os pés, sem centralizar o personagem pelo alcance da arma."""
    a = np.array(im)
    b = im.getbbox()
    y, x = np.indices(a.shape[:2])
    skin = ((a[:, :, 3] > 180) & (y >= b[3]-max(5, (b[3]-b[1])*.07))
            & (a[:, :, 0].astype(float) > a[:, :, 1]*1.12)
            & (a[:, :, 1].astype(float) > a[:, :, 2]*1.10))
    yy, xx = np.where(skin)
    if len(xx) < 3:
        yy, xx = np.where((a[:, :, 3] > 120) & (y >= b[3]-4))
    return float(np.median(xx)), float(np.percentile(yy, 99)+1)


def pack(im, scale, ax, floor):
    b = im.getbbox()
    crop = im.crop(b)
    crop = crop.resize((max(1, round(crop.width*scale)), max(1, round(crop.height*scale))),
                       Image.Resampling.NEAREST)
    out = Image.new('RGBA', (320, 260))
    out.alpha_composite(crop, (round(160-(ax-b[0])*scale), round(258-(floor-b[1])*scale)))
    out.paste((0, 0, 0, 0), (0, 258, 320, 260))
    return out


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    manifest = json.loads((FOLDER/'source/manifest.json').read_text(encoding='utf8'))
    extracted = {}
    for source, groups in manifest.items():
        rows = cells(Image.open(FOLDER/'source'/f'{source}.png').convert('RGBA'), len(groups))
        extracted.update(zip(groups, rows))
    palette = palette_for([im for frames in extracted.values() for im in frames])
    frames_by_group = {}
    for group, frames in extracted.items():
        first = frames[0]
        first_height = first.getbbox()[3]-first.getbbox()[1]
        scale = 130/first_height
        packed = []
        for im in frames:
            ax, floor = anchor(im)
            # Repouso usa altura uniforme; agachamentos e recuos mantêm sua trajetória.
            actual_scale = 130/(im.getbbox()[3]-im.getbbox()[1]) if group == 'idle' else scale
            packed.append(grade(pack(im, actual_scale, ax, floor), palette))
        frames_by_group[group] = packed
    idle = frames_by_group['idle'][0]
    for group, frames in frames_by_group.items():
        if group != 'idle':
            frames[0] = idle.copy()
        frames[-1] = idle.copy()
        preview = Image.new('RGB', (8*200, 185), '#18302b')
        for i, frame in enumerate(frames, 1):
            frame.save(FOLDER/f'{group}_{i}.png')
            thumb = frame.resize((200, 162), Image.Resampling.NEAREST)
            preview.paste(thumb, ((i-1)*200, 20), thumb)
        ImageDraw.Draw(preview).text((8, 4), group, fill='#e7cb91')
        preview.save(ROOT/'docs'/f'player_{group}_eight_frames.png')
    (FOLDER/'manifest.json').write_text(json.dumps(list(frames_by_group), indent=2), encoding='utf8')
    (FOLDER/'palette.json').write_text(json.dumps(palette.getpalette()), encoding='utf8')
    fx_source = FOLDER/'source/ultimate_fx.png'
    if fx_source.exists():
        rows = cells(Image.open(fx_source).convert('RGBA'), 3)
        for uid, frames in zip(('mana_ancestral', 'forcas_ancestrais', 'rugido_da_floresta'), rows):
            scale = (175 if uid == 'mana_ancestral' else 270 if uid == 'forcas_ancestrais' else 230)
            scale /= max(max(im.getbbox()[2]-im.getbbox()[0], im.getbbox()[3]-im.getbbox()[1]) for im in frames)
            for i, im in enumerate(frames, 1):
                crop = im.crop(im.getbbox())
                crop = crop.resize((max(1, round(crop.width*scale)), max(1, round(crop.height*scale))), Image.Resampling.NEAREST)
                out = Image.new('RGBA', (384, 320))
                out.alpha_composite(crop, (192-crop.width//2, 160-crop.height//2))
                out.save(FOLDER/f'{uid}_effect_{i}.png')
    print(f'{len(frames_by_group)} sequencias, {len(frames_by_group)*8} sprites exportados.')
    pygame.quit()


if __name__ == '__main__':
    main()
