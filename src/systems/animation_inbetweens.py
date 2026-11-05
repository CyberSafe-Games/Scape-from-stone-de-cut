"""Insere poses sem deslocar os instantes das oito poses chave aprovadas."""
from bisect import bisect_right

ORIGINAL_TWELVE_INDICES = (0, 2, 3, 5, 6, 8, 9, 11)
NEW_TWELVE_INDICES = (1, 4, 7, 10)


def frame_boundaries(original, count):
    if count == 12 and len(original) == 8:
        return tuple(value for i in range(0,8,2)
                     for value in (original[i], (original[i]+original[i+1])/2, original[i+1]))
    return original


def timed_frame(progress, original, count):
    if count not in (8,12):
        return max(0,min(count-1,int(progress*count)))
    boundaries = frame_boundaries(original,count)
    return max(0,min(count-1,bisect_right(boundaries,max(0,progress))-1))
