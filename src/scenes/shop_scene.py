"""Acesso preparado para a futura loja; ainda não vende itens."""
import pygame

from src.config.colors import BG, BLACK, WHITE, GOLD, GRAY, BUTTON_BG, BUTTON_HOVER
from src.config.settings import WIDTH, HEIGHT
from src.scenes.base_scene import BaseScene
from src.ui.helpers import draw_text
from src.ui import dark_fantasy_theme as theme


class ShopScene(BaseScene):
    """Tela informativa da loja, mantendo o contexto do save selecionado."""

    def __init__(self, scene_manager, window_manager, asset_manager,
                 save_manager, save_data):
        super().__init__(scene_manager, window_manager, asset_manager)
        self.save_manager = save_manager
        self.save_data = save_data
        self.back_button = pygame.Rect(WIDTH // 2 - 150, 493, 300, 60)

    def update(self, dt):
        pass

    def draw(self, surface):
        theme.backdrop(surface, self.asset_manager.background, opacity=216)
        outer = pygame.Rect(253, 141, 774, 460)
        theme.panel(surface, outer, highlighted=True)
        center = WIDTH // 2
        theme.eyebrow(surface, "POSTO AVANÇADO", self.asset_manager.small_font,
                      center, 195, center=True)
        draw_text(surface, "O MERCADO SILENCIOSO", self.asset_manager.big_font,
                  WHITE, center, 241, center=True)
        theme.divider(surface, 427, 854, 291)
        # Selo metálico no centro substitui ícones alegres/genéricos.
        pygame.draw.circle(surface, (88, 80, 58), (center, 346), 34, 1)
        pygame.draw.polygon(surface, (175, 141, 83),
                            [(center, 318), (center+24, 346),
                             (center, 374), (center-24, 346)], 2)
        draw_text(surface, "COMÉRCIO INDISPONÍVEL", self.asset_manager.menu_font,
                  GOLD, center, 401, center=True)
        draw_text(surface, "Mercadorias e melhorias serão disponibilizadas em outra etapa.",
                  self.asset_manager.font, GRAY, center, 442, center=True)
        draw_text(surface, f"SEU OURO: {self.save_data['progresso']['moedas']}",
                  self.asset_manager.small_font, WHITE, center, 474, center=True)
        hovered = self.back_button.collidepoint(self.window_manager.get_virtual_mouse_pos())
        theme.button(surface, self.back_button, "RETORNAR AOS TERRITÓRIOS",
                     self.asset_manager.small_font, hover=hovered, prominent=True)
        self.window_manager.draw_fullscreen_button(self.asset_manager.small_font)
        theme.footer(surface, "ESC  ·  RETORNAR AO MAPA", self.asset_manager.small_font)

    def handle_event(self, event):
        if self.window_manager.handle_window_event(event):
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.window_manager.map_to_virtual(event.pos)
            if self.window_manager.get_fullscreen_button_rect().collidepoint(pos):
                self.window_manager.toggle_fullscreen()
            elif self.back_button.collidepoint(pos):
                self._back()

    def _back(self):
        from src.scenes.map_scene import MapScene
        self.scene_manager.change_scene(MapScene(
            self.scene_manager, self.window_manager, self.asset_manager,
            self.save_manager, self.save_data,
        ))
