from src.models.card import Card
from src.models.effects.tactical_card_effect import TacticalCardEffect
from src.systems.card_definitions import CARD_SPECS
from src.config.colors import RED, BLUE, GOLD

CARD_POOL = [Card(s[1], s[2], s[3], s[4], s[7],
                  {'attack': RED, 'skill': BLUE, 'power': GOLD}[s[3]],
                  effect=TacticalCardEffect(s)) for s in CARD_SPECS]
CARD_BY_NAME = {card.name: card for card in CARD_POOL}


def create_starting_deck():
    return [CARD_BY_NAME[name].copy() for name in ('Soco Simples', 'Esfera Protetora') for _ in range(3)]
