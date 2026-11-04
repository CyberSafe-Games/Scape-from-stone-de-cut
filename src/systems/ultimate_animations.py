"""Tempos compartilhados por poses, camadas de magia e impacto das ultimates."""
from dataclasses import dataclass


@dataclass(frozen=True)
class UltimateAnimation:
    ultimate_id: str
    duration: int
    release: float
    impact: float
    color: tuple[int, int, int]


ULTIMATE_ANIMATIONS = {
    'Mana Ancestral': UltimateAnimation('mana_ancestral', 2200, .45, .52, (65, 185, 255)),
    'Forças Ancestrais': UltimateAnimation('forcas_ancestrais', 2400, .40, .50, (255, 193, 72)),
    'Rugido da Floresta': UltimateAnimation('rugido_da_floresta', 2500, .38, .78, (85, 235, 125)),
}


def cast_frame(progress, release=.38):
    """Oito poses, da preparação até o retorno à postura de repouso."""
    from src.systems.player_animation_kits import player_frame
    return player_frame(progress, release=release)


def roar_projectile_pose(progress, start_x, end_x, y):
    spec = ULTIMATE_ANIMATIONS['Rugido da Floresta']
    if not spec.release <= progress < spec.impact:
        return None
    flight = (progress-spec.release)/(spec.impact-spec.release)
    return start_x+(end_x-start_x)*flight, y, flight
