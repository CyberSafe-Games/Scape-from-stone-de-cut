"""A composição nativa usa menos pixels sem duplicar a arte da interface."""
import unittest
from unittest.mock import Mock
from types import SimpleNamespace
import pygame
from src.core.mobile_canvas import MobileCanvas,drawing_coordinates
from src.core.web_window import WebWindowManager
from src.config.responsive_layout import resolve_layout


class ReducedCanvasTests(unittest.TestCase):
    def setUp(self):pygame.display.init();pygame.display.set_mode((1280,720))
    def tearDown(self):pygame.display.quit()
    def test_physical_storage_is_720p_with_original_logical_coordinates(self):
        surface=MobileCanvas()
        self.assertEqual(pygame.Surface.get_size(surface),(1280,720))
        self.assertEqual(surface.get_size(),(1920,1080))
        self.assertEqual(surface.get_rect().center,(960,540))
    def test_native_primitives_and_alpha_blits_keep_positions(self):
        surface=MobileCanvas();surface.fill((0,0,0))
        tile=pygame.Surface((300,300),pygame.SRCALPHA);tile.fill((255,0,0,128))
        original=pygame.draw.rect
        with drawing_coordinates():
            pygame.draw.rect(surface,(0,255,0),(900,450,300,300))
            surface.blit(tile,(900,450))
        self.assertIs(pygame.draw.rect,original)
        self.assertLess(max(abs(a-b) for a,b in zip(pygame.Surface.get_at(surface,(700,400))[:3],(128,127,0))),5)
        self.assertEqual(pygame.Surface.get_at(surface,(50,50))[:3],(0,0,0))
    def test_static_scaled_art_is_cached_but_mutable_layers_are_not(self):
        surface=MobileCanvas();art=pygame.Surface((600,300));art.fill((10,20,30));surface.freeze(art)
        surface.blit(art,(0,0));surface.blit(art,(0,0))
        self.assertEqual(surface.cache_hits,1)
        mutable=pygame.Surface((60,60));mutable.fill((255,0,0));surface.blit(mutable,(0,0))
        mutable.fill((0,0,255));surface.blit(mutable,(0,0))
        self.assertGreater(pygame.Surface.get_at(surface,(10,10)).b,250)
        self.assertLessEqual(surface.cache_bytes,surface.cache_limit)
    def test_drawing_scope_restores_native_functions_on_failure(self):
        original=pygame.draw.circle
        with self.assertRaises(RuntimeError):
            with drawing_coordinates():raise RuntimeError()
        self.assertIs(pygame.draw.circle,original)
    def test_mobile_output_ignores_high_dpr_and_desktop_returns_to_native_path(self):
        service=SimpleNamespace(render_viewport=lambda:dict(width=844,height=390,dpr=3))
        window=WebWindowManager(platform_service=service)
        window.configure_viewport(resolve_layout(844,390,web=True,coarse=True))
        self.assertEqual(window.display_surface.get_size(),(1280,720))
        self.assertEqual(pygame.Surface.get_size(window.screen),(1280,720))
        window.present()
        window.configure_viewport(resolve_layout(1280,720,web=True))
        self.assertFalse(window.compact)
        self.assertNotIsInstance(window.screen,MobileCanvas)
        self.assertEqual(window.screen.get_size(),(1920,1080))
    def test_cached_art_tracks_global_alpha_without_stale_pixels(self):
        canvas=MobileCanvas();image=pygame.Surface((60,60));image.fill((255,0,0));canvas.freeze(image)
        image.set_alpha(64);canvas.fill((0,0,0));canvas.blit(image,(0,0))
        first=pygame.Surface.get_at(canvas,(10,10)).r
        image.set_alpha(192);canvas.fill((0,0,0));canvas.blit(image,(0,0))
        self.assertGreater(pygame.Surface.get_at(canvas,(10,10)).r,first+80)
        self.assertEqual(canvas.cache_hits,1)
    def test_text_cache_preserves_native_font_pixels(self):
        pygame.font.init()
        canvas=MobileCanvas();font=pygame.font.Font(None,32)
        first=canvas.render_text(font,"Energia 8",(255,220,150))
        self.assertIs(first,canvas.render_text(font,"Energia 8",(255,220,150)))
        self.assertEqual(pygame.image.tobytes(first,"RGBA"),
                         pygame.image.tobytes(font.render("Energia 8",True,(255,220,150)),"RGBA"))
        self.assertLessEqual(canvas.text_bytes,8*1024*1024)
    def test_clipping_is_mapped_without_changing_logical_bounds(self):
        surface=MobileCanvas();surface.fill((0,0,0));surface.set_clip((0,0,960,1080))
        with drawing_coordinates():pygame.draw.rect(surface,(255,0,0),(0,0,1920,1080))
        self.assertEqual(pygame.Surface.get_at(surface,(600,300))[:3],(255,0,0))
        self.assertEqual(pygame.Surface.get_at(surface,(700,300))[:3],(0,0,0))
        surface.set_clip(None)
        self.assertEqual(surface.get_clip(),pygame.Rect(0,0,1920,1080))
