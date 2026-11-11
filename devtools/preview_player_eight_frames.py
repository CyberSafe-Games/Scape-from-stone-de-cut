"""Prévia em combate das 27 interações, sem ler ou alterar saves."""
import os
import sys
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
from src.systems.card_definitions import CARD_SPECS
from src.systems.ultimate_animations import ULTIMATE_ANIMATIONS


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    assets = AssetManager()
    window = SimpleNamespace(get_virtual_mouse_pos=lambda: (-1, -1), draw_fullscreen_button=lambda *_: None)
    sequence, posters, durations = [], [], []
    cases = [('idle', None), ('dano', None), ('vitoria', None)]
    cases += [(s[1], s) for s in CARD_SPECS]
    cases += [(name, None) for name in ULTIMATE_ANIMATIONS]
    for name, card in cases:
        scene = BattleScene(None, window, assets, selected_level=1)
        scene.engine.player.hp = scene.engine.player.max_hp = 500
        view = scene.entity_view
        duration = 1200
        if name == 'dano':
            view.trigger_flash('player')
            from src.config.layout import FLASH_DURATION
            duration = FLASH_DURATION
        elif name == 'vitoria':
            scene.engine.state = 'victory'
            scene._draw_victory = lambda surface: None
        elif name in ULTIMATE_ANIMATIONS:
            view.trigger_player_action(name)
            duration = view.player_action_duration
        elif card:
            if card[3] == 'attack':
                view.trigger_attack('player', name)
            else:
                view.trigger_player_action(name)
            duration = view.player_action_duration
        canvas = pygame.Surface((1280, 720))
        count = max(12, round(duration/80))
        for i in range(count+1):
            if i:
                scene.update(duration/count)
            scene.draw(canvas)
            im = Image.frombytes('RGB', canvas.get_size(), pygame.image.tobytes(canvas, 'RGB'))
            small = im.resize((768, 432), Image.Resampling.LANCZOS)
            ImageDraw.Draw(small).text((15, 105), name, fill='#ffe5a8', stroke_width=1, stroke_fill='#111111')
            sequence.append(small)
            durations.append(max(20, round(duration/count)))
            if i == count//2:
                player_x, _ = view.get_player_frame(scene.engine.state)
                left = max(0, min(835, round(player_x)-205))
                posters.append((name, im.crop((left, 230, left+445, 490)).resize((356, 208))))
    atlas = Image.new('RGB', (356*4, 228*7), '#16291f')
    for i, (name, im) in enumerate(posters):
        x, y = (i % 4)*356, (i//4)*228
        atlas.paste(im, (x, y+20))
        ImageDraw.Draw(atlas).text((x+8, y+3), name, fill='#ffe5a8')
    atlas.save(ROOT/'docs/protagonista_oito_frames.png')
    palette = atlas.quantize(colors=224)
    frames = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in sequence]
    frames[0].save(ROOT/'docs/protagonista_oito_frames.gif', save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, optimize=True)
    print('Prévia de todas as interações exportada.')
    pygame.quit()


if __name__ == '__main__':
    main()
