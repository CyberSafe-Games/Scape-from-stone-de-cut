"""Mostra os retratos na moldura real e em uma batalha, sem acessar saves."""
import os
import sys
from pathlib import Path
from types import SimpleNamespace
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from src.core.asset_manager import AssetManager
from src.systems.character_portraits import PORTRAITS
from src.ui.battle_hud import BattleHUD
from src.ui.helpers import draw_text,wrap_text
from src.scenes.battle_scene import BattleScene
from src.systems.enemy_factory import create_zanzara,choose_next_action


def main():
    pygame.init();pygame.display.set_mode((1,1))
    assets=AssetManager();hud=BattleHUD(assets)
    names=list(PORTRAITS)+['Slime','Macaco Selvagem','Jaum Manel']
    canvas=pygame.Surface((1272,720));canvas.fill((17,30,25))
    for i,name in enumerate(names):
        x,y=(i%6)*212,(i//6)*180
        for j,line in enumerate(wrap_text(name,assets.small_font,200)):
            draw_text(canvas,line,assets.small_font,(231,209,157),x+6,y+5+j*16)
        hud.portrait(canvas,pygame.Rect(x+60,y+45,88,96),name,player=name=='Jaum Manel')
    pygame.image.save(canvas,str(ROOT/'docs/retratos_personagens.png'))
    window=SimpleNamespace(get_virtual_mouse_pos=lambda:(-1,-1),draw_fullscreen_button=lambda *_:None)
    scene=BattleScene(None,window,assets)
    scene.engine.level=7;scene.engine.enemy=create_zanzara();choose_next_action(scene.engine.enemy)
    battle=pygame.Surface((1280,720));scene.draw(battle)
    pygame.image.save(battle,str(ROOT/'docs/retratos_batalha.png'))
    pygame.quit()


if __name__=='__main__':main()
