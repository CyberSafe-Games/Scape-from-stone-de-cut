"""Modo janela: Full HD por padrão e opção de janela na resolução antiga."""
import os
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

from src.config.settings import WIDTH, HEIGHT, TITLE, LEGACY_WINDOW_SIZE
from src.core.window import WindowManager


class TestWindowModes(unittest.TestCase):
    def setUp(self):
        pygame.init()

    def test_default_window_is_full_hd(self):
        wm = WindowManager(WIDTH, HEIGHT, TITLE)
        self.assertEqual((WIDTH, HEIGHT), (1920, 1080))
        self.assertEqual(wm.display_surface.get_size(), (1920, 1080))
        self.assertEqual(wm.virtual_screen.get_size(), (1920, 1080))

    def test_legacy_window_keeps_full_hd_render_and_maps_mouse(self):
        wm = WindowManager(WIDTH, HEIGHT, TITLE, window_size=LEGACY_WINDOW_SIZE)
        self.assertEqual(wm.display_surface.get_size(), (1280, 720))
        self.assertEqual(wm.virtual_screen.get_size(), (1920, 1080))
        self.assertEqual(wm.map_to_virtual((640, 360)), (960, 540))
        self.assertEqual(wm.map_to_virtual((1280, 720)), (1920, 1080))
        wm.present()

    def test_f10_toggles_between_full_hd_and_legacy_window(self):
        wm = WindowManager(WIDTH, HEIGHT, TITLE)
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F10)
        self.assertTrue(wm.handle_window_event(event))
        self.assertEqual(wm.display_surface.get_size(), LEGACY_WINDOW_SIZE)
        self.assertTrue(wm.handle_window_event(event))
        self.assertEqual(wm.display_surface.get_size(), (WIDTH, HEIGHT))

    def test_f10_leaves_fullscreen_into_legacy_window(self):
        wm = WindowManager(WIDTH, HEIGHT, TITLE)
        wm.is_fullscreen = True
        wm.toggle_legacy_window()
        self.assertFalse(wm.is_fullscreen)
        self.assertEqual(wm.display_surface.get_size(), LEGACY_WINDOW_SIZE)


if __name__ == "__main__":
    unittest.main()
