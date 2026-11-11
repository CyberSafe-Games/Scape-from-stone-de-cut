"""Referências e preparo dos quatro intervalos novos; conserva as oito poses aprovadas."""
import os
import sys
import json
import itertools
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pygame
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from src.systems.boss_animation_kits import KITS
from src.systems.boss_ultimate_animations import BOSS_ULTIMATE_ANIMATIONS
from devtools.polish_boss_sequences import boot_anchor, grade, material_map, recolor_materials
from devtools.prepare_boss_eight_frames import silhouette

BODY = ROOT/'assets/bosses/twelve_frames'
FX = ROOT/'assets/boss_ultimate_effects/twelve_frames'
PAIRS = ((0,1),(2,3),(4,5),(6,7))


def reference(images, groups, destination, cell=(224,180)):
    out = Image.new('RGBA', (cell[0]*8,cell[1]*len(groups)))
    draw = ImageDraw.Draw(out)
    for row,group in enumerate(groups):
        draw.text((4,row*cell[1]+2), group, fill='#d6b675')
        for col,im in enumerate(images[group]):
            resized=im.copy()
            resized.thumbnail((cell[0],cell[1]-16),Image.Resampling.NEAREST)
            out.alpha_composite(resized,(col*cell[0]+(cell[0]-resized.width)//2,
                                        (row+1)*cell[1]-resized.height))
    destination.parent.mkdir(parents=True,exist_ok=True)
    out.save(destination)


def references():
    metadata={}
    for name,(slug,groups) in KITS.items():
        folder=ROOT/'assets/bosses/eight_frames'/slug
        images={g:[Image.open(folder/f'{g}_{i}.png').convert('RGBA') for i in range(1,9)] for g in groups}
        reference(images,groups,BODY/slug/'reference.png')
        metadata[slug]={'name':name,'groups':groups,'canvas':images['idle'][0].size}
    (BODY/'sources.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf8')
    for spec in BOSS_ULTIMATE_ANIMATIONS.values():
        images={'effect':[Image.open(ROOT/'assets/boss_ultimate_effects/eight_frames'/spec.asset_id/f'effect_{i}.png').convert('RGBA') for i in range(1,9)]}
        reference(images,('effect',),FX/spec.asset_id/'reference.png',cell=(224,240))
    print('Referências: oito formas de boss e seis efeitos especiais.')


def split(sheet,rows,columns=4):
    a=np.array(sheet)
    occupancy=(a[:,:,3]>180).sum(1)
    score=np.convolve(occupancy,np.ones(5),mode='same')
    cuts=[0]
    for row in range(1,rows):
        center=round(row*sheet.height/rows);radius=round(sheet.height/rows*.35)
        lo=max(cuts[-1]+10,center-radius);hi=min(sheet.height,center+radius)
        candidates=np.flatnonzero(score[lo:hi]==score[lo:hi].min())+lo
        cuts.append(int(candidates[np.argmin(abs(candidates-center))]))
    cuts.append(sheet.height)
    return [[silhouette(sheet.crop((round(c*sheet.width/columns),cuts[r],
                                    round((c+1)*sheet.width/columns),cuts[r+1])))
             for c in range(columns)] for r in range(rows)]


def comparison(im):
    # Comparação apenas para ordenar desenhos; nenhuma mistura é exportada.
    im=im.resize((80,60),Image.Resampling.BOX).filter(ImageFilter.GaussianBlur(1))
    a=np.array(im).astype(float)/255
    a[:,:,:3]*=a[:,:,3:4]
    a[:,:,3]*=2
    return a


def intermediates(originals,row,idle_row,palette,scale,group,idle_entry=False):
    candidates=list(row) if group=='idle' else list(row)+list(idle_row)
    scores=np.zeros((4,len(candidates)))
    choices={}
    for column,(left,right) in enumerate(PAIRS):
        a,b=originals[left],originals[right]
        target=(comparison(a)+comparison(b))/2
        dest_x=(boot_anchor(a)[0]+boot_anchor(b)[0])/2
        dest_y=(boot_anchor(a)[1]+boot_anchor(b)[1])/2
        for candidate,im in enumerate(candidates):
            ax,floor=boot_anchor(im)
            harmonized=recolor_materials(im,material_map([im],[a,b]))
            p=grade(harmonized,palette,group=='dano')
            bounds=p.getbbox();crop=p.crop(bounds)
            actual_scale=scale
            if group=='idle':
                actual_scale=((a.getbbox()[3]-a.getbbox()[1])+(b.getbbox()[3]-b.getbbox()[1]))/2/crop.height
            crop=crop.resize((max(1,round(crop.width*actual_scale)),max(1,round(crop.height*actual_scale))),Image.Resampling.NEAREST)
            frame=Image.new('RGBA',a.size)
            frame.alpha_composite(crop,(round(dest_x-(ax-bounds[0])*actual_scale),round(dest_y-(floor-bounds[1])*actual_scale)))
            frame.paste((0,0,0,0),(0,a.height-2,a.width,a.height))
            if group=='idle':
                targets=[]
                for key in (a,b):
                    pixels=np.array(key)
                    targets.append(float(pixels[:,:,:3][pixels[:,:,3]>210].mean()))
                target_brightness=sum(targets)/2
                for _ in range(4):
                    pixels=np.array(frame)
                    current=float(pixels[:,:,:3][pixels[:,:,3]>210].mean())
                    pixels[:,:,:3]=np.clip(pixels[:,:,:3].astype(float)*target_brightness/max(1,current),0,255).astype('uint8')
                    frame=grade(Image.fromarray(pixels),palette)
            scores[column,candidate]=float(np.mean((comparison(frame)-target)**2))
            choices[column,candidate]=frame
    # O repouso só complementa entrada/saída. Nunca interrompe o golpe ou a cura.
    if group!='idle':
        scores[1:3,4:]=float('inf')
        scores[0,1:4]=float('inf')
        scores[3,:3]=float('inf')
        if idle_entry:
            scores[0,:4]=float('inf')
    order=min(itertools.permutations(range(len(candidates)),4),key=lambda ids:sum(scores[i,j] for i,j in enumerate(ids)))
    return [choices[i,j] for i,j in enumerate(order)],list(order)


