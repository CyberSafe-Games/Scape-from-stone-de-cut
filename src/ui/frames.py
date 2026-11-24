"""Molduras de ouro envelhecido: espessura fixa e cantos sem deformação."""
import pygame
from src.config.colors import GOLD, BRONZE_DARK, BRONZE_LIGHT


def nine_slice(source, size, margin=None, edge=22):
    """Escala somente as faixas; os quatro cantos mantêm proporção quadrada."""
    width, height = map(int, size)
    result = pygame.Surface((max(1, width), max(1, height)), pygame.SRCALPHA)
    if width < 1 or height < 1:
        return result
    margin = margin or max(1, round(min(source.get_size()) * .14))
    margin = min(margin, source.get_width() // 2, source.get_height() // 2)
    edge = max(1, min(edge, width // 2, height // 2))
    sx = (0, margin, source.get_width() - margin, source.get_width())
    sy = (0, margin, source.get_height() - margin, source.get_height())
    dx, dy = (0, edge, width-edge, width), (0, edge, height-edge, height)
    for y in range(3):
        for x in range(3):
            area = pygame.Rect(sx[x], sy[y], sx[x+1]-sx[x], sy[y+1]-sy[y])
            target = pygame.Rect(dx[x], dy[y], dx[x+1]-dx[x], dy[y+1]-dy[y])
            if area.width and area.height and target.width and target.height:
                result.blit(pygame.transform.smoothscale(source.subsurface(area), target.size), target)
    return result


def gold_outline(surface, rect, highlighted=False, compact=False):
    """Mesmo bronze, luz e espessura nos slots, status, retratos e painéis."""
    rect = pygame.Rect(rect)
    edge = GOLD if highlighted else BRONZE_LIGHT
    pygame.draw.rect(surface, BRONZE_DARK, rect, 2, border_radius=5)
    pygame.draw.rect(surface, edge, rect.inflate(-4, -4), 1, border_radius=4)
    if not compact and rect.width > 30 and rect.height > 30:
        for x, y, dx, dy in ((rect.left+7, rect.top+7, 1, 1),
                             (rect.right-8, rect.top+7, -1, 1),
                             (rect.left+7, rect.bottom-8, 1, -1),
                             (rect.right-8, rect.bottom-8, -1, -1)):
            pygame.draw.line(surface, edge, (x,y), (x+dx*8,y), 2)
            pygame.draw.line(surface, edge, (x,y), (x,y+dy*8), 2)


def horizontal_frame(source, size):
    """Estende o trilho central sem alargar os ornamentos das extremidades."""
    width, height = size
    factor = height / source.get_height()
    cap = min(round(source.get_width() * .28), source.get_width() // 2)
    edge = min(width // 2, max(1, round(cap * factor)))
    result = pygame.Surface(size, pygame.SRCALPHA)
    for start, span, x, target_width in ((0,cap,0,edge),
        (cap,source.get_width()-2*cap,edge,width-2*edge),
        (source.get_width()-cap,cap,width-edge,edge)):
        if span and target_width:
            part = source.subsurface((start,0,span,source.get_height()))
            result.blit(pygame.transform.smoothscale(part,(target_width,height)),(x,0))
    return result
