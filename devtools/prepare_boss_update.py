"""Prepara os PNGs finais dos dois pacotes de atualização dos chefes."""
import argparse
import json
import sys
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from devtools.polish_boss_sequences import boot_anchor, grade, pack, palette_for
from src.models.action import action_status_effects
from src.systems.card_catalog import CARD_BY_NAME
from src.systems.boss_animation_kits import KITS
from src.systems.enemy_factory import create_alvaro_tex, create_point_enemy


SPRITES = {
    'alvaro_tex_phase1': ('alvaro e tex/alvaro e tex', {
        'idle': 'idle', 'dano': 'dano', 'atk1': 'atk1', 'atk2': 'atk2',
        'atk3': 'atk3', 'atk4': 'atk4', 'transition': 'morte',
    }),
    'alvaro_tex_phase2': ('tex', {
        'idle': 'idle', 'dano': 'dano', 'atk1': 'atk1', 'atk2': 'atk2',
        'atk3': 'atk3', 'atk4': 'atk4',
    }),
    'goblin_nerd': ('goblin nerd', {
        'idle': 'idle', 'dano': 'dano', 'atk1': 'atk1', 'atk2': 'atk4',
        'healer2': 'atk3', 'ultimate': 'atk4',
    }),
    'gordofera': ('gordofera', {
        'idle': 'idle', 'dano': 'dano', 'atk1': 'atk1', 'atk2': 'atk2',
        'atk3': 'atk3', 'ultimate': 'atk4',
    }),
}
IDLE_HEIGHTS = {
    'alvaro_tex_phase1': 188, 'alvaro_tex_phase2': 100,
    'goblin_nerd': 126, 'gordofera': 164,
}

# Ordem da leitura: superior esquerda, superior direita, inferior esquerda, inferior direita.
CARDS = {
    'cards Alvaro tex.png': ('alvaro_tex_phase1', ('atk1', 'atk2', 'healer2', 'ultimate')),
    'cards tex.png': ('alvaro_tex_phase2', ('atk4', 'atk2', 'atk1', 'ultimate')),
    'cards goblin nerd.png': ('goblin_nerd', ('atk1', 'atk3', 'atk2', 'ultimate')),
    'card goblin nerd.png': ('goblin_nerd', ('healer2',)),
    'cards Gordofera.png': ('gordofera', ('atk1', 'atk2', 'atk3', 'ultimate')),
    'cards Corpo Seco.png': ('corpo_seco', ('atk1', 'def', 'atk3', 'ultimate')),
    'cards carrasco da vigilia.png': ('carrasco_da_vigilia', ('healer2', 'atk1', 'atk2', 'ultimate')),
}


def clean(im, *, gray_matte=False, projectile=False):
    """Remove fundos impressos e projéteis que já são desenhados em separado."""
    import pygame

    pixels = np.array(im.convert('RGBA'))
    rgb = pixels[:, :, :3].astype(int)
    chroma = np.ptp(rgb, axis=2)
    white = (rgb.min(axis=2) >= 212) & (chroma < 23)
    if gray_matte:
        white |= (chroma < 30) & (rgb[:, :, 2] >= rgb[:, :, 0])
    pixels[white | (pixels[:, :, 3] < 42)] = 0
    sprite = pygame.image.frombytes(pixels.tobytes(), im.size, 'RGBA')
    parts = pygame.mask.from_surface(sprite, 68).connected_components(8)
    body = max(parts, key=lambda part: part.count())
    keep = pygame.mask.Mask(im.size)
    bounds = body.get_bounding_rects()[0]
    for part in parts:
        rect = part.get_bounding_rects()[0]
        if part is body or (not projectile and bounds.inflate(56, 44).colliderect(rect)):
            keep.draw(part, (0, 0))
    kept = pygame.surfarray.array3d(keep.to_surface(setcolor='white', unsetcolor='black'))[:, :, 0].T
    pixels[kept == 0] = 0
    return Image.fromarray(pixels)


