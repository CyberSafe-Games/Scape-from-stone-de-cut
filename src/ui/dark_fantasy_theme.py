"""Padrões visuais compartilhados por menu, saves, mapa e modais.

Todos os desenhos são feitos por Pygame, sem fonte externa obrigatória,
sem alterar eventos/retângulos clicáveis e sem assets adicionais.
"""
import pygame
from src.config.settings import WIDTH, HEIGHT
from src.config.colors import (
    BG, WHITE, GRAY, GOLD, STONE, STONE_RAISED, BRONZE_DARK,
    BRONZE_LIGHT, BUTTON_BG, BUTTON_HOVER, DISABLED,
)
from src.ui.helpers import draw_text


def _bevel_polygon(rect, bevel=10):
    r = pygame.Rect(rect)
    b = min(bevel, r.height // 4, r.width // 4)
    return [(r.left+b, r.top), (r.right-b, r.top),
            (r.right, r.top+b), (r.right, r.bottom-b),
            (r.right-b, r.bottom), (r.left+b, r.bottom),
            (r.left, r.bottom-b), (r.left, r.top+b)]


def backdrop(surface, background=None, opacity=196, focal_side="left"):
    """A mesma atmosfera noturna em todas as telas, com contraste controlado."""
    if background is None:
        surface.fill(BG)
    else:
        surface.blit(background, (0, 0))
    veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    veil.fill((4, 11, 11, opacity))
    # Mais profundidade nas laterais, preservando um pouco do cenário original.
    for n in range(12):
        span = 32
        a = max(1, 19 - n)
        pygame.draw.rect(veil, (0, 0, 0, a), (n * span, 0, span, HEIGHT))
        pygame.draw.rect(veil, (0, 0, 0, a), (WIDTH - (n + 1) * span, 0, span, HEIGHT))
    surface.blit(veil, (0, 0))
    # Ornamentação arquitetônica sutil, sem competir com a interface.
    color = (75, 68, 52)
    pygame.draw.line(surface, color, (33, 28), (33, HEIGHT - 27), 1)
    pygame.draw.line(surface, color, (WIDTH-33, 28), (WIDTH-33, HEIGHT-27), 1)
    pygame.draw.line(surface, (52, 51, 43), (38, HEIGHT-27), (WIDTH-38, HEIGHT-27), 1)


def panel(surface, rect, highlighted=False, fill=None, border=None):
    """Moldura octogonal de pedra/ferro, com bronze discreto e cantos esculpidos."""
    rect = pygame.Rect(rect)
    shadow = rect.move(4, 6)
    pygame.draw.polygon(surface, (3, 6, 6), _bevel_polygon(shadow, 11))
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    local = pygame.Rect(0, 0, rect.width, rect.height)
    bg = fill if fill is not None else (14, 21, 21, 238)
    edge = border or (BRONZE_LIGHT if highlighted else BRONZE_DARK)
    pygame.draw.polygon(layer, bg, _bevel_polygon(local, 10))
    pygame.draw.lines(layer, edge, True, _bevel_polygon(local, 10), 2 if highlighted else 1)
    inset = local.inflate(-10, -10)
    pygame.draw.lines(layer, (61, 65, 56, 130), True, _bevel_polygon(inset, 7), 1)
    pygame.draw.line(layer, (*edge, 180), (22, 6), (min(rect.width-22, 92), 6), 2)
    surface.blit(layer, rect.topleft)
    for cx, cy, xs, ys in [
        (rect.left+14, rect.top+14, 1, 1),
        (rect.right-14, rect.top+14, -1, 1),
        (rect.left+14, rect.bottom-14, 1, -1),
        (rect.right-14, rect.bottom-14, -1, -1),
    ]:
        pygame.draw.line(surface, edge, (cx, cy), (cx+xs*9, cy), 1)
        pygame.draw.line(surface, edge, (cx, cy), (cx, cy+ys*9), 1)


def divider(surface, x1, x2, y, color=BRONZE_DARK):
    pygame.draw.line(surface, color, (x1, y), (x2, y), 1)
    mid = (x1 + x2) // 2
    pygame.draw.polygon(surface, GOLD, [(mid, y-4), (mid+5, y), (mid, y+4), (mid-5, y)])


def button(surface, rect, label, font, hover=False, prominent=False, enabled=True, danger=False):
    rect = pygame.Rect(rect)
    if not enabled:
        bg, edge, fg = (26, 29, 29), DISABLED, (114, 119, 114)
    elif danger:
        bg, edge, fg = ((66, 35, 32) if hover else (39, 28, 27)), (144, 75, 65), WHITE
    elif prominent:
        bg = (76, 63, 42) if hover else (49, 46, 33)
        edge, fg = BRONZE_LIGHT, WHITE
    else:
        bg = BUTTON_HOVER if hover else BUTTON_BG
        edge, fg = BRONZE_LIGHT if hover else BRONZE_DARK, WHITE
    pygame.draw.rect(surface, (2, 5, 5), rect.move(2, 4), border_radius=3)
    pygame.draw.polygon(surface, bg, _bevel_polygon(rect, 7))
    pygame.draw.lines(surface, edge, True, _bevel_polygon(rect, 7), 2 if hover else 1)
    pygame.draw.line(surface, edge, (rect.left + 9, rect.top + 11),
                     (rect.left + 9, rect.bottom - 11), 2)
    if prominent:
        x = rect.right - 19
        pygame.draw.polygon(surface, BRONZE_LIGHT,
                            [(x, rect.centery-4), (x+5, rect.centery),
                             (x, rect.centery+4), (x-5, rect.centery)])
    draw_text(surface, label, font, fg, rect.centerx, rect.centery, center=True)


def eyebrow(surface, text, font, x, y, center=False):
    draw_text(surface, text, font, BRONZE_LIGHT, x, y, center=center)


def footer(surface, text, font):
    draw_text(surface, text, font, (133, 139, 128), WIDTH // 2, HEIGHT-31, center=True)
