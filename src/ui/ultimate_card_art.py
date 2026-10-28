"""Moldura suprema no mesmo formato 300 x 440 das cartas comuns.

A ilustração é uma imagem; regras, carga e tipografia vêm do modelo real.
"""
import pygame
from src.ui.helpers import draw_text, wrap_text


def build_ultimate_card(art, meta, assets):
    card = pygame.Surface((300, 440), pygame.SRCALPHA)
    gold, light, dark = (188, 140, 59), (247, 214, 135), (56, 40, 22)
    accent = meta['accent_color']
    pygame.draw.rect(card, (9, 17, 17), card.get_rect(), border_radius=12)
    pygame.draw.rect(card, gold, card.get_rect().inflate(-2, -2), 4, border_radius=12)
    pygame.draw.rect(card, dark, card.get_rect().inflate(-12, -12), 3, border_radius=7)
    pygame.draw.rect(card, light, card.get_rect().inflate(-20, -20), 1, border_radius=5)
    if art is not None:
        card.blit(pygame.transform.smoothscale(art, (270, 225)), (15, 22))
    pygame.draw.rect(card, gold, (13, 20, 274, 229), 2)
    # Entalhes e gemas marcam a raridade sem mudar a proporção da carta.
    for x, y, dx, dy in ((10, 10, 1, 1), (290, 10, -1, 1),
                         (10, 430, 1, -1), (290, 430, -1, -1)):
        pygame.draw.lines(card, light, False, [(x, y+dy*22), (x, y), (x+dx*22, y)], 2)
        pygame.draw.polygon(card, dark, [(x, y+dy*3), (x+dx*11, y+dy*12), (x, y+dy*21)])
        pygame.draw.circle(card, accent, (x+dx*6, y+dy*8), 3)
    badge = [(31, 12), (56, 37), (31, 62), (6, 37)]
    pygame.draw.polygon(card, (4, 12, 15), badge)
    pygame.draw.lines(card, light, True, badge, 2)
    draw_text(card, str(meta['charge_requirement']), assets.menu_font, light, 31, 36, center=True)
    pygame.draw.rect(card, (13, 20, 19), (13, 249, 274, 43))
    pygame.draw.rect(card, gold, (13, 249, 274, 43), 2)
    title_font = assets.menu_font if assets.menu_font.size(meta['name'])[0] < 260 else assets.font
    draw_text(card, meta['name'], title_font, light, 150, 270, center=True)
    lines = wrap_text(meta['description'], assets.font, 258)
    step = 21
    top = 350-(len(lines)-1)*step//2
    for i, line in enumerate(lines):
        draw_text(card, line, assets.font, (231, 225, 200), 150, top+i*step, center=True)
    pygame.draw.line(card, dark, (28, 409), (272, 409))
    draw_text(card, 'ULTIMATE  ·  SEM CUSTO', assets.small_font, accent, 150, 421, center=True)
    for x in (92, 208):
        pygame.draw.polygon(card, light, [(x, 11), (x+5, 16), (x, 21), (x-5, 16)])
    return card
