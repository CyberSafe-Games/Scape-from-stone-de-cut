"""Prévia dos sete chefes, duas fases da dupla e todos os grupos ativos; sem saves."""
import os
import sys
import math
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from PIL import Image
from src.core.asset_manager import AssetManager
from src.scenes.battle_scene import BattleScene
from src.systems.enemy_factory import create_point_enemy,create_alvaro_tex,choose_next_action
from src.systems.alvaro_tex_animations import TRANSITION_MS
from src.systems.boss_animation_kits import KITS


def main():
    pygame.init();pygame.display.set_mode((1,1))
    assets=AssetManager()
    window=SimpleNamespace(get_virtual_mouse_pos=lambda:(-1,-1),draw_fullscreen_button=lambda *_:None)
    clock=0
    posters=[]
    for level,phase in ((1,1),(2,1),(2,2),(3,1),(4,1),(5,1),(6,1),(7,1)):
        if '--corpo-seco' in sys.argv and level!=5:
            continue
        scene=BattleScene(None,window,assets,selected_level=level)
        scene.engine.level=level
        boss=create_alvaro_tex(phase=phase) if level==2 else create_point_enemy(level)
        scene.engine.enemy=boss
        choose_next_action(boss)
        scene.engine.player.hp=scene.engine.player.max_hp=999
        canvas=pygame.Surface((1280,720))
        sequence=[]

        def capture(duration,poster=False):
            nonlocal clock
            for i in range(math.ceil(duration/40)+1):
                clock+=40
                with patch('pygame.time.get_ticks',return_value=clock):
                    scene.update(40);scene.draw(canvas)
                im=Image.frombytes('RGB',canvas.get_size(),pygame.image.tobytes(canvas,'RGB'))
                sequence.append(im.resize((640,360),Image.Resampling.LANCZOS))
                if poster and i==round(duration*.6/40):posters.append(im.resize((480,270),Image.Resampling.LANCZOS))
        capture(1500)
        scene.entity_view.trigger_flash('enemy');capture(300)
        actions=list(boss.actions)+[boss.special_action]
        for action in actions:
            boss.hp=max(1,boss.max_hp-20)
            boss.reset_energy()
            scene.engine.state='player_turn'
            scene.engine.end_turn()
            boss.set_intent(action.action_type,action.value,action)
            scene.engine.enemy_actions_remaining=1
            scene.engine.enemy_turn()
            view=scene.entity_view
            duration=view.enemy_attack_duration if action.action_type=='attack' else view.enemy_action_duration
            capture(duration,poster=action is boss.special_action)
        if level==2 and phase==1:
            boss.hp=0;scene.engine._on_enemy_defeated();capture(TRANSITION_MS+500)
        palette=sequence[len(sequence)//2].quantize(colors=192)
        frames=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in sequence]
        slug=KITS[boss.name.lower()][0]
        frames[0].save(ROOT/'docs'/f'boss_{slug}_twelve_frames.gif',save_all=True,append_images=frames[1:],duration=40,loop=0,optimize=True)
    atlas=Image.new('RGB',(480*2,270*4),'#172923')
    for i,im in enumerate(posters):atlas.paste(im,((i%2)*480,(i//2)*270))
    destination='corpo_seco_melee_in_battle.png' if '--corpo-seco' in sys.argv else 'bosses_twelve_frames_in_battle.png'
    atlas.save(ROOT/'docs'/destination)
    pygame.quit()
    print('Sete bosses e duas fases da dupla renderizados, sem saves.')


if __name__=='__main__':main()
