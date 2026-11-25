"""Isolamento desktop/web e invariantes de desenho, sem slots reais."""
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pygame
from src.platforms.capabilities import detect_capabilities
from src.platforms.desktop import DesktopPlatform
from src.platforms.web import WebPlatform
from src.core.window import WindowManager, create_window_manager
from src.core.web_window import WebWindowManager
from src.core.scene_manager import SceneManager
from src.core.application import Application
from src.scenes.menu_scene import MenuScene
from src.ui.render_cache import blit_actor, scaled_image, RenderCache


class CapabilityTests(TestCase):
    def test_detects_wasm_and_native_without_guessing_from_screen_size(self):
        self.assertTrue(detect_capabilities("emscripten").is_web)
        self.assertFalse(detect_capabilities("win32").is_web)
        self.assertTrue(detect_capabilities("linux").persistent_storage)
        self.assertTrue(detect_capabilities("emscripten").persistent_storage)

    def test_runtime_detection(self):
        with patch.object(sys, "platform", "emscripten"):
            self.assertTrue(detect_capabilities().cooperative_loop)

    def test_desktop_resources_preserve_meipass(self):
        service=DesktopPlatform("source")
        with patch.object(sys,"_MEIPASS","bundle",create=True):
            self.assertEqual(service.resource_path("assets","x.png"),os.path.join("bundle","assets","x.png"))

    def test_desktop_writable_data_never_use_meipass(self):
        service=DesktopPlatform("source")
        with patch.object(sys,"frozen",True,create=True), patch.object(sys,"_MEIPASS","bundle",create=True), patch.dict(os.environ,{"LOCALAPPDATA":"user-data"}):
            self.assertEqual(service.user_data_path("saves"),os.path.join("user-data","ScapeFromStoneDeCut","saves"))

    def test_unfrozen_data_stay_in_project(self):
        with patch.object(sys,"frozen",False,create=True):
            self.assertEqual(DesktopPlatform("source").user_data_path("saves"),os.path.join("source","saves"))

    def test_web_paths_are_posix_and_temporary_without_claiming_persistence(self):
        service=WebPlatform("/app")
        self.assertEqual(service.resource_path("assets","a.png"),"/app/assets/a.png")
        self.assertEqual(service.user_data_path("saves"),"/tmp/scape-from-stone-session/saves")
        self.assertTrue(service.capabilities.persistent_storage)

    def test_web_bridge_reports_visibility_and_resume_generation(self):
        bridge=MagicMock()
        bridge.snapshot.return_value=json.dumps(dict(active=False,resume=3))
        self.assertEqual(WebPlatform(bridge=bridge).lifecycle_state(),(False,3))

    def test_desktop_exit_is_a_request_not_system_exit(self):
        scenes=SceneManager(platform_service=DesktopPlatform())
        menu=MenuScene.__new__(MenuScene)
        menu.scene_manager=scenes
        menu.window_manager=MagicMock()
        menu.window_manager.handle_window_event.return_value=False
        menu.play_ui_sound=MagicMock()
        menu.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
        self.assertTrue(scenes.exit_requested)

    def test_web_exit_returns_home_without_ending_interpreter(self):
        home=object()
        scenes=SceneManager(platform_service=WebPlatform(),home_factory=lambda:home)
        scenes.request_exit()
        self.assertIs(scenes.current_scene,home)
        self.assertFalse(scenes.exit_requested)

    def test_hidden_loop_does_not_advance_and_resume_discards_elapsed_time(self):
        service=MagicMock()
        service.lifecycle_state.side_effect=[(False,0),(True,1),(True,1)]
        scenes=SimpleNamespace(platform=service,exit_requested=False,
                               update=MagicMock(),draw=MagicMock(),handle_event=MagicMock())
        window,assets,audio,preferences,clock=[MagicMock() for _ in range(5)]
        clock.tick.side_effect=[5000,5000,16]
        preferences.get.return_value=False
        app=Application(window,assets,audio,preferences,scenes,clock)
        with patch("pygame.event.get",return_value=[]),patch("pygame.event.clear") as clear:
            app.frame(web=True)
            scenes.update.assert_not_called()
            app.frame(web=True)
            scenes.update.assert_called_once_with(0)
            clear.assert_called_once()
            app.frame(web=True)
            self.assertEqual(scenes.update.call_args.args,(16,))
        self.assertEqual(audio.set_suspended.call_args_list[0].args,(True,))