def main():
    if '--references' in sys.argv:
        references();return
    pygame.init();pygame.display.set_mode((1,1))
    manifest={}
    overview=Image.new('RGB',(4*320,8*220),'#172923')
    for number,(name,(slug,groups)) in enumerate(KITS.items()):
        old=ROOT/'assets/bosses/eight_frames'/slug
        folder=BODY/slug
        rows=split(Image.open(folder/'inbetweens.png').convert('RGBA'),len(groups))
        colors=json.loads((old/'palette.json').read_text(encoding='utf8'))
        palette=Image.new('P',(1,1));palette.putpalette([v for color in colors for v in color])
        prepared={}
        selection={}
        for group,row in zip(groups,rows):
            originals=[Image.open(old/f'{group}_{i}.png').convert('RGBA') for i in range(1,9)]
            # A ready drawing sets body size; raised weapons and effects must not shrink the actor.
            idle=Image.open(old/'idle_1.png').convert('RGBA')
            native=idle.getbbox();first=rows[0][0].getbbox()
            scale=(native[3]-native[1])/(first[3]-first[1])
            additions,selection[group]=intermediates(originals,row,rows[0],palette,scale,group,
                                                    idle_entry=slug=='gordofera' and group=='ultimate')
            frames=[]
            for column,(left,right) in enumerate(PAIRS):
                frames.extend((originals[left],additions[column],originals[right]))
            prepared[group]=frames
            for i,im in enumerate(frames,1):im.save(folder/f'{group}_{i}.png')
        atlas=Image.new('RGB',(12*160,len(groups)*145),'#172923')
        for r,group in enumerate(groups):
            for i,im in enumerate(prepared[group]):
                thumb=im.copy();thumb.thumbnail((160,128),Image.Resampling.NEAREST)
                atlas.paste(thumb,(i*160,r*145+16),thumb)
            ImageDraw.Draw(atlas).text((4,r*145+2),group,fill='#e5c68d')
        atlas.save(ROOT/'docs'/f'boss_{slug}_twelve_frames.png')
        ImageDraw.Draw(overview).text((5,number*220+3),name,fill='#e5c68d')
        for c,g in enumerate(('idle','dano',next(g for g in groups if g.startswith('atk')),'ultimate' if 'ultimate' in groups else 'atk3')):
            im=prepared[g][7 if g=='idle' else 6]
            thumb=im.copy();thumb.thumbnail((320,200),Image.Resampling.NEAREST)
            overview.paste(thumb,(c*320,number*220+20),thumb)
        (folder/'palette.json').write_text(json.dumps(colors),encoding='utf8')
        (folder/'selection.json').write_text(json.dumps(selection,indent=2),encoding='utf8')
        manifest[slug]=list(groups)
    # The duo's last transition pose must remain the small form's ready pose.
    (BODY/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    overview.save(ROOT/'docs/bosses_twelve_frames_overview.png')
    prepare_effects()
    pygame.quit()
    print('55 sequências de corpo, 660 quadros: oito originais + quatro intermediários.')


def prepare_effects():
    overview=Image.new('RGB',(12*160,6*170),'#172923')
    manifest={}
    for row,(name,spec) in enumerate(BOSS_ULTIMATE_ANIMATIONS.items()):
        folder=FX/spec.asset_id
        originals=[Image.open(ROOT/'assets/boss_ultimate_effects/eight_frames'/spec.asset_id/f'effect_{i}.png').convert('RGBA') for i in range(1,9)]
        additions=split(Image.open(folder/'inbetweens.png').convert('RGBA'),1)[0]
        frames=[]
        for i,(left,right) in enumerate(PAIRS):
            a,b=originals[left],originals[right]
            sizes=[max(im.getbbox()[2]-im.getbbox()[0],im.getbbox()[3]-im.getbbox()[1]) for im in (a,b)]
            crop=additions[i].crop(additions[i].getbbox())
            ratio=sum(sizes)/2/max(crop.size)
            crop=crop.resize((max(1,round(crop.width*ratio)),max(1,round(crop.height*ratio))),Image.Resampling.LANCZOS)
            frame=Image.new('RGBA',(384,320))
            frame.alpha_composite(crop,(192-crop.width//2,160-crop.height//2))
            pixels=np.array(frame);pixels[pixels[:,:,3]<5]=0
            frames.extend((a,Image.fromarray(pixels),b))
        for i,im in enumerate(frames,1):
            im.save(folder/f'effect_{i}.png')
            thumb=im.copy();thumb.thumbnail((156,145))
            overview.paste(thumb,((i-1)*160,row*170+20),thumb)
        ImageDraw.Draw(overview).text((5,row*170+2),name,fill='#e5c68d')
        manifest[spec.asset_id]={'frames':12,'original_keys':[1,3,4,6,7,9,10,12],'new_intermediates':[2,5,8,11]}
    (FX/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    overview.save(ROOT/'docs/boss_ultimate_effects_twelve_frames.png')


if __name__=='__main__':main()
