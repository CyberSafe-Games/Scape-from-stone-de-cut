"""Intercala quatro desenhos inéditos com as quatro camadas originais, sem alterá-las."""
import os
import sys
import json
import shutil
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
import numpy as np
from PIL import Image,ImageDraw
from devtools.prepare_boss_eight_frames import silhouette
from src.systems.boss_ultimate_animations import BOSS_ULTIMATE_ANIMATIONS


def main():
    pygame.init();pygame.display.set_mode((1,1))
    folder=ROOT/'assets/boss_ultimate_effects'
    atlas=Image.new('RGB',(8*210,len(BOSS_ULTIMATE_ANIMATIONS)*205),'#14271f')
    manifest={}
    for row,(name,spec) in enumerate(BOSS_ULTIMATE_ANIMATIONS.items()):
        target=folder/'eight_frames'/spec.asset_id
        sheet=Image.open(target/'intermediates.png').convert('RGBA')
        original=[Image.open(folder/spec.asset_id/f'effect_{i}.png').convert('RGBA') for i in range(1,5)]
        sizes=[max(im.getbbox()[2]-im.getbbox()[0],im.getbbox()[3]-im.getbbox()[1]) for im in original]
        for i in range(4):
            shutil.copyfile(folder/spec.asset_id/f'effect_{i+1}.png',target/f'effect_{i*2+1}.png')
            cell=sheet.crop((round(i*sheet.width/4),0,round((i+1)*sheet.width/4),sheet.height))
            flight_override=target/'flight_transition.png'
            if spec.asset_id=='goblin_nerd' and i==1 and flight_override.exists():
                cell=Image.open(flight_override).convert('RGBA')
            cell=silhouette(cell)
            crop=cell.crop(cell.getbbox())
            maximum=(sizes[i]+sizes[i+1])/2 if i<3 else sizes[-1]*.75
            ratio=maximum/max(crop.size)
            crop=crop.resize((max(1,round(crop.width*ratio)),max(1,round(crop.height*ratio))),Image.Resampling.LANCZOS)
            pixels=np.array(crop);pixels[pixels[:,:,3]<5]=0
            crop=Image.fromarray(pixels)
            out=Image.new('RGBA',(384,320))
            out.alpha_composite(crop,(192-crop.width//2,160-crop.height//2))
            out.save(target/f'effect_{i*2+2}.png')
        for i in range(8):
            im=Image.open(target/f'effect_{i+1}.png').convert('RGBA')
            im.thumbnail((205,175))
            atlas.paste(im,(i*210+(210-im.width)//2,row*205+24+(175-im.height)//2),im)
        ImageDraw.Draw(atlas).text((5,row*205+3),name,fill='#e6c88e')
        manifest[spec.asset_id]={'frames':8,'original_keys':[1,3,5,7],'new_intermediates':[2,4,6,8]}
    (folder/'eight_frames/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    atlas.save(ROOT/'docs/boss_ultimate_effects_eight_frames.png')
    print('48 camadas: 24 originais preservadas e 24 desenhos novos.')
    pygame.quit()


if __name__=='__main__':main()
