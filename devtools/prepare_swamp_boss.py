"""Exporta o guardião do Pântano em sete sequências de oito poses."""
import os
import sys
import json
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pygame
from PIL import Image
from devtools.polish_boss_sequences import cells, boot_anchor, palette_for, grade, pack, save_kit
from devtools.prepare_boss_eight_frames import silhouette
from src.systems.boss_animation_kits import KITS

FOLDER = ROOT/'assets/bosses/eight_frames/gordofera'


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    groups = next(groups for slug, groups in KITS.values() if slug == 'gordofera')
    rows = cells(Image.open(FOLDER/'source/sequence.png').convert('RGBA'), len(groups))
    palette = palette_for([im for row in rows for im in row])
    idle = rows[0][0].getbbox()
    base_scale = 165/(idle[3]-idle[1])
    frames = {}
    for group, row in zip(groups, rows):
        b = row[0].getbbox()
        scale = base_scale if group in ('dano', 'ultimate') else 165/(b[3]-b[1])
        ax = boot_anchor(row[0])[0]
        frames[group] = []
        for im in row:
            b = im.getbbox()
            pose_scale = 165/(b[3]-b[1]) if group == 'idle' else scale
            frames[group].append(pack(grade(im, palette, group=='dano'), pose_scale, ax, boot_anchor(im)[1]))
    for group in groups:
        frames[group][-1] = frames['idle'][0].copy()
    save_kit('gordofera', groups, frames, palette)
    manifest_path = FOLDER.parent/'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf8'))
    manifest['gordofera'] = list(groups)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf8')
    sheet = Image.open(FOLDER/'source/effects.png').convert('RGBA')
    effects_folder = ROOT/'assets/boss_ultimate_effects/gordofera'
    effects_folder.mkdir(parents=True, exist_ok=True)
    atlas = Image.new('RGB', (4*300, 250), '#172923')
    for col in range(4):
        im = silhouette(sheet.crop((round(col*sheet.width/4), 0, round((col+1)*sheet.width/4), sheet.height)))
        crop = im.crop(im.getbbox())
        scale = 240/max(crop.size)
        crop = crop.resize((max(1, round(crop.width*scale)), max(1, round(crop.height*scale))), Image.Resampling.NEAREST)
        out = Image.new('RGBA', (384, 320))
        out.alpha_composite(crop, (192-crop.width//2, 160-crop.height//2))
        out.save(effects_folder/f'effect_{col+1}.png')
        thumb = out.copy()
        thumb.thumbnail((290, 240))
        atlas.paste(thumb, (col*300+150-thumb.width//2, 0), thumb)
    atlas.save(ROOT/'docs/gordofera_efeitos.png')
    print('56 poses e quatro efeitos próprios da ultimate exportados.')
    pygame.quit()


if __name__ == '__main__':
    main()
