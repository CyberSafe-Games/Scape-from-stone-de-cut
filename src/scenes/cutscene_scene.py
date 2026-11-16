"""Cena reutilizável de quadrinhos, com diálogos e sem dependência de save."""

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
    """Exibe imagens com múltiplas falas, digitação e transições visuais."""

    TYPING_SPEED = 35  # Caracteres por segundo. Ajuste para acelerar/desacelerar.
    DIALOGUE_DELAY_MS = 1300  # Tempo para observar cada imagem antes das falas.

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
        self._dialogue_index = 0
        self._visible_characters = 0
        self._typing_elapsed = 0.0
        self._dialogue_wait_ms = self.DIALOGUE_DELAY_MS
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

    def _dialogues(self):
        """Devolve falas do quadro; também aceita o antigo campo 'text'."""
        if not self.scenes or self.index >= len(self.scenes):
            return []
        entry = self.scenes[self.index]
        if "dialogues" in entry:
            result = []
            for dialogue in entry["dialogues"] or []:
                if isinstance(dialogue, (tuple, list)) and len(dialogue) == 2:
                    speaker, text = dialogue
                    result.append((str(speaker), str(text)))
            return result
        text = entry.get("text", "")
        return [("Narrador", str(text))] if text else []

    def _current_dialogue(self):
        dialogues = self._dialogues()
        if self._dialogue_index < len(dialogues):
            return dialogues[self._dialogue_index]
        return None

    def _layout_dialogue(self, text):
        """Quebra o texto completo antes da digitação para não saltar linhas."""
        font = self.asset_manager.get_font("default")
        return "\n".join(self._wrap_text(text, font, WIDTH - 220))

    def _reset_dialogue(self):
        self._dialogue_index = 0
        self._visible_characters = 0
        self._typing_elapsed = 0.0
        self._dialogue_wait_ms = self.DIALOGUE_DELAY_MS

    def _build_layer(self, index):
        """Prepara imagem e dicas de controle uma vez por mudança de quadro."""
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

    def _advance(self):
        # Um clique durante a pausa exibe a caixa, sem pular a fala.
        if self._dialogue_wait_ms > 0 and self._current_dialogue() is not None:
            self._dialogue_wait_ms = 0.0
            return
        dialogue = self._current_dialogue()
        if dialogue is not None:
            full_text = self._layout_dialogue(dialogue[1])
            if self._visible_characters < len(full_text):
                self._visible_characters = len(full_text)
                return
            if self._dialogue_index + 1 < len(self._dialogues()):
                self._dialogue_index += 1
                self._visible_characters = 0
                self._typing_elapsed = 0.0
                return

        if self.index == len(self.scenes) - 1:
            self._phase = "exit"
            self._elapsed_ms = 0.0
            return

        self._previous_layer = self._current_layer
        self.index += 1
        self._reset_dialogue()
        self._current_layer = self._build_layer(self.index)
        self._phase = "crossfade"
        self._elapsed_ms = 0.0

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
        if click or key:
            self._advance()

    def update(self, dt):
        if self._finished:
            return
        if self._phase == "empty":
            self._finish()
            return

        # O jogo fornece dt em milissegundos (clock.tick). A digitação pausa durante os fades.
        if self._phase == "idle":
            delta_ms = max(0, dt)
            if self._dialogue_wait_ms > 0:
                remaining_ms = self._dialogue_wait_ms
                self._dialogue_wait_ms = max(0.0, remaining_ms - delta_ms)
                # Só conta para a digitação o tempo após a pausa.
                typing_dt = max(0.0, delta_ms - remaining_ms) / 1000.0
            else:
                typing_dt = max(0, dt) / 1000.0
            dialogue = self._current_dialogue()
            if dialogue is not None and self._dialogue_wait_ms <= 0:
                total = len(self._layout_dialogue(dialogue[1]))
                if self._visible_characters < total:
                    self._typing_elapsed += typing_dt
                    self._visible_characters = min(
                        total, int(self._typing_elapsed * self.TYPING_SPEED)
                    )
            return

        self._elapsed_ms += max(0, dt)
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

    def _draw_dialogue(self, surface):
        dialogue = self._current_dialogue()
        if dialogue is None or self._dialogue_wait_ms > 0:
            return
        speaker, text = dialogue
        full_text = self._layout_dialogue(text)
        visible_text = full_text[:self._visible_characters]
        font = self.asset_manager.get_font("default")
        name_font = self.asset_manager.get_font("default")
        padding = 24
        box_width = WIDTH - 140
        # Reserva espaço para até quatro linhas sem alterar a caixa enquanto digita.
        line_height = font.get_linesize()
        box_height = min(HEIGHT - 130, max(145, 4 * line_height + 75))
        entry = self.scenes[self.index]
        box_y = 80 if entry.get("position", "bottom") == "top" else HEIGHT - box_height - 110
        panel = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (14, 17, 20, 210), panel.get_rect(),
                         border_radius=8)
        pygame.draw.rect(panel, (168, 131, 73, 210), panel.get_rect(),
                         width=2, border_radius=8)
        if speaker:
            label = name_font.render(speaker, True, (245, 200, 125))
            panel.blit(label, (padding, 12))
        text_y = 20 + (name_font.get_linesize() if speaker else 0)
        for line in visible_text.split("\n"):
            if text_y + line_height > box_height - 8:
                break
            rendered = font.render(line, True, (237, 222, 193))
            panel.blit(rendered, (padding, text_y))
            text_y += line_height + 3
        surface.blit(panel, (70, box_y))

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

        # A caixa é desenhada dinamicamente, sem recriar a imagem a cada letra.
        if self._phase == "idle":
            self._draw_dialogue(surface)

        if self._phase in ("enter", "exit"):
            duration = (FADE_IN_DURATION_MS if self._phase == "enter"
                        else FADE_OUT_DURATION_MS)
            progress = min(1.0, self._elapsed_ms / max(1, duration))
            alpha = round(255 * (1 - progress if self._phase == "enter" else progress))
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, alpha))
            surface.blit(overlay, (0, 0))
