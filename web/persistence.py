"""Piloto de persistência: slots, telas reais de gerenciamento e encontro Slime."""
import asyncio
from copy import deepcopy
import json
import time
import pygame
from src.core.application import Application
from src.core.scene_manager import SceneManager
from src.core.window import create_window_manager
from src.platforms import get_platform
from src.core.audio_manager import AudioManager
from src.config.music import MUSIC_VOLUME
from src.systems.game_preferences import GamePreferences
from src.systems.save_manager import SaveError
from src.storage.browser_store import BrowserStore
from src.storage.manager import BrowserSaveManager
from src.scenes.base_scene import BaseScene
from src.scenes.save_selection_scene import SaveSelectionScene
from src.scenes.battle_scene import BattleScene
from src.ui import dark_fantasy_theme as theme
from src.ui.helpers import draw_text
from web.poc import ProofAssets, ProofMenu, ProofBattle


class PersistentMenu(ProofMenu):
    def _start_game(self):
        manager=self.scene_manager.save_manager
        async def refresh():
            await manager.refresh()
        self.scene_manager.submit(refresh,lambda _:self.scene_manager.change_scene(
            WebSlots(self.scene_manager,self.window_manager,self.asset_manager,manager)))
    def _open_options(self):
        from src.scenes.options_scene import OptionsScene
        self.scene_manager.push_modal(OptionsScene(self.scene_manager,self.window_manager,self.asset_manager,modal=True))
    def draw(self,surface):
        super().draw(surface)
        pygame.draw.rect(surface,(9,16,13),(0,995,1920,85))
        draw_text(surface,"WEB · SAVES V15 NO NAVEGADOR · EXPORTE SEU BACKUP",
                  self.asset_manager.small_font,(230,200,145),960,1030,center=True)


class WebSlots(SaveSelectionScene):
    def _select(self,index):
        status,data=self.slots[index]
        if status=="corrupted":
            self.error="Backup inválido. Importe um arquivo válido ou exclua o slot."
            return
        def complete(document):
            self.scene_manager.management_home(self.save_manager,document)
        if status=="empty":
            self.scene_manager.submit(
                lambda:self.save_manager.run(None,lambda m,d:m.create_save(m.slot_id(index+1),f"Jornada {index+1:02d}")),
                complete)
        else:
            complete(data)
    def _back(self):
        self.scene_manager.change_scene(PersistentMenu(self.scene_manager,self.window_manager,self.asset_manager))
    def _open_test_save(self):
        self.error="A campanha/laboratório completo será integrado na Etapa 4."
    def _request_delete(self,index):
        from src.scenes.confirmation_modal import ConfirmationModal
        key=self.save_manager.slot_id(index+1)
        def confirm():
            self.scene_manager.submit(lambda:self.save_manager.run(None,lambda m,d:m.delete_save(key)),
                                      lambda _:self.refresh())
        self.scene_manager.push_modal(ConfirmationModal(self.scene_manager,self.window_manager,self.asset_manager,
            on_confirm=confirm,title="EXCLUIR JORNADA?",message="Exporte um backup antes de excluir.",confirm_label="SIM, EXCLUIR"))


