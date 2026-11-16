"""Contador opcional de quadros por segundo, desenhado sobre a cena ativa."""

import pygame

from src.config.settings import WIDTH
from src.ui.helpers import draw_text

FPS_COUNTER_WIDTH = 116
FPS_COUNTER_HEIGHT = 30
FPS_COUNTER_TOP = 6


def draw_fps(surface, font, fps):
    """Mostra o FPS no topo central, acima do conteúdo das cenas."""
    rect = pygame.Rect(
        WIDTH // 2 - FPS_COUNTER_WIDTH // 2,
        FPS_COUNTER_TOP,
        FPS_COUNTER_WIDTH,
        FPS_COUNTER_HEIGHT,
    )
    pygame.draw.rect(surface, (7, 12, 12), rect, border_radius=6)
    pygame.draw.rect(surface, (91, 83, 61), rect, 1, border_radius=6)
    draw_text(
        surface,
        f"FPS {int(round(fps))}",
        font,
        (205, 200, 170),
        rect.centerx,
        rect.centery,
        center=True,
    )
