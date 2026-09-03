from src.models.card import Card
from src.config.colors import RED, BLUE, GOLD

CARD_POOL = [
    Card(
        name="Golpe",
        cost=1,
        card_type="attack",
        value=6,
        description="Cause 6 de dano",
        color=RED,
    ),
    Card(
        name="Defesa",
        cost=1,
        card_type="skill",
        value=5,
        description="Ganhe 5 de bloqueio",
        color=BLUE,
    ),
    Card(
        name="Investida",
        cost=2,
        card_type="attack",
        value=10,
        description="Cause 10 de dano",
        color=RED,
    ),
    Card(
        name="Fortalecer",
        cost=2,
        card_type="skill",
        value=8,
        description="Ganhe 8 de bloqueio",
        color=BLUE,
    ),
    Card(
        name="Fúria",
        cost=1,
        card_type="power",
        value=3,
        description="Ganhe 3 de força permanente",
        color=GOLD,
    ),
    Card(
        name="Golpe Duplo",
        cost=2,
        card_type="attack",
        value=5,
        description="Cause 5 de dano duas vezes",
        color=RED,
    ),
]


def create_starting_deck():
    """Gera o baralho inicial do jogador: 4 Golpes e 3 Defesas."""
    deck = []
    for _ in range(4):
        deck.append(CARD_POOL[0].copy())
    for _ in range(3):
        deck.append(CARD_POOL[1].copy())
    return deck
