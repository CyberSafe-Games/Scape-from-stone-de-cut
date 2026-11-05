"""Tempos compartilhados por poses, camadas de magia e impacto das ultimates."""
from dataclasses import dataclass
from bisect import bisect_right
from src.systems.animation_inbetweens import timed_frame, frame_boundaries


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


def cast_frame(progress, release=.38, count=8):
    """Oito ou doze poses, da preparação até o retorno ao repouso."""
    from src.systems.player_animation_kits import player_frame
    return player_frame(progress, release=release, count=count)


def player_effect_frame(progress, spec, count=8):
    """Efeitos próprios; a dissipação do rugido começa somente após o impacto."""
    if spec.ultimate_id!='rugido_da_floresta':
        return timed_frame(progress,tuple(i/8 for i in range(8)),count)
    flight=spec.impact-spec.release
    original=(0,spec.release/2,*(spec.release+flight*i/5 for i in range(5)),spec.impact)
    boundaries=list(frame_boundaries(original,count))
    if count==12:
        boundaries[10]=spec.impact
        boundaries[11]=spec.impact+(1-spec.impact)/2
    return max(0,min(count-1,bisect_right(boundaries,max(0,progress))-1))


def roar_projectile_pose(progress, start_x, end_x, y):
    spec = ULTIMATE_ANIMATIONS['Rugido da Floresta']
    if not spec.release <= progress < spec.impact:
        return None
    flight = (progress-spec.release)/(spec.impact-spec.release)
    return start_x+(end_x-start_x)*flight, y, flight