class PersistenceHub(BaseScene):
    music_context="menu"
    def __init__(self,scenes,window,assets,manager,data):
        super().__init__(scenes,window,assets)
        self.save_manager,self.save_data=manager,data
        self.actions=[
            ("MERCADO SILENCIOSO",lambda:self.open_management("shop")),
            ("MOCHILA / BARALHO",lambda:self.open_management("backpack")),
            ("ALTAR DE APRIMORAMENTO",lambda:self.open_management("workshop")),
            ("RETOMAR / INICIAR SLIME",self.fight),
            ("CONFIGURAÇÕES",self.open_options_modal),
            ("ATUALIZAR / ESCOLHER SLOT",self.slots),
            ("SOLICITAR PERSISTÊNCIA",self.persist_permission),
        ]
        self.rects=[pygame.Rect(530,300+i*90,860,66) for i in range(len(self.actions))]
        self.preparing=None
    def update(self,dt):
        if self.preparing:
            try:next(self.preparing)
            except StopIteration:
                self.preparing=None
                self.fight()
    def draw(self,surface):
        theme.backdrop(surface,self.asset_manager.background,opacity=210)
        a,p=self.asset_manager,self.save_data["progresso"]
        draw_text(surface,self.save_data["nome"],a.big_font,(240,210,150),960,100,center=True)
        draw_text(surface,f"Ouro {p['moedas']} · Revisão {self.save_data.get('revisao',0)} · {p['estado']}",
                  a.font,(240,210,150),960,190,center=True)
        for (label,_),rect in zip(self.actions,self.rects):
            theme.button(surface,rect,label,a.menu_font,hover=rect.collidepoint(self.window_manager.get_virtual_mouse_pos()))
        draw_text(surface,"Piloto de persistência · Campanha completa na Etapa 4",a.small_font,
                  (200,180,140),960,1020,center=True)
    def handle_event(self,event):
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            point=self.window_manager.map_to_virtual(event.pos)
            for (_,command),rect in zip(self.actions,self.rects):
                if rect.collidepoint(point):command();return
    def open_management(self,kind):
        if kind=="shop":
            from src.scenes.shop_scene import ShopScene as Scene
        elif kind=="backpack":
            from src.scenes.backpack_scene import BackpackScene as Scene
        else:
            from src.scenes.roguelite_scene import RogueliteScene as Scene
        options = {"preparation":True} if kind=="workshop" and self.save_data["progresso"]["estado"]!="ativa" else {}
        self.scene_manager.change_scene(Scene(self.scene_manager,self.window_manager,self.asset_manager,
                                             self.save_manager,self.save_data,**options))
    def slots(self):
        async def refresh():await self.save_manager.refresh()
        self.scene_manager.submit(refresh,lambda _:self.scene_manager.change_scene(
            WebSlots(self.scene_manager,self.window_manager,self.asset_manager,self.save_manager)))
    def persist_permission(self):
        self.scene_manager.submit(lambda:self.save_manager.browser_store.request("persist"),
            lambda granted:setattr(self.scene_manager,"storage_error",
                "Dados protegidos contra remoção automática." if granted else
                "O navegador não garantiu permanência. Mantenha um backup exportado."))
    def fight(self):
        if self.save_data["progresso"]["estado"]!="ativa":
            return self.open_management("workshop")
        snapshot=self.save_data["progresso"].get("combat_snapshot")
        if snapshot and snapshot["enemy"]["name"]!="Slime":
            self.scene_manager.storage_error="Este encontro pertence à campanha da Etapa 4; o snapshot foi preservado."
            return
        if not self.asset_manager.combat_ready:
            if self.preparing is None:self.preparing=self.asset_manager.prepare_combat()
            return
        self.scene_manager.change_scene(PersistentBattle(self.scene_manager,self.window_manager,
                                         self.asset_manager,self.save_manager,self.save_data))


