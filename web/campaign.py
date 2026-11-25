"""Campanha web: cenas nativas e confirmação IndexedDB na fronteira de comandos."""
import asyncio
from copy import deepcopy
import gc
import json
import pygame
from src.core.scene_manager import SceneManager
from src.scenes.base_scene import BaseScene
from src.scenes.menu_scene import MenuScene
from src.scenes.save_selection_scene import SaveSelectionScene
from src.scenes.map_scene import MapScene
from src.scenes.battle_scene import BattleScene
from src.scenes.tutorial_scene import TutorialScene
from src.scenes.cutscene_scene import CutsceneScene
from src.systems.territory_map import TERRITORIES, encounter_status
from src.systems.normal_enemy_catalog import BIOME_ENEMIES
from src.systems.enemy_factory import create_point_enemy
from src.systems.save_manager import SaveError
from src.storage.manager import BrowserSaveManager
from src.ui.helpers import draw_text
from src.ui import dark_fantasy_theme as theme
from src.ui.inspection_controller import InspectionController
from web.persistence import (PersistentBattle,StorageUnavailable,Application,get_platform,
    create_window_manager,BrowserStore,GamePreferences,AudioManager,MUSIC_VOLUME)

def flag(manager,data,name):
    data["perfil"][name]=True
    data["progresso"][name]=True
    manager.save(data)
    return True,"Progresso confirmado."

class LoadingScene(BaseScene):
    def __init__(self,scenes,window,assets,retry):
        super().__init__(scenes,window,assets)
        self.retry=retry
    def update(self,dt):pass
    def draw(self,surface):
        surface.fill((8,15,13))
        theme.panel(surface,pygame.Rect(450,365,1020,350))
        draw_text(surface,"PREPARANDO A JORNADA",self.asset_manager.title_font,(230,194,117),960,420,center=True)
        draw_text(surface,self.asset_manager.label,self.asset_manager.font,(202,201,171),960,510,center=True)
        pygame.draw.rect(surface,(48,53,39),(540,580,840,22))
        pygame.draw.rect(surface,(188,148,68),(540,580,round(840*self.asset_manager.progress),22))
        if self.scene_manager.storage_error:
            draw_text(surface,"Falha no carregamento. Clique para tentar novamente.",
                      self.asset_manager.small_font,(236,163,126),960,650,center=True)
    def handle_event(self,event):
        if event.type==pygame.MOUSEBUTTONDOWN and not self.scene_manager.saving:self.retry()

