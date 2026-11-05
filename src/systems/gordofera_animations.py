"""O salto inclui preparação, voo, descida, impacto e recuperação próprios."""
from src.systems.animation_inbetweens import timed_frame


def tremor_frame(progress, count=8):
    return timed_frame(progress,(0, .10, .20, .34, .52, .64, .82, .94),count)
