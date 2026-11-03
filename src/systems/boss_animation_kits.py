"""Kits territoriais com oito poses e tempos compartilhados pelo corpo e impactos."""
from bisect import bisect_right

KITS = {
    'guardião da pedra': ('guardiao_da_pedra', ('idle','atk1','atk2','def','healer2','dano','ultimate')),
    'goblin nerd': ('goblin_nerd', ('idle','atk1','atk2','atk3','healer2','dano','ultimate')),
    'corpo seco': ('corpo_seco', ('idle','atk1','atk3','atk4','healer2','dano','ultimate')),
    'carrasco da vigília': ('carrasco_da_vigilia', ('idle','atk1','atk2','atk3','healer2','dano','ultimate')),
    'álvaro e tex': ('alvaro_tex_phase1', ('idle','dano','atk1','atk2','atk3','atk4','transition')),
    'álvaro e tex · pequeno': ('alvaro_tex_phase2', ('idle','dano','atk1','atk2','atk3','atk4')),
}

# The last four bosses keep their established action durations and damage values.
# These boundaries insert anticipation/recovery between the original key poses.
STRIKE_BOUNDARIES = (0,.18,.35,.43,.50,.66,.82,.93)


def kit_frame(progress, count=8, release=None):
    """All eight drawings are reachable, including the final recovery pose."""
    if count != 8:
        return min(max(0,count-1),max(0,int(progress*count)))
    boundaries = (0,.12,.22,(.22+release)/2,release,(release+.80)/2,.80,.92) if release else STRIKE_BOUNDARIES
    return max(0,min(7,bisect_right(boundaries,max(0,progress))-1))
