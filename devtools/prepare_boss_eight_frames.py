"""Intercala quatro desenhos novos com as quatro poses originais de cada kit.

As folhas intermediate.png são geradas com a ferramenta de imagem integrada.
Nunca reamostra uma sequência já expandida: usa as referências originais do loader.
"""
import os
import sys
import json
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
import pygame
from PIL import Image, ImageDraw
from src.core.asset_manager import AssetManager


def silhouette(image, particles=True):
    arr = np.array(image.convert('RGBA'))
    arr[arr[:,:,3] < 32] = 0
    im = Image.fromarray(arr)
    surf = pygame.image.frombytes(im.tobytes(), im.size, 'RGBA')
    parts = pygame.mask.from_surface(surf,40).connected_components(4)
    main = max(parts,key=lambda p:p.count())
    body = main.get_bounding_rects()[0]
    keep = pygame.mask.Mask(im.size)
    for p in parts:
        b = p.get_bounding_rects()[0]
        if not particles and p is not main:
            continue
        if (p is not main and p.count()<main.count()*.20
                and (b.left<3 or b.right>im.width-3 or b.top<2 or b.bottom>im.height-2)):
            continue
        if body.inflate(38,30).colliderect(b) and p.count() > 10:
            keep.draw(p,(0,0))
    mask = pygame.surfarray.array3d(keep.to_surface(setcolor='white',unsetcolor='black'))[:,:,0].T
    arr[mask == 0] = 0
    return Image.fromarray(arr)


def canonical(image, height=None, particles=True):
    """Pivô dos pés e canvas comum; não altera pixels das poses chave sem necessidade."""
    im = silhouette(image,particles)
    b = im.getbbox()
    im = im.crop(b)
    if height:
        scale = height/im.height
        im = im.resize((max(1,round(im.width*scale)),height),Image.Resampling.NEAREST)
    # Floor centering avoids sideways drift when a dagger, aura or gun extends out.
    a = np.array(im)[:,:,3]
    yy,xx = np.where(a[-min(6,im.height):] > 40)
    ax = float(np.median(xx)) if len(xx) else im.width/2
    canvas = Image.new('RGBA',(448,320))
    canvas.alpha_composite(im,(round(224-ax),318-im.height))
    return canvas


def match_palette(image, reference):
    """Match the new drawing's brightness to the original, avoiding alternating flashes."""
    a = np.array(image).astype(float)
    b = np.array(reference).astype(float)
    source = a[:,:,3] > 180
    target = b[:,:,3] > 180
    gain = np.clip(b[:,:,:3][target].mean(0)/np.maximum(1,a[:,:,:3][source].mean(0)),.5,1.4)
    a[:,:,:3] *= gain
    return Image.fromarray(np.clip(a,0,255).astype('uint8'))


def main():
    if (ROOT/'assets/bosses/eight_frames/guardiao_da_pedra/sequence_v2.png').exists():
        from devtools.polish_boss_sequences import main as polish
        return polish()
    pygame.init();pygame.display.set_mode((1,1))
    assets = AssetManager()
    meta = json.loads((ROOT/'docs/boss_eight_frames_sources.json').read_text(encoding='utf8'))
    manifest_path = ROOT/'assets/bosses/eight_frames/manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf8')) if manifest_path.exists() else {}
    for slug,spec in meta.items():
        folder = ROOT/'assets/bosses/eight_frames'/slug
        sheet = Image.open(folder/'intermediate.png').convert('RGBA')
        original_groups = getattr(assets,'_boss_original_groups',{}).get(spec['name'],{})
        original_ultimates = getattr(assets,'_boss_original_ultimates',{}).get(spec['name'])
        preview = Image.new('RGB',(8*224,7*175),'#14221f')
        for row,group in enumerate(spec['groups']):
            frames = ((original_ultimates or assets.get_boss_ultimate_sprites(spec['name'])) if group=='ultimate'
                      else original_groups.get(group) or assets.get_enemy_sprite_group(spec['name'],group))
            originals = [Image.frombytes('RGBA',f.get_size(),pygame.image.tobytes(f,'RGBA')) for f in frames[:4]]
            heights = [silhouette(im).getbbox()[3]-silhouette(im).getbbox()[1] for im in originals]
            ratio = 127/heights[0] if slug=='goblin_nerd' and group not in ('idle','dano','ultimate') else 1
            results = []
            for col in range(4):
                original = canonical(originals[col],round(heights[col]*ratio) if ratio!=1 else None,
                                     particles=slug!='goblin_nerd')
                box = (round(col*sheet.width/4),round(row*sheet.height/7),
                       round((col+1)*sheet.width/4),round((row+1)*sheet.height/7))
                addition = sheet.crop(box)
                target = round((heights[col]+heights[(col+1)%4])*ratio/2)
                new = match_palette(canonical(addition,target),original)
                results.extend((original,new))
            for i,frame in enumerate(results,1):
                frame.save(folder/f'{group}_{i}.png')
                thumb = frame.resize((224,160),Image.Resampling.NEAREST)
                preview.paste(thumb,((i-1)*224,row*175+15),thumb)
            ImageDraw.Draw(preview).text((5,row*175),group,fill='white')
        preview.save(ROOT/'docs'/f'{slug}_eight_frames.png')
        manifest[slug] = spec['groups']
    duo = Image.open(ROOT/'assets/bosses/eight_frames/alvaro_tex_intermediate.png').convert('RGBA')
    for phase in (1,2):
        slug = f'alvaro_tex_phase{phase}'
        folder = ROOT/'assets/bosses/eight_frames'/slug
        folder.mkdir(exist_ok=True)
        for gr,group in enumerate(('idle','dano')):
            row = (phase-1)*2+gr
            originals = [Image.open(ROOT/f'assets/bosses/alvaro_tex/phase{phase}/{group}_{i}.png').convert('RGBA') for i in range(1,5)]
            heights = [im.getbbox()[3]-im.getbbox()[1] for im in originals]
            for col in range(4):
                box = (round(col*duo.width/4),round(row*duo.height/4),round((col+1)*duo.width/4),round((row+1)*duo.height/4))
                target = round((heights[col]+heights[(col+1)%4])/2)
                added = match_palette(canonical(duo.crop(box),target).crop((0,72,448,322)),originals[col])
                originals[col].save(folder/f'{group}_{2*col+1}.png')
                added.save(folder/f'{group}_{2*col+2}.png')
        manifest[slug] = ['idle','dano']
    manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf8')
    pygame.quit()


if __name__=='__main__':
    main()
