"""Amplia as 27 interações preservando as oito poses e a paleta aprovadas."""
import os
import sys
import json
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from PIL import Image,ImageDraw
from devtools.prepare_boss_twelve_frames import reference,split,intermediates,PAIRS
from devtools.prepare_player_eight_frames import anchor
from devtools.polish_boss_sequences import grade,material_map,recolor_materials

OLD=ROOT/'assets/player/eight_frames'
NEW=ROOT/'assets/player/twelve_frames'
ULTIMATES=('mana_ancestral','forcas_ancestrais','rugido_da_floresta')
WEAPON_POSES={'machados_gemeos':{1:1,2:3},'machado_quebra_escudo':{1:1},'adaga_sangrenta':{2:3}}


def refined_weapon_pose(im,a,b,palette,scale):
    """Mantém a arma na mão e a preparação antes do golpe, conforme conferência visual."""
    ax,floor=anchor(im)
    dest_x=(anchor(a)[0]+anchor(b)[0])/2
    dest_y=(anchor(a)[1]+anchor(b)[1])/2
    prepared=grade(recolor_materials(im,material_map([im],[a,b])),palette)
    bounds=prepared.getbbox();crop=prepared.crop(bounds)
    crop=crop.resize((max(1,round(crop.width*scale)),max(1,round(crop.height*scale))),Image.Resampling.NEAREST)
    out=Image.new('RGBA',a.size)
    out.alpha_composite(crop,(round(dest_x-(ax-bounds[0])*scale),round(dest_y-(floor-bounds[1])*scale)))
    out.paste((0,0,0,0),(0,258,320,260))
    return out


def save_png(im,path):
    temporary=path.with_suffix('.tmp.png')
    im.save(temporary)
    temporary.replace(path)


def batches():
    groups=json.loads((OLD/'manifest.json').read_text(encoding='utf8'))
    result={'base':groups[:4],'ultimates':['idle']+groups[4:7]}
    for i in range(5):result[f'cards_{i+1}']=['idle']+groups[7+i*4:11+i*4]
    return result


def references():
    for batch,groups in batches().items():
        images={g:[Image.open(OLD/f'{g}_{i}.png').convert('RGBA') for i in range(1,9)] for g in groups}
        reference(images,groups,NEW/'source'/f'{batch}_reference.png',cell=(200,180))
    reference({g:[Image.open(OLD/f'{g}_effect_{i}.png').convert('RGBA') for i in range(1,9)] for g in ULTIMATES},
              ULTIMATES,NEW/'source/effects_reference.png',cell=(224,210))
    (NEW/'source/manifest.json').write_text(json.dumps(batches(),indent=2),encoding='utf8')


