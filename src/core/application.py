"""Ciclo compartilhado; a execução desktop permanece síncrona."""
import asyncio
import time
import pygame
from src.config.settings import FPS, LEGACY_WINDOW_SIZE
from src.ui.fps_counter import draw_fps


class Application:
    def __init__(self, window, assets, audio, preferences, scenes, clock=None):
        self.window, self.assets, self.audio = window, assets, audio
        self.preferences, self.scenes = preferences, scenes
        self.clock = clock or pygame.time.Clock()
        self.running = True
        self.frames = 0
        self.platform = scenes.platform
        self._active = True
        self._resume_serial = 0

    def frame(self, web=False):
        poll = getattr(self.scenes, "poll_pending", None)
        if poll:
            poll()
        dt = self.clock.tick(0 if web else FPS)
        active, serial = self.platform.lifecycle_state() if web else (True, 0)
        resumed = web and active and (not self._active or serial != self._resume_serial)
        self._active, self._resume_serial = active, serial
        if web:
            checkpoint_serial = self.platform.checkpoint_serial() if hasattr(self.platform,"checkpoint_serial") else 0
            if ((not active and getattr(self, "_was_active_for_checkpoint", True))
                    or checkpoint_serial != getattr(self,"_checkpoint_serial",0)):
                scene = getattr(self.scenes,"current_scene",None)
                if hasattr(scene, "request_checkpoint"):
                    scene.request_checkpoint()
            self._checkpoint_serial = checkpoint_serial
            self._was_active_for_checkpoint = active
            self.audio.set_suspended(not active)
            dt = 0 if resumed else min(dt, 100)
            if resumed:
                pygame.event.clear()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                break
            if web and not active:
                continue
            if web and event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                self.audio.unlock_after_interaction()
            shortcut = event.type == pygame.KEYDOWN and event.key in (pygame.K_F11, pygame.K_F10)
            if self.window.handle_window_event(event):
                if shortcut:
                    self.audio.play_sfx("ui.click", volume=1.0)
                    self.preferences.set("fullscreen", self.window.is_fullscreen)
                    self.preferences.set("window_size", "legacy" if self.window.windowed_size == LEGACY_WINDOW_SIZE else "large")
                    try:
                        self.preferences.save()
                    except OSError:
                        pass
                continue
            self.scenes.handle_event(event)
        if self.scenes.exit_requested:
            self.running = False
        if not self.running or (web and not active):
            return 0
        before = time.perf_counter() if web else 0
        self.scenes.update(dt)
        after_update = time.perf_counter() if web else 0
        self.scenes.draw(self.window.virtual_screen)
        if self.preferences.get("show_fps"):
            draw_fps(self.window.virtual_screen, self.assets.small_font, self.clock.get_fps())
        after_draw = time.perf_counter() if web else 0
        self.window.present()
        if web:
            self.frame_cost_ms = dict(update=(after_update-before)*1000,
                                      draw=(after_draw-after_update)*1000,
                                      present=(time.perf_counter()-after_draw)*1000)
        self.frames += 1
        return dt

    def run_desktop(self):
        while self.running:
            self.frame()

    async def run_web(self, observe=None):
        # Não há sys.exit no caminho web; o host conserva o controle da aba.
        while self.running:
            self.frame(web=True)
            if observe:
                observe(self)
            await asyncio.sleep(0)

