"""Tempos da dupla e do pequeno, compatíveis com oito ou doze poses."""
from src.systems.animation_inbetweens import timed_frame
DUO = 'álvaro e tex'
SMALL = 'álvaro e tex · pequeno'
NAMES = (DUO, SMALL)
TRANSITION_MS = 2000
ATTACK_MS = {
    DUO: {'atk1': 1300, 'atk2': 1700, 'atk3': 1800, 'atk4': 2100, 'healer2': 1800},
    SMALL: {'atk1': 1100, 'atk2': 1250, 'atk3': 1900, 'atk4': 1500},
}
RANGED = {
    DUO: {'atk2': (1700, .30, .68)},
    SMALL: {'atk4': (1500, .38, .72)},
}
ATTACK_BOUNDARIES = tuple(i / 8 for i in range(8))


def attack_frame(progress, count=8):
    return timed_frame(progress, ATTACK_BOUNDARIES, count)
