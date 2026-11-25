"""Contratos da campanha web, recursos por contexto e entrada unificada."""
import json
from pathlib import Path
import unittest
from unittest.mock import Mock
import pygame
from src.systems.web_resources import owner,context_groups
from src.core.input_router import InputRouter
from src.ui.inspection_controller import InspectionController

class ContextManifestTests(unittest.TestCase):
    def test_menu_does_not_depend_on_campaign(self):
        self.assertEqual(context_groups("menu"),{"menu"})
        self.assertEqual(owner("assets/fonts/IgarapePixel-Regular.ttf"),"menu")
        self.assertNotEqual(owner("assets/bosses/sheets_eight/corpo_seco/idle.png"),"menu")
    def test_boss_phases_share_one_context(self):
        self.assertEqual(owner("assets/bosses/twelve_frames/alvaro_tex_phase2/atk1_1.png"),"enemy:alvaro_tex")
        self.assertEqual(owner("assets/boss_ultimate_effects/twelve_frames/zanzara/effect_1.png"),"enemy:zanzara")
    def test_common_defeat_has_same_owner_as_animated_poses(self):
        self.assertEqual(owner("assets/enemies/defeat/slime.png"),
                         owner("assets/enemies/eight_frames/slime/idle_1.png"))
    def test_cutscenes_have_distinct_contexts(self):
        self.assertEqual(owner("assets/cutscenes/intro_01.png"),"cutscene:intro")
        self.assertEqual(owner("assets/cutscenes/pos_tutorial.png"),"cutscene:post")
        self.assertEqual(owner("assets/cutscenes/final_01.png"),"cutscene:final")
    def test_battle_loads_only_requested_enemy_groups(self):
        groups=context_groups("battle",5,["corpo_seco"])
        self.assertIn("enemy:corpo_seco",groups)
        self.assertNotIn("enemy:zanzara",groups)
        self.assertIn("player",groups)
        self.assertIn("territory:5",groups)
    def test_outside_assets_and_traversal_rejected(self):
        for name in ("saves/slot_1.json","assets/../saves/a.json"):
            with self.assertRaises(ValueError):owner(name)
    def test_complete_active_resource_inventory_has_one_owner(self):
        root=Path(__file__).resolve().parents[1]/"assets"
        resources=[p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in
                   (".png",".jpg",".jpeg",".ogg",".wav",".ttf",".json")]
        self.assertGreater(len(resources),2000)
        for path in resources:
            self.assertTrue(owner("assets/"+path.relative_to(root).as_posix()))
    def test_native_loaders_default_to_all_characters(self):
        import inspect
        from src.core.asset_manager import AssetManager
        for name in ("_load_common_eight_frames","_load_boss_eight_frame_sprites","_load_boss_ultimate_sprites"):
            self.assertIsNone(inspect.signature(getattr(AssetManager,name)).parameters["names"].default)

class InputRouterTests(unittest.TestCase):
    def setUp(self):
        self.window=Mock()
        self.window.map_to_virtual.return_value=(300,200)
        self.window.get_virtual_mouse_pos.return_value=(400,250)
        self.router=InputRouter(self.window)
    def test_mouse_uses_virtual_position_and_preserves_original_event(self):
        event=pygame.event.Event(pygame.MOUSEBUTTONDOWN,pos=(200,100),button=1)
        receiver=Mock()
        self.router.dispatch(event,receiver)
        self.assertEqual(self.router.last.position,(300,200))
        receiver.assert_called_once_with(event)
        self.assertEqual(event.pos,(200,100))
    def test_wheel_preserves_both_axes(self):
        result=self.router.route(pygame.event.Event(pygame.MOUSEWHEEL,x=1,y=-2))
        self.assertEqual(result.wheel,(1,-2))
        self.assertEqual(result.position,(400,250))
    def test_keyboard_keeps_escape_and_browser_fullscreen_shortcuts(self):
        for key in (pygame.K_ESCAPE,pygame.K_F11,pygame.K_c):
            self.assertEqual(self.router.route(pygame.event.Event(pygame.KEYDOWN,key=key)).key,key)

