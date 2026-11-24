"""Menu de pausa da batalha, empilhado como modal sobre a cena."""

import pygame

from src.config.settings import WIDTH, HEIGHT
from src.config.colors import GOLD, GRAY
from src.config.layout import compute_pause_menu_layout
from src.scenes.base_scene import BaseScene
from src.ui import dark_fantasy_theme as theme
from src.ui.helpers import draw_text
from src.ui.options_sanctuary_view import OptionsSanctuaryView


class PauseMenuModal(BaseScene):
    """Congela a batalha e oferece continuar, opções e sair."""

    def __init__(
        self,
        scene_manager,
        window_manager,
        asset_manager,
        on_options=None,
        on_exit=None,
        exit_label="SAIR DA BATALHA",
        subtitle="A batalha está congelada até você continuar.",
    ):
        super().__init__(scene_manager, window_manager, asset_manager)
        self.visuals = OptionsSanctuaryView(asset_manager)
        self.on_options = on_options
        self.on_exit = on_exit
        self.exit_label = exit_label
        self.subtitle = subtitle
        self.layout = compute_pause_menu_layout(3)
        self.panel_rect = pygame.Rect(self.layout.panel)
        self.continue_button = pygame.Rect(self.layout.buttons[0])
        self.options_button = pygame.Rect(self.layout.buttons[1])
        self.exit_button = pygame.Rect(self.layout.buttons[2])

    def update(self, dt):
        self.visuals.update(dt)

    def draw(self, surface):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((3, 8, 8, 218))
        surface.blit(overlay, (0, 0))
        self.visuals.modal_panel(surface, self.panel_rect)
        theme.eyebrow(
            surface,
            "BATALHA PAUSADA",
            self.asset_manager.small_font,
            self.panel_rect.centerx,
            self.layout.eyebrow_center_y,
            center=True,
        )
        draw_text(
            surface,
            "PAUSA",
            self.asset_manager.big_font,
            GOLD,
            self.panel_rect.centerx,
            self.layout.title_center_y,
            center=True,
        )
        draw_text(
            surface,
            self.subtitle,
            self.asset_manager.small_font,
            GRAY,
            self.panel_rect.centerx,
            self.layout.subtitle_center_y,
            center=True,
        )
        theme.divider(
            surface,
            self.layout.divider_x1,
            self.layout.divider_x2,
            self.layout.divider_y,
        )
        mouse = self.window_manager.get_virtual_mouse_pos()
        self.visuals.button(
            surface,
            self.continue_button,
            "RETORNAR AO COMBATE",
            self.asset_manager.font,
            hover=self.continue_button.collidepoint(mouse),
            prominent=True,
        )
        self.visuals.button(
            surface,
            self.options_button,
            "OPÇÕES",
            self.asset_manager.font,
            hover=self.options_button.collidepoint(mouse),
        )
        self.visuals.button(
            surface,
            self.exit_button,
            self.exit_label,
            self.asset_manager.small_font,
            hover=self.exit_button.collidepoint(mouse),
        )
        draw_text(
            surface,
            "ESC  ·  CONTINUAR",
            self.asset_manager.small_font,
            (133, 139, 128),
            self.panel_rect.centerx,
            self.layout.footer_center_y,
            center=True,
        )

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._continue()
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        point = self.window_manager.map_to_virtual(event.pos)
        if self.continue_button.collidepoint(point):
            self._continue()
        elif self.options_button.collidepoint(point):
            self.play_ui_sound("ui.click")
            if self.on_options:
                self.on_options()
        elif self.exit_button.collidepoint(point):
            self.play_ui_sound("ui.click")
            if self.on_exit:
                self.on_exit()

    def _continue(self):
        self.play_ui_sound("ui.click")
        self.scene_manager.pop_modal()
