"""Exporta as sete animações de Zanzara, projéteis e camadas da ultimate."""
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

FOLDER = ROOT/'assets/bosses/eight_frames/zanzara'


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    groups = KITS['zanzara'][1]
    rows = cells(Image.open(FOLDER/'source/sequence.png').convert('RGBA'), len(groups))
    palette = palette_for([im for line in rows for im in line])
    frames = {}
    for group, row in zip(groups, rows):
        b = row[0].getbbox()
        scale = 170/(b[3]-b[1])
        ax = boot_anchor(row[0])[0]
        frames[group] = [pack(grade(im, palette, group=='dano'), scale, ax, boot_anchor(im)[1]) for im in row]
    ready = frames['idle'][0]
    for group in groups:
        frames[group][-1] = ready.copy()
    save_kit('zanzara', groups, frames, palette)
    manifest_path = FOLDER.parent/'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf8'))
    manifest['zanzara'] = list(groups)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf8')
    sheet = Image.open(FOLDER/'source/effects.png').convert('RGBA')
    effects_folder = ROOT/'assets/boss_ultimate_effects/zanzara'
    effects_folder.mkdir(parents=True, exist_ok=True)
    atlas = Image.new('RGB', (4*300, 3*225), '#172923')
    for row in range(3):
        for col in range(4):
            im = silhouette(sheet.crop((round(col*sheet.width/4), round(row*sheet.height/3),
                                        round((col+1)*sheet.width/4), round((row+1)*sheet.height/3))))
            crop = im.crop(im.getbbox())
            maximum = (220 if row == 0 else 82 if row == 1 else 135)
            scale = maximum/max(crop.size)
            crop = crop.resize((max(1, round(crop.width*scale)), max(1, round(crop.height*scale))), Image.Resampling.NEAREST)
            out = Image.new('RGBA', (384, 320) if row == 0 else (160, 160))
            out.alpha_composite(crop, (out.width//2-crop.width//2, out.height//2-crop.height//2))
            if row == 0:
                out.save(effects_folder/f'effect_{col+1}.png')
            else:
                out.save(FOLDER/f'projectile_atk{row+1}_{col+1}.png')
            thumb = out.copy()
            thumb.thumbnail((290, 210))
            atlas.paste(thumb, (col*300+150-thumb.width//2, row*225+12), thumb)
    atlas.save(ROOT/'docs/zanzara_efeitos.png')
    print('Zanzara: 56 poses, 8 projéteis animados e 4 efeitos da ultimate.')
    pygame.quit()


if __name__ == '__main__':
    main()
