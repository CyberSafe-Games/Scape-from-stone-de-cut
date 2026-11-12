"""Piloto de trilha em cenas reais; usa apenas save temporário para desenhar o mapa."""
import ast,gc,os,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
if '--smoke' in sys.argv:
    os.environ['SDL_VIDEODRIVER']='dummy'
    os.environ['SDL_AUDIODRIVER']='dummy'
import pygame
from src.core.audio_manager import AudioManager
from src.core.asset_manager import AssetManager
from src.core.window import WindowManager
from src.core.scene_manager import SceneManager
from src.config.audio_mix import SOUND_VOLUMES
from src.scenes.menu_scene import MenuScene
from src.scenes.map_scene import MapScene
from src.scenes.battle_scene import BattleScene
from src.systems.enemy_factory import create_road_enemy,create_guardiao_da_pedra,create_zanzara
from src.systems.save_manager import SaveManager

TRACKS={
 1:('Menu / mapa — Deep forest','music/menu_floresta_v1.ogg'),
 2:('Combate — The Last Stand','music/combate_tambores_v1.ogg'),
 3:('Zanzara final — Jungle Tribe','music/chefes_jungle_tribe_v2.ogg'),
 6:('Demais chefes — Jungle Chase','music/chefes_jungle_chase_v2.ogg'),
}

def main():
    pygame.init()
    window=WindowManager(title='Scape from Stone — piloto da trilha | 1 a 6')
    assets=AssetManager()
    audio=AudioManager(music_volume=.45)
    tree=ast.parse((ROOT/'main.py').read_text(encoding='utf-8'))
    sounds=next(ast.literal_eval(n.args[0]) for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='register_sounds')
    audio.register_sounds(sounds)
    for name,gain in SOUND_VOLUMES.items():audio.set_sound_volume(name,gain)
    manager=SceneManager(audio_manager=audio)
    volume=.45;muted=False;choice=1;show_map=False;scene=None
    folder=tempfile.TemporaryDirectory(prefix='scape-piloto-trilha-')
    saves=SaveManager(folder.name)
    data=saves.create_save('slot_1')
    data['progresso']['guia_mapa_visto']=True

    def change(number,restart_music=True):
        nonlocal scene,choice
        choice=number
        audio.stop_all_sfx()
        if number==1:
            scene=MapScene(manager,window,assets,saves,data) if show_map else MenuScene(manager,window,assets)
        else:
            level=7 if number==3 else 1
            scene=BattleScene(manager,window,assets,selected_level=level)
            scene.engine.enemy=create_zanzara() if level==7 else create_guardiao_da_pedra() if number==6 else create_road_enemy(1)
            scene.engine.level=level
            scene.engine.player.hp=scene.engine.player.max_hp=999
            scene.engine.state='player_turn'
        manager.change_scene(scene)
        gc.collect()

    def action(index):
        if not isinstance(scene,BattleScene):
            audio.play_sfx('ui.click')
            return
        enemy=scene.engine.enemy
        moves=list(enemy.actions[:3])
        ultimate=getattr(enemy,'special_action',None)
        move=ultimate if index==3 else moves[index] if index<len(moves) else None
        if move is None:return
        audio.stop_all_sfx()
        if move.action_type=='attack':
            scene._handle_combat_event('attack',attacker='enemy',action=move.visual_effect or 'atk',ultimate=move is ultimate)
            scene._handle_combat_event('flash',target='player')
        else:
            scene._handle_combat_event('enemy_action',action=move.visual_effect or 'def')

    def draw():
        scene.draw(window.screen)
        panel=pygame.Surface((1920,114),pygame.SRCALPHA);panel.fill((4,8,10,235))
        window.screen.blit(panel,(0,0))
        for text,y,color in ((TRACKS[choice][0]+f' | Música: {0 if muted else round(volume*100)}%',8,(150,245,185)),
             ('1 Menu/Mapa | 2 Combate | 3 Zanzara final | 6 Demais chefes',42,(255,235,180)),
             ('A/S/D/F golpes | Cima/Baixo volume | M silenciar | T menu/mapa | Espaço reiniciar | Esc sair',77,(210,220,225))):
            window.screen.blit(assets.get_font('small').render(text,True,color),(24,y))
        window.present()

    try:
        if '--smoke' in sys.argv:
            for number in TRACKS:
                change(number)
                assert audio.available and pygame.mixer.music.get_busy()
                draw()
                action(0)
                for tick in range(210):
                    manager.update(16)
                    if tick in (30,100,209):draw()
                assert audio._music_path == audio.assets_dir / TRACKS[number][1]
                assert pygame.mixer.music.get_busy()
                print('OK trilha/contexto',number,flush=True)
            show_map=True;change(1,restart_music=False);manager.update(400);draw()
            print('OK mapa; quatro trilhas aprovadas carregadas; sem escuta crítica.',flush=True)
            return
        change(1)
        clock=pygame.time.Clock();running=True
        while running:
            dt=clock.tick(60)
            for event in pygame.event.get():
                if event.type==pygame.QUIT or event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
                    running=False
                elif event.type==pygame.KEYDOWN:
                    if event.key-pygame.K_0 in TRACKS:change(event.key-pygame.K_0)
                    elif event.key in (pygame.K_a,pygame.K_s,pygame.K_d,pygame.K_f):action((pygame.K_a,pygame.K_s,pygame.K_d,pygame.K_f).index(event.key))
                    elif event.key in (pygame.K_UP,pygame.K_DOWN):
                        volume=round(max(.05,min(1,volume+(.05 if event.key==pygame.K_UP else -.05))),2)
                        audio.set_music_volume(0 if muted else volume)
                    elif event.key==pygame.K_m:
                        muted=not muted;audio.set_music_volume(0 if muted else volume)
                    elif event.key==pygame.K_t and choice==1:
                        show_map=not show_map;change(1,restart_music=False)
                    elif event.key==pygame.K_SPACE:audio.play_music(TRACKS[choice][1],loops=-1)
                window.handle_window_event(event)
            manager.update(dt);draw()
    finally:
        audio.shutdown();pygame.quit();folder.cleanup()

if __name__=='__main__':main()