class InspectionTests(unittest.TestCase):
    def test_hover_finds_first_target_and_clears_outside(self):
        inspect=InspectionController()
        targets=[("card",pygame.Rect(20,20,100,200))]
        self.assertEqual(inspect.hover(targets,(40,60)),"card")
        self.assertIsNone(inspect.hover(targets,(400,60)))
    def test_pinned_inspection_is_independent_of_hover_until_explicit_clear(self):
        inspect=InspectionController()
        inspect.inspect("card",pinned=True)
        self.assertEqual(inspect.hover([],(-10,-10)),"card")
        inspect.clear()
        self.assertFalse(inspect.pinned)
        self.assertIsNone(inspect.target)
    def test_repeated_hover_does_not_invalidate_generation(self):
        inspect=InspectionController()
        inspect.inspect("same")
        generation=inspect.generation
        inspect.inspect("same")
        self.assertEqual(inspect.generation,generation)
    def test_preview_is_bounded_for_landscape_and_small_viewport(self):
        for viewport in ((0,0,1920,1080),(0,0,800,450)):
            rect=InspectionController.bounded_preview((440,519),viewport,(1900,1000))
            self.assertTrue(pygame.Rect(viewport).contains(rect))



class ContextMemoryTests(unittest.TestCase):
    def test_shared_files_reused_but_previous_enemy_is_not_retained(self):
        from src.systems.web_resources import working_set
        resident={"menu","management","player","audio","enemy:zanzara","territory:7"}
        desired={"menu","management"}
        self.assertEqual(working_set("map",desired,resident),
                         {"menu","management","player","audio"})
        self.assertEqual(working_set("menu",{"menu"},resident),{"menu"})


class CompositionPixelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.display.init()
        pygame.display.set_mode((1,1))
    def test_backdrop_is_pixel_identical_after_cached_draw(self):
        from src.ui.composition_cache import CompositionCache
        cache=CompositionCache()
        expected=pygame.Surface((180,120)).convert()
        def draw(surface):
            surface.fill((44,51,33))
            layer=pygame.Surface(surface.get_size(),pygame.SRCALPHA)
            layer.fill((5,13,9,183));surface.blit(layer,(0,0))
        draw(expected)
        actual=pygame.Surface(expected.get_size()).convert()
        cache.backdrop(actual,"same",draw)
        actual.fill((255,0,0))
        cache.backdrop(actual,"same",draw)
        self.assertEqual(pygame.image.tobytes(actual,"RGB"),pygame.image.tobytes(expected,"RGB"))
    def test_cached_panel_matches_native_over_changing_underlay_and_overlap(self):
        from src.ui.composition_cache import CompositionCache
        from src.ui import dark_fantasy_theme as theme
        cache=CompositionCache()
        for color in ((30,50,40),(80,20,18)):
            expected=pygame.Surface((220,180)).convert();expected.fill(color)
            actual=expected.copy()
            draw=lambda s,r,selected:theme.panel(s,r,highlighted=selected,fill=(5,13,10,172))
            for rect in ((10,10,150,100),(40,40,160,120)):
                draw(expected,rect,False)
                cache.panel(actual,rect,False,draw)
            self.assertEqual(pygame.image.tobytes(actual,"RGB"),pygame.image.tobytes(expected,"RGB"))
    def test_sparse_frame_matches_complete_alpha_blit(self):
        from src.ui.composition_cache import CompositionCache
        cache=CompositionCache()
        image=pygame.Surface((160,200),pygame.SRCALPHA)
        pygame.draw.rect(image,(187,145,60,180),image.get_rect(),12)
        expected=pygame.Surface((220,240)).convert();expected.fill((20,40,30))
        actual=expected.copy()
        expected.blit(image,(15,10))
        cache.sparse_blit(actual,image,(15,10))
        self.assertEqual(pygame.image.tobytes(actual,"RGB"),pygame.image.tobytes(expected,"RGB"))
    def test_filled_frame_keeps_center_pixels(self):
        from src.ui.composition_cache import CompositionCache
        image=pygame.Surface((160,200),pygame.SRCALPHA);image.fill((180,120,40,170))
        expected=pygame.Surface((220,240)).convert();expected.fill((20,40,30))
        actual=expected.copy()
        expected.blit(image,(15,10))
        CompositionCache().sparse_blit(actual,image,(15,10))
        self.assertEqual(pygame.image.tobytes(actual,"RGB"),pygame.image.tobytes(expected,"RGB"))
    def test_memory_bound_is_enforced(self):
        from src.ui.composition_cache import CompositionCache
        cache=CompositionCache(limit=20000)
        surface=pygame.Surface((50,50)).convert()
        for i in range(12):cache.backdrop(surface,i,lambda s:s.fill((i,1,1)))
        self.assertLessEqual(cache.bytes,20000)


    def test_root_panel_cache_preserves_overlapping_previews(self):
        from src.ui.composition_cache import CompositionCache
        from src.ui import dark_fantasy_theme as theme
        cache=CompositionCache()
        draw=lambda s,r,selected:theme.panel(s,r,highlighted=selected,fill=(5,13,10,172))
        for frame in range(3):
            expected=pygame.Surface((220,180)).convert();expected.fill((20,40,35))
            actual=expected.copy()
            cache.begin_frame()
            for rect in ((10,10,150,100),(40,40,160,120)):
                draw(expected,rect,False)
                cache.root_panel(actual,rect,False,draw)
            self.assertEqual(pygame.image.tobytes(actual,"RGB"),pygame.image.tobytes(expected,"RGB"))



