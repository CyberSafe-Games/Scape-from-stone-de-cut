import sys
import pygame
from pygame import surface

from src.scenes.base_scene import BaseScene
from src.config.settings import WIDTH, HEIGHT
from src.config.colors import (
    BG,
    BLACK,
    WHITE,
    GOLD,
    GRAY,
    BUTTON_BG,
    BUTTON_HOVER,
)
from src.ui.helpers import draw_text
from src.ui import dark_fantasy_theme as theme


class MenuScene(BaseScene):
    """Cena do Menu Principal do jogo."""

    def __init__(self, scene_manager, window_manager, asset_manager):
        super().__init__(scene_manager, window_manager, asset_manager)

        self.play_button = pygame.Rect(216, 684, 489, 84)
        self.options_button = pygame.Rect(216, 789, 489, 80)
        self.quit_button = pygame.Rect(216, 894, 489, 80)

    def draw_button(self, surface, rect, text):
        hovered = rect.collidepoint(self.window_manager.get_virtual_mouse_pos())
        theme.button(
            surface,
            rect,
            text,
            self.asset_manager.menu_font,
            hover=hovered,
            prominent=(rect == self.play_button),
        )

    def update(self, dt):
        pass

    def draw(self, surface):
        theme.backdrop(surface, self.asset_manager.background, opacity=186)
        # Placa vertical e sigilo discreto em vez de botões coloridos genéricos.
        pygame.draw.line(surface, (118, 91, 52), (174, 198), (174, 980), 3)
        for y in (198, 980):
            pygame.draw.polygon(
                surface, GOLD, [(174, y - 9), (183, y), (174, y + 9), (165, y)]
            )
        theme.eyebrow(
            surface,
            "CRÔNICAS DA PEDRA CORTADA",
            self.asset_manager.small_font,
            216,
            240,
        )
        draw_text(surface, "SCAPE FROM", self.asset_manager.title_font, WHITE, 209, 312)
        draw_text(
            surface, "STONE DE CUT", self.asset_manager.title_font, GOLD, 209, 420
        )
        pygame.draw.line(surface, (117, 94, 57), (219, 563), (795, 563), 2)
        draw_text(
            surface,
            "A FLORESTA NÃO ESQUECE.",
            self.asset_manager.font,
            (200, 199, 179),
            218,
            590,
        )
        draw_text(
            surface,
            "Um roguelike de cartas entre ruínas, tribos e sombras.",
            self.asset_manager.small_font,
            GRAY,
            218,
            639,
        )
        self.draw_button(surface, self.play_button, "INICIAR JORNADA")
        self.draw_button(surface, self.options_button, "OPÇÕES DE ÁUDIO")
        self.draw_button(surface, self.quit_button, "SAIR DO JOGO")

        # Marca ornamental sobre o cenário. Não é um botão.
        cx, cy = 1427, 522
        pygame.draw.circle(surface, (74, 78, 60), (cx, cy), 179, 2)
        pygame.draw.circle(surface, (90, 78, 54), (cx, cy), 147, 2)
        for d in range(0, 360, 45):
            import math

            a = math.radians(d)
            px, py = int(cx + 162 * math.cos(a)), int(cy + 162 * math.sin(a))
            pygame.draw.circle(surface, (126, 102, 64), (px, py), 5)
        pts = [(cx, cy - 102), (cx + 83, cy), (cx, cy + 102), (cx - 83, cy)]
        pygame.draw.lines(surface, (127, 100, 61), True, pts, 3)
        pygame.draw.line(surface, (127, 100, 61), (cx, cy - 102), (cx, cy + 102), 2)
        pygame.draw.circle(surface, (127, 100, 61), (cx, cy), 20, 3)
        draw_text(
            surface, "I", self.asset_manager.small_font, GOLD, cx, cy + 209, center=True
        )

        self.window_manager.draw_fullscreen_button(self.asset_manager.small_font)
        theme.footer(
            surface,
            "ENTER / ESPAÇO · JOGAR     O · OPÇÕES     F11 · TELA CHEIA",
            self.asset_manager.small_font,
        )

    def handle_event(self, event):
        # Janela / tela cheia
        if self.window_manager.handle_window_event(event):
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            virt_pos = self.window_manager.map_to_virtual(event.pos)

            if self.window_manager.get_fullscreen_button_rect().collidepoint(virt_pos):
                self.play_ui_sound("ui.click")
                self.window_manager.toggle_fullscreen()
                return

            if self.play_button.collidepoint(virt_pos):
                self.play_ui_sound("ui.confirm")
                self._start_game()
                return

            if self.options_button.collidepoint(virt_pos):
                self.play_ui_sound("ui.confirm")
                self._open_audio_options()
                return

            if self.quit_button.collidepoint(virt_pos):
                self.play_ui_sound("ui.click")
                pygame.quit()
                sys.exit()

        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.play_ui_sound("ui.confirm")
                self._start_game()
            elif event.key == pygame.K_o:
                self.play_ui_sound("ui.confirm")
                self._open_audio_options()
            elif event.key == pygame.K_ESCAPE:
                self.play_ui_sound("ui.click")
                pygame.quit()
                sys.exit()

    def _open_audio_options(self):
        from src.scenes.audio_options_scene import AudioOptionsScene
        self.scene_manager.change_scene(AudioOptionsScene(
            self.scene_manager, self.window_manager, self.asset_manager, return_scene=self))

    def _start_game(self):
        from src.scenes.save_selection_scene import SaveSelectionScene

        self.scene_manager.change_scene(
            SaveSelectionScene(
                self.scene_manager, self.window_manager, self.asset_manager
            )
        )
