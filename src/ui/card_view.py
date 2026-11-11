import pygame
from src.config.settings import WIDTH, HEIGHT
from src.config.colors import CARD_BG, WHITE
from src.config.layout import CARD_WIDTH, CARD_HEIGHT, CARD_SPACING
from src.ui.helpers import draw_text, draw_panel, wrap_text


class CardView:
    """Responsável por calcular posições e renderizar as cartas na tela."""

    @staticmethod
    def draw_tooltip(surface, card, assets, point, cost_label=None):
        lines = wrap_text(card.description, assets.font, 525)
        height = 84 + len(lines) * 35
        rect = pygame.Rect(min(WIDTH - 585, max(15, int(point[0]) - 285)),
                           max(18, min(HEIGHT - height - 18, int(point[1]) - height - 30)), 570, height)
        draw_panel(surface, rect, fill=(8, 16, 16, 250), border=(169, 127, 66), radius=11)
        title_font = assets.font if assets.font.size(card.name)[0] < 450 else assets.small_font
        draw_text(surface, card.name, title_font, WHITE, rect.x + 23, rect.y + 18)
        draw_text(surface, cost_label or f'{card.cost} E', assets.small_font, (239, 199, 111), rect.right - 72, rect.y + 23)
        for i, line in enumerate(lines):
            draw_text(surface, line, assets.font, (218, 220, 202), rect.x + 23, rect.y + 63 + i * 35)

    @staticmethod
    def draw_card(surface, rect, card, asset_manager, hovered=False):
        """Desenha a arte PNG completa da carta; caso não exista, desenha um fallback com borda colorida."""
        draw_rect = rect.move(0, -18 if hovered else 0)
        shadow = pygame.Surface((draw_rect.width + 15, draw_rect.height + 15), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 110), (8, 8, draw_rect.width, draw_rect.height), border_radius=18)
        surface.blit(shadow, (draw_rect.x - 8, draw_rect.y - 5))

        image = asset_manager.get_card_image(card.name)
        if image is not None:
            scaled = pygame.transform.smoothscale(image, draw_rect.size)
            surface.blit(scaled, draw_rect)
            if hovered:
                pygame.draw.rect(surface, (245, 222, 160), draw_rect, 3, border_radius=15)
            return

        pygame.draw.rect(surface, CARD_BG, draw_rect, border_radius=15)
        pygame.draw.rect(surface, card.color, draw_rect, 5, border_radius=15)
        font = asset_manager.small_font
        padding = 12
        line_height = font.get_linesize()
        cost_surface = font.render(f'{card.cost} E', True, (239, 199, 111))
        cost_surface_rect = cost_surface.get_rect(topright=(draw_rect.right - padding, draw_rect.y + padding))
        surface.blit(cost_surface, cost_surface_rect)

        title_lines = wrap_text(card.name, font, max(35, draw_rect.width - 22))
        max_title_lines = max(
            1,
            (draw_rect.height - 2 * padding - 2 * line_height) // line_height,
        )
        if len(title_lines) > max_title_lines:
            title_lines = title_lines[:max_title_lines]
            title_lines[-1] = title_lines[-1].rstrip(' .') + '...'
        title_y = draw_rect.y + padding + line_height + 2
        for index, line in enumerate(title_lines):
            draw_text(
                surface,
                line,
                font,
                WHITE,
                draw_rect.centerx,
                title_y + index * line_height,
                center=True,
            )
        if draw_rect.width >= 112 and draw_rect.height >= 155:
            description_lines = wrap_text(card.description, font, draw_rect.width - 22)
            available_lines = max(
                1,
                (draw_rect.bottom - padding - title_y - len(title_lines) * line_height)
                // line_height,
            )
            if len(description_lines) > available_lines:
                description_lines = description_lines[:available_lines]
                description_lines[-1] = description_lines[-1].rstrip(' .') + '...'
            description_y = title_y + len(title_lines) * line_height + 5
            for index, line in enumerate(description_lines):
                draw_text(
                    surface,
                    line,
                    font,
                    (218, 220, 202),
                    draw_rect.centerx,
                    description_y + index * line_height,
                    center=True,
                )

    @staticmethod
    def get_hand_rects(count):
        """Calcula os retângulos de colisão para as cartas na mão do jogador."""
        rects = []
        if count == 0:
            return rects

        # Mãos persistentes podem acumular cartas extras (ex.: Mana Ancestral).
        # Encolhe apenas quando necessário, para não invadir Cemitério/fim do turno.
        max_width = WIDTH - 435
        spacing = CARD_SPACING
        card_width = min(CARD_WIDTH, max(63, (max_width - (count - 1) * spacing) // count))
        card_height = max(105, round(CARD_HEIGHT * card_width / CARD_WIDTH))
        total_width = count * card_width + (count - 1) * spacing
        start_x = WIDTH // 2 - total_width // 2
        y = HEIGHT - card_height - 27

        for index in range(count):
            x = start_x + index * (card_width + spacing)
            rects.append(pygame.Rect(x, y, card_width, card_height))

        return rects

    @staticmethod
    def get_reward_rects(count):
        """Calcula os retângulos de colisão para as cartas oferecidas como recompensa."""
        rects = []
        if count == 0:
            return rects

        spacing = 30
        total_width = count * CARD_WIDTH + (count - 1) * spacing
        start_x = WIDTH // 2 - total_width // 2
        y = HEIGHT // 2 - CARD_HEIGHT // 2

        for index in range(count):
            x = start_x + index * (CARD_WIDTH + spacing)
            rects.append(pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT))

        return rects
