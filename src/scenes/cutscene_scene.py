"""Cena reutilizável de quadrinhos, sem dependência de progressão ou save."""

import logging
import os

import pygame

from src.config.cutscenes import (
    CONTINUE_HINT,
    CROSSFADE_DURATION_MS,
    FADE_IN_DURATION_MS,
    FADE_OUT_DURATION_MS,
    INTRO_CUTSCENE,
    INTRO_LAST_HINT,
    SKIP_HINT,
)
from src.config.settings import ASSETS_DIR, HEIGHT, WIDTH
from src.scenes.base_scene import BaseScene


logger = logging.getLogger(__name__)


class CutsceneScene(BaseScene):
    """Exibe quadros estáticos com avanço manual e transições visuais."""

    def __init__(self, scene_manager, window_manager, asset_manager,
                 scenes, next_scene_factory, on_finish=None):
        super().__init__(scene_manager, window_manager, asset_manager)
        self.scenes = list(scenes)
        self.next_scene_factory = next_scene_factory
        self.on_finish = on_finish
        self.index = 0
        self._finished = False
        self._phase = "enter"
        self._elapsed_ms = 0.0
        self._previous_layer = None
        self._current_layer = None
        self._music_context = getattr(
            getattr(scene_manager, "current_scene", None), "music_context", None
        )
        if not self.scenes:
            self._phase = "empty"
        else:
            self._current_layer = self._build_layer(self.index)

    @property
    def music_context(self):
        """Mantém a trilha em execução ao trocar para esta cena."""
        return self._music_context

    def _finish(self):
        if self._finished:
            return
        self._finished = True
        if self.on_finish is not None:
            self.on_finish()
        self.scene_manager.change_scene(self.next_scene_factory())

    @staticmethod
    def _wrap_text(text, font, max_width):
        lines = []
        for paragraph in text.split("\n"):
            if not paragraph.strip():
                lines.append("")
                continue
            line = ""
            for word in paragraph.split():
                candidate = f"{line} {word}" if line else word
                if font.size(candidate)[0] <= max_width:
                    line = candidate
                    continue
                if line:
                    lines.append(line)
                    line = ""
                # Divide palavras maiores que a largura disponível.
                for letter in word:
                    if line and font.size(line + letter)[0] > max_width:
                        lines.append(line)
                        line = ""
                    line += letter
            lines.append(line)
        return lines

    def _build_layer(self, index):
        """Prepara imagem e textos uma única vez por mudança de quadro."""
        entry = self.scenes[index]
        layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        layer.fill((12, 12, 16, 255))
        filename = os.path.join(ASSETS_DIR, entry.get("image", ""))
        try:
            image = pygame.image.load(filename).convert_alpha()
            image_width, image_height = image.get_size()
            if not image_width or not image_height:
                raise ValueError("imagem sem dimensões")
            scale = min(WIDTH / image_width, HEIGHT / image_height)
            new_size = (max(1, round(image_width * scale)),
                        max(1, round(image_height * scale)))
            scaled = pygame.transform.smoothscale(image, new_size)
            layer.blit(scaled, scaled.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        except (OSError, ValueError, pygame.error) as error:
            logger.warning("Imagem de cutscene indisponível: %s (%s)", filename, error)

        text = entry.get("text", "")
        if text:
            font = self.asset_manager.get_font("default")
            lines = self._wrap_text(text, font, WIDTH - 220)
            line_height = font.get_linesize()
            padding = 30
            box_height = min(HEIGHT - 130, len(lines) * line_height + 2 * padding)
            position = entry.get("position", "bottom")
            box_y = 80 if position == "top" else HEIGHT - box_height - 110
            panel = pygame.Surface((WIDTH - 140, box_height), pygame.SRCALPHA)
            panel.fill((14, 17, 20, 210))
            pygame.draw.rect(panel, (168, 131, 73, 210),
                             panel.get_rect(), width=2, border_radius=8)
            for line_index, line in enumerate(lines):
                y = padding + line_index * line_height
                if y + line_height > box_height:
                    break
                panel.blit(font.render(line, True, (237, 222, 193)), (40, y))
            layer.blit(panel, (70, box_y))

        font = self.asset_manager.get_font("small")
        is_intro_end = (self.scenes is INTRO_CUTSCENE or
                        self.scenes == INTRO_CUTSCENE) and index == len(self.scenes) - 1
        hint = INTRO_LAST_HINT if is_intro_end else CONTINUE_HINT
        hints = f"{hint}   ·   {SKIP_HINT}"
        rendered = font.render(hints, True, (226, 217, 195))
        hint_panel = pygame.Surface((rendered.get_width() + 36,
                                     rendered.get_height() + 18), pygame.SRCALPHA)
        hint_panel.fill((12, 14, 18, 125))
        hint_panel.blit(rendered, (18, 9))
        layer.blit(hint_panel, hint_panel.get_rect(
            midbottom=(WIDTH // 2, HEIGHT - 18)))
        return layer

    def handle_event(self, event):
        if self.window_manager.handle_window_event(event):
            return
        if self._finished:
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._finish()
            return
        if self._phase != "idle":
            return
        click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
        key = (event.type == pygame.KEYDOWN and
               event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER) and
               not getattr(event, "repeat", False))
        if not (click or key):
            return
        if self.index == len(self.scenes) - 1:
            self._phase = "exit"
            self._elapsed_ms = 0.0
            return
        self._previous_layer = self._current_layer
        self.index += 1
        self._current_layer = self._build_layer(self.index)
        self._phase = "crossfade"
        self._elapsed_ms = 0.0

    def update(self, dt):
        if self._finished or self._phase == "idle":
            return
        if self._phase == "empty":
            self._finish()
            return
        self._elapsed_ms += max(0, dt) * 1000
        duration = {
            "enter": FADE_IN_DURATION_MS,
            "crossfade": CROSSFADE_DURATION_MS,
            "exit": FADE_OUT_DURATION_MS,
        }[self._phase]
        if self._elapsed_ms >= duration:
            if self._phase == "exit":
                self._finish()
            else:
                self._phase = "idle"
                self._previous_layer = None
                self._elapsed_ms = 0.0

    def draw(self, surface):
        surface.fill((0, 0, 0))
        if self._finished or self._current_layer is None:
            return
        if self._phase == "crossfade" and self._previous_layer is not None:
            progress = min(1.0, self._elapsed_ms / max(1, CROSSFADE_DURATION_MS))
            surface.blit(self._previous_layer, (0, 0))
            self._current_layer.set_alpha(round(255 * progress))
            surface.blit(self._current_layer, (0, 0))
            self._current_layer.set_alpha(None)
        else:
            surface.blit(self._current_layer, (0, 0))
        if self._phase in ("enter", "exit"):
            duration = (FADE_IN_DURATION_MS if self._phase == "enter"
                        else FADE_OUT_DURATION_MS)
            progress = min(1.0, self._elapsed_ms / max(1, duration))
            alpha = round(255 * (1 - progress if self._phase == "enter" else progress))
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, alpha))
            surface.blit(overlay, (0, 0))
