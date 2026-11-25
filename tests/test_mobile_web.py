"""Contratos do modo compacto, confirmação touch e relógio suspenso."""
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
import pygame
from src.config.responsive_layout import resolve_layout,css_to_virtual
from src.core.active_timeline import ActiveTimeline
from src.core.input_router import InputRouter
from src.ui.inspection_controller import InspectionController
from src.config.visual_quality import set_compact_effects,particle_amount
from web.mobile import MobileInterface

class ResponsiveTests(unittest.TestCase):
    def test_desktop_never_enables_compact(self):
        self.assertFalse(resolve_layout(640,360,web=False,coarse=True).compact)
    def test_web_wide_is_unchanged(self):
        result=resolve_layout(1920,1080,web=True)
        self.assertFalse(result.compact)
        self.assertFalse(result.portrait_blocked)
    def test_android_landscape(self):
        result=resolve_layout(915,412,web=True,coarse=True)
        self.assertTrue(result.compact)
        self.assertFalse(result.portrait_blocked)
        self.assertEqual(result.min_target,44)
    def test_iphone_portrait_is_blocked(self):
        self.assertTrue(resolve_layout(390,844,web=True,coarse=True).portrait_blocked)
    def test_desktop_portrait_window_is_not_rotation_locked(self):
        self.assertFalse(resolve_layout(500,900,web=True).portrait_blocked)
    def test_safe_areas_reduce_useful_geometry(self):
        r=resolve_layout(1024,600,web=True,coarse=True,insets=(0,40,20,40))
        self.assertEqual((r.width,r.height),(944,580))
        self.assertTrue(r.compact)
    def test_exact_breakpoints(self):
        self.assertFalse(resolve_layout(1000,600,web=True).compact)
        self.assertTrue(resolve_layout(999,600,web=True).compact)
        self.assertTrue(resolve_layout(1000,599,web=True).compact)
    def test_point_mapping_accounts_for_canvas_offset(self):
        self.assertEqual(css_to_virtual((432,220),(10,25,844,390)),(960,540))
    def test_point_outside_canvas_is_rejected(self):
        self.assertIsNone(css_to_virtual((9,0),(10,25,844,390)))
        self.assertIsNone(css_to_virtual((10,25),(10,25,0,0)))

class TouchInspectionTests(unittest.TestCase):
    def test_touch_select_does_not_confirm_implicitly(self):
        c=InspectionController();c.touch_select("card")
        self.assertEqual(c.target,"card")
        self.assertTrue(c.pinned)
    def test_confirmation_is_consumed_only_once(self):
        c=InspectionController();c.touch_select("card")
        self.assertTrue(c.confirm("card"))
        self.assertFalse(c.confirm("card"))
    def test_wrong_or_stale_target_cannot_confirm(self):
        c=InspectionController();c.touch_select("card")
        self.assertFalse(c.confirm("other"))
        c.clear()
        self.assertFalse(c.confirm("card"))
    def test_hover_does_not_override_touch_selection(self):
        c=InspectionController();c.touch_select("card")
        self.assertEqual(c.hover([],(-1,-1)),"card")
    def test_normalized_sdl_touch_uses_virtual_dimensions(self):
        window=SimpleNamespace(width=1920,height=1080)
        r=InputRouter(window).route(pygame.event.Event(pygame.FINGERDOWN,x=.5,y=.25,finger_id=1))
        self.assertTrue(r.touch)
        self.assertEqual(r.position,(960,270))

class TimelineTests(unittest.TestCase):
    def test_pause_freezes_ticks(self):
        clock=Mock(return_value=100)
        t=ActiveTimeline(clock);t.set_active(False)
        clock.return_value=9100
        self.assertEqual(t.ticks(),100)
    def test_resume_excludes_elapsed_time_without_jump(self):
        clock=Mock(return_value=100);t=ActiveTimeline(clock);t.set_active(False)
        clock.return_value=9100;t.set_active(True)
        clock.return_value=9125
        self.assertEqual(t.ticks(),125)
    def test_repeated_pause_notifications_are_idempotent(self):
        clock=Mock(return_value=100);t=ActiveTimeline(clock);t.set_active(False)
        clock.return_value=200;t.set_active(False)
        clock.return_value=300;t.set_active(True)
        self.assertEqual(t.ticks(),100)
    def test_multiple_rotations_remain_monotonic(self):
        clock=Mock(return_value=0);t=ActiveTimeline(clock)
        for start in (100,200,300):
            clock.return_value=start;t.set_active(False)
            clock.return_value=start+50;t.set_active(True)
        self.assertEqual(t.ticks(),200)