class FinalCampaignTransactionTests(unittest.TestCase):
    def fixture(self,folder):
        from types import SimpleNamespace
        from src.systems.save_manager import SaveManager
        from src.systems.territory_map import TERRITORIES
        from src.systems.combat_engine import CombatEngine
        manager=SaveManager(folder);data=manager.create_save("slot_1")
        p=data["progresso"]
        p["territorios_desbloqueados"]=[t.id for t in TERRITORIES]
        p["territorios_concluidos"]=[t.id for t in TERRITORIES[:-1]]
        p["encontros_por_territorio"]={t.id:2 for t in TERRITORIES}
        manager.save(data)
        engine=CombatEngine(map_mode=True)
        engine.resume_from_save(data,manager,level=7,encounter_kind="point",encounter_index=None)
        engine.enemy.hp=0;engine.state="victory";engine.finish_map_phase()
        scenes=Mock();scenes.saving=False
        owner=SimpleNamespace(engine=engine,save_data=data,scene_manager=scenes)
        owner.persist_command=lambda command,complete:complete(command(manager,data))
        return owner,manager,data
    def test_final_phase_commits_run_before_opening_epilogue(self):
        from tempfile import TemporaryDirectory
        from web.campaign import CampaignBattle
        with TemporaryDirectory() as folder:
            owner,manager,data=self.fixture(folder)
            CampaignBattle._finalize_map_phase(owner,7)
            loaded=manager.load_save("slot_1")
            self.assertEqual(loaded["run"]["estado"],"concluida")
            self.assertEqual(loaded["perfil"]["campanhas_concluidas"],1)
            self.assertIsNone(loaded["run"]["combat_snapshot"])
            owner.scene_manager.open_cutscene.assert_called_once()
    def test_failed_final_commit_does_not_open_epilogue(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from web.campaign import CampaignBattle
        with TemporaryDirectory() as folder:
            owner,manager,data=self.fixture(folder)
            with patch("src.storage.disk_store.os.replace",side_effect=OSError("quota")):
                with self.assertRaises(OSError):CampaignBattle._finalize_map_phase(owner,7)
            self.assertEqual(data["run"]["estado"],"ativa")
            self.assertEqual(data["perfil"]["campanhas_concluidas"],0)
            owner.scene_manager.open_cutscene.assert_not_called()


class RealShopPixelTests(unittest.TestCase):
    def test_web_composition_matches_real_shop_including_hover_preview(self):
        from tempfile import TemporaryDirectory
        from src.core.asset_manager import AssetManager
        from src.scenes.shop_scene import ShopScene
        from src.systems.save_manager import SaveManager
        from src.ui.composition_cache import optimize_visuals
        pygame.font.init()
        pygame.display.init();pygame.display.set_mode((1,1))
        assets=AssetManager(preload=False)
        window=Mock()
        scenes=Mock()
        with TemporaryDirectory() as folder:
            manager=SaveManager(folder);data=manager.create_save("slot_1")
            for mouse in ((5,5),(700,500)):
                window.get_virtual_mouse_pos.return_value=mouse
                normal=ShopScene(scenes,window,assets,manager,data)
                cached=ShopScene(scenes,window,assets,manager,data)
                normal.management_guide.active=cached.management_guide.active=False
                expected=pygame.Surface((1920,1080)).convert()
                normal.draw(expected)
                optimize_visuals(cached.visuals)
                for _ in range(2):
                    actual=pygame.Surface((1920,1080)).convert()
                    cached.draw(actual)
                    self.assertEqual(pygame.image.tobytes(actual,"RGB"),pygame.image.tobytes(expected,"RGB"))



class SnapshotContextTests(unittest.TestCase):
    def test_temporary_engine_restores_territory_kind_and_index(self):
        from src.systems.combat_engine import CombatEngine
        from src.systems.combat_snapshot import capture,restore
        original=CombatEngine(map_mode=True)
        original.level=7;original.encounter_kind="road";original.encounter_index=1
        temporary=CombatEngine(map_mode=True)
        restore(temporary,capture(original))
        self.assertEqual((temporary.level,temporary.encounter_kind,temporary.encounter_index),(7,"road",1))



class ContextReachabilityTests(unittest.TestCase):
    def test_dual_boss_intent_cards_share_loaded_boss_context(self):
        for phase in (1,2):
            self.assertEqual(owner(f"assets/intent_art/alvaro_tex_phase{phase}/atk1.png"),"enemy:alvaro_tex")
    def test_all_enemy_resource_groups_are_reachable_by_registered_kits(self):
        from src.systems.common_animation_kits import COMMON_KITS
        from src.systems.web_resources import BOSS_SLUGS
        known={"enemy:"+item[0] for item in COMMON_KITS.values()} | {"enemy:"+s for s in BOSS_SLUGS}
        root=Path(__file__).resolve().parents[1]/"assets"
        actual={owner("assets/"+p.relative_to(root).as_posix()) for p in root.rglob("*")
                if p.is_file() and p.suffix.lower() in (".png",".ogg",".json",".ttf",".wav",".jpg",".jpeg")}
        self.assertFalse({group for group in actual if group.startswith("enemy:")}-known)



class ContextCacheReleaseTests(unittest.TestCase):
    def test_leaving_context_releases_pose_and_support_lru_references(self):
        from src.ui.pose_playback import pose_mask
        from src.ui.enemy_reactions import _support_cached
        from src.ui.render_cache import clear_context_caches
        frame=pygame.Surface((32,64),pygame.SRCALPHA)
        frame.fill((100,90,70,255))
        pose_mask(frame);_support_cached(frame)
        self.assertGreater(pose_mask.cache_info().currsize,0)
        self.assertGreater(_support_cached.cache_info().currsize,0)
        clear_context_caches()
        self.assertEqual(pose_mask.cache_info().currsize,0)
        self.assertEqual(_support_cached.cache_info().currsize,0)

