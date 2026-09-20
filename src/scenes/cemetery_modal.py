import pygame

from src.scenes.base_scene import BaseScene
from src.ui.card_view import CardView
from src.ui.helpers import draw_text
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

    Permite ao jogador inspecionar as cartas da mão e descartar uma carta
    selecionada ao custo de 1 de energia.
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

        # Botões de ação do rodapé
        button_y = self.modal_rect.bottom - 75
        self.discard_button_rect = pygame.Rect(
            WIDTH // 2 - 210, button_y, 190, 50
        )
        self.close_button_rect = pygame.Rect(
            WIDTH // 2 + 20, button_y, 190, 50
        )

    def _get_card_rects(self, count):
        """Calcula os retângulos de colisão para as cartas disponíveis dentro do modal."""
        rects = []
        if count == 0:
            return rects

        spacing = 16
        total_width = count * CARD_WIDTH + (count - 1) * spacing
        start_x = WIDTH // 2 - total_width // 2
        y = self.modal_rect.top + 145

        for index in range(count):
            x = start_x + index * (CARD_WIDTH + spacing)
            rects.append(pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT))

        return rects

    def update(self, dt):
        if self.feedback_timer > 0:
            self.feedback_timer -= dt
            if self.feedback_timer <= 0:
                self.feedback_message = ""

    def draw(self, surface):
        # 1. Overlay escurecido de fundo
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(225)
        overlay.fill((8, 6, 14))
        surface.blit(overlay, (0, 0))

        # 2. Painel central do Cemitério com borda temática
        panel = pygame.Surface((self.modal_width, self.modal_height), pygame.SRCALPHA)
        panel.fill((22, 18, 34, 245))
        pygame.draw.rect(
            panel,
            (145, 95, 205),
            (0, 0, self.modal_width, self.modal_height),
            3,
            border_radius=16,
        )
        pygame.draw.rect(
            panel,
            (70, 45, 105),
            (6, 6, self.modal_width - 12, self.modal_height - 12),
            1,
            border_radius=12,
        )
        surface.blit(panel, (self.modal_rect.x, self.modal_rect.y))

        # 3. Cabeçalho estilizado
        draw_text(
            surface,
            "CEMITÉRIO",
            self.asset_manager.big_font,
            (215, 175, 255),
            WIDTH // 2,
            self.modal_rect.top + 35,
            center=True,
        )
        draw_text(
            surface,
            "Selecione uma carta da sua mão para descartar. Custo: 1 Energia.",
            self.asset_manager.font,
            WHITE,
            WIDTH // 2,
            self.modal_rect.top + 70,
            center=True,
        )

        # 4. Status de Energia
        player = self.engine.player
        has_energy = player.can_use_cemetery()
        energy_color = (100, 220, 255) if has_energy else (255, 90, 90)
        energy_text = (
            f"Energia Disponível: {player.energy}/{player.energy_max}   |   Custo: 1 Energia"
        )
        draw_text(
            surface,
            energy_text,
            self.asset_manager.font,
            energy_color,
            WIDTH // 2,
            self.modal_rect.top + 102,
            center=True,
        )

        # 5. Lista de cartas na mão disponíveis para descarte
        hand = self.engine.hand
        mouse_pos = self.window_manager.get_virtual_mouse_pos()
        card_rects = self._get_card_rects(len(hand))

        if not hand:
            draw_text(
                surface,
                "Sua mão está vazia! Nenhuma carta disponível para descarte.",
                self.asset_manager.font,
                GRAY,
                WIDTH // 2,
                self.modal_rect.centery,
                center=True,
            )
        else:
            for index, (rect, card) in enumerate(zip(card_rects, hand)):
                is_selected = (self.selected_index == index)
                hovered = rect.collidepoint(mouse_pos)

                # Desenha a carta com o renderer oficial
                CardView.draw_card(
                    surface,
                    rect,
                    card,
                    self.asset_manager,
                    hovered=(hovered or is_selected),
                )

                # Destaque de seleção
                if is_selected:
                    draw_rect = rect.move(0, -14)
                    pygame.draw.rect(
                        surface,
                        GOLD,
                        draw_rect.inflate(8, 8),
                        4,
                        border_radius=12,
                    )
                    pygame.draw.rect(
                        surface,
                        (220, 150, 255),
                        draw_rect.inflate(14, 14),
                        2,
                        border_radius=14,
                    )
                    draw_text(
                        surface,
                        "SELECIONADA",
                        self.asset_manager.small_font,
                        GOLD,
                        draw_rect.centerx,
                        draw_rect.top - 16,
                        center=True,
                    )

        # 6. Mensagens de feedback / avisos
        if self.feedback_message:
            draw_text(
                surface,
                self.feedback_message,
                self.asset_manager.font,
                RED,
                WIDTH // 2,
                self.modal_rect.bottom - 110,
                center=True,
            )
        elif not has_energy:
            draw_text(
                surface,
                "Energia insuficiente para realizar o descarte!",
                self.asset_manager.small_font,
                (255, 110, 110),
                WIDTH // 2,
                self.modal_rect.bottom - 110,
                center=True,
            )

        # 7. Botão Descartar Carta
        can_discard = (
            self.selected_index is not None
            and 0 <= self.selected_index < len(hand)
            and has_energy
        )
        discard_hover = self.discard_button_rect.collidepoint(mouse_pos) and can_discard

        if can_discard:
            discard_bg = (130, 60, 165) if discard_hover else (95, 40, 125)
            discard_border = GOLD
            discard_text_color = WHITE
        else:
            discard_bg = (45, 42, 55)
            discard_border = (80, 75, 95)
            discard_text_color = GRAY

        pygame.draw.rect(
            surface, discard_bg, self.discard_button_rect, border_radius=10
        )
        pygame.draw.rect(
            surface, discard_border, self.discard_button_rect, 2, border_radius=10
        )
        draw_text(
            surface,
            "DESCARTAR (1 ENERGIA)",
            self.asset_manager.font,
            discard_text_color,
            self.discard_button_rect.centerx,
            self.discard_button_rect.centery,
            center=True,
        )

        # 8. Botão Fechar / Cancelar
        close_hover = self.close_button_rect.collidepoint(mouse_pos)
        close_bg = BUTTON_HOVER if close_hover else BUTTON_BG

        pygame.draw.rect(
            surface, close_bg, self.close_button_rect, border_radius=10
        )
        pygame.draw.rect(
            surface, (150, 140, 170), self.close_button_rect, 2, border_radius=10
        )
        draw_text(
            surface,
            "FECHAR",
            self.asset_manager.font,
            WHITE,
            self.close_button_rect.centerx,
            self.close_button_rect.centery,
            center=True,
        )

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._close()
                return

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            virt_pos = self.window_manager.map_to_virtual(event.pos)

            # Clique no botão Fechar
            if self.close_button_rect.collidepoint(virt_pos):
                self._close()
                return

            # Clique em uma carta da mão
            card_rects = self._get_card_rects(len(self.engine.hand))
            for idx, rect in enumerate(card_rects):
                if rect.collidepoint(virt_pos):
                    if self.selected_index == idx:
                        self.selected_index = None
                    else:
                        self.selected_index = idx
                    self.feedback_message = ""
                    return

            # Clique no botão Descartar
            if self.discard_button_rect.collidepoint(virt_pos):
                self._attempt_discard()

    def _attempt_discard(self):
        """Valida e processa o descarte pelo Cemitério."""
        if self.selected_index is None or self.selected_index >= len(self.engine.hand):
            self.feedback_message = "Selecione uma carta para descartar!"
            self.feedback_timer = 2000
            return

        if not self.engine.player.can_use_cemetery():
            self.feedback_message = "Energia insuficiente para usar o Cemitério!"
            self.feedback_timer = 2000
            return

        # Executa o descarte com consumo de energia e atualização das pilhas
        success = self.engine.use_cemetery(self.selected_index)
        if success:
            if self.on_discard_success:
                self.on_discard_success()
            self._close()
        else:
            self.feedback_message = self.engine.message or "Não foi possível descartar a carta."
            self.feedback_timer = 2000

    def _close(self):
        """Fecha o modal e executa callbacks de encerramento."""
        self.scene_manager.pop_modal()
        if self.on_close:
            self.on_close()