class MobileCommandTests(unittest.TestCase):
    def setUp(self):
        self.bridge=Mock()
        self.bridge.viewport.return_value=json.dumps(dict(width=844,height=390,coarse=True,generation=1))
        self.bridge.drain.return_value="[]"
        self.scene=SimpleNamespace(dragging="music")
        self.scenes=SimpleNamespace(current_scene=self.scene,modal_stack=[],saving=False,
            window=Mock(),audio_manager=Mock())
        self.ui=MobileInterface(self.scenes,self.bridge)
        self.ui.poll()
    def tearDown(self):set_compact_effects(False)
    def test_duplicate_commands_execute_once(self):
        action=Mock()
        self.ui.callbacks={"buy":lambda _:action()}
        self.ui.epoch=3
        self.bridge.drain.return_value=json.dumps([dict(id="buy",epoch="3",generation=1)]*2)
        self.ui.poll()
        action.assert_called_once()
    def test_stale_epoch_does_not_execute(self):
        action=Mock();self.ui.callbacks={"buy":action}
        self.bridge.drain.return_value=json.dumps([dict(id="buy",epoch="old",generation=1)])
        self.ui.poll();action.assert_not_called()
    def test_pending_commit_blocks_actions(self):
        action=Mock();self.ui.callbacks={"buy":action};self.scenes.saving=True
        self.bridge.drain.return_value=json.dumps([dict(id="buy",epoch="0",generation=1)])
        self.ui.poll();action.assert_not_called()
    def test_rotation_clears_inspection_and_drag(self):
        self.ui.select("c","description",None)
        self.bridge.viewport.return_value=json.dumps(dict(width=390,height=844,coarse=True,generation=2))
        self.ui.poll()
        self.assertIsNone(self.ui.selection)
        self.assertIsNone(self.scene.dragging)
    def test_old_orientation_gesture_is_rejected(self):
        action=Mock();self.ui.callbacks={"buy":action}
        self.bridge.drain.return_value=json.dumps([dict(id="buy",epoch="0",generation=0)])
        self.ui.poll();action.assert_not_called()
    def test_compact_quality_reduces_particles_only(self):
        from src.config.visual_quality import begin_frame
        begin_frame()
        self.assertEqual(particle_amount(24),6)
        set_compact_effects(False)
        self.assertEqual(particle_amount(24),24)


class RealCompactSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.display.init();pygame.display.set_mode((1,1));pygame.font.init()
        from src.core.asset_manager import AssetManager
        cls.assets=AssetManager(preload=False)
    def setUp(self):
        from tempfile import TemporaryDirectory
        from src.systems.save_manager import SaveManager
        self.folder=TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.manager=SaveManager(self.folder.name);self.data=self.manager.create_save("slot_1")
        from tests.management_fixtures import guides_seen
        guides_seen(self.data);self.data["progresso"]["guia_mapa_visto"]=True
        self.window=Mock()
        self.scenes=Mock(current_scene=None,modal_stack=[],saving=False,storage_error="",assets=self.assets,window=self.window)
        self.bridge=Mock()
        self.ui=MobileInterface(self.scenes,self.bridge)
        self.ui.layout=resolve_layout(844,390,web=True,coarse=True)
    def publish(self,scene):
        self.scenes.current_scene=scene;self.ui.publish()
        return json.loads(self.bridge.publish.call_args.args[0])
    def test_map_uses_real_territory_titles(self):
        from src.scenes.map_scene import MapScene
        scene=MapScene(self.scenes,self.window,self.assets,self.manager,self.data)
        model=self.publish(scene)
        self.assertEqual(model["items"][0]["label"],"Stone de Cut")
        self.assertEqual(len(model["items"]),7)
    def test_shop_inspection_does_not_purchase(self):
        from src.scenes.shop_scene import ShopScene
        scene=ShopScene(self.scenes,self.window,self.assets,self.manager,self.data)
        model=self.publish(scene);before=self.data["progresso"]["moedas"]
        self.ui.callbacks[model["items"][0]["id"]](None)
        self.assertIsNotNone(self.ui.selection)
        self.assertEqual(self.data["progresso"]["moedas"],before)
        self.assertEqual(scene.PAGE_SIZE,2)
    def test_altar_exposes_both_level_art_variants(self):
        from src.scenes.roguelite_scene import RogueliteScene
        scene=RogueliteScene(self.scenes,self.window,self.assets,self.manager,self.data)
        model=self.publish(scene)
        self.ui.callbacks[model["items"][0]["id"]](None)
        self.assertEqual([v[0] for v in self.ui.selection["variants"]],["ANTES · LV1","DEPOIS · LV2"])
        self.assertNotEqual(self.ui.selection["variants"][0][1],self.ui.selection["variants"][1][1])
    def test_tablet_with_primary_touch_uses_safe_controls(self):
        self.assertTrue(resolve_layout(1280,800,web=True,coarse=True).compact)


class ParticleBudgetTests(unittest.TestCase):
    def test_compact_frame_budget_is_bounded_and_resets(self):
        from src.config.visual_quality import begin_frame
        set_compact_effects(True)
        try:
            begin_frame()
            self.assertEqual(sum(particle_amount(20) for _ in range(10)),24)
            begin_frame()
            self.assertEqual(particle_amount(20),6)
        finally:set_compact_effects(False)
