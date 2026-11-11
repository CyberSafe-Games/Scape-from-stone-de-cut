"""Prévia real dos seis especiais com oito efeitos, sem saves."""
import os
import sys
import math
from pathlib import Path
from types import SimpleNamespace
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from PIL import Image
from src.core.asset_manager import AssetManager
from src.scenes.battle_scene import BattleScene
from src.systems.enemy_factory import create_point_enemy,choose_next_action
from src.systems.boss_ultimate_animations import BOSS_ULTIMATE_ANIMATIONS


def main():
    pygame.init();pygame.display.set_mode((1,1))
    assets=AssetManager()
    window=SimpleNamespace(get_virtual_mouse_pos=lambda:(-1,-1),draw_fullscreen_button=lambda *_:None)
    sequence=[];posters=[]
    for level in (1,3,4,5,6,7):
        scene=BattleScene(None,window,assets)
        scene.engine.level=level
        scene.engine.enemy=boss=create_point_enemy(level)
        scene.engine.player.hp=scene.engine.player.max_hp=999
        boss.action_counter=7;choose_next_action(boss)
        scene.engine.end_turn();scene.engine.enemy_actions_remaining=1
        scene.engine.enemy_turn()
        spec=BOSS_ULTIMATE_ANIMATIONS[boss.name.lower()]
        canvas=pygame.Surface((1280,720))
        for i in range(math.ceil(spec.duration/60)+1):
            if i:scene.update(60)
            scene.draw(canvas)
            im=Image.frombytes('RGB',canvas.get_size(),pygame.image.tobytes(canvas,'RGB'))
            sequence.append(im.resize((768,432),Image.Resampling.LANCZOS))
            peak=(spec.release+spec.impact)/2 if spec.mode in ('bear','plasma','sovereign','blades') else spec.impact+.025
            if i==round(spec.duration*peak/60):posters.append(im.resize((640,360),Image.Resampling.LANCZOS))
    atlas=Image.new('RGB',(1920,720))
    for i,im in enumerate(posters):atlas.paste(im,((i%3)*640,(i//3)*360))
    atlas.save(ROOT/'docs/boss_ultimate_effects_em_combate.png')
    palette=atlas.quantize(colors=224)
    frames=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in sequence]
    frames[0].save(ROOT/'docs/boss_ultimate_effects_eight_frames.gif',save_all=True,append_images=frames[1:],duration=60,loop=0,optimize=True)
    pygame.quit()


if __name__=='__main__':main()