class PersistentBattle(ProofBattle):
    def __init__(self,scenes,window,assets,manager,data):
        super().__init__(scenes,window,assets)
        self.save_manager,self.save_data=manager,data
        from src.systems.territory_map import by_level,ROAD_FIGHTS
        p=data["progresso"]
        snapshot=p.get("combat_snapshot")
        self.engine.map_mode=True
        self.engine.encounter_kind="road"
        self.engine.encounter_index=snapshot["index"] if snapshot else min(
            p["encontros_por_territorio"].get(by_level(1).id,0),ROAD_FIGHTS-1)
        manager.apply_to_game(data,self.engine.player,self.engine.deck_manager)
        self.engine.run_progress=p
        self.engine.owned_card_names=set(p["cartas_colecao"])
        self.engine.start_combat()
        from src.systems.territory_map import encounter_status
        self.engine.is_replay=encounter_status(data,by_level(1).id,self.engine.encounter_index)=="completed"
        if snapshot:
            from src.systems.combat_snapshot import restore
            restore(self.engine,snapshot)
        else:
            self.engine.is_replay=p["encontros_por_territorio"].get(by_level(1).id,0)>=ROAD_FIGHTS
        self._saved_signature=None
        self._confirmed_snapshot=deepcopy(snapshot)
        self.request_checkpoint()
    def request_checkpoint(self):
        if self.scene_manager.saving:return
        from src.systems.combat_snapshot import capture,restore
        signature={"state":"game_over"} if self.engine.state=="game_over" else capture(self.engine,include_random=False)
        if signature==self._saved_signature:return
        if self.engine.state in ("phase_complete","boss_transition"):return
        snapshot=None if self.engine.state=="game_over" else capture(self.engine)
        def command(manager,data):
            if snapshot is None:return manager.end_run(data,self.engine.level)
            manager.update_from_game(data,self.engine.player,self.engine.deck_manager)
            data["progresso"]["combat_snapshot"]=snapshot
            data["progresso"]["retomada_legada"]=False
            manager.save(data)
            return True,"Checkpoint confirmado."
        def complete(result):
            if not result[0]:
                return failed(SaveError(result[1]))
            self._saved_signature=signature
            self._confirmed_snapshot=deepcopy(snapshot)
            self.engine.run_progress=self.save_data["progresso"]
        def failed(error):
            if self._confirmed_snapshot:
                restore(self.engine,self._confirmed_snapshot)
                from src.ui.entity_view import EntityView
                self.entity_view=EntityView(self.asset_manager)
                self._outcome_elapsed=None
            self.engine.show_message("Falha ao salvar; ação revertida. "+str(error),6000)
            self.scene_manager.storage_error=str(error)
        self.scene_manager.submit(lambda:self.save_manager.run(self.save_data,command),complete,failed)
    def update(self,dt):
        super().update(dt)
        self.request_checkpoint()
    def _reward_progress(self):
        return self.save_data["progresso"]
    def _commit_reward(self,choice):
        from src.systems.combat_snapshot import capture,restore
        from src.systems.campaign_progress import record_road_victory
        original=capture(self.engine)
        def command(manager,data):
            # A cópia do motor impede publicar recompensa antes da confirmação.
            from src.systems.combat_engine import CombatEngine
            engine=CombatEngine(map_mode=True)
            restore(engine,original)
            engine.run_progress=data["progresso"]
            engine.encounter_kind="road"
            engine.encounter_index=original["index"]
            kind,value=choice
            if kind=="card":engine.choose_reward(value)
            elif kind=="material":engine.choose_material(value)
            else:engine.skip_reward()
            record_road_victory(manager,data,engine,lambda:None)
            return True,"Recompensa confirmada."
        def complete(result):
            if result[0]:self.scene_manager.management_home(self.save_manager,self.save_data)
            else:self.scene_manager.storage_error=result[1]
        self.persist_command(command,complete)
    def handle_event(self,event):
        if self._victory_ready:
            return BattleScene.handle_event(self,event)
        if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
            self.scene_manager.management_home(self.save_manager,self.save_data);return
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            if self.menu_button_rect.collidepoint(self.window_manager.map_to_virtual(event.pos)):
                self.scene_manager.management_home(self.save_manager,self.save_data);return
        if self.engine.state=="game_over":
            if event.type==pygame.KEYDOWN and event.key==pygame.K_r:
                self.scene_manager.management_home(self.save_manager,self.save_data)
            return
        super().handle_event(event)
    def save_on_exit(self):
        self.request_checkpoint()
        return not self.scene_manager.saving


