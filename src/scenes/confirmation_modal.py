import pygame
from src.scenes.base_scene import BaseScene
from src.config.settings import WIDTH, HEIGHT
from src.config.colors import (
    BLACK,
    WHITE,
    GOLD,
    BUTTON_BG,
    BUTTON_HOVER,
)
from src.ui.helpers import draw_text


class ConfirmationModal(BaseScene):
    """Modal de confirmação para retornar ao menu principal ou abandonar a partida."""

    def __init__(
        self,
        scene_manager,
        window_manager,
        asset_manager,
        on_confirm=None,
        on_cancel=None,
    ):
        super().__init__(scene_manager, window_manager, asset_manager)
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

        self.confirm_button = pygame.Rect(
            WIDTH // 2 - 130, HEIGHT // 2 + 20, 260, 55
        )
        self.cancel_button = pygame.Rect(
            WIDTH // 2 - 130, HEIGHT // 2 + 90, 260, 55
        )

    def draw_button(self, surface, rect, text):
        mouse_pos = self.window_manager.get_virtual_mouse_pos()
        hovered = rect.collidepoint(mouse_pos)
        color = BUTTON_HOVER if hovered else BUTTON_BG

        pygame.draw.rect(surface, color, rect, border_radius=10)
        pygame.draw.rect(surface, GOLD, rect, 2, border_radius=10)
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
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(220)
        overlay.fill(BLACK)
        surface.blit(overlay, (0, 0))

        draw_text(
            surface,
            "VOLTAR AO MENU?",
            self.asset_manager.big_font,
            GOLD,
            WIDTH // 2,
            HEIGHT // 2 - 65,
            center=True,
        )

        draw_text(
            surface,
            "Seu progresso desta partida será perdido.",
            self.asset_manager.font,
            WHITE,
            WIDTH // 2,
            HEIGHT // 2 - 25,
            center=True,
        )

        self.draw_button(surface, self.confirm_button, "SIM, VOLTAR")
        self.draw_button(surface, self.cancel_button, "CANCELAR")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._cancel()
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            virt_pos = self.window_manager.map_to_virtual(event.pos)

            if self.confirm_button.collidepoint(virt_pos):
                self._confirm()
            elif self.cancel_button.collidepoint(virt_pos):
                self._cancel()

    def _confirm(self):
        self.scene_manager.pop_modal()
        if self.on_confirm:
            self.on_confirm()
        else:
            from src.scenes.menu_scene import MenuScene
            self.scene_manager.change_scene(
                MenuScene(self.scene_manager, self.window_manager, self.asset_manager)
            )

    def _cancel(self):
        self.scene_manager.pop_modal()
        if self.on_cancel:
            self.on_cancel()
