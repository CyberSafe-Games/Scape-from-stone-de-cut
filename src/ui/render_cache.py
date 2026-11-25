"""Caches por proprietário; fontes imutáveis mantêm a composição original."""
import weakref
import pygame


class RenderCache:
    def __init__(self):
        self._targets = {}

    def target(self, size, reference):
        key = tuple(size), reference.get_bitsize(), reference.get_masks()
        if key not in self._targets:
            self._targets.clear()
            self._targets[key] = pygame.Surface(size).convert(reference)
        return self._targets[key]


_actor_bounds = weakref.WeakKeyDictionary()
_scaled_images = weakref.WeakKeyDictionary()


def actor_bounds(frame, minimum=1):
    entries = _actor_bounds.setdefault(frame, {})
    if minimum not in entries:
        entries[minimum] = frame.get_bounding_rect(min_alpha=minimum)
    return entries[minimum].copy()


def scaled_image(image, size):
    entries = _scaled_images.setdefault(image, {})
    size = tuple(size)
    if size not in entries:
        if len(entries) >= 8:
            entries.clear()
        entries[size] = pygame.transform.smoothscale(image, size)
    return entries[size]



def blit_actor(surface, frame, rect, blend_flags=0):
    """Evita percorrer margens transparentes de uma pose imutável."""
    bounds = actor_bounds(frame)
    if bounds.width and bounds.height:
        return surface.blit(frame, (rect.x+bounds.x, rect.y+bounds.y),
                            bounds, special_flags=blend_flags)
    return pygame.Rect(rect.topleft, (0,0))

