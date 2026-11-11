"""Prepara 13 kits completos com paleta por personagem e pivôs estáveis."""
import os
import sys
import json
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
import numpy as np
from PIL import Image,ImageDraw
from devtools.polish_boss_sequences import cells,boot_anchor,palette_for,grade

FOLDER=ROOT/'assets/enemies/eight_frames'


def pack(im,scale,ax,floor):
    b=im.getbbox();crop=im.crop(b)
    crop=crop.resize((max(1,round(crop.width*scale)),max(1,round(crop.height*scale))),Image.Resampling.NEAREST)
    out=Image.new('RGBA',(448,260))
    out.alpha_composite(crop,(round(224-(ax-b[0])*scale),round(258-(floor-b[1])*scale)))
    out.paste((0,0,0,0),(0,258,448,260))
    return out


def bat_anchor(im,scale,fallback):
    a=np.array(im);rgb=a[:,:,:3].astype(float)
    eyes=(a[:,:,3]>180)&(rgb[:,:,0]>110)&(rgb[:,:,0]>rgb[:,:,1]*1.7)&(rgb[:,:,0]>rgb[:,:,2]*1.3)
    yy,xx=np.where(eyes)
    return (float(np.median(xx))+50/scale,float(np.median(yy))+100/scale) if len(xx) else fallback


def slime_projectile():
    source=pygame.image.load(str(ROOT/'assets/slime/atk2.png')).convert_alpha()
    parts=pygame.mask.from_surface(source,80).connected_components(6)
    main=max(parts,key=lambda p:p.count());body=main.get_bounding_rects()[0]
    candidates=[p for p in parts if p is not main and p.get_bounding_rects()[0].centerx<body.centerx]
    if not candidates:
        raise ValueError('Projétil do Slime não encontrado na referência original.')
    selected=max(candidates,key=lambda p:p.count())
    mask=selected.to_surface(setcolor=(255,255,255,255),unsetcolor=(0,0,0,0))
    source.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
    bounds=selected.get_bounding_rects()[0]
    bounds.width=min(bounds.width,round(bounds.height*.9))
    crop=source.subsurface(bounds).copy()
    factor=25/max(crop.get_size())
    crop=pygame.transform.scale(crop,(max(1,round(crop.get_width()*factor)),max(1,round(crop.get_height()*factor))))
    pygame.image.save(crop,str(FOLDER/'slime/projectile_atk.png'))


def main():
    pygame.init();pygame.display.set_mode((1,1))
    meta=json.loads((FOLDER/'sources.json').read_text(encoding='utf8'))
    manifest={}
    overview=Image.new('RGB',(1200,200*len(meta)),'#172923')
    for number,(slug,spec) in enumerate(meta.items()):
        folder=FOLDER/slug;groups=spec['groups']
        rows=cells(Image.open(folder/'sequence.png').convert('RGBA'),4)
        # Revisão apenas da conjuração de fogo: conserva as demais linhas aprovadas.
        fire_revision=folder/'fire_cast_revision.png'
        if slug=='mago' and fire_revision.is_file():
            rows[2]=cells(Image.open(fire_revision).convert('RGBA'),4)[2]
        palette=palette_for([im for row in rows for im in row])
        first=rows[0][0].getbbox();base_scale=spec['height']/(first[3]-first[1])
        frames={}
        for group,row in zip(groups,rows):
            b=row[0].getbbox()
            scale=base_scale if group=='dano' or slug=='morcego' else spec['height']/(b[3]-b[1])
            ax=boot_anchor(row[0])[0]
            frames[group]=[]
            previous=(ax,boot_anchor(row[0])[1])
            for im in row:
                actual_scale=scale
                if group=='idle' and slug not in ('morcego','macaco','lagarto','slime'):
                    b=im.getbbox();actual_scale=spec['height']/(b[3]-b[1])
                floor=boot_anchor(im)[1]
                if slug=='morcego':
                    ax,floor=bat_anchor(im,scale,previous);previous=(ax,floor)
                frames[group].append(pack(grade(im,palette,group=='dano'),actual_scale,ax,floor))
        ready=frames['idle'][0]
        for group in groups:frames[group][-1]=ready.copy()
        atlas=Image.new('RGB',(8*224,4*150),'#172923')
        for r,group in enumerate(groups):
            for i,im in enumerate(frames[group],1):
                im.save(folder/f'{group}_{i}.png')
                thumb=im.resize((224,130),Image.Resampling.NEAREST)
                atlas.paste(thumb,((i-1)*224,r*150+17),thumb)
            ImageDraw.Draw(atlas).text((5,r*150+2),group,fill='#e5c68d')
        atlas.save(ROOT/'docs'/f'common_{slug}_eight_frames.png')
        ImageDraw.Draw(overview).text((6,200*number+5),spec['name'],fill='#e5c68d')
        for column,group in enumerate(groups):
            pose=frames[group][4].resize((300,174),Image.Resampling.NEAREST)
            overview.paste(pose,(column*300,number*200+24),pose)
        (folder/'palette.json').write_text(json.dumps([palette.getpalette()[i:i+3] for i in range(0,768,3)]),encoding='utf8')
        manifest[slug]=groups
    slime_projectile()
    overview.save(ROOT/'docs/common_eight_frames_overview.png')
    (FOLDER/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print('13 inimigos, 52 sequências e 416 sprites exportados.')
    pygame.quit()


if __name__=='__main__':main()