class WindowAndRenderTests(TestCase):
    def setUp(self):
        pygame.display.init()
        pygame.display.set_mode((1280,720))

    def tearDown(self):
        pygame.display.quit()

    def test_web_window_never_queries_monitor_and_preserves_mapping(self):
        with patch("pygame.display.get_desktop_sizes",side_effect=AssertionError("monitor nativo")):
            window=create_window_manager(platform_service=WebPlatform(bridge=MagicMock()))
        self.assertIsInstance(window,WebWindowManager)
        self.assertEqual(window.map_to_virtual((640,360)),(960,540))
        self.assertEqual(window.virtual_screen.get_size(),(1920,1080))

    def test_desktop_factory_keeps_original_controller(self):
        window=create_window_manager(platform_service=DesktopPlatform())
        self.assertIsInstance(window,WindowManager)
        self.assertEqual(window.windowed_size,(1280,720))

    def test_web_fullscreen_uses_browser_service(self):
        bridge=MagicMock()
        window=create_window_manager(platform_service=WebPlatform(bridge=bridge))
        window.toggle_fullscreen()
        bridge.toggleFullscreen.assert_called_once()
        self.assertTrue(window.handle_window_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F10)))

    def test_destination_surface_is_reused(self):
        cache=RenderCache()
        ref=pygame.Surface((100,100))
        self.assertIs(cache.target((40,40),ref),cache.target((40,40),ref))

    def test_card_scale_cache_preserves_original_smoothscale_pixels(self):
        source=pygame.Surface((30,40),pygame.SRCALPHA)
        pygame.draw.circle(source,(170,80,30,180),(15,20),12)
        first=scaled_image(source,(13,19))
        self.assertIs(first,scaled_image(source,(13,19)))
        expected=pygame.transform.smoothscale(source,(13,19))
        self.assertEqual(pygame.image.tobytes(first,"RGBA"),pygame.image.tobytes(expected,"RGBA"))

    def test_cropped_blit_is_pixel_identical_for_alpha_and_premultiplied(self):
        frame=pygame.Surface((90,90),pygame.SRCALPHA)
        pygame.draw.circle(frame,(190,70,20,160),(45,45),12)
        for flags, source in ((0,frame),(pygame.BLEND_PREMULTIPLIED,frame.premul_alpha())):
            actual=pygame.Surface((120,120)).convert()
            actual.fill((30,60,90))
            expected=actual.copy()
            rect=source.get_rect(topleft=(12,16))
            expected.blit(source,rect,special_flags=flags)
            blit_actor(actual,source,rect,flags)
            self.assertEqual(pygame.image.tobytes(actual,"RGBA"),pygame.image.tobytes(expected,"RGBA"))



class CompositionAndAudioTests(TestCase):
    def test_audio_suspend_resume_is_idempotent(self):
        from src.core.audio_manager import AudioManager
        audio=AudioManager(defer_initialization=True)
        audio._audio_locked=False
        audio._mixer_available=True
        with patch("pygame.mixer.get_init",return_value=(44100,-16,2)), patch("pygame.mixer.pause") as pause, patch("pygame.mixer.unpause") as unpause, patch("pygame.mixer.music.pause") as music_pause, patch("pygame.mixer.music.unpause") as music_unpause:
            audio.set_suspended(True)
            audio.set_suspended(True)
            audio.set_suspended(False)
            audio.set_suspended(False)
        for operation in (pause,unpause,music_pause,music_unpause):
            operation.assert_called_once()

    def test_web_tray_preserves_pixels_during_supported_combat_actions(self):
        from web.poc import ProofAssets, ProofBattle, SessionPreferences
        from src.scenes.battle_scene import BattleScene
        pygame.init()
        try:
            window=WindowManager()
            assets=ProofAssets()
            list(assets.prepare_combat())
            scenes=SceneManager(audio_preferences=SessionPreferences())
            battle=ProofBattle(scenes,window,assets)
            actual=pygame.Surface((1920,1080))
            expected=actual.copy()
            for action in (None,"Soco Simples","Esfera Protetora"):
                if action:
                    battle.entity_view.trigger_player_action(action)
                    battle.entity_view.update(200)
                battle.draw(actual)
                with patch.object(battle,"_draw_bottom_hud",side_effect=lambda surface:BattleScene._draw_bottom_hud(battle,surface)):
                    battle.draw(expected)
                self.assertEqual(pygame.image.tobytes(actual,"RGBA"),pygame.image.tobytes(expected,"RGBA"),action)
        finally:
            pygame.quit()