def intermediate(left, right, palette):
    """Suaviza a passagem sem desenhar uma segunda silhueta semitransparente."""
    a, b = np.array(left), np.array(right)
    shared = (a[:, :, 3] > 90) & (b[:, :, 3] > 90)
    similar = np.max(np.abs(a[:, :, :3].astype(int) - b[:, :, :3]), axis=2) < 90
    blend = shared & similar
    a[blend, :3] = np.rint(a[blend, :3] * .55 + b[blend, :3] * .45).astype(np.uint8)
    return grade(Image.fromarray(a), palette)


def save_frames(folder, group, frames, archive):
    for index, frame in enumerate(frames, 1):
        path = folder / f'{group}_{index}.png'
        if archive and path.is_file():
            target = archive / path.relative_to(ROOT)
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                path.replace(target)
        frame.save(path, optimize=True)


def import_sprites(z, archive):
    for slug, (prefix, groups) in SPRITES.items():
        eight = ROOT / 'assets/bosses/eight_frames' / slug
        twelve = ROOT / 'assets/bosses/twelve_frames' / slug
        idle_height = IDLE_HEIGHTS[slug]
        rows = {}
        for group, source in groups.items():
            rows[group] = [
                clean(Image.open(z.open(f'SpritesAtualizadaBoss/{prefix}/{source}_{i}.png')),
                      gray_matte=slug == 'alvaro_tex_phase2' and group == 'dano',
                      projectile=(slug, group) in {
                          ('alvaro_tex_phase1', 'atk2'), ('alvaro_tex_phase2', 'atk4'),
                          ('goblin_nerd', 'atk1'), ('goblin_nerd', 'atk2'),
                          ('goblin_nerd', 'ultimate'),
                      })
                for i in range(1, 9)
            ]
        palette = palette_for([image for row in rows.values() for image in row], grey=True)
        poses = {}
        idle = rows['idle'][0]
        baseline = idle_height / idle.crop(idle.getbbox()).height
        for group, row in rows.items():
            # Pacotes têm canvases diferentes para ataque e repouso.
            first = row[0]
            first_height = first.crop(first.getbbox()).height
            scale = min(idle_height / first_height, 1.25 * baseline)
            if group == 'transition':
                scale = baseline
            poses[group] = []
            for image in row:
                anchor, floor = boot_anchor(image)
                poses[group].append(pack(grade(image, palette, group == 'dano'), scale, anchor, floor))
        for group, row in poses.items():
            if group != 'transition':
                row[-1] = poses['idle'][0]
            save_frames(eight, group, row, archive)
            if group in ('idle', 'dano'):
                continue
            expanded = []
            for index, frame in enumerate(row):
                expanded.append(frame)
                if index % 2 == 0:
                    expanded.append(intermediate(frame, row[index+1], palette))
            save_frames(twelve, group, expanded, archive)
        # As ações sem substituto também fecham na nova pose de repouso.
        for folder, count in ((eight, 8), (twelve, 12)):
            manifest = json.loads((folder.parent / 'manifest.json').read_text(encoding='utf-8'))
            for group in set(manifest[slug]) - set(poses):
                path = folder / f'{group}_{count}.png'
                if not path.is_file():
                    continue
                if archive:
                    target = archive / path.relative_to(ROOT)
                    if not target.exists():
                        target.parent.mkdir(parents=True, exist_ok=True)
                        path.replace(target)
                poses['idle'][0].save(path, optimize=True)
            palette_path = folder / 'palette.json'
            existing = json.loads(palette_path.read_text(encoding='utf-8'))
            colors = palette.getpalette()
            combined = sorted({tuple(color) for color in existing} |
                              {tuple(colors[i:i+3]) for i in range(0, len(colors), 3)})
            palette_path.write_text(json.dumps(combined, indent=2), encoding='utf-8')


def rules_text(action):
    if action.action_type == 'attack':
        lines = [f'Causa {action.damage} de dano.']
    elif action.action_type == 'defend':
        lines = [f'Recebe {action.defense} de Escudo por 2 turnos.']
    else:
        lines = [f'Recupera até {action.defense} de vida.']
    if action.self_heal:
        lines.append(f'Recupera até {action.self_heal} de vida.')
    buff = action.self_attack_buff
    if action.effect and action.effect.attack_bonus:
        buff = (action.effect.duration, action.effect.attack_bonus)
    if buff:
        lines.append(f'+{buff[1]} de dano por {buff[0]} turnos, sem acumular.')
    for name, turns, potency in action_status_effects(action):
        if name == 'shock':
            lines.append(f'Choque ×{potency}: −{potency} energia no próximo turno.')
        elif name in ('bleed', 'poison'):
            label = {'bleed': 'Sangramento', 'poison': 'Veneno'}[name]
            noun = 'stack' if potency == 1 else 'stacks'
            lines.append(f'{potency} {noun} de {label} por {turns} turnos.')
        elif name == 'vulnerable':
            lines.append(f'Aplica Vulnerável por {turns} turnos (+{potency}% de dano recebido).')
    return '\n'.join(lines)


