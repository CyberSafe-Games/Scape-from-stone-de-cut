"""Renderiza as três ultimates no combate real sem acessar saves do jogador."""
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
from src.systems.enemy_factory import create_guardiao_da_pedra, choose_enemy_intent
from src.systems.ultimate_animations import ULTIMATE_ANIMATIONS


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    assets = AssetManager()
    window = SimpleNamespace(get_virtual_mouse_pos=lambda: (-1, -1),
                             draw_fullscreen_button=lambda *args: None)
    sequence = []
    sheet = pygame.Surface((1280, 720*3))
    for i, (name, spec) in enumerate(ULTIMATE_ANIMATIONS.items()):
        scene = BattleScene(None, window, assets, selected_level=1)
        scene.engine.enemy = create_guardiao_da_pedra()
        scene.engine.enemy.hp = scene.engine.enemy.max_hp = 220
        choose_enemy_intent(scene.engine.enemy)
        scene.engine.equip_ultimate(spec.ultimate_id)
        scene.engine.player.ultimate_charge = 20
        scene.engine.player.energy = 0
        scene.engine.activate_ultimate()
        canvas = pygame.Surface((1280, 720))
        last = None
        for frame in range(round(spec.duration/100)+5):
            if frame:
                scene.update(100)
            scene.draw(canvas)
            image = Image.frombytes('RGB', canvas.get_size(), pygame.image.tobytes(canvas, 'RGB'))
            sequence.append(image.resize((768, 432), Image.Resampling.LANCZOS))
            if frame == round(spec.duration*(.61 if i != 2 else .56)/100):
                pygame.image.save(canvas, str(ROOT/'docs'/f'animacao_{spec.ultimate_id}.png'))
                sheet.blit(canvas, (0, i*720))
            last = sequence[-1]
        sequence.extend([last]*3)
    palette_source = Image.new('RGB', (768*3, 432))
    for i, spec in enumerate(ULTIMATE_ANIMATIONS.values()):
        poster = Image.open(ROOT/'docs'/f'animacao_{spec.ultimate_id}.png')
        palette_source.paste(poster.resize((768, 432)), (i*768, 0))
    palette = palette_source.quantize(colors=192)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in sequence]
    indexed[0].save(ROOT/'docs'/'ultimates_em_acao.gif', save_all=True,
                    append_images=indexed[1:], duration=100, loop=0, optimize=True, disposal=1)
    pygame.image.save(sheet, str(ROOT/'docs'/'ultimates_animadas_batalha.png'))
    print('Prévia das três animações exportada.')
    pygame.quit()


if __name__ == '__main__':
    main()
