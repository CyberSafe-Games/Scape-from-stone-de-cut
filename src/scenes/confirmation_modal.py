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
from src.ui import dark_fantasy_theme as theme


class ConfirmationModal(BaseScene):
    """Modal de confirmação para retornar ao menu principal ou abandonar a partida."""

    def __init__(
        self,
        scene_manager,
        window_manager,
        asset_manager,
        on_confirm=None,
        on_cancel=None,
        title="VOLTAR AO MENU?",
        message="Seu progresso será salvo antes de sair.",
        confirm_label="SIM, VOLTAR",
    ):
        super().__init__(scene_manager, window_manager, asset_manager)
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.title = title
        self.message = message
        self.confirm_label = confirm_label

        self.confirm_button = pygame.Rect(
            WIDTH // 2 - 130, HEIGHT // 2 + 20, 260, 55
        )
        self.cancel_button = pygame.Rect(
            WIDTH // 2 - 130, HEIGHT // 2 + 90, 260, 55
        )

    def draw_button(self, surface, rect, text):
        hovered = rect.collidepoint(self.window_manager.get_virtual_mouse_pos())
        theme.button(surface, rect, text, self.asset_manager.small_font, hover=hovered,
                     prominent=rect == self.confirm_button,
                     danger="EXCLUIR" in text)

    def update(self, dt):
        pass

    def draw(self, surface):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((3, 8, 8, 225))
        surface.blit(overlay, (0, 0))
        rect = pygame.Rect(WIDTH // 2 - 345, HEIGHT // 2 - 165, 690, 370)
        theme.panel(surface, rect, highlighted=True)
        theme.eyebrow(surface, "CONFIRMAÇÃO", self.asset_manager.small_font,
                      WIDTH // 2, rect.y + 34, center=True)
        draw_text(surface, self.title, self.asset_manager.big_font,
                  WHITE, WIDTH // 2, HEIGHT // 2 - 69, center=True)
        theme.divider(surface, rect.x + 75, rect.right - 75, HEIGHT // 2 - 36)
        draw_text(surface, self.message, self.asset_manager.font,
                  (201, 201, 190), WIDTH // 2, HEIGHT // 2 - 9, center=True)
        self.draw_button(surface, self.confirm_button, self.confirm_label)
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
