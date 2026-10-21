import pygame
from src.config.colors import DARK_GRAY, WHITE, BLACK


def draw_text(surface, text, font, color, x, y, center=False):
    """Renderiza texto na superfície informada com sombra leve para contraste."""
    rendered = font.render(str(text), True, color)
    shadow = font.render(str(text), True, (0, 0, 0))
    rect = rendered.get_rect()
    shadow_rect = shadow.get_rect()
    if center:
        rect.center = (int(x), int(y))
        shadow_rect.center = (int(x + 1), int(y + 1))
    else:
        rect.topleft = (int(x), int(y))
        shadow_rect.topleft = (int(x + 1), int(y + 1))
    surface.blit(shadow, shadow_rect)
    surface.blit(rendered, rect)


def draw_text_shadow(surface, text, font, color, x, y, center=False, shadow_color=(0, 0, 0), offset=2):
    """Renderiza texto com uma sombra simples para melhorar o contraste."""
    shadow = font.render(str(text), True, shadow_color)
    shadow_rect = shadow.get_rect()
    if center:
        shadow_rect.center = (int(x + offset), int(y + offset))
    else:
        shadow_rect.topleft = (int(x + offset), int(y + offset))
    surface.blit(shadow, shadow_rect)
    draw_text(surface, text, font, color, x, y, center=center)



def draw_panel(surface, rect, fill=(18, 18, 28, 220), border=(122, 104, 62),
               radius=14, shadow=True, shadow_offset=(4, 5), shadow_alpha=90):
    """Desenha um painel dark com borda dupla, brilho superior e sombra."""
    rect = pygame.Rect(rect)
    if shadow:
        shadow_surf = pygame.Surface((rect.width + 12, rect.height + 12), pygame.SRCALPHA)
        pygame.draw.rect(
            shadow_surf,
            (0, 0, 0, shadow_alpha),
            pygame.Rect(6, 6, rect.width, rect.height),
            border_radius=radius + 2,
        )
        surface.blit(shadow_surf, (rect.x + shadow_offset[0] - 6, rect.y + shadow_offset[1] - 6))

    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, fill, panel.get_rect(), border_radius=radius)

    sheen = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(sheen, (255, 255, 255, 16), pygame.Rect(2, 2, rect.width - 4, max(8, rect.height // 3)), border_radius=max(8, radius - 2))
    panel.blit(sheen, (0, 0))

    pygame.draw.rect(panel, border, panel.get_rect(), 2, border_radius=radius)
    inner_color = tuple(max(0, min(255, c + 28)) for c in border)
    pygame.draw.rect(panel, inner_color, pygame.Rect(4, 4, rect.width - 8, rect.height - 8), 1, border_radius=max(6, radius - 4))
    surface.blit(panel, rect.topleft)



def draw_health_bar(surface, x, y, width, height, current, maximum, color,
                    background=(26, 24, 34), border=(236, 229, 210), glow=None):
    """Desenha barra de vida/progresso com fundo escuro, brilho e contorno."""
    rect = pygame.Rect(int(x), int(y), int(width), int(height))
    pygame.draw.rect(surface, (0, 0, 0), rect.move(2, 3), border_radius=height // 2)
    pygame.draw.rect(surface, background, rect, border_radius=height // 2)

    if maximum > 0:
        ratio = max(0, min(current, maximum)) / maximum
    else:
        ratio = 0

    inner_pad = 2
    fill_width = max(0, int((width - inner_pad * 2) * ratio))
    if fill_width > 0:
        fill_rect = pygame.Rect(rect.x + inner_pad, rect.y + inner_pad,
                                fill_width, max(1, height - inner_pad * 2))
        pygame.draw.rect(surface, color, fill_rect, border_radius=max(4, height // 2 - 2))
        highlight = pygame.Rect(fill_rect.x, fill_rect.y, fill_rect.width, max(2, fill_rect.height // 3))
        pygame.draw.rect(surface, glow or tuple(min(255, c + 35) for c in color),
                         highlight, border_radius=max(3, height // 3))
    pygame.draw.rect(surface, border, rect, 2, border_radius=height // 2)



def draw_vignette(surface, width, height, alpha=110):
    """Aplica uma vinheta simples para escurecer as bordas da cena."""
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    steps = 8
    for i in range(steps):
        inset_x = int(i * width * 0.018)
        inset_y = int(i * height * 0.025)
        rect = pygame.Rect(inset_x, inset_y, width - inset_x * 2, height - inset_y * 2)
        current_alpha = max(0, alpha - i * (alpha // steps))
        pygame.draw.rect(overlay, (0, 0, 0, current_alpha), rect, width=18, border_radius=18)
    surface.blit(overlay, (0, 0))



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
