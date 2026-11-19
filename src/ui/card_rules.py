"""Composição de regras atualizadas, preservando os PNGs originais."""
import pygame
from src.ui.helpers import wrap_text


def with_rules(image, description, cost=None, level=None):
    result = image.copy()
    w, h = result.get_size()
    area = pygame.Rect(round(w * .055), round(h * .612), round(w * .89), round(h * .34))
    pygame.draw.rect(result, (7, 15, 14), area)
    size = max(12, round(w * .065))
    while True:
        font = pygame.font.Font(None, size)
        lines = wrap_text(description, font, area.width - 14)
        if len(lines) * font.get_linesize() <= area.height - 12 or size <= 10:
            break
        size -= 1
    y = area.centery - len(lines) * font.get_linesize() // 2
    for line in lines:
        text = font.render(line, True, (239, 220, 175))
        result.blit(text, text.get_rect(centerx=area.centerx, top=y))
        y += font.get_linesize()
    if cost is not None:
        # Oculta a região inteira dos dois badges impressos nos PNGs antigos.
        # O recobrimento é opaco e idempotente, inclusive ao recompor LV1 em LV2.
        corner = [(2, 2), (round(w * .33), 2),
                  (round(w * .33), round(h * .10)),
                  (round(w * .20), round(h * .20)), (2, round(h * .20))]
        pygame.draw.polygon(result, (7, 15, 14), corner)
        center = (round(w * .14), round(h * .095))
        radius = round(w * .12)
        diamond = [(center[0], center[1] - radius),
                   (center[0] + radius, center[1]),
                   (center[0], center[1] + radius),
                   (center[0] - radius, center[1])]
        pygame.draw.polygon(result, (19, 22, 15), diamond)
        pygame.draw.polygon(result, (215, 173, 91), diamond, max(1, round(w * .007)))
        font = pygame.font.Font(None, max(14, round(w * .115)))
        text = font.render(str(cost), True, (255, 223, 158))
        if text.get_width() > radius * 1.25:
            ratio = radius * 1.25 / text.get_width()
            text = pygame.transform.smoothscale(text, (
                max(1, round(text.get_width() * ratio)),
                max(1, round(text.get_height() * ratio))))
        result.blit(text, text.get_rect(center=center))
    if level is not None:
        text = pygame.font.Font(None, max(14, round(w * .07))).render(f'LV{level}', True, (255, 216, 118))
        box = text.get_rect(topright=(w - 18, 15)).inflate(8, 4)
        pygame.draw.rect(result, (10, 18, 16), box)
        result.blit(text, text.get_rect(center=box.center))
    return result
