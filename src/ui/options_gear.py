"""Botão discreto de engrenagem para abrir as Opções durante o gameplay."""

import math

import pygame

from src.config.options_layout import (
    OPTIONS_GEAR_RIGHT_MARGIN,
    OPTIONS_GEAR_SIZE,
    OPTIONS_GEAR_TOP,
)
from src.config.settings import WIDTH
from src.config.colors import GOLD

OPTIONS_GEAR_RECT = pygame.Rect(
    WIDTH - OPTIONS_GEAR_RIGHT_MARGIN - OPTIONS_GEAR_SIZE,
    OPTIONS_GEAR_TOP,
    OPTIONS_GEAR_SIZE,
    OPTIONS_GEAR_SIZE,
)


def draw_options_gear(surface, window_manager):
    """Desenha a engrenagem no canto superior direito, com destaque no hover."""
    rect = OPTIONS_GEAR_RECT
    hovered = rect.collidepoint(window_manager.get_virtual_mouse_pos())
    edge = GOLD if hovered else (132, 113, 76)
    fill = (37, 44, 39) if hovered else (22, 29, 27)
    pygame.draw.rect(surface, (2, 5, 5), rect.move(3, 5), border_radius=7)
    pygame.draw.rect(surface, fill, rect, border_radius=7)
    pygame.draw.rect(surface, edge, rect, 2, border_radius=7)

    center = rect.center
    radius = 13
    pygame.draw.circle(surface, edge, center, radius, 3)
    for index in range(8):
        angle = index * 45
        radians = math.radians(angle)
        inner = (
            center[0] + round((radius - 1) * math.cos(radians)),
            center[1] + round((radius - 1) * math.sin(radians)),
        )
        outer = (
            center[0] + round((radius + 6) * math.cos(radians)),
            center[1] + round((radius + 6) * math.sin(radians)),
        )
        pygame.draw.line(surface, edge, inner, outer, 4)
    pygame.draw.circle(surface, fill, center, 4)
    pygame.draw.circle(surface, edge, center, 4, 2)


def options_gear_clicked(point):
    return OPTIONS_GEAR_RECT.collidepoint(point)
