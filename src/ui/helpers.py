import pygame
from src.config.colors import DARK_GRAY, WHITE


def draw_text(surface, text, font, color, x, y, center=False):
    """Renderiza texto na superfície informada."""
    rendered = font.render(str(text), True, color)
    rect = rendered.get_rect()
    if center:
        rect.center = (int(x), int(y))
    else:
        rect.topleft = (int(x), int(y))
    surface.blit(rendered, rect)


def draw_health_bar(surface, x, y, width, height, current, maximum, color):
    """Desenha barra de vida com fundo e contorno."""
    pygame.draw.rect(surface, DARK_GRAY, (x, y, width, height))

    if maximum > 0:
        ratio = max(0, current) / maximum
    else:
        ratio = 0

    pygame.draw.rect(surface, color, (x, y, width * ratio, height))
    pygame.draw.rect(surface, WHITE, (x, y, width, height), 2)


def wrap_text(text, font, max_width):
    """Quebra textos longos em múltiplas linhas respeitando a largura máxima."""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line}{word} "
        if font.size(test_line)[0] > max_width:
            if current_line:
                lines.append(current_line.strip())
            current_line = f"{word} "
        else:
            current_line = test_line

    if current_line:
        lines.append(current_line.strip())

    return lines


def ease(t):
    """Função de interpolação suave (Smoothstep) para movimentações e animações."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)
