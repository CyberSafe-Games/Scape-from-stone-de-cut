"""Tempos da dupla e do pequeno; todos os oito quadros de ataque são usados."""
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


def attack_frame(progress, count=8):
    return min(count-1, max(0, int(progress*count)))
