"""Contratos de densidade e mix exclusivos da Web, sem modificar o Desktop."""
import json
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch, MagicMock
import pygame
from src.core.web_window import backing_size, WebWindowManager
from src.core.audio_manager import AudioManager, prepare_web_audio, WEB_MIXER


class WebDensityTests(TestCase):
    def test_windows_fractional_dpi_uses_physical_pixels(self):
        self.assertEqual(backing_size(1280,720,1.25),(1600,900))
        self.assertEqual(backing_size(1280,720,1.5),(1920,1080))

    def test_mobile_density_is_capped_at_two_and_native_art(self):
        self.assertEqual(backing_size(800,450,3),(1600,900))
        self.assertEqual(backing_size(3840,2160,2),(1920,1080))

    def test_invalid_viewport_is_rejected(self):
        for value in (0,-1,float("nan"),float("inf")):
            with self.assertRaises(ValueError):
                backing_size(value,720,1)

    def test_present_resizes_once_and_maps_the_physical_center(self):
        pygame.display.init()
        try:
            viewport=dict(width=1280,height=720,dpr=1.25)
            service=SimpleNamespace(render_viewport=lambda:viewport)
            window=WebWindowManager(platform_service=service)
            window.present()
            self.assertEqual(window.display_surface.get_size(),(1600,900))
            self.assertEqual(window.map_to_virtual((800,450)),(960,540))
            with patch("pygame.display.set_mode",side_effect=AssertionError("realocação por frame")):
                window.present()
            viewport["dpr"]=1.5
            window.present()
            self.assertEqual(window.display_surface.get_size(),(1920,1080))
        finally:
            pygame.display.quit()

    def test_native_resolution_is_blitted_without_downscale(self):
        pygame.display.init()
        try:
            service=SimpleNamespace(render_viewport=lambda:dict(width=1280,height=720,dpr=1.5))
            window=WebWindowManager(platform_service=service)
            window.screen.fill((32,64,128))
            pygame.draw.line(window.screen,(255,255,255),(100,0),(100,1079))
            with patch("pygame.transform.smoothscale",side_effect=AssertionError("redução intermediária")):
                window.present()
            self.assertEqual(pygame.image.tobytes(window.screen,"RGB"),
                             pygame.image.tobytes(window.display_surface,"RGB"))
        finally:
            pygame.display.quit()


class WebAudioTests(TestCase):
    def make_web_audio(self):
        with patch("src.core.audio_manager.sys.platform","emscripten"):
            return AudioManager(defer_initialization=True)

    def test_preinit_only_configures_web_and_does_not_unlock(self):
        with patch("pygame.mixer.pre_init") as pre, patch("pygame.mixer.init") as init:
            with patch("src.core.audio_manager.sys.platform","emscripten"):
                prepare_web_audio()
            pre.assert_called_once_with(**WEB_MIXER)
            init.assert_not_called()
            with patch("src.core.audio_manager.sys.platform","win32"):
                prepare_web_audio()
            self.assertEqual(pre.call_count,1)

    def test_unlock_initializes_explicit_format_once(self):
        audio=self.make_web_audio()
        state=[None]
        def initialize(**kwargs):state[0]=(44100,-16,2)
        with patch("pygame.mixer.get_init",side_effect=lambda:state[0]), patch("pygame.mixer.init",side_effect=initialize) as init, patch("pygame.mixer.set_num_channels") as channels:
            self.assertFalse(audio.available)
            self.assertTrue(audio.unlock_after_interaction())
            self.assertTrue(audio.unlock_after_interaction())
            init.assert_called_once_with(**WEB_MIXER)
            channels.assert_called_once_with(4)

    def test_web_mix_has_headroom_even_at_all_volumes_maximum(self):
        audio=self.make_web_audio()
        audio.music_volume=1
        sfx=audio._effective_sfx_volume("gameplay.player.attack",100)
        music=audio._effective_music_volume()
        self.assertAlmostEqual(sfx,0.16)
        self.assertAlmostEqual(music,0.25)
        self.assertLess(4*sfx+music,0.9)
        audio.set_master_volume(0)
        self.assertEqual(audio._effective_sfx_volume("ui.click",1),0)
        self.assertEqual(audio._effective_music_volume(),0)

    def test_volume_and_unlock_do_not_duplicate_music(self):
        audio=self.make_web_audio()
        with patch.object(audio,"_initialize_mixer"), patch.object(audio,"play_music",return_value=True) as play:
            audio._deferred_music=("music.ogg",-1,0.0,0)
            audio.unlock_after_interaction()
            audio.unlock_after_interaction()
            play.assert_called_once()
            audio.set_music_volume(1)
            self.assertEqual(play.call_count,1)

    def test_desktop_keeps_original_format_channels_and_gain(self):
        with patch("src.core.audio_manager.sys.platform","win32"):
            audio=AudioManager(defer_initialization=True)
        with patch("pygame.mixer.get_init",return_value=None), patch("pygame.mixer.init") as init, patch("pygame.mixer.set_num_channels") as channels:
            audio._initialize_mixer()
            init.assert_called_once_with()
            channels.assert_not_called()
        audio.music_volume=1
        self.assertEqual(audio._effective_sfx_volume("ui.click",1),1)
        self.assertEqual(audio._effective_music_volume(),1)
