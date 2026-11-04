"""Oito poses do protagonista, alinhadas aos efeitos e impactos do combate."""
from bisect import bisect_right


def player_frame(progress, mode='self', release=None):
    """Seleciona preparação, ação e retorno sem pular poses intermediárias."""
    if release is None:
        release = .64 if mode == 'ranged' else .52
    boundaries = (0, .12, .24, (.24 + release) / 2, release,
                  release + (1-release)*.36, release + (1-release)*.66, .94)
    return max(0, min(7, bisect_right(boundaries, progress)-1))
