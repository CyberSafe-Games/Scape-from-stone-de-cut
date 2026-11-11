"""Prévia do kit completo no combate, sem acessar saves."""
import os
import sys
import math
from pathlib import Path
from types import SimpleNamespace
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pygame
from PIL import Image, ImageDraw
from src.core.asset_manager import AssetManager
from src.scenes.battle_scene import BattleScene
from src.systems.enemy_factory import create_gordofera, choose_next_action


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    assets = AssetManager()
    window = SimpleNamespace(get_virtual_mouse_pos=lambda: (-1, -1), draw_fullscreen_button=lambda *_: None)
    scene = BattleScene(None, window, assets, selected_level=4)
    scene.engine.level = 4
    scene.engine.enemy = boss = create_gordofera()
    scene.engine.player.hp = scene.engine.player.max_hp = 999
    choose_next_action(boss)
    sequence, posters = [], []
    canvas = pygame.Surface((1280, 720))

    def capture(duration, label, poster=False):
        for i in range(math.ceil(duration/70)+1):
            if i:
                scene.update(70)
            scene.draw(canvas)
            im = Image.frombytes('RGB', canvas.get_size(), pygame.image.tobytes(canvas, 'RGB'))
            small = im.resize((896, 504), Image.Resampling.LANCZOS)
            ImageDraw.Draw(small).text((15, 115), label, fill='#ffe29c', stroke_width=1, stroke_fill='#101010')
            sequence.append(small)
            if poster and i == round(duration*.58/70):
                posters.append(im.resize((768, 432), Image.Resampling.LANCZOS))

    capture(1400, 'Gordofera · repouso')
    scene.entity_view.trigger_flash('enemy')
    capture(400, 'Reação de dano')
    for action in boss.actions+[boss.special_action]:
        scene.engine.state = 'player_turn'
        scene.engine.end_turn()
        boss.set_intent(action.action_type, action.value, action)
        scene.engine.enemy_actions_remaining = 1
        scene.engine.enemy_turn()
        view = scene.entity_view
        duration = view.enemy_attack_duration if action.action_type == 'attack' else view.enemy_action_duration
        capture(duration, action.name, poster=True)
    atlas = Image.new('RGB', (768*2, 432*3), '#13241d')
    for i, im in enumerate(posters):
        atlas.paste(im, ((i % 2)*768, (i//2)*432))
    atlas.save(ROOT/'docs/gordofera_em_combate.png')
    palette = atlas.quantize(colors=224)
    frames = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in sequence]
    frames[0].save(ROOT/'docs/gordofera_em_acao.gif', save_all=True, append_images=frames[1:], duration=70, loop=0, optimize=True)
    pygame.image.save(canvas, str(ROOT/'docs/gordofera_batalha.png'))
    print('Prévia de Gordofera exportada.')
    pygame.quit()


if __name__ == '__main__':
    main()
