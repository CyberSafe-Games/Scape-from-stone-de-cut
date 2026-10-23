import pygame

from src.scenes.base_scene import BaseScene
from src.ui.card_view import CardView
from src.ui.helpers import draw_text
from src.ui import dark_fantasy_theme as theme
from src.config.settings import WIDTH, HEIGHT
from src.config.colors import (
    BLACK,
    WHITE,
    GOLD,
    RED,
    GRAY,
    BUTTON_BG,
    BUTTON_HOVER,
)
from src.config.layout import CARD_WIDTH, CARD_HEIGHT


class CemeteryModal(BaseScene):
    """Modal de interface do Cemitério.

    Permite descartes repetidos por 1 energia cada e uma troca gratuita por turno.
    Cartas descartadas ficam fora da mão até nova compra.
    """

    def __init__(
        self,
        scene_manager,
        window_manager,
        asset_manager,
        engine,
        on_discard_success=None,
        on_close=None,
    ):
        super().__init__(scene_manager, window_manager, asset_manager)
        self.engine = engine
        self.on_discard_success = on_discard_success
        self.on_close = on_close

        self.selected_index = None
        self.feedback_message = ""
        self.feedback_timer = 0

        # Dimensões da janela modal central
        self.modal_width = 1060
        self.modal_height = 540
        self.modal_rect = pygame.Rect(
            WIDTH // 2 - self.modal_width // 2,
            HEIGHT // 2 - self.modal_height // 2,
            self.modal_width,
            self.modal_height,
        )

        # Ações independentes: descarte livre, troca única e fechamento.
        button_y = self.modal_rect.bottom - 74
        self.discard_button_rect = pygame.Rect(WIDTH // 2 - 360, button_y, 224, 48)
        self.swap_button_rect = pygame.Rect(WIDTH // 2 - 112, button_y, 224, 48)
        self.close_button_rect = pygame.Rect(WIDTH // 2 + 136, button_y, 224, 48)

    def _get_card_rects(self, count):
        """Centraliza as cartas e reduz seu tamanho em mãos muito grandes."""
        if count <= 0:
            return []
        spacing = 12
        usable_width = self.modal_rect.width - 80
        card_width = min(CARD_WIDTH, max(46, (usable_width - (count - 1) * spacing) // count))
        card_height = int(CARD_HEIGHT * (card_width / CARD_WIDTH))
        total_width = count * card_width + (count - 1) * spacing
        start_x = WIDTH // 2 - total_width // 2
        y = self.modal_rect.top + 185
        return [pygame.Rect(start_x + i * (card_width + spacing), y, card_width, card_height)
                for i in range(count)]

    def update(self, dt):
        if self.feedback_timer > 0:
            self.feedback_timer -= dt
            if self.feedback_timer <= 0:
                self.feedback_message = ""

    def draw(self, surface):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((3, 9, 9, 230))
        surface.blit(overlay, (0, 0))
        theme.panel(surface, self.modal_rect, highlighted=True)
        theme.divider(surface, self.modal_rect.x + 72, self.modal_rect.right - 72,
                      self.modal_rect.y + 129)

        draw_text(surface, "CEMITÉRIO", self.asset_manager.big_font, WHITE,
                  WIDTH // 2, self.modal_rect.top + 33, center=True)
        draw_text(surface, "Descarte: 1 energia por carta (sem limite fixo de usos por turno).",
                  self.asset_manager.small_font, WHITE, WIDTH // 2,
                  self.modal_rect.top + 74, center=True)

        swap_available = not self.engine.cemetery_swap_used
        swap_text = "Troca grátis disponível: 1/1" if swap_available else "Troca grátis já usada: 0/1"
        draw_text(surface, "Trocar: descarte uma carta e compre outra (1 vez por turno, sem energia).",
                  self.asset_manager.small_font, (179, 187, 170),
                  WIDTH // 2, self.modal_rect.top + 100, center=True)
        draw_text(surface, swap_text, self.asset_manager.small_font,
                  GOLD if swap_available else GRAY,
                  WIDTH // 2, self.modal_rect.top + 145, center=True)

        hand = self.engine.hand
        mouse_pos = self.window_manager.get_virtual_mouse_pos()
        card_rects = self._get_card_rects(len(hand))
        if not hand:
            draw_text(surface, "A mão está vazia. Volte no próximo turno para comprar novas cartas.",
                      self.asset_manager.small_font, GRAY, WIDTH // 2,
                      self.modal_rect.centery, center=True)
        else:
            for index, (rect, card) in enumerate(zip(card_rects, hand)):
                selected = self.selected_index == index
                hovered = rect.collidepoint(mouse_pos)
                CardView.draw_card(surface, rect, card, self.asset_manager,
                                   hovered=(hovered or selected))
                if selected:
                    # Mantém a seleção no mesmo deslocamento do efeito hover.
                    draw_rect = rect.move(0, -12)
                    pygame.draw.rect(surface, GOLD, draw_rect.inflate(8, 8), 3, border_radius=12)
                    draw_text(surface, "SELECIONADA", self.asset_manager.small_font,
                              GOLD, draw_rect.centerx, draw_rect.top - 17, center=True)

        if self.feedback_message:
            draw_text(surface, self.feedback_message, self.asset_manager.small_font,
                      (205, 186, 137), WIDTH // 2,
                      self.modal_rect.bottom - 100, center=True)

        index_valid = self.selected_index is not None and 0 <= self.selected_index < len(hand)
        can_discard = index_valid and self.engine.can_use_cemetery()
        can_swap = index_valid and self.engine.can_swap_cemetery(self.selected_index)
        theme.button(surface, self.discard_button_rect, "DESCARTAR (1 E)",
                     self.asset_manager.small_font,
                     hover=self.discard_button_rect.collidepoint(mouse_pos) and can_discard,
                     enabled=can_discard, prominent=True)
        theme.button(surface, self.swap_button_rect,
                     "TROCA USADA" if self.engine.cemetery_swap_used else "TROCAR (1/TURNO)",
                     self.asset_manager.small_font,
                     hover=self.swap_button_rect.collidepoint(mouse_pos) and can_swap,
                     enabled=can_swap)
        theme.button(surface, self.close_button_rect, "FECHAR", self.asset_manager.small_font,
                     hover=self.close_button_rect.collidepoint(mouse_pos))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._close()
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        point = self.window_manager.map_to_virtual(event.pos)
        if self.close_button_rect.collidepoint(point):
            self._close()
            return

        card_rects = self._get_card_rects(len(self.engine.hand))
        for index, rect in enumerate(card_rects):
            if rect.collidepoint(point):
                self.selected_index = None if self.selected_index == index else index
                self.feedback_message = ""
                return

        if self.discard_button_rect.collidepoint(point):
            self._attempt_action("discard")
        elif self.swap_button_rect.collidepoint(point):
            self._attempt_action("swap")

    def _attempt_action(self, action):
        if self.selected_index is None or not 0 <= self.selected_index < len(self.engine.hand):
            self.feedback_message = "Selecione uma carta primeiro."
            self.feedback_timer = 2200
            return
        if action == "swap":
            success = self.engine.swap_cemetery(self.selected_index)
        else:
            success = self.engine.use_cemetery(self.selected_index)
        if success:
            self.selected_index = None
            self.feedback_message = self.engine.message
            self.feedback_timer = 2500
            if self.on_discard_success:
                self.on_discard_success()
            # Mantém o modal aberto para outros descartes ou para a troca.
        else:
            self.feedback_message = self.engine.message or "Não foi possível realizar essa ação."
            self.feedback_timer = 2200

    def _close(self):
        """Fecha o modal e executa callbacks de encerramento."""
        self.scene_manager.pop_modal()
        if self.on_close:
            self.on_close()
