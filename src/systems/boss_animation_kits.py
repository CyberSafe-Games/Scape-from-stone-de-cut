"""Kits territoriais com doze poses e os instantes de impacto preservados."""
from src.systems.animation_inbetweens import action_pose, timed_frame

KITS = {
    'guardião da pedra': ('guardiao_da_pedra', ('idle','atk1','atk2','def','healer2','dano','ultimate')),
    'goblin nerd': ('goblin_nerd', ('idle','atk1','atk2','atk3','healer2','dano','ultimate')),
    'corpo seco': ('corpo_seco', ('idle','atk1','atk3','atk4','healer2','dano','ultimate')),
    'carrasco da vigília': ('carrasco_da_vigilia', ('idle','atk1','atk2','atk3','healer2','dano','ultimate')),
    'álvaro e tex': ('alvaro_tex_phase1', ('idle','dano','atk1','atk2','atk3','atk4','transition')),
    'álvaro e tex · pequeno': ('alvaro_tex_phase2', ('idle','dano','atk1','atk2','atk3','atk4')),
    'zanzara': ('zanzara', ('idle','dano','atk1','atk2','atk3','healer2','ultimate')),
    'gordofera': ('gordofera', ('idle','dano','atk1','atk2','atk3','def','ultimate')),
}

# The last four bosses keep their established action durations and damage values.
# These boundaries insert anticipation/recovery between the original key poses.
STRIKE_BOUNDARIES = (0,.18,.35,.43,.50,.66,.82,.93)


def kit_frame(progress, count=8, release=None):
    """Oito ou doze desenhos, mantendo preparação, golpe e recuperação."""
    if count not in (8,12):
        return min(max(0,count-1),max(0,int(progress*count)))
    if count == 12 or release is not None:
        return action_pose(progress, count, .50 if release is None else release)
    return timed_frame(progress, STRIKE_BOUNDARIES, count)
