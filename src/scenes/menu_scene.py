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


class MenuScene(BaseScene):
    """Cena do Menu Principal do jogo."""

    def __init__(self, scene_manager, window_manager, asset_manager):
        super().__init__(scene_manager, window_manager, asset_manager)

        self.play_button = pygame.Rect(
            WIDTH // 2 - 130, HEIGHT // 2 + 45, 260, 60
        )
        self.quit_button = pygame.Rect(
            WIDTH // 2 - 130, HEIGHT // 2 + 125, 260, 60
        )

    def draw_button(self, surface, rect, text):
        mouse_pos = self.window_manager.get_virtual_mouse_pos()
        hovered = rect.collidepoint(mouse_pos)
        color = BUTTON_HOVER if hovered else BUTTON_BG

        pygame.draw.rect(surface, color, rect, border_radius=12)
        pygame.draw.rect(surface, GOLD, rect, 3, border_radius=12)
        draw_text(
            surface,
            text,
            self.asset_manager.menu_font,
            WHITE,
            rect.centerx,
            rect.centery,
            center=True,
        )

    def update(self, dt):
        pass

    def draw(self, surface):
        # 1. Fundo com imagem ou cor sólida
        if self.asset_manager.background is not None:
            surface.blit(self.asset_manager.background, (0, 0))
        else:
            surface.fill(BG)

        # 2. Escurecimento translúcido
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(145)
        overlay.fill(BLACK)
        surface.blit(overlay, (0, 0))

        # 3. Título e subtítulo estilizados
        draw_text(
            surface,
            "SCAPE FROM",
            self.asset_manager.title_font,
            WHITE,
            WIDTH // 2,
            HEIGHT // 2 - 105,
            center=True,
        )
        draw_text(
            surface,
            "STONE DE CUT",
            self.asset_manager.title_font,
            GOLD,
            WIDTH // 2,
            HEIGHT // 2 - 40,
            center=True,
        )
        draw_text(
            surface,
            "Uma aventura de cartas por turnos",
            self.asset_manager.small_font,
            WHITE,
            WIDTH // 2,
            HEIGHT // 2 + 5,
            center=True,
        )

        # 4. Botões de ação
        self.draw_button(surface, self.play_button, "JOGAR")
        self.draw_button(surface, self.quit_button, "SAIR")

        # 5. Botão de tela cheia e rodapé
        self.window_manager.draw_fullscreen_button(self.asset_manager.small_font)
        draw_text(
            surface,
            "ENTER / ESPAÇO para jogar   |   F11 para tela cheia",
            self.asset_manager.small_font,
            GRAY,
            WIDTH // 2,
            HEIGHT - 30,
            center=True,
        )

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
        from src.scenes.battle_scene import BattleScene
        self.scene_manager.change_scene(
            BattleScene(self.scene_manager, self.window_manager, self.asset_manager)
        )
