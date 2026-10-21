import sys
import pygame

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

        self.play_button = pygame.Rect(144, 456, 326, 56)
        self.quit_button = pygame.Rect(144, 526, 326, 53)

    def draw_button(self, surface, rect, text):
        hovered = rect.collidepoint(self.window_manager.get_virtual_mouse_pos())
        theme.button(surface, rect, text, self.asset_manager.menu_font,
                     hover=hovered, prominent=(rect == self.play_button))

    def update(self, dt):
        pass

    def draw(self, surface):
        theme.backdrop(surface, self.asset_manager.background, opacity=186)
        # Placa vertical e sigilo discreto em vez de botões coloridos genéricos.
        pygame.draw.line(surface, (118, 91, 52), (116, 132), (116, 583), 2)
        for y in (132, 583):
            pygame.draw.polygon(surface, GOLD,
                                [(116, y-6), (122, y), (116, y+6), (110, y)])
        theme.eyebrow(surface, "CRÔNICAS DA PEDRA CORTADA", self.asset_manager.small_font, 144, 160)
        draw_text(surface, "SCAPE FROM", self.asset_manager.title_font, WHITE, 139, 208)
        draw_text(surface, "STONE DE CUT", self.asset_manager.title_font, GOLD, 139, 280)
        pygame.draw.line(surface, (117, 94, 57), (146, 375), (530, 375), 1)
        draw_text(surface, "A FLORESTA NÃO ESQUECE.", self.asset_manager.font,
                  (200, 199, 179), 145, 393)
        draw_text(surface, "Um roguelike de cartas entre ruínas, tribos e sombras.",
                  self.asset_manager.small_font, GRAY, 145, 426)
        self.draw_button(surface, self.play_button, "INICIAR JORNADA")
        self.draw_button(surface, self.quit_button, "SAIR DO JOGO")

        # Marca ornamental sobre o cenário. Não é um botão.
        cx, cy = 951, 348
        pygame.draw.circle(surface, (74, 78, 60), (cx, cy), 119, 1)
        pygame.draw.circle(surface, (90, 78, 54), (cx, cy), 98, 1)
        for d in range(0, 360, 45):
            import math
            a = math.radians(d)
            px, py = int(cx + 108 * math.cos(a)), int(cy + 108 * math.sin(a))
            pygame.draw.circle(surface, (126, 102, 64), (px, py), 3)
        pts = [(cx, cy-68), (cx+55, cy), (cx, cy+68), (cx-55, cy)]
        pygame.draw.lines(surface, (127, 100, 61), True, pts, 2)
        pygame.draw.line(surface, (127, 100, 61), (cx, cy-68), (cx, cy+68), 1)
        pygame.draw.circle(surface, (127, 100, 61), (cx, cy), 13, 2)
        draw_text(surface, "I", self.asset_manager.small_font, GOLD, cx, cy+139, center=True)

        self.window_manager.draw_fullscreen_button(self.asset_manager.small_font)
        theme.footer(surface, "ENTER / ESPAÇO  ·  JOGAR                         F11  ·  TELA CHEIA",
                     self.asset_manager.small_font)

    def handle_event(self, event):
        # Janela / tela cheia
        if self.window_manager.handle_window_event(event):
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            virt_pos = self.window_manager.map_to_virtual(event.pos)

            if self.window_manager.get_fullscreen_button_rect().collidepoint(virt_pos):
                self.window_manager.toggle_fullscreen()
                return

            if self.play_button.collidepoint(virt_pos):
                self._start_game()
                return

            if self.quit_button.collidepoint(virt_pos):
                pygame.quit()
                sys.exit()

        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._start_game()
            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

    def _start_game(self):
        from src.scenes.save_selection_scene import SaveSelectionScene
        self.scene_manager.change_scene(
            SaveSelectionScene(self.scene_manager, self.window_manager, self.asset_manager)
        )
