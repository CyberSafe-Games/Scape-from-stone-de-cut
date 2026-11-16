"""Recorta as cartas de Zanzara e monta a baforada com o corpo aprovado."""
import argparse
import json
import sys
from pathlib import Path
from zipfile import ZipFile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from devtools.prepare_boss_update import (
    import_cards, paint_card_text, refresh_player_stack_card_texts, rules_text, save_frames,
)
from src.systems.animation_inbetweens import ORIGINAL_TWELVE_INDICES
from src.systems.enemy_factory import create_zanzara


def zanzara_cards(sheet, archive):
    folder = ROOT / 'assets/intent_art/zanzara'
    folder.mkdir(parents=True, exist_ok=True)
    boxes = {
        'atk1': (6, 2, 525, 712),
        'atk2': (535, 2, 1053, 712),
        'atk3': (6, 720, 525, 1460),
        'ultimate': (535, 720, 1053, 1460),
    }
    boss = create_zanzara()
    updated_rules = {
        'atk1': (boss.actions[0], 'Zanzara desfere um corte amplo com sua foice.'),
        'atk2': (boss.actions[1], 'Desaparece em chamas verdes, golpeia e retorna.'),
        'ultimate': (boss.special_action, 'Invoca o avatar espectral de Caronte e seu barco.'),
    }
    for name, box in boxes.items():
        path = folder / f'{name}.png'
        # Uma reexecução com o mesmo recorte nunca arquiva a própria versão atual.
        card = sheet.crop(box)
        if name in updated_rules:
            action, flavor = updated_rules[name]
            paint_card_text(card, rules_text(action) + '\n' + flavor, region=(.10, .65, .90, .94))
        if path.exists():
            with Image.open(path) as previous:
                changed = previous.size != card.size or previous.convert('RGB').tobytes() != card.tobytes()
            if changed:
                target = archive / path.relative_to(ROOT)
                if not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    path.replace(target)
        card.save(path, optimize=True)


def effect_cells(atlas):
    cells = []
    for i in range(8):
        x, y = i % 4, i // 4
        cell = atlas.crop((round(x*atlas.width/4), round(y*atlas.height/2),
                           round((x+1)*atlas.width/4), round((y+1)*atlas.height/2)))
        alpha = cell.getchannel('A').point(lambda value: 255 if value >= 100 else 0)
        cell = cell.crop(alpha.getbbox())
        rgb = cell.convert('RGB').quantize(colors=48).convert('RGB')
        rgb.putalpha(alpha.crop(alpha.getbbox()))
        cells.append(rgb)
    return cells


def poison_pose(base, effect=None, *, lean=0, crouch=0, reach=0, drift=0):
    frame = Image.new('RGBA', base.size)
    left, top, right, floor = base.getbbox()
    body = base.crop((left, top, right, floor))
    body = body.resize((body.width, body.height-crouch), Image.Resampling.NEAREST)
    for y in range(body.height):
        # O movimento parte do tronco e deixa os pés no pivô original.
        dx = round(lean * max(0, 1-y/(body.height*.72)))
        frame.alpha_composite(body.crop((0, y, body.width, y+1)), (left-dx, floor-body.height+y))
    if effect is not None:
        w = reach
        h = max(1, round(effect.height*w/effect.width))
        effect = effect.resize((w, h), Image.Resampling.NEAREST)
        mouth_x = left + round(body.width*.24) - round(lean*.59)
        mouth_y = floor - body.height + round(body.height*.31)
        frame.alpha_composite(effect, (mouth_x-w-drift, mouth_y-round(h*.38)))
    return frame


def goblin_poison(atlas, archive):
    root = ROOT / 'assets/bosses'
    eight = root / 'eight_frames/goblin_nerd'
    twelve = root / 'twelve_frames/goblin_nerd'
    idle = [Image.open(eight/f'idle_{i}.png').convert('RGBA') for i in range(1, 9)]
    fx = effect_cells(atlas)
    # Os oito desenhos-chave continuam nos mesmos índices do kit de doze poses.
    poses = [
        poison_pose(idle[0], lean=-3, crouch=2),
        poison_pose(idle[1], fx[0], lean=1, crouch=4, reach=19),
        poison_pose(idle[2], fx[1], lean=5, crouch=6, reach=42),
        poison_pose(idle[3], fx[2], lean=9, crouch=7, reach=79),
        poison_pose(idle[4], fx[4], lean=11, crouch=8, reach=110),
        poison_pose(idle[5], fx[5], lean=7, crouch=5, reach=92, drift=12),
        poison_pose(idle[6], fx[6], lean=3, crouch=3, reach=57, drift=18),
        idle[0],
    ]
    added = [
        poison_pose(idle[0], lean=-1, crouch=3),
        poison_pose(idle[2], fx[2], lean=7, crouch=7, reach=56),
        poison_pose(idle[4], fx[3], lean=10, crouch=7, reach=101, drift=8),
        poison_pose(idle[6], fx[7], lean=1, crouch=2, reach=36, drift=11),
    ]
    key_frames, intervals = iter(poses), iter(added)
    expanded = [next(key_frames) if i in ORIGINAL_TWELVE_INDICES else next(intervals) for i in range(12)]
    save_frames(eight, 'atk3', poses, archive)
    save_frames(twelve, 'atk3', expanded, archive)
    colors = {pixel[:3] for pose in expanded for pixel in pose.getdata() if pixel[3] > 210}
    for folder in (eight, twelve):
        metadata = folder / 'palette.json'
        palette = {tuple(color) for color in json.loads(metadata.read_text(encoding='utf-8'))}
        metadata.write_text(json.dumps(sorted(palette | colors), indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cards_zip', type=Path)
    parser.add_argument('zanzara_sheet', type=Path)
    parser.add_argument('poison_atlas', type=Path)
    args = parser.parse_args()
    archive = ROOT / '_arquivos_antigos_para_deletar'
    with ZipFile(args.cards_zip) as cards:
        import_cards(cards)
    zanzara_cards(Image.open(args.zanzara_sheet).convert('RGB'), archive)
    refresh_player_stack_card_texts()
    goblin_poison(Image.open(args.poison_atlas).convert('RGBA'), archive)


if __name__ == '__main__':
    main()
