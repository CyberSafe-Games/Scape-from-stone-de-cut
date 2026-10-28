"""Exporta os especiais reais dos quatro chefes e o cenário das Ruínas."""
import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pygame
from PIL import Image
from src.core.asset_manager import AssetManager
from src.scenes.battle_scene import BattleScene
from src.systems.enemy_factory import create_point_enemy
from src.systems.boss_ultimate_animations import BOSS_ULTIMATE_ANIMATIONS


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    assets = AssetManager()
    window = SimpleNamespace(get_virtual_mouse_pos=lambda: (-1, -1), draw_fullscreen_button=lambda *args: None)
    sequence, posters = [], []
    for level in (1, 3, 5, 6):
        scene = BattleScene(None, window, assets, selected_level=level)
        scene.engine.enemy = create_point_enemy(level)
        boss = scene.engine.enemy
        spec = BOSS_ULTIMATE_ANIMATIONS[boss.name.lower()]
        # Imortal only for this preview; no save is read or written.
        scene.engine.player.hp = scene.engine.player.max_hp = 220
        scene.engine.end_turn()
        boss.set_intent('attack', boss.special_action.value, boss.special_action)
        boss.action_counter = 7
        scene.engine.enemy_turn()
        canvas = pygame.Surface((1280, 720))
        poster_at = round(spec.duration*(.60 if spec.mode in ('bear', 'plasma') else spec.impact+.035)/100)
        for frame in range(round(spec.duration/100)+1):
            if frame:
                scene.update(100)
            scene.draw(canvas)
            image = Image.frombytes('RGB', canvas.get_size(), pygame.image.tobytes(canvas, 'RGB'))
            sequence.append(image.resize((768, 432), Image.Resampling.LANCZOS))
            if frame == poster_at:
                pygame.image.save(canvas, str(ROOT/'docs'/f'boss_ultimate_{spec.asset_id}.png'))
                posters.append(image.resize((768, 432), Image.Resampling.LANCZOS))
        sequence.extend([sequence[-1]]*4)
    atlas = Image.new('RGB', (768*4, 432))
    for i, poster in enumerate(posters): atlas.paste(poster, (i*768, 0))
    palette = atlas.quantize(colors=192)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in sequence]
    indexed[0].save(ROOT/'docs'/'bosses_ultimates_em_acao.gif', save_all=True,
                    append_images=indexed[1:], duration=100, loop=0, optimize=True, disposal=1)
    print('Quatro especiais renderizados; Ruínas aplicadas ao Goblin Nerd.')
    pygame.quit()


if __name__ == '__main__':
    main()
