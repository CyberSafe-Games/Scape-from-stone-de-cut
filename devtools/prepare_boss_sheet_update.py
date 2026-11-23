"""Importa BossesNovasSprites.zip em folhas RGBA 4×2 alinhadas.

Leia docs/bosses_spritesheets_oito.md. Os arquivos externos nunca são alterados.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import sys
from zipfile import ZipFile

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import pygame

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SIZE = (448, 320)
MAP = {
    'Boss1': ('guardiao_da_pedra', ('atk1', 'def', 'healer2', 'ultimate', 'dano', 'idle'), 156),
    'Boss5': ('corpo_seco', ('idle', 'dano', 'ultimate', 'atk1', 'healer2', 'atk3'), 132),
    'Boss6': ('carrasco_da_vigilia', ('idle', 'dano', 'atk1', 'atk2', 'healer2', 'ultimate'), 171),
}


def clean_background(image):
    """Remove o xadrez RGB, inclusive nos espaços fechados entre a magia."""
    a = np.array(image.convert('RGBA'))
    rgb = a[:, :, :3].astype(int)
    if image.mode != 'RGBA':
        neutral = (np.ptp(rgb, axis=2) < 10) & (rgb.mean(axis=2) > 28)
        a[neutral] = 0
        # Núcleos brancos cercados por cor pertencem à magia, não ao fundo.
        colored = (np.ptp(rgb, axis=2) > 80) & (rgb.max(axis=2) > 190)
        surrounded = np.array(Image.fromarray((colored * 255).astype('uint8')).filter(ImageFilter.BoxBlur(5))) > 170
        core = neutral & surrounded & (rgb.min(axis=2) > 240)
        a[core, :3] = rgb[core]
        a[core, 3] = 255
        # Auras semitransparentes foram achatadas sobre o xadrez no ZIP.
        # Retira a componente cinza do matte; cor da magia vira alfa real.
        body = ((rgb[:,:,0] > rgb[:,:,2]+7) & (rgb[:,:,0] > rgb[:,:,1]*.94)
                & (rgb.max(axis=2) < 185)) | (rgb.max(axis=2) < 65)
        solid = Image.fromarray((body*255).astype('uint8')).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))
        filled = solid.copy()
        ImageDraw.floodfill(filled, (0,0), 128, thresh=0)
        protected = np.array(filled) != 128
        r,g,b = rgb.transpose(2,0,1)
        magic = ((g > r*1.015) | (b > r*1.015) | ((r > g*1.4) & (r > 170)))
        matte = magic & (rgb.min(axis=2)>65) & ~protected & ~neutral
        chroma = np.ptp(rgb,axis=2)
        stripped = np.maximum(0,rgb-rgb.min(axis=2)[:,:,None])
        color = np.rint(stripped*255/np.maximum(1,chroma)[:,:,None]).clip(0,255).astype('uint8')
        a[matte,:3] = color[matte]
        a[matte,3] = np.minimum(255,chroma[matte]*2).astype('uint8')
    a[a[:, :, 3] < 55] = 0
    a[a[:, :, 3] == 0, :3] = 0
    return Image.fromarray(a)


def body_mask(image):
    a = np.array(image)
    r, g, b = a[:, :, :3].astype(int).transpose(2, 0, 1)
    # Azul/verde/púrpura das auras e vermelho luminoso não definem anatomia.
    return ((a[:, :, 3] > 100) & (r > b + 7) & (r > g * .94)
            & ~((r > 175) & (r > g * 1.8) & (g < 130)))


def body_bounds(image):
    mask = body_mask(image)
    yy, xx = np.where(mask)
    if len(xx) < 50:
        return image.getbbox()
    return int(xx.min()), int(yy.min()), int(xx.max()+1), int(yy.max()+1)


def row_cut(image):
    occupancy = (np.array(image)[:, :, 3] > 100).sum(axis=1)
    mid = image.height // 2
    candidates = np.arange(mid-70, mid+71)
    score = occupancy[candidates] * 100 + np.abs(candidates-mid)
    return int(candidates[np.argmin(score)])


def split_source(image, *, missing_fourth=False, uniform=False):
    """Mantém a ordem 4×2; identifica margens reais para não amputar pés/armas."""
    result, boxes = [], []
    y_cut = image.height // 2 if uniform else row_cut(image)
    for row, (top, bottom) in enumerate(((0, y_cut), (y_cut, image.height))):
        band = image.crop((0, top, image.width, bottom))
        pixels = np.array(band)
        body = body_mask(band)
        cuts = [0]
        for col in (1, 2, 3):
            expected = image.width * col // 4
            candidates = np.arange(max(cuts[-1]+1, expected-65), min(image.width, expected+66))
            score = body[:, candidates].sum(axis=0) * 50 + np.abs(candidates-expected)
            cuts.append(expected if uniform else int(candidates[np.argmin(score)]))
        cuts.append(image.width)
        mask = pygame.mask.from_surface(pygame.image.frombytes(band.tobytes(), band.size, 'RGBA'), 30)
        owned = [np.zeros_like(pixels) for _ in range(4)]
        for part in mask.connected_components(30):
            bounds = part.get_bounding_rects()[0]
            p = np.frombuffer(pygame.image.tobytes(part.to_surface(
                setcolor=(255,255,255,255), unsetcolor=(0,0,0,0)), 'RGBA'), dtype='uint8').reshape(pixels.shape)[:, :, 3] > 0
            # A terceira pose de Jan lança a magia pela quarta célula vazia.
            if missing_fourth and row == 0 and bounds.width > image.width*.35:
                owned[2][p] = pixels[p]
            elif bounds.width > image.width*.41:
                for col in range(4):
                    selection = p.copy()
                    selection[:, :cuts[col]] = False
                    selection[:, cuts[col+1]:] = False
                    owned[col][selection] = pixels[selection]
            else:
                col = min(3, max(0, int(np.searchsorted(cuts, bounds.centerx, side='right')-1)))
                owned[col][p] = pixels[p]
        for col, array in enumerate(owned):
            result.append(Image.fromarray(array))
            boxes.append([cuts[col], top, cuts[col+1], bottom])
    return result, boxes


def replacement_frame(source, neighbors, multiplier=1):
    art = clean_background(Image.open(source))
    bounds = body_bounds(art)
    heights = [body_bounds(n)[3]-body_bounds(n)[1] for n in neighbors]
    factor = float(np.mean(heights)) / (bounds[3]-bounds[1]) * multiplier
    return art.resize((round(art.width*factor), round(art.height*factor)), Image.Resampling.NEAREST)


def normalize(frame, scale):
    bounds = body_bounds(frame)
    mask = body_mask(frame)
    # O apoio é calculado pelos pixels opacos dos pés, e não por faíscas soltas.
    floor = bounds[3]
    yy, xx = np.where(mask & (np.indices(mask.shape)[0] >= floor-13))
    center = float((np.percentile(xx, 3) + np.percentile(xx, 97))/2) if len(xx) else (bounds[0]+bounds[2])/2
    crop_box = frame.getbbox()
    crop = frame.crop(crop_box)
    crop = crop.resize((max(1, round(crop.width*scale)), max(1, round(crop.height*scale))), Image.Resampling.NEAREST)
    canvas = Image.new('RGBA', SIZE)
    canvas.alpha_composite(crop, (round(224-(center-crop_box[0])*scale), round(318-(floor-crop_box[1])*scale)))
    canvas = canvas.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    # A limpeza de borda não altera os reflexos internos nem cria fundo branco.
    from src.ui.sprite_cleanup import remove_white_fringe
    surface = remove_white_fringe(pygame.image.frombytes(canvas.tobytes(), SIZE, 'RGBA'))
    canvas = Image.frombytes('RGBA', SIZE, pygame.image.tobytes(surface, 'RGBA'))
    a = np.array(canvas)
    a[-2:] = 0
    a[a[:, :, 3] == 0, :3] = 0
    return Image.fromarray(a)


def harmonize(rows, folder):
    """Paleta única por chefe; remove fragmentos castanhos sem relação com o corpo."""
    samples=[]
    for frames in rows.values():
        for i, frame in enumerate(frames):
            a=np.array(frame)
            surface=pygame.image.frombytes(frame.tobytes(), SIZE, 'RGBA')
            for part in pygame.mask.from_surface(surface,60).connected_components(1):
                if part.count() >= 100:
                    continue
                rect=part.get_bounding_rects()[0]
                region=a[rect.top:rect.bottom,rect.left:rect.right]
                rgb=region[:,:,:3]
                magic=(np.ptp(rgb.astype(int),axis=2)>105)&(rgb.max(axis=2)>170)&(region[:,:,3]>0)
                if not magic.any():
                    mask=np.frombuffer(pygame.image.tobytes(part.to_surface(
                        setcolor=(255,255,255,255),unsetcolor=(0,0,0,0)),'RGBA'),dtype='uint8').reshape(a.shape)[:,:,3]>0
                    a[mask]=0
            frames[i]=Image.fromarray(a)
            samples.append(a[:,:,:3][a[:,:,3]>100][::3])
    palette=Image.fromarray(np.concatenate(samples).reshape(1,-1,3)).quantize(colors=256)
    colors=palette.getpalette()
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'palette.json').write_text(json.dumps([colors[i:i+3] for i in range(0,768,3)]),encoding='utf-8')
    for frames in rows.values():
        for i,frame in enumerate(frames):
            alpha=frame.getchannel('A')
            rgb=frame.convert('RGB').quantize(palette=palette,dither=Image.Dither.NONE).convert('RGBA')
            rgb.putalpha(alpha)
            a=np.array(rgb)
            a[a[:,:,3]==0]=0
            frames[i]=Image.fromarray(a)
    return rows


def prepare(zip_path, repairs_path, output, preview, only_boss=None):
    pygame.init()
    pygame.display.set_mode((1, 1))
    repairs = json.loads(repairs_path.read_text(encoding='utf-8'))
    manifest = {'version': 1, 'grid': [4, 2], 'cell_size': list(SIZE), 'frame_count': 8,
                'direction': 'left', 'baseline': 318, 'source_sha256': hashlib.sha256(zip_path.read_bytes()).hexdigest(),
                'bosses': {}, 'repairs': {}, 'audit': {}}
    if only_boss and (output/'manifest.json').exists():
        previous=json.loads((output/'manifest.json').read_text(encoding='utf-8'))
        for section in ('bosses','repairs','audit'):
            manifest[section]=previous.get(section,{})
    with ZipFile(zip_path) as archive:
        for boss, (slug, actions, target_height) in MAP.items():
            if only_boss and boss != only_boss:
                continue
            rows = {}
            for sheet, action in enumerate(actions, 1):
                source_id = f'{boss}/Sprite{sheet}.png'
                source = Image.open(io.BytesIO(archive.read('BossesNovasSprites/'+source_id)))
                key = f'{boss}/Sprite{sheet}'
                repaired = repairs.get(key)
                if repaired and repaired.get('sheet'):
                    source = Image.open(repaired['sheet'])
                    manifest['repairs'][key] = {'sha256': hashlib.sha256(Path(repaired['sheet']).read_bytes()).hexdigest(),
                                              'frames': repaired['frames'], 'reason': repaired['reason']}
                frames, boxes = split_source(clean_background(source), missing_fourth=(boss == 'Boss5' and sheet == 4),
                                             uniform=bool(repaired and repaired.get('sheet')))
                if repaired and repaired.get('frame'):
                    index = repaired['index']-1
                    frames[index] = replacement_frame(repaired['frame'], [frames[max(0,index-1)], frames[min(7,index+1)]], repaired.get('multiplier',1))
                    manifest['repairs'][key] = {'sha256': hashlib.sha256(Path(repaired['frame']).read_bytes()).hexdigest(),
                                              'frames': [repaired['index']], 'reason': repaired['reason']}
                # A pose final é a referência de escala, sem usar a extensão da magia.
                box = body_bounds(frames[-1])
                height = box[3]-box[1]
                stance = .85 if (boss, sheet) == ('Boss5', 3) else .91 if (boss, sheet) == ('Boss5', 4) else 1
                scale = target_height*stance/height
                if boss == 'Boss5' and action == 'idle':
                    first=body_bounds(frames[0])
                    scale=target_height/(first[3]-first[1])
                if max((f.getbbox()[2]-f.getbbox()[0])*scale for f in frames) > 440:
                    raise ValueError(f'Efeito excede canvas: {source_id}')
                row = []
                for i, frame in enumerate(frames):
                    current_scale = scale
                    if action == 'idle' and boss != 'Boss5':
                        b = body_bounds(frame)
                        current_scale = target_height/(b[3]-b[1])
                    row.append(normalize(frame, current_scale))
                rows[action] = row
                manifest['audit'][key] = {'source': source_id, 'source_mode': source.mode,
                                         'logical_order': list(range(1,9)), 'source_boxes': boxes,
                                         'scale': round(scale,6), 'anatomy_checked_frames': list(range(1,9))}
            folder = output/slug
            folder.mkdir(parents=True, exist_ok=True)
            rows=harmonize(rows,folder)
            alignment=None
            if boss == 'Boss5':
                from devtools.stabilize_jan_pietro import stabilize_rows
                rows,alignment=stabilize_rows(rows)
            manifest['bosses'][slug] = {'source_folder': boss, 'groups': {}, 'body_height': target_height}
            if alignment:
                manifest['bosses'][slug]['alignment']=alignment
            poster = Image.new('RGB', (8*224,6*175), '#11231e')
            for r, (action, frames) in enumerate(rows.items()):
                sheet = Image.new('RGBA', (4*SIZE[0],2*SIZE[1]))
                for i, frame in enumerate(frames):
                    sheet.alpha_composite(frame, ((i%4)*SIZE[0], (i//4)*SIZE[1]))
                    small = frame.resize((224,160),Image.Resampling.NEAREST)
                    poster.paste(small, (i*224,r*175+15),small)
                ImageDraw.Draw(poster).text((4,r*175),action,fill='white')
                sheet.save(folder/f'{action}.png', optimize=True)
                manifest['bosses'][slug]['groups'][action] = f'{action}.png'
            preview.mkdir(parents=True, exist_ok=True)
            poster.save(preview/f'{slug}_audit.png')
            print(slug, '6 folhas / 48 quadros preparados', flush=True)
    output.mkdir(parents=True, exist_ok=True)
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
    pygame.quit()


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--boss',choices=tuple(MAP),default=None)
    parser.add_argument('--zip',type=Path,required=True)
    parser.add_argument('--repairs',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'assets/bosses/sheets_eight')
    parser.add_argument('--preview',type=Path,required=True)
    args=parser.parse_args()
    prepare(args.zip,args.repairs,args.output,args.preview,args.boss)