class CampaignScenes(SceneManager):
    def configure(self,window,assets,manager):
        self.window,self.assets,self.save_manager=window,assets,manager
        self.inspection=InspectionController()
        import platform
        self.profiling="profile=1" in str(platform.window.location.search)
        self.draw_profile={}
        self.home_factory=lambda:CampaignMenu(self,window,assets)
        self.management_home=lambda m,d:self.open_map(d)
    def change_scene(self,scene):
        if type(scene) is MapScene:
            return self.open_map(scene.save_data)
        if type(scene) is MenuScene:
            scene=self.home_factory()
        if hasattr(scene,"reward_view"):
            from src.ui.composition_cache import optimize_visuals
            optimize_visuals(scene.reward_view)
        if hasattr(scene,"visuals"):
            from src.ui.composition_cache import optimize_visuals
            optimize_visuals(scene.visuals)
        if getattr(self,"profiling",False) and hasattr(scene,"visuals"):
            import time
            for name in ("backdrop","panel","framed_card","card","price_button","balance","feedback"):
                original=getattr(scene.visuals,name,None)
                if original is None:continue
                def instrument(method,label):
                    def measured(*args,**kwargs):
                        before=time.perf_counter()
                        result=method(*args,**kwargs)
                        self.draw_profile[label]=self.draw_profile.get(label,0)+(time.perf_counter()-before)*1000
                        return result
                    return measured
                setattr(scene.visuals,name,instrument(original,name))
        super().change_scene(scene)
    def push_modal(self,modal):
        if hasattr(modal,"visuals"):
            from src.ui.composition_cache import optimize_visuals
            optimize_visuals(modal.visuals)
        super().push_modal(modal)
    def draw(self,surface):
        import time
        mobile=getattr(self,"mobile",None)
        target=self.modal_stack[-1] if self.modal_stack else self.current_scene
        if mobile and mobile.layout.compact and not isinstance(target,(BattleScene,CutsceneScene)):
            key=(id(self.current_scene),id(target))
            now=pygame.time.get_ticks()
            if key==getattr(self,"_mobile_draw_key",None) and now-getattr(self,"_mobile_draw_at",0)<250:
                self.draw_profile={"total":0}
                return
            self._mobile_draw_key,self._mobile_draw_at=key,now
        self.draw_profile={}
        before=time.perf_counter()
        super().draw(surface)
        self.draw_profile["total"]=(time.perf_counter()-before)*1000
    def handle_event(self,event):
        if event.type==pygame.MOUSEMOTION and not self.saving:
            scene=self.current_scene
            target=None
            if isinstance(scene,BattleScene):
                index=scene._hand_card_at(self.window.map_to_virtual(event.pos))
                if index is not None:target=("hand",index)
            self.inspection.inspect(target)
        if event.type==pygame.MOUSEWHEEL and not self.saving and not self.modal_stack:
            scene=self.current_scene
            from src.scenes.shop_scene import ShopScene
            from src.scenes.roguelite_scene import RogueliteScene
            if isinstance(scene,ShopScene):
                scene._set_page(max(0,min(scene.page_count-1,scene.page-event.y)))
                return
            if isinstance(scene,RogueliteScene) and not scene.preparation:
                scene._page(-event.y)
                return
        super().handle_event(event)
    def load(self,kind,data,factory,level=1,names=()):
        if self.saving:return False
        self.inspection.clear()
        cards=data["progresso"]["cartas"] if data else ()
        def retry():self.load(kind,data,factory,level,names)
        super().change_scene(LoadingScene(self,self.window,self.assets,retry))
        async def work():
            if self.audio_manager:
                self.audio_manager.stop_music()
                self.audio_manager._sounds.clear()
                self.audio_manager._failed_sounds.clear()
            await asyncio.sleep(0)
            gc.collect()
            await self.assets.prepare(kind,level,names,cards)
        return self.submit(work,lambda _:self.change_scene(factory()))
    def open_map(self,data):
        return self.load("map",data,lambda:CampaignMap(self,self.window,self.assets,self.save_manager,data))
    def open_tutorial(self,data):
        return self.load("tutorial",data,lambda:CampaignTutorial(self,self.window,self.assets,self.save_manager,data),
                         names=("Slime","Viniurgo"))
    def open_cutscene(self,kind,data,next_action,seen=None):
        from src.config.cutscenes import INTRO_CUTSCENE,POST_TUTORIAL_CUTSCENE,FINAL_CUTSCENE
        frames={"intro":INTRO_CUTSCENE,"post":POST_TUTORIAL_CUTSCENE,"final":FINAL_CUTSCENE}[kind]
        return self.load("cutscene:"+kind,data,
            lambda:CampaignCutscene(self,self.window,self.assets,frames,next_action,data,seen))
    def enter(self,data):
        p=data["progresso"]
        if not p["tutorial_concluido"]:
            if not p.get("intro_vista"):
                return self.open_cutscene("intro",data,lambda:self.open_tutorial(data),"intro_vista")
            return self.open_tutorial(data)
        if not p.get("pos_tutorial_visto"):
            return self.open_cutscene("post",data,lambda:self.open_map(data),"pos_tutorial_visto")
        return self.open_map(data)
    def open_battle(self,data,level,index):
        snapshot=data["progresso"].get("combat_snapshot")
        if snapshot:
            level,index=snapshot["level"],snapshot["index"] if snapshot["kind"]=="road" else None
        names=BIOME_ENEMIES[level] if index is not None else (create_point_enemy(level).name,)
        if snapshot:names=(*names,snapshot["enemy"]["name"])
        return self.load("battle",data,
            lambda:CampaignBattle(self,self.window,self.assets,self.save_manager,data,
                                  map_mode=True,selected_level=level,
                                  encounter_kind="road" if index is not None else "point",encounter_index=index),
            level,names)

class CampaignMenu(MenuScene):
    def _open_options(self):
        from src.scenes.options_scene import OptionsScene
        self.scene_manager.load("management",None,
            lambda:OptionsScene(self.scene_manager,self.window_manager,self.asset_manager,return_scene=self))
    def _start_game(self):
        self.scene_manager.submit(lambda:self.scene_manager.save_manager.refresh(),
            lambda _:self.scene_manager.change_scene(CampaignSlots(
                self.scene_manager,self.window_manager,self.asset_manager,self.scene_manager.save_manager)))
    def handle_event(self,event):
        # O nome do método nativo de abertura é preservado via override abaixo.
        super().handle_event(event)
    def _open_save_selection(self):self._start_game()