def paint_rules(card, action):
    paint_card_text(card, rules_text(action))


def paint_card_text(card, text, region=(.09, .65, .91, .945), background=(15, 13, 14)):
    """Atualiza o texto impresso sem alterar a moldura, o título ou a arte."""
    w, h = card.size
    draw = ImageDraw.Draw(card)
    left, top, right, bottom = region
    draw.rounded_rectangle((round(left*w), round(top*h), round(right*w), round(bottom*h)),
                           radius=round(.025*w), fill=background)
    max_width = w*(right-left-.05)
    for size in range(round(w*.073), 7, -1):
        font = ImageFont.truetype(str(ROOT/'assets/fonts/IgarapePixel-Regular.ttf'), size)
        lines = []
        for paragraph in text.splitlines():
            line = ''
            for word in paragraph.split():
                candidate = f'{line} {word}' if line else word
                if line and font.getlength(candidate) > max_width:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
        if len(lines)*size*1.2 <= h*(bottom-top-.035):
            break
    height = font.size * 1.2
    top = ((top+bottom)/2-.0025)*h - height * (len(lines) - 1) / 2
    for index, line in enumerate(lines):
        draw.text((w/2, top + index*height), line, fill=(244, 220, 166),
                  font=font, anchor='mm')


def refresh_player_stack_card_texts():
    for filename, name in (
        ('adaga_sangrenta', 'Adaga Sangrenta'),
        ('pocao_venenosa', 'Poção Venenosa'),
        ('zarabatana_venenosa', 'Zarabatana Venenosa'),
    ):
        path = ROOT / 'assets/cards' / f'{filename}.png'
        card = Image.open(path).convert('RGBA')
        paint_card_text(card, CARD_BY_NAME[name].description, region=(.065, .65, .935, .94),
                        background=card.getpixel((20, 287)))
        card.save(path, optimize=True)


def card_actions():
    bosses = [create_point_enemy(level) for level in (2, 3, 4, 5, 6)]
    bosses.append(create_alvaro_tex(phase=2))
    return {
        KITS[boss.name.lower()][0]: {
            **{action.visual_effect: action for action in boss.actions},
            'ultimate': boss.special_action,
        }
        for boss in bosses
    }


def import_cards(z):
    actions = card_actions()
    for name, (slug, groups) in CARDS.items():
        sheet = Image.open(z.open('CardsBosses/' + name)).convert('RGB')
        columns = 1 if len(groups) == 1 else 2
        w, h = sheet.width / columns, sheet.height / columns
        folder = ROOT / 'assets/intent_art' / slug
        folder.mkdir(parents=True, exist_ok=True)
        for index, group in enumerate(groups):
            x, y = index % columns, index // columns
            crop = sheet.crop((round(x*w), round(y*h), round((x+1)*w), round((y+1)*h)))
            # Retira só o fundo da folha que sobra ao redor do cartão.
            border = crop.convert('L').point(lambda value: 255 if value >= 83 else 0).getbbox()
            if border:
                crop = crop.crop(border)
            paint_rules(crop, actions[slug][group])
            crop.save(folder / f'{group}.png', optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sprites_zip', type=Path)
    parser.add_argument('cards_zip', type=Path)
    parser.add_argument('--archive', action='store_true', help='Arquiva apenas os PNGs substituídos.')
    args = parser.parse_args()
    archive = ROOT / '_arquivos_antigos_para_deletar' if args.archive else None
    with ZipFile(args.sprites_zip) as sprites, ZipFile(args.cards_zip) as cards:
        import_sprites(sprites, archive)
        import_cards(cards)


if __name__ == '__main__':
    main()
