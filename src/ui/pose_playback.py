"""Transições da camada do personagem para as sequências de doze poses."""
from functools import lru_cache
from typing import NamedTuple

import pygame

from src.systems.animation_inbetweens import NEW_TWELVE_INDICES
from src.ui.helpers import ARENA_ACTOR_LIGHT, ease, scale_actor_to_display

UNIFORM_TWELVE = tuple(index / 12 for index in range(12))
TRANSITION_PART = .72
MIN_POSE_OVERLAP = .81
BLEND_STEPS = 16


class PoseBlend(NamedTuple):
    previous: pygame.Surface
    current: pygame.Surface
    offset: tuple[int, int]
    step: int


@lru_cache(maxsize=384)
def pose_mask(frame):
    size = tuple(max(1, dimension // 2) for dimension in frame.get_size())
    mask = pygame.mask.from_surface(pygame.transform.scale(frame, size), 96)
    return mask, mask.count()


@lru_cache(maxsize=512)
def pose_match(previous, current):
    """Mede quanto as silhuetas coincidem e alinha pequenos deslocamentos."""
    if previous.get_size() != current.get_size():
        return 0, (0, 0)
    left, left_area = pose_mask(previous)
    right, right_area = pose_mask(current)
    if not left_area or not right_area:
        return 0, (0, 0)
    score = left.overlap_area(right, (0, 0))
    offset = (0, 0)
    left_x, left_y = left.centroid()
    right_x, right_y = right.centroid()
    guess = (max(-14, min(14, left_x - right_x)), max(-3, min(3, left_y - right_y)))
    candidates = {(x + seed_x, y + seed_y) for seed_x, seed_y in ((0, 0), guess)
                  for x in range(-2, 3) for y in range(-2, 3)}
    for candidate in sorted(candidates, key=lambda delta: (abs(delta[0]) + abs(delta[1]), delta)):
        overlap = left.overlap_area(right, candidate)
        if overlap > score:
            score, offset = overlap, candidate
    return 2 * score / (left_area + right_area), (offset[0] * 2, offset[1] * 2)


@lru_cache(maxsize=384)
def pose_continuity(previous, current):
    overlap, (x, y) = pose_match(previous, current)
    height = max(1, previous.get_bounding_rect(min_alpha=96).height)
    return overlap - (abs(x) + abs(y)) / height


@lru_cache(maxsize=384)
def needs_bridge(previous, current, following):
    direct = pose_continuity(previous, following)
    arrival = pose_continuity(previous, current)
    departure = pose_continuity(current, following)
    # Exige que ambos os lados da pose inserida sejam piores que o caminho direto.
    return direct >= MIN_POSE_OVERLAP and direct - max(arrival, departure) >= .12


def blend_pose(previous, current, progress):
    step = round(ease(progress) * BLEND_STEPS)
    if previous is current or step == BLEND_STEPS:
        return current
    score, offset = pose_match(previous, current)
    if score < MIN_POSE_OVERLAP:
        return current
    if not step:
        return previous
    return PoseBlend(previous, current, offset, step)


def sample_pose(sprites, index, progress, boundaries, interpolate, *, loop=False, cuts=()):
    """Mantém as poses de contato e suaviza só as trocas visualmente compatíveis."""
    current = sprites[index]
    if not interpolate or len(sprites) != 12 or index in cuts:
        return current

    end = boundaries[index + 1] if index < 11 else 1
    local = (progress - boundaries[index]) / (end - boundaries[index])
    previous = sprites[index - 1]
    if (index in NEW_TWELVE_INDICES and index + 1 not in cuts
            and needs_bridge(previous, current, sprites[index + 1])):
        return blend_pose(previous, sprites[index + 1], local)
    if (index == 0 and not loop) or local >= TRANSITION_PART:
        return current
    if (index - 1 in NEW_TWELVE_INDICES and index - 1 not in cuts
            and needs_bridge(sprites[index - 2], previous, current)):
        return current
    return blend_pose(previous, current, local / TRANSITION_PART)


def foot_center(frame):
    body = frame.get_bounding_rect(min_alpha=96)
    if not body.height:
        return frame.get_width() // 2
    band = max(1, body.height // 8)
    feet = frame.subsurface((0, body.bottom - band, frame.get_width(), band))
    return feet.get_bounding_rect(min_alpha=96).centerx


@lru_cache(maxsize=12)
def align_stance(sprites, ready):
    """Mantém o apoio no chão e no mesmo eixo da pose de repouso."""
    floor = ready.get_bounding_rect(min_alpha=96).bottom
    center = foot_center(ready)
    result = []
    for frame in sprites:
        offset = (center - foot_center(frame), floor - frame.get_bounding_rect(min_alpha=96).bottom)
        if offset != (0, 0):
            aligned = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
            aligned.blit(frame, offset, special_flags=pygame.BLEND_RGBA_ADD)
            frame = aligned
        result.append(frame)
    return tuple(result)


def loop_pose(sprites, elapsed, frame_ms, interpolate):
    if not interpolate or len(sprites) != 12:
        return sprites[int(elapsed // frame_ms) % len(sprites)]
    position = elapsed / frame_ms % len(sprites)
    return sample_pose(sprites, int(position), position / len(sprites),
                       UNIFORM_TWELVE, True, loop=True)


@lru_cache(maxsize=32)
def render_blend(pose, light):
    previous = scale_actor_to_display(pose.previous, light)
    current = scale_actor_to_display(pose.current, light)
    fraction = pose.step / BLEND_STEPS
    offset = pygame.Vector2(pose.offset) * (current.get_width() / pose.current.get_width())
    previous_shift = (-round(offset.x * fraction), -round(offset.y * fraction))
    current_shift = (round(offset.x * (1 - fraction)), round(offset.y * (1 - fraction)))
    if fraction < .5:
        dominant, dominant_shift = previous, previous_shift
        secondary, secondary_shift = current, current_shift
    else:
        dominant, dominant_shift = current, current_shift
        secondary, secondary_shift = previous, previous_shift

    result = pygame.Surface(dominant.get_size(), pygame.SRCALPHA)
    bounds = dominant.get_bounding_rect()
    position = bounds.move(dominant_shift)
    result.blit(dominant.subsurface(bounds).premul_alpha(), position, special_flags=pygame.BLEND_RGBA_ADD)

    # Só mistura onde já existe corpo na pose dominante. O restante mantém um
    # único contorno, sem braços ou armas semitransparentes em duplicidade.
    overlap = position.clip(secondary.get_bounding_rect().move(secondary_shift)).clip(result.get_rect())
    if overlap.width and overlap.height:
        mask = pygame.mask.from_surface(result.subsurface(overlap), 96)
        stencil = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
        layer = secondary.subsurface(overlap.move(-secondary_shift[0], -secondary_shift[1])).premul_alpha()
        opacity = round(255 * min(fraction, 1 - fraction))
        layer.fill((opacity,) * 4, special_flags=pygame.BLEND_RGBA_MULT)
        layer.blit(stencil, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        result.blit(layer, overlap, special_flags=pygame.BLEND_PREMULTIPLIED)
    return result


def display_pose(pose, light=ARENA_ACTOR_LIGHT):
    if isinstance(pose, PoseBlend):
        return render_blend(pose, light), pygame.BLEND_PREMULTIPLIED
    return scale_actor_to_display(pose, light), 0
