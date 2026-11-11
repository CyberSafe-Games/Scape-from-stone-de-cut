"""Oito ou doze poses do protagonista, alinhadas aos impactos do combate."""
from src.systems.animation_inbetweens import action_pose, timed_frame


def player_frame(progress, mode='self', release=None, count=8):
    """Seleciona preparação, ação e retorno sem pular poses intermediárias."""
    if release is None:
        release = .64 if mode == 'ranged' else .52
    if count == 12:
        return action_pose(progress, count, release)
    boundaries = (0, .12, .24, (.24 + release) / 2, release,
                  release + (1-release)*.36, release + (1-release)*.66, .94)
    return timed_frame(progress,boundaries,count)
