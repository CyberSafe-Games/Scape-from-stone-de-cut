"""Moldura suprema no mesmo formato 450 x 660 das cartas comuns.

A ilustração é uma imagem; regras, carga e tipografia vêm do modelo real.
"""
import pygame
from src.ui.helpers import draw_text, wrap_text


def build_ultimate_card(art, meta, assets):
    card = pygame.Surface((450, 660), pygame.SRCALPHA)
    gold, light, dark = (188, 140, 59), (247, 214, 135), (56, 40, 22)
    accent = meta['accent_color']
    pygame.draw.rect(card, (9, 17, 17), card.get_rect(), border_radius=18)
    pygame.draw.rect(card, gold, card.get_rect().inflate(-3, -3), 6, border_radius=18)
    pygame.draw.rect(card, dark, card.get_rect().inflate(-18, -18), 5, border_radius=11)
    pygame.draw.rect(card, light, card.get_rect().inflate(-30, -30), 2, border_radius=8)
    if art is not None:
        card.blit(pygame.transform.smoothscale(art, (405, 338)), (23, 33))
    pygame.draw.rect(card, gold, (20, 30, 411, 344), 3)
    # Entalhes e gemas marcam a raridade sem mudar a proporção da carta.
    for x, y, dx, dy in ((15, 15, 1, 1), (435, 15, -1, 1),
                         (15, 645, 1, -1), (435, 645, -1, -1)):
        pygame.draw.lines(card, light, False, [(x, y+dy*33), (x, y), (x+dx*33, y)], 3)
        pygame.draw.polygon(card, dark, [(x, y+dy*5), (x+dx*17, y+dy*18), (x, y+dy*32)])
        pygame.draw.circle(card, accent, (x+dx*9, y+dy*12), 5)
    badge = [(47, 18), (84, 56), (47, 93), (9, 56)]
    pygame.draw.polygon(card, (4, 12, 15), badge)
    pygame.draw.lines(card, light, True, badge, 3)
    draw_text(card, str(meta['charge_requirement']), assets.menu_font, light, 47, 54, center=True)
    pygame.draw.rect(card, (13, 20, 19), (20, 374, 411, 65))
    pygame.draw.rect(card, gold, (20, 374, 411, 65), 3)
    title_font = assets.menu_font if assets.menu_font.size(meta['name'])[0] < 390 else assets.font
    draw_text(card, meta['name'], title_font, light, 225, 405, center=True)
    lines = wrap_text(meta['description'], assets.font, 387)
    step = 32
    top = 525-(len(lines)-1)*step//2
    for i, line in enumerate(lines):
        draw_text(card, line, assets.font, (231, 225, 200), 225, top+i*step, center=True)
    pygame.draw.line(card, dark, (42, 614), (408, 614))
    draw_text(card, 'ULTIMATE  ·  SEM CUSTO', assets.small_font, accent, 225, 632, center=True)
    for x in (138, 312):
        pygame.draw.polygon(card, light, [(x, 17), (x+8, 24), (x, 32), (x-8, 24)])
    return card
