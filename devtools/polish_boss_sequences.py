"""Prepara sequências completas com a paleta nova; não alterna arte antiga/nova."""
import os
import sys
import json
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import pygame
from src.systems.boss_animation_kits import KITS
from devtools.prepare_boss_eight_frames import silhouette

FOLDER = ROOT/'assets/bosses/eight_frames'
HEIGHTS = {'guardiao_da_pedra':156,'goblin_nerd':127,'corpo_seco':126,'carrasco_da_vigilia':171,
           'alvaro_tex_phase1':190,'alvaro_tex_phase2':102}


def cells(sheet, rows):
    result = []
    occupancy=(np.array(sheet)[:,:,3]>180).sum(1)
    score=np.convolve(occupancy,np.ones(5),mode='same')
    cuts=[0]
    for row in range(1,rows):
        center=round(row*sheet.height/rows)
        radius=round(sheet.height/rows*.48)
        lo=max(cuts[-1]+10,center-radius);hi=min(sheet.height,center+radius)
        candidates=np.flatnonzero(score[lo:hi]==score[lo:hi].min())+lo
        # Find an actual transparent gutter; generated grids can drift vertically.
        cuts.append(int(candidates[np.argmin(abs(candidates-center))]))
    cuts.append(sheet.height)
    for row in range(rows):
        line = []
        for col in range(8):
            box = (round(col*sheet.width/8),cuts[row],
                   round((col+1)*sheet.width/8),cuts[row+1])
            line.append(silhouette(sheet.crop(box)))
        result.append(line)
    return result


def boot_anchor(im):
    a = np.array(im)
    bounds = im.getbbox()
    y,x = np.indices(a.shape[:2])
    hsv = np.array(im.convert('RGB').convert('HSV'))
    boots = ((a[:,:,3]>180) & (y>bounds[3]-(bounds[3]-bounds[1])*.18)
             & (x>im.width*.20) & (x<im.width*.80)
             & (hsv[:,:,0]<45) & (hsv[:,:,1]>35) & (hsv[:,:,2]<220))
    yy,xx = np.where(boots)
    if len(xx)>12:
        return float(np.median(xx)),float(np.percentile(yy,99)+1)
    yy,xx = np.where((a[:,:,3]>180) & (y>=bounds[3]-6))
    return (float(np.median(xx)) if len(xx) else im.width/2),float(bounds[3])


def palette_for(images, grey=False):
    pixels = []
    for im in images:
        a=np.array(im);pixels.append(a[:,:,:3][a[:,:,3]>60][::3])
    colors = np.concatenate(pixels)
    sample = Image.fromarray(colors.reshape(1,-1,3))
    palette = sample.quantize(colors=240 if grey else 256)
    if grey:
        p=palette.getpalette()[:720]
        for grey_value in range(16):p.extend([grey_value*17]*3)
        palette.putpalette(p)
    return palette


def grade(im,palette,hurt=False):
    a=np.array(im)
    # The characters are opaque. Remove low-alpha ghosts from recoil artwork;
    # preserve translucency in smoke and magic rather than darkening the whole actor.
    a[a[:,:,3]<(180 if hurt else 45)]=0
    a[:,:,3][a[:,:,3]>210]=255
    rgb=Image.fromarray(a[:,:,:3]).quantize(palette=palette,dither=Image.Dither.NONE).convert('RGB')
    a[:,:,:3]=np.array(rgb)
    a[a[:,:,3]==0]=0
    return Image.fromarray(a)


def pack(im,scale,anchor_x,floor,height=320):
    b=im.getbbox()
    crop=im.crop(b)
    crop=crop.resize((max(1,round(crop.width*scale)),max(1,round(crop.height*scale))),Image.Resampling.NEAREST)
    out=Image.new('RGBA',(448,height))
    out.alpha_composite(crop,(round(224-(anchor_x-b[0])*scale),round(height-2-(floor-b[1])*scale)))
    out.paste((0,0,0,0),(0,height-2,448,height))
    return out


def save_kit(slug,groups,frames,palette):
    folder=FOLDER/slug;folder.mkdir(exist_ok=True)
    preview=Image.new('RGB',(8*224,len(groups)*175),'#172923')
    for row,g in enumerate(groups):
        for i,im in enumerate(frames[g],1):
            im.save(folder/f'{g}_{i}.png')
            small=im.resize((224,160),Image.Resampling.NEAREST)
            preview.paste(small,((i-1)*224,row*175+15),small)
        ImageDraw.Draw(preview).text((6,row*175),g,fill='white')
    palette_colors=[palette.getpalette()[i:i+3] for i in range(0,768,3)]
    (folder/'palette.json').write_text(json.dumps(palette_colors),encoding='utf8')
    preview.save(ROOT/'docs'/f'{slug}_eight_frames.png')


