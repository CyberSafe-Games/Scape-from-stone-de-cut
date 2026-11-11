"""Renderiza as duas fases usando o jogo real, sem ler ou gravar saves."""
import os
import sys
from pathlib import Path
from types import SimpleNamespace
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from PIL import Image
from src.core.asset_manager import AssetManager
from src.scenes.battle_scene import BattleScene
from src.systems.enemy_factory import create_point_enemy
from src.systems.alvaro_tex_animations import ATTACK_MS


def main():
    pygame.init()
    pygame.display.set_mode((1,1))
    assets = AssetManager()
    window = SimpleNamespace(get_virtual_mouse_pos=lambda:(-1,-1), draw_fullscreen_button=lambda *_:None)
    scene = BattleScene(None,window,assets,selected_level=2)
    scene.engine.level = 2
    scene.engine.enemy = create_point_enemy(2)
    scene.engine.player.hp = scene.engine.player.max_hp = 500
    canvas = pygame.Surface((1280,720))
    frames = []
    def capture(count, filename=None):
        for i in range(count):
            scene.update(100)
            scene.draw(canvas)
            frame = Image.frombytes('RGB',canvas.get_size(),pygame.image.tobytes(canvas,'RGB'))
            frames.append(frame.resize((768,432),Image.Resampling.LANCZOS))
            if filename and i == count//2:
                frame.save(ROOT/'docs'/filename)
    capture(8,'alvaro_tex_fase1.png')
    for phase in (1,2):
        enemy = scene.engine.enemy
        for action in enemy.actions + [enemy.special_action]:
            scene.engine.state = 'player_turn'
            enemy.set_intent(action.action_type,action.value,action)
            if action.action_type == 'buff':
                enemy.hp = max(1,enemy.hp-14)
            scene.engine.end_turn()
            scene.engine.enemy_actions_remaining = 1
            scene.engine.enemy_turn()
            count = round(ATTACK_MS[enemy.name.lower()][action.visual_effect]/100)+1
            poster = ('alvaro_tex_cura.png' if action.action_type == 'buff'
                      else f'alvaro_tex_especial_fase{phase}.png' if action is enemy.special_action else None)
            capture(count, poster)
        scene.engine.enemy.hp = 0
        scene.engine._on_enemy_defeated()
        if phase == 1:
            capture(24,'alvaro_tex_transicao.png')
            assert scene.engine.enemy.phase == 2
            capture(8,'alvaro_tex_fase2.png')
        else:
            capture(8)
    palette_sheet = Image.new('RGB',(768*3,432))
    for i,j in enumerate((0,len(frames)//2,len(frames)-12)):
        palette_sheet.paste(frames[j],(i*768,0))
    palette = palette_sheet.quantize(colors=192)
    indexed = [f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
    indexed[0].save(ROOT/'docs/alvaro_tex_em_acao.gif',save_all=True,append_images=indexed[1:],duration=100,loop=0,optimize=True)
    print('Duas fases, ataques, cura/buff e transição renderizados sem saves.')
    pygame.quit()


if __name__ == '__main__':
    main()
