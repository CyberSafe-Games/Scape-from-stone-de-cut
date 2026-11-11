"""Renderiza intenções e tooltips na cena real sem acessar saves."""
import os
import sys
from pathlib import Path
from types import SimpleNamespace
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pygame
from PIL import Image
from src.core.asset_manager import AssetManager
from src.scenes.battle_scene import BattleScene
from src.systems.enemy_factory import create_point_enemy, create_road_enemy, choose_next_action


def main():
    pygame.init(); pygame.display.set_mode((1, 1))
    assets = AssetManager()
    mouse = [-1, -1]
    window = SimpleNamespace(get_virtual_mouse_pos=lambda: tuple(mouse), draw_fullscreen_button=lambda *_: None)
    posters = []
    for label, level, road, hover in (('duas_acoes', 4, False, None), ('ultimate', 4, False, 1),
                                      ('recuperacao', 7, False, 0), ('inimigo_comum', 4, True, 0)):
        scene = BattleScene(None, window, assets)
        scene.engine.level = level
        boss = create_road_enemy(level) if road else create_point_enemy(level)
        scene.engine.enemy = boss
        if not road: boss.action_counter = 6
        choose_next_action(boss)
        if level == 4 and not road:
            first = boss.actions[0]
            boss.set_intent(first.action_type, first.value, first)
        if level == 7:
            buff = next(a for a in boss.actions if a.action_type == 'buff')
            boss.action_plan = [buff, boss.actions[0]]
            boss.set_intent(buff.action_type, buff.value, buff)
        canvas = pygame.Surface((1280, 720))
        mouse[:] = [-1, -1]
        scene.draw(canvas)
        if hover is not None:
            mouse[:] = scene.intent_view.entries[hover][0].center
            scene.draw(canvas)
        pygame.image.save(canvas, str(ROOT/'docs'/f'intencoes_{label}.png'))
        posters.append(Image.frombytes('RGB', canvas.get_size(), pygame.image.tobytes(canvas, 'RGB')).resize((896, 504)))
    atlas = Image.new('RGB', (1792, 1008))
    for i, im in enumerate(posters): atlas.paste(im, ((i % 2)*896, (i//2)*504))
    atlas.save(ROOT/'docs/intencoes_preview.png')
    pygame.quit()


if __name__ == '__main__': main()
