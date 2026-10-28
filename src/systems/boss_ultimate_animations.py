"""Apresentação dos especiais territoriais; não altera regras ou dano."""
from dataclasses import dataclass


@dataclass(frozen=True)
class BossUltimateAnimation:
    asset_id: str
    title: str
    duration: int
    release: float
    impact: float
    color: tuple[int, int, int]
    mode: str
    height: int


BOSS_ULTIMATE_ANIMATIONS = {
    'guardião da pedra': BossUltimateAnimation('guardiao_da_pedra', 'Rugido Espiritual', 2600, .42, .78,
                                               (71, 183, 255), 'bear', 155),
    'goblin nerd': BossUltimateAnimation('goblin_nerd', 'Descarga Sobrecarregada', 2400, .44, .77,
                                         (167, 123, 255), 'plasma', 125),
    'corpo seco': BossUltimateAnimation('corpo_seco', 'Ataque Giratório', 2500, .40, .62,
                                       (174, 213, 231), 'blades', 132),
    'carrasco da vigília': BossUltimateAnimation('carrasco_da_vigilia', 'Execução Escarlate', 2800, .40, .64,
                                               (244, 64, 76), 'execution', 170),
}

# A identidade vem das próprias sprites das lutas normais, sem redesenho.
# Índices começam em zero: preparação, canalização, golpe e recuperação.
BOSS_ORIGINAL_CASTS = {
    'guardião da pedra': (('healer2', 0), ('healer2', 1), ('healer2', 2), ('idle', 0)),
    'goblin nerd': (('idle', 0), ('atk2', 0), ('atk2', 3), ('idle', 0)),
    'corpo seco': (('atk1', 0), ('atk3', 0), ('atk4', 2), ('idle', 0)),
    'carrasco da vigília': (('idle', 0), ('atk3', 0), ('atk3', 1), ('idle', 0)),
}


def boss_cast_frame(progress, spec=None):
    release = spec.release if spec and spec.mode in ('bear', 'plasma') else .50
    return 0 if progress < .22 else 1 if progress < release else 2 if progress < .80 else 3


def boss_ultimate_pose(spec, progress, home_x, target_x):
    if spec.mode in ('bear', 'plasma') or progress < .25:
        return home_x, 0
    if progress < .52:
        t = (progress-.25)/.27
        eased = t*t*(3-2*t)
        import math
        lift = math.sin(t*math.pi)*65 if spec.mode == 'execution' else 0
        return home_x+(target_x-home_x)*eased, lift
    if progress < .76:
        return target_x, 0
    t = min(1, (progress-.76)/.24)
    eased = t*t*(3-2*t)
    return target_x+(home_x-target_x)*eased, 0