class CampaignSlots(SaveSelectionScene):
    def _select(self,index):
        status,data=self.slots[index]
        if status=="corrupted":
            self.error="Save inválido. Importe um backup ou exclua o espaço."
            return
        if status=="empty":
            self.scene_manager.submit(
                lambda:self.save_manager.run(None,lambda m,d:m.create_save(m.slot_id(index+1))),
                self.scene_manager.enter)
        else:self.scene_manager.enter(data)
    def _delete(self,index):
        self.scene_manager.submit(
            lambda:self.save_manager.run(None,lambda m,d:m.delete_save(m.slot_id(index+1))),
            lambda _:self.refresh())
    def _open_test_save(self):
        self.scene_manager.submit(
            lambda:self.save_manager.run(None,lambda m,d:m.load_or_create_test_save()),
            self.scene_manager.open_map)
    def _back(self):self.scene_manager.request_exit()

class CampaignMap(MapScene):
    def _background(self,surface):
        if not hasattr(self,"_web_map_background"):
            self._web_map_background=surface.copy().convert(surface)
            super()._background(self._web_map_background)
        surface.blit(self._web_map_background,(0,0))
    def _dismiss_guide(self):
        def complete(result):
            self.guide_open=False
            self.error=""
        self.persist_command(lambda m,d:flag(m,d,"guia_mapa_visto"),complete)
    def _start_selected(self):
        snapshot=self.save_data["progresso"].get("combat_snapshot")
        territory=next(t for t in TERRITORIES if t.id==self.selected)
        if not snapshot and encounter_status(self.save_data,territory.id,self.selected_encounter)=="locked":
            self.error="Ponto bloqueado! Conclua os encontros anteriores."
            return
        self.scene_manager.open_battle(self.save_data,territory.level,self.selected_encounter)
    def _back(self):self.scene_manager.request_exit()

class CampaignCutscene(CutsceneScene):
    def __init__(self,scenes,window,assets,frames,next_action,data,seen):
        self.save_manager,self.save_data=scenes.save_manager,data
        self.next_action,self.seen=next_action,seen
        super().__init__(scenes,window,assets,frames,lambda:None)
        self.skip_button=pygame.Rect(1550,24,320,66)
    def _finish(self):
        if self._finished:return
        self._finished=True
        if self.seen:
            def failed(error):
                self._finished=False
                self._phase="idle"
                self.scene_manager.storage_error=str(error)
            self.scene_manager.submit(
                lambda:self.save_manager.run(self.save_data,lambda m,d:flag(m,d,self.seen)),
                lambda _:self.next_action(),failed)
        else:self.next_action()
    def draw(self,surface):
        super().draw(surface)
        theme.button(surface,self.skip_button,"PULAR / CONTINUAR",self.asset_manager.small_font)
    def handle_event(self,event):
        if event.type==pygame.MOUSEBUTTONDOWN and self.skip_button.collidepoint(self.window_manager.map_to_virtual(event.pos)):
            self._finish();return
        super().handle_event(event)

class CampaignTutorial(TutorialScene):
    def _complete_tutorial(self):
        if self.engine.state!="victory" or self._tutorial_completion_committed:return
        def command(manager,data):
            if not data["perfil"]["tutorial_concluido"]:
                data["progresso"]["moedas"]+=30
                data["progresso"]["vida"]=self.engine.player.max_hp
                flag(manager,data,"tutorial_concluido")
            return True,"Tutorial confirmado."
        def complete(result):
            self._tutorial_completion_committed=True
            self.scene_manager.enter(self.save_data)
        self.persist_command(command,complete)
    def _return_to_main_menu(self):self.scene_manager.request_exit()

