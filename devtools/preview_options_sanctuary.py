"""Prévia de configurações e retratos, com preferências e saves temporários."""
import argparse
import os
from pathlib import Path
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.smoke:
        os.environ['SDL_VIDEODRIVER']='dummy'
        os.environ['SDL_AUDIODRIVER']='dummy'
    import pygame
    from src.core.asset_manager import AssetManager
    from src.core.audio_manager import AudioManager
    from src.core.scene_manager import SceneManager
    from src.core.window import WindowManager
    from src.systems.game_preferences import GamePreferences
    from src.systems.save_manager import SaveManager
    from src.systems.normal_enemy_catalog import BIOME_ENEMIES
    from src.scenes.options_scene import OptionsScene
    from src.scenes.pause_menu_modal import PauseMenuModal
    from src.scenes.guide_library_scene import GuideLibraryScene
    from src.scenes.battle_scene import BattleScene
    from src.config.preferences import OPTIONS_TABS
    from src.ui.battle_hud import BattleHUD
    pygame.init()
    args.output.mkdir(parents=True,exist_ok=True)
    window,assets=WindowManager(),AssetManager()
    window.get_virtual_mouse_pos=lambda:(-1,-1)
    with tempfile.TemporaryDirectory() as folder:
        prefs=GamePreferences(Path(folder)/'preferences.json')
        audio=AudioManager()
        prefs.apply_audio(audio)
        manager=SceneManager(audio,prefs)
        options=OptionsScene(manager,window,assets)
        manager.change_scene(options)
        for key,_ in OPTIONS_TABS:
            options.tab=key
            options.draw(window.screen)
            pygame.image.save(window.screen,args.output/f'opcoes_{key}.png')
            if key=='audio':
                pygame.image.save(pygame.transform.smoothscale(window.screen,(1280,720)),args.output/'opcoes_1280.png')
        library=GuideLibraryScene(manager,window,assets)
        for key in library.tabs:
            library.key=key
            library.draw(window.screen)
            pygame.image.save(window.screen,args.output/f'guia_{key}.png')
        window.screen.fill((9,14,12))
        hud=BattleHUD(assets)
        names=[name for group in BIOME_ENEMIES.values() for name in group]
        for i,name in enumerate(names):
            rect=pygame.Rect(65+(i%7)*265,70+(i//7)*500,198,216)
            hud.portrait(window.screen,rect,name)
            label=assets.small_font.render(name,True,(222,196,137))
            if label.get_width()>246:label=pygame.transform.smoothscale(label,(246,round(label.get_height()*246/label.get_width())))
            window.screen.blit(label,label.get_rect(midtop=(rect.centerx,rect.bottom+15)))
        pygame.image.save(window.screen,args.output/'retratos_comuns.png')
        window.screen.fill((9,14,12))
        for i,name in enumerate(names):
            rect=pygame.Rect(210+(i%2)*820,16+(i//2)*148,680,138)
            hud.combatant(window.screen,rect,name,60,60,[],enemy=True)
        pygame.image.save(window.screen,args.output/'hud_comuns_14.png')
        pygame.image.save(pygame.transform.smoothscale(window.screen,(1280,720)),args.output/'hud_comuns_14_1280.png')

        from src.systems.enemy_factory import ENEMY_TYPES
        window.screen.fill((9,14,12))
        legacy=[name for name,_,_ in ENEMY_TYPES if name not in names]
        for i,name in enumerate(legacy):
            rect=pygame.Rect(210+i*820,460,680,138)
            hud.combatant(window.screen,rect,name,60,60,[],enemy=True)
        pygame.image.save(window.screen,args.output/'hud_comuns_legados.png')
        saves=SaveManager(Path(folder)/'saves')
        data=saves.create_save('preview')
        battle=BattleScene(manager,window,assets,saves,data,map_mode=True,selected_level=6,encounter_kind='road',encounter_index=0)
        battle.boss_dialogue=None
        battle.draw(window.screen)
        pygame.image.save(window.screen,args.output/'hud_inimigo_comum.png')
        PauseMenuModal(manager,window,assets).draw(window.screen)
        pygame.image.save(window.screen,args.output/'pausa.png')
    pygame.quit()
    print('Quatro abas, guias, retratos e pausa renderizados sem slots reais.')


if __name__=='__main__':main()
