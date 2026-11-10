"""O salto inclui preparação, voo, descida, impacto e recuperação próprios."""
from src.systems.animation_inbetweens import timed_frame

TREMOR_BOUNDARIES = (0, .10, .20, .34, .52, .64, .82, .94)


def tremor_frame(progress, count=8):
    return timed_frame(progress, TREMOR_BOUNDARIES, count)