def main():
    if '--references' in sys.argv:
        references();return
    if '--qa' in sys.argv:
        audit_sheets();return
    pygame.init();pygame.display.set_mode((1,1))
    colors=json.loads((OLD/'palette.json').read_text(encoding='utf8'))
    palette=Image.new('P',(1,1));palette.putpalette(colors)
    prepared={};selections={}
    for batch,groups in batches().items():
        rows=split(Image.open(NEW/'source'/f'{batch}_inbetweens.png').convert('RGBA'),len(groups))
        idle=Image.open(OLD/'idle_1.png').convert('RGBA')
        height=idle.getbbox()[3]-idle.getbbox()[1]
        b=rows[0][0].getbbox();scale=height/(b[3]-b[1])
        for group,row in zip(groups,rows):
            if group=='idle' and batch!='base':continue
            originals=[Image.open(OLD/f'{group}_{i}.png').convert('RGBA') for i in range(1,9)]
            additions,indices=intermediates(originals,row,rows[0],palette,scale,group)
            for column,candidate in WEAPON_POSES.get(group,{}).items():
                left,right=PAIRS[column]
                additions[column]=refined_weapon_pose(row[candidate],originals[left],originals[right],palette,scale)
                indices[column]=candidate
            frames=[]
            for i,(left,right) in enumerate(PAIRS):frames.extend((originals[left],additions[i],originals[right]))
            prepared[group]=frames
            selections[group]={'batch':batch,'candidates':indices}
            atlas=Image.new('RGB',(12*160,160),'#172923')
            for i,im in enumerate(frames,1):
                save_png(im,NEW/f'{group}_{i}.png')
                thumb=im.resize((160,130),Image.Resampling.NEAREST)
                atlas.paste(thumb,((i-1)*160,20),thumb)
            ImageDraw.Draw(atlas).text((5,3),group,fill='#e5c68d')
            atlas.save(ROOT/'docs'/f'player_{group}_twelve_frames.png')
    effects=split(Image.open(NEW/'source/effects_inbetweens.png').convert('RGBA'),3)
    fx_atlas=Image.new('RGB',(12*160,3*175),'#172923')
    for row,(group,additions) in enumerate(zip(ULTIMATES,effects)):
        originals=[Image.open(OLD/f'{group}_effect_{i}.png').convert('RGBA') for i in range(1,9)]
        frames=[]
        for i,(left,right) in enumerate(PAIRS):
            a,b=originals[left],originals[right]
            sizes=[max(im.getbbox()[2]-im.getbbox()[0],im.getbbox()[3]-im.getbbox()[1]) for im in (a,b)]
            crop=additions[i].crop(additions[i].getbbox())
            factor=sum(sizes)/2/max(crop.size)
            crop=crop.resize((max(1,round(crop.width*factor)),max(1,round(crop.height*factor))),Image.Resampling.LANCZOS)
            im=Image.new('RGBA',(384,320));im.alpha_composite(crop,(192-crop.width//2,160-crop.height//2))
            frames.extend((a,im,b))
        for i,im in enumerate(frames,1):
            save_png(im,NEW/f'{group}_effect_{i}.png')
            thumb=im.copy();thumb.thumbnail((155,145))
            fx_atlas.paste(thumb,((i-1)*160,row*175+24),thumb)
        ImageDraw.Draw(fx_atlas).text((5,row*175+2),group,fill='#e5c68d')
    fx_atlas.save(ROOT/'docs/player_ultimate_effects_twelve_frames.png')
    overview=Image.new('RGB',(4*320,7*190),'#172923')
    for i,(group,frames) in enumerate(prepared.items()):
        x,y=(i%4)*320,(i//4)*190
        ImageDraw.Draw(overview).text((x+4,y+2),group,fill='#e5c68d')
        thumb=frames[6].copy();thumb.thumbnail((320,165))
        overview.paste(thumb,(x,y+23),thumb)
    overview.save(ROOT/'docs/player_twelve_frames_overview.png')
    (NEW/'selection.json').write_text(json.dumps(selections,indent=2),encoding='utf8')
    (NEW/'palette.json').write_text(json.dumps(colors),encoding='utf8')
    (NEW/'manifest.json').write_text(json.dumps(list(prepared),indent=2),encoding='utf8')
    audit_sheets()
    pygame.quit()
    print('27 interações, 324 sprites de corpo e 36 efeitos de ultimate preparados.')


def audit_sheets():
    groups=json.loads((NEW/'manifest.json').read_text(encoding='utf8'))
    for part in range(3):
        atlas=Image.new('RGB',(4*240,9*180),'#172923')
        for row,group in enumerate(groups[part*9:(part+1)*9]):
            ImageDraw.Draw(atlas).text((4,row*180+3),group,fill='#e5c68d')
            for column,index in enumerate((2,5,8,11)):
                im=Image.open(NEW/f'{group}_{index}.png').convert('RGBA')
                im=im.crop((40,80,320,260)).resize((240,154),Image.Resampling.NEAREST)
                atlas.paste(im,(column*240,row*180+24),im)
        atlas.save(ROOT/'docs'/f'player_new_intermediates_{part+1}.png')


if __name__=='__main__':main()