class StorageUnavailable(BaseScene):
    def __init__(self,scenes,window,assets,error,retry):
        super().__init__(scenes,window,assets)
        self.error,self.retry=error,retry
    def update(self,dt):pass
    def draw(self,surface):
        surface.fill((9,16,13))
        draw_text(surface,"ARMAZENAMENTO INDISPONÍVEL",self.asset_manager.menu_font,(240,190,140),960,350,center=True)
        draw_text(surface,self.error[:105],self.asset_manager.small_font,(240,190,140),960,450,center=True)
        draw_text(surface,"Habilite o armazenamento e clique para tentar novamente.",self.asset_manager.font,(240,190,140),960,550,center=True)
    def handle_event(self,event):
        if event.type==pygame.MOUSEBUTTONDOWN:self.retry()


async def main():
    pygame.display.init();pygame.font.init()
    import platform
    platform.window.config.user_canvas_managed=1
    service=get_platform()
    window=create_window_manager(platform_service=service)
    assets=ProofAssets()
    store=BrowserStore()
    preferences=GamePreferences(store=store)
    audio=AudioManager(music_volume=MUSIC_VOLUME,defer_initialization=True)
    from desktop_entry import configure_audio
    configure_audio(audio);preferences.apply(audio)
    scenes=SceneManager(audio_manager=audio,audio_preferences=preferences,platform_service=service)
    def install(_):
        scenes.save_manager=BrowserSaveManager(store)
        scenes.management_home=lambda manager,data:scenes.change_scene(PersistenceHub(scenes,window,assets,manager,data))
        scenes.home_factory=lambda:PersistentMenu(scenes,window,assets)
        scenes.change_scene(scenes.home_factory())
        if store.preference_error:scenes.storage_error=store.preference_error
    def unavailable(error):
        scenes.change_scene(StorageUnavailable(scenes,window,assets,str(error),
            lambda:scenes.submit(lambda:store.open(),install,unavailable)))
    try:
        await store.open();install(None)
    except Exception as error:unavailable(error)
    app=Application(window,assets,audio,preferences,scenes)
    def observe(application):
        if application.frames%5 and application._active:return
        scene=scenes.current_scene
        data=getattr(scene,"save_data",None)
        engine=getattr(scene,"engine",None)
        report=dict(scene=type(scene).__name__,saving=scenes.saving,error=scenes.storage_error,
                    frames=application.frames,active=application._active,
                    data=data,preferences=preferences.values)
        report["modal"]=type(scenes.modal_stack[-1]).__name__ if scenes.modal_stack else None
        target=scenes.modal_stack[-1] if scenes.modal_stack else scene
        report["ui"]={key:list(value) for key,value in vars(target).items() if isinstance(value,pygame.Rect)}
        report["rect_maps"]={key:{str(k):list(v) for k,v in value.items()}
            for key,value in vars(scene).items() if isinstance(value,dict) and value and
            all(isinstance(v,pygame.Rect) for v in value.values())}
        if hasattr(scene,"draft_slots"):report["draft_slots"]=scene.draft_slots
        report["message"]=str(getattr(scene,"message",getattr(scene,"notice",getattr(scene,"error",""))))
        if engine:
            report.update(victory_ready=scene._victory_ready,state=engine.state,player_hp=engine.player.hp,enemy_hp=engine.enemy.hp,energy=engine.energy,
                action=scene.entity_view.player_action,
                hand=[dict(name=c.name,cost=c.cost,rect=list(rect)) for c,rect in
                      zip(engine.hand,scene._get_battle_hand_rects())])
        if engine:
            report["reward_offers"]=[dict(kind=option[0],value=option[1],rect=list(rect))
                for option,rect in scene.reward_view.offers(engine,scene._reward_progress())]
        if getattr(scene,"management_guide",None):
            report["guide"]=dict(active=scene.management_guide.active,key=scene.management_guide.key)
        platform.window.webStorageMetrics=json.dumps(report,ensure_ascii=True)
    try:await app.run_web(observe)
    finally:audio.shutdown();pygame.quit()

