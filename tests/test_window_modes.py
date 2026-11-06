"""Modos de janela: render Full HD, janela que cabe na tela, tela cheia e janela 1280x720."""
import os
import unittest
from unittest.mock import patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

from src.config.settings import WIDTH, HEIGHT, TITLE, LEGACY_WINDOW_SIZE
from src.core.window import WindowManager

F10 = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F10)
F11 = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F11)


def window_on_desktop(size, **kwargs):
    with patch("pygame.display.get_desktop_sizes", return_value=[size]):
        return WindowManager(WIDTH, HEIGHT, TITLE, **kwargs)


class ModeRecorder:
    """Registra os modos pedidos ao pygame (o driver dummy não reflete tela cheia)."""

    def __init__(self, testcase):
        self.calls = []
        real = pygame.display.set_mode

        def record(size=(0, 0), flags=0, *args, **kwargs):
            self.calls.append((tuple(size), flags))
            return real(size, flags, *args, **kwargs)

        patcher = patch("pygame.display.set_mode", side_effect=record)
        patcher.start()
        testcase.addCleanup(patcher.stop)

    @property
    def last(self):
        size, flags = self.calls[-1]
        return size, bool(flags & pygame.FULLSCREEN)


class TestWindowModes(unittest.TestCase):
    def setUp(self):
        pygame.init()

    def test_render_is_full_hd_and_window_fits_the_desktop(self):
        self.assertEqual((WIDTH, HEIGHT), (1920, 1080))
        cases = {(2560, 1440): (1920, 1080), (1920, 1080): (1600, 900), (1366, 768): (1169, 658)}
        for desktop, expected in cases.items():
            with self.subTest(desktop=desktop):
                wm = window_on_desktop(desktop)
                self.assertEqual(wm.virtual_screen.get_size(), (1920, 1080))
                self.assertEqual(wm.windowed_size, expected)
                self.assertEqual(wm.display_surface.get_size(), expected)

    def test_legacy_window_keeps_full_hd_render_and_maps_mouse(self):
        wm = window_on_desktop((1920, 1080), window_size=LEGACY_WINDOW_SIZE)
        self.assertEqual(wm.display_surface.get_size(), (1280, 720))
        self.assertEqual(wm.virtual_screen.get_size(), (1920, 1080))
        self.assertEqual(wm.map_to_virtual((640, 360)), (960, 540))
        self.assertEqual(wm.map_to_virtual((1280, 720)), (1920, 1080))
        wm.present()

    def test_f11_switches_fullscreen_and_back_to_the_same_window(self):
        wm = window_on_desktop((1920, 1080))
        window = wm.windowed_size
        modes = ModeRecorder(self)
        self.assertTrue(wm.handle_window_event(F11))
        self.assertTrue(wm.is_fullscreen)
        self.assertEqual(modes.last, ((0, 0), True))
        self.assertTrue(wm.handle_window_event(F11))
        self.assertFalse(wm.is_fullscreen)
        self.assertEqual(modes.last, (window, False))

    def test_resize_echo_after_leaving_fullscreen_does_not_restore_screen_size(self):
        wm = window_on_desktop((1920, 1080))
        window = wm.windowed_size
        modes = ModeRecorder(self)
        wm.handle_window_event(F11)
        wm.handle_window_event(F11)
        calls = len(modes.calls)
        # Eco que alguns sistemas enviam com o tamanho da tela cheia anterior.
        wm.handle_window_event(pygame.event.Event(pygame.VIDEORESIZE, w=1920, h=1080, size=(1920, 1080)))
        self.assertEqual(wm.windowed_size, window)
        self.assertEqual(len(modes.calls), calls)  # nenhum set_mode extra

    def test_user_resize_is_remembered_when_returning_from_fullscreen(self):
        wm = window_on_desktop((1920, 1080))
        modes = ModeRecorder(self)
        wm._mode_changed_at = -10_000
        wm.handle_window_event(pygame.event.Event(pygame.VIDEORESIZE, w=1400, h=800, size=(1400, 800)))
        self.assertEqual(wm.windowed_size, (1400, 800))
        wm.handle_window_event(F11)
        wm.handle_window_event(F11)
        self.assertEqual(modes.last, ((1400, 800), False))

    def test_f10_toggles_legacy_window_and_leaves_fullscreen(self):
        wm = window_on_desktop((2560, 1440))
        modes = ModeRecorder(self)
        self.assertTrue(wm.handle_window_event(F10))
        self.assertEqual(modes.last, (LEGACY_WINDOW_SIZE, False))
        self.assertTrue(wm.handle_window_event(F10))
        self.assertEqual(modes.last, ((1920, 1080), False))
        wm.handle_window_event(F11)
        self.assertTrue(wm.is_fullscreen)
        wm.handle_window_event(F10)
        self.assertFalse(wm.is_fullscreen)
        self.assertEqual(modes.last, (LEGACY_WINDOW_SIZE, False))


if __name__ == "__main__":
    unittest.main()
