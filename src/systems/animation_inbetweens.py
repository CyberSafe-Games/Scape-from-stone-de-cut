"""Cadência das poses e dos intervalos entre os desenhos."""
from bisect import bisect_right
from functools import lru_cache

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


@lru_cache(maxsize=48)
def action_boundaries(count, accent):
    """Reparte a preparação e a recuperação em torno da pose de contato."""
    anticipation = count // 2
    recovery = count - anticipation - 1
    hold = min(.12, (1 - accent) * .24)
    boundaries = [accent * i / anticipation for i in range(anticipation)]
    boundaries.append(accent)
    boundaries.extend(
        accent + hold + (1 - accent - hold) * i / recovery
        for i in range(recovery)
    )
    return tuple(boundaries)


def action_pose(progress, count, accent):
    return bisect_right(action_boundaries(count, accent), max(0, progress)) - 1


def recovery_progress(elapsed, duration, extension, accent):
    """Alongar a recuperação preserva o instante da pose de contato ou lançamento."""
    contact = duration * accent
    if elapsed < contact:
        return max(0, elapsed / duration)
    return min(1.0, accent + (1 - accent) * (elapsed - contact) / (duration - contact + extension))
