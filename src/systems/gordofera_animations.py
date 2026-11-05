"""O salto inclui preparação, voo, descida, impacto e recuperação próprios."""
from bisect import bisect_right


def tremor_frame(progress):
    return max(0, min(7, bisect_right((0, .10, .20, .34, .52, .64, .82, .94), progress)-1))
