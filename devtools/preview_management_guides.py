"""Renderiza os guias e a HUD usando somente saves temporários."""
import argparse
import os
from pathlib import Path
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--smoke',action='store_true')
    args=parser.parse_args()
    if args.smoke:
        os.environ['SDL_VIDEODRIVER']='dummy'
        os.environ['SDL_AUDIODRIVER']='dummy'
    import pygame
    from src.core.asset_manager import AssetManager
    from src.core.window import WindowManager
    from src.core.scene_manager import SceneManager
    from src.scenes.shop_scene import ShopScene
    from src.scenes.backpack_scene import BackpackScene
    from src.scenes.roguelite_scene import RogueliteScene
    from src.scenes.battle_scene import BattleScene
    from src.systems.save_manager import SaveManager
    from src.systems.card_catalog import AVAILABLE_CARD_NAMES
    pygame.init()
    args.output.mkdir(parents=True,exist_ok=True)
    window,scenes,assets=WindowManager(),SceneManager(),AssetManager()
    window.get_virtual_mouse_pos=lambda:(-1,-1)
    with tempfile.TemporaryDirectory() as folder:
        saves=SaveManager(folder)
        data=saves.create_save('preview_guides')
        p=data['progresso']
        p['moedas']=2000
        p['cartas_colecao']=list(AVAILABLE_CARD_NAMES)
        p['materials']={name:6 for name in AVAILABLE_CARD_NAMES}
        saves.save(data)
        for cls,key in ((ShopScene,'loja'),(BackpackScene,'mochila'),(RogueliteScene,'altar')):
            scene=cls(scenes,window,assets,saves,data)
            scenes.change_scene(scene)
            guide=scene.management_guide
            for i in range(len(guide.steps)):
                guide.index=i
                scene.draw(window.screen)
                pygame.image.save(window.screen,args.output/f'{key}_guia_{i+1}.png')
            guide.active=False
            scene.draw(window.screen)
            pygame.image.save(window.screen,args.output/f'{key}_sem_guia.png')
        battle=BattleScene(scenes,window,assets,saves,data,map_mode=True,selected_level=7)
        battle.boss_dialogue=None
        battle.draw(window.screen)
        pygame.image.save(window.screen,args.output/'combate_menu_central.png')
        pygame.image.save(pygame.transform.smoothscale(window.screen,(1280,720)),args.output/'combate_1280.png')
    pygame.quit()
    print('Guias e HUD renderizados com save temporário.')


if __name__=='__main__':main()
