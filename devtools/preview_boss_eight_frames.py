"""Prévia dos kits reais, sem saves nem alterações no estado da campanha."""
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from PIL import Image
from src.core.asset_manager import AssetManager
from src.scenes.battle_scene import BattleScene
from src.systems.enemy_factory import create_point_enemy,create_alvaro_tex,choose_next_action


def main():
    pygame.init();pygame.display.set_mode((1,1))
    assets = AssetManager()
    window = SimpleNamespace(get_virtual_mouse_pos=lambda:(-1,-1),draw_fullscreen_button=lambda *_:None)
    sequence = []
    posters = []
    clock = 0
    for level,phase in ((1,1),(2,1),(2,2),(3,1),(5,1),(6,1)):
        scene = BattleScene(None,window,assets,selected_level=level)
        scene.engine.level = level
        boss = create_alvaro_tex(phase=phase) if level==2 else create_point_enemy(level)
        scene.engine.enemy = boss
        choose_next_action(boss)
        scene.engine.player.hp = scene.engine.player.max_hp = 600
        canvas = pygame.Surface((1280,720))
        def capture(duration,poster=False):
            nonlocal clock
            for i in range(round(duration/80)+1):
                clock += 80
                with patch('pygame.time.get_ticks',return_value=clock):
                    scene.update(80)
                    scene.draw(canvas)
                im = Image.frombytes('RGB',canvas.get_size(),pygame.image.tobytes(canvas,'RGB'))
                sequence.append(im.resize((768,432),Image.Resampling.LANCZOS))
                if poster and i==round(duration/160):
                    posters.append(im.resize((640,360),Image.Resampling.LANCZOS))
        capture(1100)
        support = next((a for a in boss.actions if a.action_type!='attack'),None)
        actions = [boss.actions[0]]+([support] if support else [])+[boss.special_action]
        for action in actions:
            scene.engine.state = 'player_turn'
            boss.set_intent(action.action_type,action.value,action)
            scene.engine.end_turn();scene.engine.enemy_actions_remaining=1
            scene.engine.enemy_turn()
            duration = scene.entity_view.enemy_attack_duration if action.action_type=='attack' else scene.entity_view.enemy_action_duration
            capture(duration,poster=action is boss.special_action)
    atlas = Image.new('RGB',(640*3,360*2))
    for i,p in enumerate(posters):atlas.paste(p,((i%3)*640,(i//3)*360))
    atlas.save(ROOT/'docs/bosses_oito_frames.png')
    palette = atlas.resize((1920,1080)).quantize(colors=192)
    frames = [f.quantize(palette=palette,dither=Image.Dither.NONE) for f in sequence]
    frames[0].save(ROOT/'docs/bosses_oito_frames.gif',save_all=True,append_images=frames[1:],duration=80,loop=0,optimize=True)
    print('Kits de seis formas de boss renderizados com oito quadros.')
    pygame.quit()


if __name__=='__main__':main()
