"""A composição nativa usa menos pixels sem duplicar a arte da interface."""
import unittest
from unittest.mock import Mock
from types import SimpleNamespace
import pygame
from src.core.mobile_canvas import MobileCanvas,drawing_coordinates
from src.core.web_window import WebWindowManager
from src.config.responsive_layout import resolve_layout


class ReducedCanvasTests(unittest.TestCase):
    def setUp(self):pygame.display.init();pygame.display.set_mode((960,540))
    def tearDown(self):pygame.display.quit()
    def test_physical_storage_is_540p_with_original_logical_coordinates(self):
        surface=MobileCanvas()
        self.assertEqual(pygame.Surface.get_size(surface),(960,540))
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
        self.assertLess(max(abs(a-b) for a,b in zip(pygame.Surface.get_at(surface,(525,300))[:3],(128,127,0))),5)
        self.assertEqual(pygame.Surface.get_at(surface,(50,50))[:3],(0,0,0))
    def test_static_scaled_art_is_cached_but_mutable_layers_are_not(self):
        surface=MobileCanvas();art=pygame.Surface((400,300));art.fill((10,20,30));surface.freeze(art)
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
        self.assertEqual(window.display_surface.get_size(),(960,540))
        self.assertEqual(pygame.Surface.get_size(window.screen),(960,540))
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
        self.assertEqual(pygame.Surface.get_at(surface,(400,300))[:3],(255,0,0))
        self.assertEqual(pygame.Surface.get_at(surface,(550,300))[:3],(0,0,0))
        surface.set_clip(None)
        self.assertEqual(surface.get_clip(),pygame.Rect(0,0,1920,1080))

    def test_transparent_scratch_is_reused_without_black_rectangle(self):
        canvas=MobileCanvas();canvas.begin_frame()
        image=canvas.scratch((200,100),pygame.SRCALPHA,"effect")
        with drawing_coordinates():pygame.draw.circle(image,(255,0,0,255),(100,50),20)
        canvas.fill((0,255,0));canvas.blit(image,(0,0))
        self.assertEqual(pygame.Surface.get_at(canvas,(2,2))[:3],(0,255,0))
        self.assertGreater(pygame.Surface.get_at(canvas,(50,25)).r,240)
        canvas.begin_frame();again=canvas.scratch((200,100),pygame.SRCALPHA,"effect")
        self.assertIs(image,again);self.assertEqual(canvas.pool_created,0)
        self.assertEqual(pygame.Surface.get_at(again,(50,25)).a,0)

    def test_fine_pointer_compact_web_pc_keeps_720p_profile(self):
        service=SimpleNamespace(render_viewport=lambda:dict(width=844,height=390,dpr=2))
        window=WebWindowManager(platform_service=service)
        window.configure_viewport(resolve_layout(844,390,web=True,coarse=False))
        self.assertEqual(pygame.Surface.get_size(window.screen),(1280,720))

    def test_warm_frame_has_zero_resize_raster_and_scratch_allocations(self):
        from src.ui.helpers import draw_text
        pygame.font.init();font=pygame.font.Font(None,24)
        canvas=MobileCanvas();canvas.raster_diagnostics=True
        image=pygame.Surface((200,300));canvas.freeze(image)
        for _ in range(3):
            canvas.begin_frame()
            with drawing_coordinates(canvas):
                scratch=canvas.scratch((220,320),pygame.SRCALPHA,"shadow")
                pygame.draw.rect(scratch,(0,0,0,100),(0,0,220,320))
                canvas.blit(scratch,(0,0));canvas.blit(image,(10,10))
                draw_text(canvas,"Energia 8",font,(255,255,255),20,20)
        self.assertEqual((canvas.native_scale_calls,canvas.text_renders,canvas.pool_created),(0,0,0))

    def test_profiler_restores_transform_functions_on_failure(self):
        canvas=MobileCanvas();canvas.raster_diagnostics=True
        original=pygame.transform.smoothscale
        with self.assertRaises(RuntimeError):
            with drawing_coordinates(canvas):raise RuntimeError()
        self.assertIs(pygame.transform.smoothscale,original)

    def test_changing_crop_reuses_full_immutable_image_scale(self):
        canvas=MobileCanvas();image=pygame.Surface((200,200));image.fill((200,20,30));canvas.freeze(image)
        canvas.blit(image,(100,100),pygame.Rect(0,0,100,100))
        self.assertEqual(canvas.scale_operations,1)
        canvas.begin_frame()
        canvas.blit(image,(100,100),pygame.Rect(20,20,80,80))
        self.assertEqual(canvas.scale_operations,0)
        self.assertEqual(pygame.Surface.get_at(canvas,(60,60))[:3],(200,20,30))
