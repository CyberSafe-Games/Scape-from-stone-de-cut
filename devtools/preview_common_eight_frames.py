"""Renderiza todos os encontros comuns com o fluxo real, sem gravar saves."""
import os
import sys
import math
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pygame
from PIL import Image
from src.core.asset_manager import AssetManager
from src.scenes.battle_scene import BattleScene
from src.systems.enemy_factory import create_road_enemy, choose_next_action
from src.systems.normal_enemy_catalog import BIOME_ENEMIES


def main():
    pygame.init()
    pygame.display.set_mode((1,1))
    assets = AssetManager()
    window = SimpleNamespace(get_virtual_mouse_pos=lambda: (-1,-1), draw_fullscreen_button=lambda *_: None)
    posters, sequence = [], []
    clock = 0
    for level, names in BIOME_ENEMIES.items():
        for name in names:
            with patch('src.systems.enemy_factory.random.choice', return_value=name):
                enemy = create_road_enemy(level)
            scene = BattleScene(None, window, assets, selected_level=level)
            scene.engine.level = level
            scene.engine.enemy = enemy
            scene.engine.player.hp = scene.engine.player.max_hp = 999
            choose_next_action(enemy)
            canvas = pygame.Surface((1280,720))

            def capture(duration, poster=False):
                nonlocal clock
                for i in range(math.ceil(duration/80)+1):
                    clock += 80
                    with patch('pygame.time.get_ticks', return_value=clock):
                        scene.update(80)
                        scene.draw(canvas)
                    im = Image.frombytes('RGB', canvas.get_size(), pygame.image.tobytes(canvas,'RGB'))
                    sequence.append(im.resize((640,360), Image.Resampling.LANCZOS))
                    if poster and i == round(duration*.60/80):
                        posters.append(im.resize((480,270), Image.Resampling.LANCZOS))
            capture(1500)
            scene.entity_view.trigger_flash('enemy')
            capture(300)
            for index, action in enumerate(enemy.actions):
                scene.engine.state = 'player_turn'
                enemy.reset_energy()
                enemy.hp = max(1, enemy.max_hp-15)
                scene.engine.end_turn()
                enemy.set_intent(action.action_type, action.value, action)
                scene.engine.enemy_actions_remaining = 1
                scene.engine.enemy_turn()
                view = scene.entity_view
                duration = view.enemy_attack_duration if action.action_type == 'attack' else view.enemy_action_duration
                capture(duration, poster=index==0)
    atlas = Image.new('RGB',(480*3,270*5),'#10231e')
    for i,im in enumerate(posters): atlas.paste(im,((i%3)*480,(i//3)*270))
    atlas.save(ROOT/'docs/common_enemies_in_battle.png')
    palette = atlas.quantize(colors=192)
    frames = [im.quantize(palette=palette, dither=Image.Dither.NONE) for im in sequence]
    frames[0].save(ROOT/'docs/common_enemies_eight_frames.gif', save_all=True, append_images=frames[1:], duration=80, loop=0, optimize=True)
    pygame.quit()
    print('13 encontros e todas as ações renderizados sem saves.')


if __name__ == '__main__': main()