class CampaignBattle(BattleScene):
    def __init__(self,scenes,window,assets,manager,data,**kwargs):
        self._saved_signature=None
        self._confirmed_snapshot=deepcopy(data["progresso"].get("combat_snapshot"))
        super().__init__(scenes,window,assets,manager,data,**kwargs)
        self.request_checkpoint()
    def _persist_logical_state(self):return True
    def request_checkpoint(self):
        if self.engine.is_replay:return
        return PersistentBattle.request_checkpoint(self)
    def update(self,dt):
        super().update(dt)
        self.request_checkpoint()
    def _save_progress(self):
        self.request_checkpoint()
        return not self.scene_manager.saving
    def save_on_exit(self):return self._save_progress()
    def _return_to_main_menu(self):
        self.scene_manager.open_map(self.save_data)
    def _make_map_scene(self):
        return CampaignMap(self.scene_manager,self.window_manager,self.asset_manager,self.save_manager,self.save_data)
    def _return_to_map(self):self.scene_manager.open_map(self.save_data)
    def _finalize_map_phase(self,level):
        if self.scene_manager.saving or self.engine.state!="phase_complete":return
        if self.engine.is_replay:
            return self.scene_manager.open_cutscene("final",self.save_data,
                lambda:self.scene_manager.open_map(self.save_data))
        from src.systems.combat_snapshot import capture,restore
        from src.systems.campaign_progress import record_victory
        snapshot=capture(self.engine)
        def command(manager,data):
            from src.systems.combat_engine import CombatEngine
            engine=CombatEngine(map_mode=True)
            restore(engine,snapshot)
            engine.run_progress=data["progresso"]
            engine.encounter_kind=snapshot["kind"]
            engine.encounter_index=snapshot["index"]
            record_victory(manager,data,engine,lambda:None)
            return True,"Campanha confirmada."
        self.persist_command(command,lambda _:self.scene_manager.open_cutscene(
            "final",self.save_data,lambda:self.scene_manager.open_map(self.save_data)))
    def handle_event(self,event):
        if self.engine.state=="phase_complete":
            if event.type in (pygame.MOUSEBUTTONDOWN,pygame.KEYDOWN):
                self._finalize_map_phase(self.engine.level)
            return
        super().handle_event(event)
    def _commit_reward(self,choice):
        if self.engine.is_replay:
            self.scene_manager.open_map(self.save_data);return
        from src.systems.combat_snapshot import capture,restore
        from src.systems.campaign_progress import record_victory,record_road_victory
        original=capture(self.engine)
        def command(manager,data):
            from src.systems.combat_engine import CombatEngine
            engine=CombatEngine(map_mode=True)
            restore(engine,original)
            engine.run_progress=data["progresso"]
            engine.encounter_kind=original["kind"]
            engine.encounter_index=original["index"]
            kind,value=choice
            if kind=="card":engine.choose_reward(value)
            elif kind=="material":engine.choose_material(value)
            else:engine.skip_reward()
            recorder=record_road_victory if engine.encounter_kind=="road" else record_victory
            recorder(manager,data,engine,lambda:None)
            return True,"Recompensa confirmada."
        def complete(result):
            if original["level"]==7 and original["kind"]=="point":
                self.scene_manager.open_cutscene("final",self.save_data,lambda:self.scene_manager.open_map(self.save_data))
            else:self.scene_manager.open_map(self.save_data)
        self.persist_command(command,complete)