def material_map(source,targets):
    def sample(images):
        parts=[]
        for im in images:
            a=np.array(im);hsv=np.array(im.convert('RGB').convert('HSV'))
            parts.append(hsv[(a[:,:,3]>210)&(hsv[:,:,1]>35)])
        return np.concatenate(parts).astype(float)
    a,b=sample(source),sample(targets)
    mapping=[]
    for sector in range(6):
        x=a[(a[:,0]*6//256)==sector];z=b[(b[:,0]*6//256)==sector]
        if len(x)>30 and len(z)>30:
            mapping.append((np.percentile(x[:,2],[0,10,30,50,70,90,100]),
                            np.percentile(z[:,2],[0,10,30,50,70,90,100]),
                            float(np.median(z[:,1])/max(1,np.median(x[:,1])))))
        else:mapping.append(None)
    return mapping


def recolor_materials(im,mapping):
    hsv=np.array(im.convert('RGB').convert('HSV')).astype(float)
    old=hsv.copy()
    for sector,rule in enumerate(mapping):
        if rule is None:continue
        mask=((old[:,:,0]*6//256)==sector)&(old[:,:,1]>35)
        hsv[:,:,2][mask]=np.interp(old[:,:,2][mask],rule[0],rule[1])
        hsv[:,:,1][mask]=np.clip(old[:,:,1][mask]*rule[2],0,255)
    rgb=Image.fromarray(hsv.astype('uint8'),mode='HSV').convert('RGB')
    rgb.putalpha(im.getchannel('A'))
    return rgb


def main():
    pygame.init();pygame.display.set_mode((1,1))
    manifest={}
    for name,(slug,groups) in list(KITS.items())[:4]:
        sheet=Image.open(FOLDER/slug/'sequence_v2.png').convert('RGBA')
        rows=cells(sheet,7)
        if slug=='carrasco_da_vigilia':
            # The generated heavy combo put a low follow-through before the spin.
            rows[3]=[rows[3][i] for i in (0,1,3,4,5,2,6,7)]
        scale=HEIGHTS[slug]/np.median([im.getbbox()[3]-im.getbbox()[1] for im in rows[0]])
        anchor=float(np.median([boot_anchor(im)[0] for im in rows[0]]))
        palette=palette_for([im for row in rows for im in row])
        frames={}
        for row,g in enumerate(groups):
            frames[g]=[]
            # Every standing action starts at ready. Match that body's scale,
            # not an overhead axe or a later spell's bounding rectangle.
            first=rows[row][0].getbbox()
            row_scale=(HEIGHTS[slug]/(first[3]-first[1])) if g!='dano' else scale
            row_anchor=boot_anchor(rows[row][0])[0]
            for im in rows[row]:
                prepared=grade(im,palette,g=='dano')
                if slug=='guardiao_da_pedra' and g=='ultimate':
                    pixels=np.array(prepared)
                    rgb=pixels[:,:,:3].astype(float)
                    blue=(rgb[:,:,2]>rgb[:,:,0]*1.1)&(rgb[:,:,2]>rgb[:,:,1]*.9)&(rgb[:,:,2]>80)
                    pixels[blue]=0
                    warm=(rgb[:,:,0]>rgb[:,:,1]*1.02)&(rgb[:,:,1]>rgb[:,:,2]*.90)&(pixels[:,:,3]>120)
                    body_zone=Image.fromarray(warm.astype('uint8')*255).filter(ImageFilter.MaxFilter(9))
                    pixels[np.array(body_zone)==0]=0
                    prepared=silhouette(Image.fromarray(pixels),particles=False)
                frames[g].append(pack(prepared,row_scale,row_anchor,boot_anchor(im)[1]))
        # Every action closes on exactly the same ready pose, including recoil.
        for group in groups:frames[group][-1]=frames['idle'][0].copy()
        save_kit(slug,groups,frames,palette)
        manifest[slug]=list(groups)

    sheet=Image.open(FOLDER/'alvaro_tex_sequence_v2.png').convert('RGBA')
    rows=cells(sheet,4)
    new_palette=palette_for([im for row in rows for im in row],grey=True)
    phase_frames={}
    for phase in (1,2):
        slug=f'alvaro_tex_phase{phase}'
        new_rows=rows[(phase-1)*2:phase*2]
        scale=HEIGHTS[slug]/np.median([im.getbbox()[3]-im.getbbox()[1] for im in new_rows[0]])
        anchor=float(np.median([boot_anchor(im)[0] for im in new_rows[0]]))
        frames={g:[pack(grade(im,new_palette,g=='dano'),scale,anchor,boot_anchor(im)[1],250) for im in line]
                for g,line in zip(('idle','dano'),new_rows)}
        folder=ROOT/f'assets/bosses/alvaro_tex/phase{phase}'
        old=[Image.open(folder/f'{g}_{i}.png').convert('RGBA') for g in ('idle','dano') for i in range(1,5)]
        mapping=material_map(old,[im for row in new_rows for im in row])
        groups=KITS['álvaro e tex' if phase==1 else 'álvaro e tex · pequeno'][1]
        for g in groups:
            if g in frames:continue
            raw=[Image.open(folder/f'{g}_{i}.png').convert('RGBA') for i in range(1,9)]
            group_mapping=material_map([raw[0]],[new_rows[0][0]])
            ready=recolor_materials(raw[0],group_mapping)
            a=np.array(ready);b=np.array(frames['idle'][0])
            gain=np.clip(b[:,:,:3][b[:,:,3]>210].mean(0)/np.maximum(1,a[:,:,:3][a[:,:,3]>210].mean(0)),.75,1.5)
            frames[g]=[]
            for original in raw:
                harmonized=np.array(recolor_materials(original,group_mapping))
                harmonized[:,:,:3]=np.clip(harmonized[:,:,:3].astype(float)*gain,0,255).astype('uint8')
                recolored=grade(Image.fromarray(harmonized),new_palette)
                aligned=Image.new('RGBA',(448,250))
                aligned.alpha_composite(recolored,(0,2))
                aligned.paste((0,0,0,0),(0,248,448,250))
                frames[g].append(aligned)
        for g in groups:
            if g!='transition':frames[g][-1]=frames['idle'][0].copy()
        phase_frames[phase]=(slug,groups,frames)
    phase_frames[1][2]['transition'][-1]=phase_frames[2][2]['idle'][0].copy()
    for slug,groups,frames in phase_frames.values():
        save_kit(slug,groups,frames,new_palette)
        manifest[slug]=list(groups)
    (FOLDER/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    pygame.quit()


if __name__=='__main__':main()
