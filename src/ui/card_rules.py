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
        box = pygame.Rect(round(w * .052), round(h * .041), round(w * .09), round(h * .055))
        pygame.draw.rect(result, (17, 16, 10), box)
        text = pygame.font.Font(None, max(14, round(w * .1))).render(str(cost), True, (255, 223, 158))
        result.blit(text, text.get_rect(center=box.center))
    if level is not None:
        text = pygame.font.Font(None, max(14, round(w * .07))).render(f'LV{level}', True, (255, 216, 118))
        box = text.get_rect(topright=(w - 18, 15)).inflate(8, 4)
        pygame.draw.rect(result, (10, 18, 16), box)
        result.blit(text, text.get_rect(center=box.center))
    return result