async def main():
    from src.core.audio_manager import prepare_web_audio
    prepare_web_audio()
    pygame.display.init();pygame.font.init()
    import platform
    platform.window.config.user_canvas_managed=1
    service=get_platform()
    window=create_window_manager(platform_service=service)
    from web.assets import CampaignAssets
    assets=CampaignAssets()
    store=BrowserStore()
    preferences=GamePreferences(store=store)
    audio=AudioManager(music_volume=MUSIC_VOLUME,defer_initialization=True)
    from desktop_entry import configure_audio
    configure_audio(audio);preferences.apply(audio)
    scenes=CampaignScenes(audio_manager=audio,audio_preferences=preferences,platform_service=service)
    def install(_):
        scenes.configure(window,assets,BrowserSaveManager(store))
        scenes.change_scene(scenes.home_factory())
        if store.preference_error:scenes.storage_error=store.preference_error
    def unavailable(error):
        scenes.change_scene(StorageUnavailable(scenes,window,assets,str(error),
            lambda:scenes.submit(lambda:store.open(),install,unavailable)))
    try:
        await store.open();install(None)
    except Exception as error:unavailable(error)
    from web.mobile import MobileInterface
    scenes.mobile=MobileInterface(scenes,platform.window.scapeMobile)
    from src.core.active_timeline import ActiveTimeline
    timeline=ActiveTimeline(pygame.time.get_ticks)
    pygame.time.get_ticks=timeline.ticks
    app=Application(window,assets,audio,preferences,scenes)
    app.timeline=timeline
    def observe(application):
        if application.frames%5 and application._active:return
        scenes.mobile.publish()
        scene=scenes.current_scene
        data=getattr(scene,"save_data",None)
        engine=getattr(scene,"engine",None)
        report=dict(scene=type(scene).__name__,saving=scenes.saving,error=scenes.storage_error,
                    frames=application.frames,active=application._active,fps=application.clock.get_fps(),
                    loading_label=assets.label,loading_progress=assets.progress,context=assets.active_context,resident=sorted(assets.resident),transfer_bytes=assets.transfer_bytes,
                    data=data,preferences=preferences.values)
        report["memfs"]=dict(freed_bytes=assets.memfs_freed_bytes,temporary_bytes=assets.pack_temporary_bytes,
            pruned_groups=sorted(assets.pruned_groups))
        report["compact"]=scenes.mobile.layout.compact
        report["portrait_blocked"]=scenes.mobile.layout.portrait_blocked
        report["audio_available"]=audio.available
        report["audio_mix"]=dict(format=pygame.mixer.get_init(),channels=pygame.mixer.get_num_channels() if audio.available else 0,
            music_volume=pygame.mixer.music.get_volume() if audio.available else 0,
            max_sfx_gain=max((sound.get_volume() for sound in audio._sounds.values()),default=0))
        report["render_buffer"]=list(window.display_surface.get_size())
        report["physical_canvas"]=list(pygame.Surface.get_size(window.screen))
        report["mobile_render_cache"]=dict(bytes=getattr(window.screen,"cache_bytes",0),
            hits=getattr(window.screen,"cache_hits",0),misses=getattr(window.screen,"cache_misses",0))
        report["missing_sounds"]=sorted(audio._failed_sounds)
        report["music_path"]=str(audio._music_path or "")
        report["draw_profile"]=scenes.draw_profile
        report["frame_cost_ms"]=getattr(application,"frame_cost_ms",{})
        report["modal"]=type(scenes.modal_stack[-1]).__name__ if scenes.modal_stack else None
        target=scenes.modal_stack[-1] if scenes.modal_stack else scene
        report["ui"]={key:list(value) for key,value in vars(target).items() if isinstance(value,pygame.Rect)}
        report["rect_maps"]={key:{str(k):list(v) for k,v in value.items()}
            for key,value in vars(target).items() if isinstance(value,dict) and value and
            all(isinstance(v,pygame.Rect) for v in value.values())}
        report["active_tab"]=getattr(target,"tab",None)
        if hasattr(scene,"draft_slots"):report["draft_slots"]=scene.draft_slots
        report["page"]=getattr(scene,"page",None)
        report["message"]=str(getattr(scene,"message",getattr(scene,"notice",getattr(scene,"error",""))))
        if isinstance(scene,CutsceneScene):
            report["cutscene_index"]=scene.index
        if hasattr(scene,"guide_open"):report["guide_open"]=scene.guide_open
        if hasattr(scene,"overlay"):
            report["tutorial_active"]=scene.overlay.is_active
            report["tutorial_step"]=scene.overlay.step_index
        if engine:
            report["enemy_name"]=engine.enemy.name
            report["boss_dialogue"]=bool(scene.boss_dialogue and not scene.boss_dialogue.finished)
            report["enemy_action"]=scene.entity_view.enemy_action
            report["boss_effect_frames"]=len(assets.get_boss_ultimate_sprites(engine.enemy.name,effects=True))
            report["enemy_max_hp"]=engine.enemy.max_hp
            report["level"]=engine.level
            report["intents"]=[list(rect) for rect,_ in scene.intent_view.entries]
            report["intent_preview"]=list(scene.intent_view.tooltip_rect) if scene.intent_view.tooltip_rect else None
            report["sprite_counts"]={key:len(value) for key,value in assets._enemy_sprites.get(engine.enemy.name.lower(),{}).items()}
            report.update(victory_ready=scene._victory_ready,state=engine.state,player_hp=engine.player.hp,enemy_hp=engine.enemy.hp,energy=engine.energy,
                action=scene.entity_view.player_action,
                hand=[dict(name=c.name,cost=c.cost,rect=list(rect)) for c,rect in
                      zip(engine.hand,scene._get_battle_hand_rects())])
        if engine:
            report["reward_offers"]=[dict(kind=option[0],value=option[1],rect=list(rect))
                for option,rect in scene.reward_view.offers(engine,scene._reward_progress())]
        if getattr(scene,"management_guide",None):
            report["guide"]=dict(active=scene.management_guide.active,key=scene.management_guide.key,rects=[list(r) for r in scene.management_guide.layout()])
        platform.window.webStorageMetrics=json.dumps(report,ensure_ascii=True)
    try:await app.run_web(observe)
    except Exception:
        import traceback
        error=traceback.format_exc()
        platform.window.webRuntimeError=error
        platform.window.console.error(error)
        raise
    finally:audio.shutdown();pygame.quit()

