"""Reações de inimigos: apoio registrado, poses válidas e recuo sem deformação."""
from functools import lru_cache
import pygame
from src.config.layout import FLASH_DURATION

# Relógio visual: entrada, contato sustentado e recuperação; não pausa regras.
HIT_HOLD = (.18, .34)
JOZEPHINO_IDLE_MS = 160
JOZEPHINO_IDLE_ORDER = tuple(range(8)) + tuple(range(6, 0, -1))


def support(frame):
    # Quadros da arena inteira pertencem à auditoria, não ao cache do jogo.
    if frame.get_width() > 768 or frame.get_height() > 512:
        return _measure_support(frame)
    return _support_cached(frame)


@lru_cache(maxsize=128)
def _support_cached(frame):
    return _measure_support(frame)


def _measure_support(frame):
    """Descarta detritos isolados antes de medir o corpo e sua faixa de apoio."""
    mask = pygame.mask.from_surface(frame, 96)
    parts = mask.get_bounding_rects()
    if not parts:
        return frame.get_width()//2, frame.get_height(), pygame.Rect(0, 0, 0, 0)
    largest = max(parts, key=lambda r: r.w*r.h)
    substantial = [r for r in parts if r.w*r.h >= largest.w*largest.h*.035]
    body = substantial[0].unionall(substantial[1:])
    band = pygame.Rect(body.x, body.bottom-max(2, body.h//12), body.w, max(2, body.h//12))
    feet = frame.subsurface(band).get_bounding_rect(min_alpha=96)
    return band.x+feet.centerx, body.bottom, body


def similarity(left, right):
    a = pygame.mask.from_surface(left, 96)
    b = pygame.mask.from_surface(right, 96)
    total = a.count()+b.count()
    return 2*a.overlap_area(b, (0, 0))/total if total else 0


@lru_cache(maxsize=12)
def prepare_hurt(frames, ready, minimum_overlap=.82):
    """Não redimensiona o corpo. Poses fora de escala/silhueta usam guarda segura."""
    cx, floor, body = support(ready)
    prepared, audit = [], []
    for i, frame in enumerate(frames):
        x, y, box = support(frame)
        offset = (cx-x, floor-y)
        aligned = pygame.Surface(ready.get_size(), pygame.SRCALPHA)
        aligned.blit(frame, offset)
        _, _, after = support(aligned)
        clipped = (box.x+offset[0] < 0 or box.y+offset[1] < 0
                   or box.right+offset[0] > ready.get_width()
                   or box.bottom+offset[1] > ready.get_height())
        score = similarity(ready, aligned)
        valid = (not clipped and body.h > 0 and .90 <= after.h/body.h <= 1.10
                 and .72 <= after.w/max(1, body.w) <= 1.32 and score >= minimum_overlap)
        # A âncora deve continuar exata depois de descartar partículas.
        valid = valid and support(aligned)[:2] == (cx, floor)
        if valid:
            prepared.append(aligned)
        audit.append(dict(frame=i+1, offset=list(offset), overlap=round(score, 4),
                          accepted=valid, anchor=list(support(aligned if valid else ready)[:2])))
    # Guarda idêntica evita corte seco nos dois limites da reação.
    return (ready, *prepared, ready), tuple(audit)


@lru_cache(maxsize=64)
def mix_pose(left, right, step):
    """Mistura só a área comum; mantém uma única silhueta opaca e pivô fixo."""
    if step <= 0 or left is right:
        return left
    if step >= 12:
        return right
    fraction = step/12
    dominant, secondary = (left, right) if fraction < .5 else (right, left)
    out = dominant.copy()
    layer = secondary.copy()
    stencil = pygame.mask.from_surface(dominant, 1).to_surface(
        setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
    layer.blit(stencil, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    layer.set_alpha(round(255*min(fraction, 1-fraction)))
    out.blit(layer, (0, 0))
    # A composição não pode engrossar pixels semitransparentes dos pés.
    # RGB branco mantém as cores; MIN restaura exatamente o alfa dominante.
    alpha = dominant.copy()
    alpha.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_MAX)
    out.blit(alpha, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return out


def hurt_progress(remaining):
    p = max(0, min(1, 1-remaining/FLASH_DURATION))
    if p < HIT_HOLD[0]:
        return p/HIT_HOLD[0]*.42
    if p < HIT_HOLD[1]:
        return .42
    return .42+(p-HIT_HOLD[1])/(1-HIT_HOLD[1])*.58


def reaction_pose(frames, ready, remaining, interpolate=True, *, minimum_overlap=.82):
    if ready is None:
        return None
    prepared, _ = prepare_hurt(tuple(frames), ready, minimum_overlap)
    position = hurt_progress(remaining)*(len(prepared)-1)
    index = min(len(prepared)-1, int(position))
    if not interpolate or index == len(prepared)-1:
        return prepared[index]
    return mix_pose(prepared[index], prepared[index+1], round((position-index)*12))


def knockback(remaining):
    """Até 12 px no canvas virtual, sem deslocamento vertical, rotação ou zoom."""
    p = max(0, min(1, 1-remaining/FLASH_DURATION))
    if p < HIT_HOLD[0]:
        t = p/HIT_HOLD[0]
        return 12*(1-(1-t)**3)
    if p < HIT_HOLD[1]:
        return 12
    t = (p-HIT_HOLD[1])/(1-HIT_HOLD[1])
    return 12*(1-t*t*(3-2*t))


def impact_tint(frame, remaining):
    # Pulso âmbar curto; multiplicativo para respeitar alfa pré-multiplicado.
    elapsed = FLASH_DURATION-remaining
    strength = max(0, min(1, elapsed/65, (160-elapsed)/95))
    if not strength:
        return frame
    tinted = frame.copy()
    tinted.fill((255, round(255-50*strength), round(255-75*strength)),
                special_flags=pygame.BLEND_RGB_MULT)
    return tinted


@lru_cache(maxsize=8)
def calm_idle_frames(ready):
    """Oito respirações discretas derivadas da guarda íntegra de Jozephino.

    Os intermediários antigos encolhiam o corpo em até 18%. Conserva o desenho
    aprovado, sem escala: desloca somente tronco/cabeça até dois pixels.
    """
    _, floor, body = support(ready)
    boots_top = floor-max(8, body.h//7)
    result = []
    motions = ((0, 0), (-1, 0), (-1, 1), (0, 2),
               (1, 2), (1, 1), (1, 0), (0, -1))
    for dx, dy in motions:
        frame = pygame.Surface(ready.get_size(), pygame.SRCALPHA)
        for y in range(body.y, boots_top):
            weight = max(0, min(1, (boots_top-y)/max(1, body.h*.45)))
            row = pygame.Rect(0, y, ready.get_width(), 1)
            frame.blit(ready, (round(dx*weight), y+round(dy*weight)), row)
        # Uma faixa de botas idêntica em todas as poses fixa a linha do chão.
        frame.blit(ready, (0, boots_top),
                   pygame.Rect(0, boots_top, ready.get_width(), ready.get_height()-boots_top))
        result.append(frame)
    return tuple(result)


def calm_idle(ready, elapsed):
    return calm_idle_frames(ready)[JOZEPHINO_IDLE_ORDER[int(max(0, elapsed)//JOZEPHINO_IDLE_MS)
                                                     % len(JOZEPHINO_IDLE_ORDER)]]
