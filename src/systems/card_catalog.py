from src.models.card import Card
from src.models.effects.tactical_card_effect import TacticalCardEffect
from src.models.effects.extended_card_effect import ExtendedCardEffect
from src.systems.card_definitions import ADDITIONAL_CARD_SPECS, CARD_SPECS
from src.config.colors import RED, BLUE, GOLD

ALL_CARD_SPECS = CARD_SPECS + ADDITIONAL_CARD_SPECS
# Retire daqui as cartas novas conforme a arte e a animação forem entregues.
UNAVAILABLE_CARD_NAMES = frozenset(spec[1] for spec in ADDITIONAL_CARD_SPECS)
CARD_POOL = [
    Card(
        s[1], s[2], s[3], s[4], s[7],
        {'attack': RED, 'skill': BLUE, 'power': GOLD}[s[3]],
        effect=ExtendedCardEffect(s) if len(s) > 8 else TacticalCardEffect(s),
        available=s[1] not in UNAVAILABLE_CARD_NAMES,
    )
    for s in ALL_CARD_SPECS
]
CARD_BY_NAME = {card.name: card for card in CARD_POOL}
AVAILABLE_CARD_POOL = [card for card in CARD_POOL if card.available]
AVAILABLE_CARD_NAMES = frozenset(card.name for card in AVAILABLE_CARD_POOL)


def create_starting_deck():
    return [CARD_BY_NAME[name].copy() for name in ('Soco Simples', 'Esfera Protetora') for _ in range(3)]
