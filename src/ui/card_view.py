import pygame
from src.config.settings import WIDTH, HEIGHT
from src.config.colors import CARD_BG, WHITE
from src.config.layout import CARD_WIDTH, CARD_HEIGHT, CARD_SPACING
from src.ui.helpers import draw_text


class CardView:
    """Responsável por calcular posições e renderizar as cartas na tela."""

    @staticmethod
    def draw_card(surface, rect, card, asset_manager, hovered=False):
        """Desenha a arte PNG completa da carta; caso não exista, desenha um fallback com borda colorida."""
        draw_rect = rect.move(0, -14 if hovered else 0)
        image = asset_manager.get_card_image(card.name)

        if image is not None:
            scaled = pygame.transform.smoothscale(image, draw_rect.size)
            surface.blit(scaled, draw_rect)
            return

        pygame.draw.rect(surface, CARD_BG, draw_rect, border_radius=10)
        pygame.draw.rect(surface, card.color, draw_rect, 3, border_radius=10)
        draw_text(
            surface,
            card.name,
            asset_manager.font,
            WHITE,
            draw_rect.centerx,
            draw_rect.centery,
            center=True,
        )

    @staticmethod
    def get_hand_rects(count):
        """Calcula os retângulos de colisão para as cartas na mão do jogador."""
        rects = []
        if count == 0:
            return rects

        total_width = count * CARD_WIDTH + (count - 1) * CARD_SPACING
        start_x = WIDTH // 2 - total_width // 2
        y = HEIGHT - CARD_HEIGHT - 20

        for index in range(count):
            x = start_x + index * (CARD_WIDTH + CARD_SPACING)
            rects.append(pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT))

        return rects

    @staticmethod
    def get_reward_rects(count):
        """Calcula os retângulos de colisão para as cartas oferecidas como recompensa."""
        rects = []
        if count == 0:
            return rects

        spacing = 20
        total_width = count * CARD_WIDTH + (count - 1) * spacing
        start_x = WIDTH // 2 - total_width // 2
        y = HEIGHT // 2 - CARD_HEIGHT // 2

        for index in range(count):
            x = start_x + index * (CARD_WIDTH + spacing)
            rects.append(pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT))

        return rects
