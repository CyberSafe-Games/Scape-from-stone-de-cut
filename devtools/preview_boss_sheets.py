"""Piloto dos kits 4×2; não lê nem grava saves. --smoke exporta a conferência."""
import argparse
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--boss',type=int,choices=(1,5,6),default=None)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.smoke:
        os.environ['SDL_VIDEODRIVER']='dummy'
        os.environ['SDL_AUDIODRIVER']='dummy'
    import pygame
    from PIL import Image,ImageDraw
    from src.core.asset_manager import AssetManager
    from src.core.window import WindowManager
    from src.core.scene_manager import SceneManager
    from src.scenes.battle_scene import BattleScene
    from src.systems.enemy_factory import create_point_enemy
    from src.systems.boss_sheet_kits import SHEET_KITS
    from src.config.boss_names import boss_display_name
    pygame.init()
    window=WindowManager()
    assets=AssetManager()
    args.output.mkdir(parents=True,exist_ok=True)
    levels = (args.boss,) if args.boss is not None else ((1,5,6) if args.smoke else (1,))
    for level in levels:
        scene=BattleScene(SceneManager(),window,assets,selected_level=level)
        scene.boss_dialogue=None
        scene._boss_events=[]
        scene.engine.enemy=create_point_enemy(level)
        boss=scene.engine.enemy
        scene.engine.player.hp=scene.engine.player.max_hp=999
        slug=SHEET_KITS[boss.name.lower()][0]
        movie=[]
        posters=[]
        actions=[None,*boss.actions,boss.special_action,'dano']
        for action in actions:
            view=scene.entity_view
            view.attacker=None
            view.enemy_action=None
            view.enemy_ultimate=None
            view.enemy_flash=0
            title='Parado'
            duration=1800
            if action=='dano':
                title='Dano'
                view.trigger_flash('enemy',boss.name)
                duration=800
            elif action is not None:
                title=action.name
                if action.action_type=='attack':
                    view.trigger_attack('enemy',action.visual_effect,boss.name,ultimate=action is boss.special_action)
                    duration=view.enemy_attack_duration+view.enemy_recovery_ms+400
                else:
                    view.trigger_enemy_action(action.visual_effect,boss.name)
                    duration=view.enemy_action_duration+view.enemy_recovery_ms+400
            for elapsed in range(0,duration,80):
                view.update(80)
                scene.draw(window.screen)
                im=Image.frombytes('RGB',window.screen.get_size(),pygame.image.tobytes(window.screen,'RGB'))
                im=im.resize((960,540),Image.Resampling.LANCZOS)
                ImageDraw.Draw(im).text((15,520),f'{boss_display_name(boss.name)} - {title}',fill='white')
                movie.append(im)
                if abs(elapsed-duration*.5)<42:posters.append(im)
                if not args.smoke:
                    for event in pygame.event.get():
                        if event.type==pygame.QUIT:
                            pygame.quit()
                            return
                    window.present()
                    pygame.time.Clock().tick(12)
        poster=Image.new('RGB',(1920,1620))
        for i,im in enumerate(posters[:6]):poster.paste(im,((i%2)*960,(i//2)*540))
        poster.save(args.output/f'{slug}_arena.png')
        movie[0].save(args.output/f'{slug}.gif',save_all=True,append_images=movie[1:],duration=80,loop=0,optimize=True)
        print(f'{slug}: idle, dano, ataques, suporte e Ultimate renderizados.',flush=True)
        if not args.smoke:
            pygame.display.set_caption(f'Prévia de animações — {boss_display_name(boss.name)}')
            clock=pygame.time.Clock()
            index=0
            paused=False
            while True:
                for event in pygame.event.get():
                    if event.type==pygame.QUIT or (event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE):
                        pygame.quit()
                        return
                    if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                        paused=not paused
                image=pygame.image.frombytes(movie[index].tobytes(),movie[index].size,'RGB')
                window.screen.blit(pygame.transform.smoothscale(image,window.screen.get_size()),(0,0))
                label=assets.small_font.render('Clique para pausar/continuar · ESC para fechar',True,(245,220,165))
                window.screen.blit(label,(25,25))
                window.present()
                if not paused:index=(index+1)%len(movie)
                clock.tick(12)

    pygame.quit()


if __name__=='__main__':main()
