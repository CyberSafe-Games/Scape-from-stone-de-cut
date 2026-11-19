"""Cartas Ultimate no molde LV2, com custo único e regras vindas do modelo."""
import pygame

from src.ui.card_rules import with_player_rules
from src.ui.helpers import draw_text


def build_ultimate_card(art, meta, assets, layout):
    if art is None:
        art = pygame.Surface(layout['size'], pygame.SRCALPHA)
        pygame.draw.rect(art, (9, 17, 17), art.get_rect(), border_radius=12)
        pygame.draw.rect(art, (188, 140, 59), art.get_rect(), 4, border_radius=12)
        draw_text(art, meta['name'], assets.small_font, (247, 214, 135), 156, 255, center=True)
        layout = dict(layout, description='')
    card = with_player_rules(art, layout, meta['energy_cost'], meta['description'], 1)
    if meta['energy_cost'] != layout['energy_cost']:
        footer = pygame.Rect(layout['footer_rect'])
        pygame.draw.rect(card, (5, 14, 13), footer)
        text = pygame.font.Font(None, 20).render(
            f"ULTIMATE - {meta['energy_cost']} ENERGIA", True, (245, 206, 123))
        card.blit(text, text.get_rect(center=footer.center))
    return card
