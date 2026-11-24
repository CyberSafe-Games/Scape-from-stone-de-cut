"""Brasões de resultado da arena."""

import math

import pygame


def build_outcome_banner(font, crest, *, defeat=False):
    banner = pygame.Surface((900, 284), pygame.SRCALPHA)
    cx, cy = banner.get_rect().center
    for radius in range(24, 0, -1):
        glow = pygame.Rect(0, 0, 35 * radius, 11 * radius)
        glow.center = (cx, cy)
        color = (126, 28, 24) if defeat else (197, 96, 23)
        pygame.draw.ellipse(banner, (*color, 3 + (24 - radius) * 3), glow)
    if crest is not None:
        bounds = crest.get_bounding_rect(min_alpha=32)
        if bounds:
            scale = min(822 / bounds.width, 246 / bounds.height)
            plate = pygame.transform.smoothscale(
                crest.subsurface(bounds),
                (round(bounds.width * scale), round(bounds.height * scale)),
            )
            if defeat:
                plate.fill((193, 116, 116, 255), special_flags=pygame.BLEND_RGBA_MULT)
            banner.blit(plate, plate.get_rect(center=(cx, cy)))
    else:
        rect = pygame.Rect(0, 0, 650, 141)
        rect.center = (cx, cy)
        pygame.draw.rect(banner, (32, 26, 20), rect, border_radius=16)
        pygame.draw.rect(banner, (177, 121, 56), rect, 3, border_radius=16)

    mask = font.render("DERROTA" if defeat else "VITÓRIA", True, (255, 255, 255))
    height = 72
    mask = pygame.transform.smoothscale(mask, (round(mask.get_width() * height / mask.get_height()), height))
    title = pygame.Surface(mask.get_size(), pygame.SRCALPHA)
    for row in range(height):
        shine = 1 - abs(row / height - 0.29)
        color = ((145 + round(100 * shine), 70 + round(103 * shine), 60 + round(90 * shine))
                 if defeat else (154 + round(99 * shine), 100 + round(122 * shine),
                                 48 + round(132 * shine)))
        pygame.draw.line(title, color, (0, row), (title.get_width(), row))
    title.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    shadow = mask.copy()
    shadow.fill((10, 9, 6, 210), special_flags=pygame.BLEND_RGBA_MULT)
    banner.blit(shadow, shadow.get_rect(center=(cx, cy + 5)))
    banner.blit(title, title.get_rect(center=(cx, cy)))
    return banner


def draw_victory_embers(surface, center, elapsed, opacity):
    if not opacity:
        return
    layer = pygame.Surface((900, 280), pygame.SRCALPHA)
    for index in range(30):
        phase = (elapsed / (770 + index % 5 * 140) + index * .147) % 1
        x = (index * 197 + 43) % 850 + 25
        x += math.sin(phase * math.tau + index) * 17
        y = 246 - phase * (130 + index % 5 * 20)
        alpha = round(215 * math.sin(phase * math.pi) * opacity)
        color = (251, 184 if index % 3 == 0 else 135, 54, alpha)
        pygame.draw.circle(layer, color, (round(x), round(y)), 1 + int(index % 3 == 0))
    surface.blit(layer, layer.get_rect(center=center))
