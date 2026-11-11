from functools import lru_cache
import weakref

import pygame
from src.config.colors import DARK_GRAY, WHITE, BLACK
from src.config.settings import UI_SCALE

# Cache das versões ampliadas; as entradas somem junto com a imagem original.
_display_cache = weakref.WeakKeyDictionary()
ARENA_ACTOR_LIGHT = (218, 210, 202)


@lru_cache(maxsize=128)
def scale_actor_to_display(image, light=ARENA_ACTOR_LIGHT):
    """Preserva os pixels da silhueta e aplica a iluminação da arena."""
    if image is None:
        return None
    size = tuple(max(1, round(value * UI_SCALE)) for value in image.get_size())
    result = pygame.transform.scale(image, size)
    result.fill(light, special_flags=pygame.BLEND_RGB_MULT)
    return result


def scale_to_display(image):
    """Amplia um sprite carregado no tamanho nativo do arquivo para a resolução

    de referência (UI_SCALE), preservando a composição original da cena.
    """
    if image is None or UI_SCALE == 1:
        return image
    scaled = _display_cache.get(image)
    if scaled is None:
        width, height = image.get_size()
        scaled = pygame.transform.smoothscale(
            image, (max(1, round(width * UI_SCALE)), max(1, round(height * UI_SCALE)))
        )
        _display_cache[image] = scaled
    return scaled


def draw_text(surface, text, font, color, x, y, center=False):
    """Renderiza texto na superfície informada com sombra leve para contraste."""
    rendered = font.render(str(text), True, color)
    shadow = font.render(str(text), True, (0, 0, 0))
    rect = rendered.get_rect()
    shadow_rect = shadow.get_rect()
    if center:
        rect.center = (int(x), int(y))
        shadow_rect.center = (int(x + 2), int(y + 2))
    else:
        rect.topleft = (int(x), int(y))
        shadow_rect.topleft = (int(x + 2), int(y + 2))
    surface.blit(shadow, shadow_rect)
    surface.blit(rendered, rect)


def draw_text_shadow(surface, text, font, color, x, y, center=False, shadow_color=(0, 0, 0), offset=3):
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
               radius=21, shadow=True, shadow_offset=(6, 8), shadow_alpha=90):
    """Desenha um painel dark com borda dupla, brilho superior e sombra."""
    rect = pygame.Rect(rect)
    if shadow:
        shadow_surf = pygame.Surface((rect.width + 18, rect.height + 18), pygame.SRCALPHA)
        pygame.draw.rect(
            shadow_surf,
            (0, 0, 0, shadow_alpha),
            pygame.Rect(9, 9, rect.width, rect.height),
            border_radius=radius + 3,
        )
        surface.blit(shadow_surf, (rect.x + shadow_offset[0] - 9, rect.y + shadow_offset[1] - 9))

    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, fill, panel.get_rect(), border_radius=radius)

    sheen = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(sheen, (255, 255, 255, 16), pygame.Rect(3, 3, rect.width - 6, max(12, rect.height // 3)), border_radius=max(12, radius - 3))
    panel.blit(sheen, (0, 0))

    pygame.draw.rect(panel, border, panel.get_rect(), 3, border_radius=radius)
    inner_color = tuple(max(0, min(255, c + 28)) for c in border)
    pygame.draw.rect(panel, inner_color, pygame.Rect(6, 6, rect.width - 12, rect.height - 12), 2, border_radius=max(9, radius - 6))
    surface.blit(panel, rect.topleft)



def draw_health_bar(surface, x, y, width, height, current, maximum, color,
                    background=(26, 24, 34), border=(236, 229, 210), glow=None):
    """Desenha barra de vida/progresso com fundo escuro, brilho e contorno."""
    rect = pygame.Rect(int(x), int(y), int(width), int(height))
    pygame.draw.rect(surface, (0, 0, 0), rect.move(3, 5), border_radius=height // 2)
    pygame.draw.rect(surface, background, rect, border_radius=height // 2)

    if maximum > 0:
        ratio = max(0, min(current, maximum)) / maximum
    else:
        ratio = 0

    inner_pad = 3
    fill_width = max(0, int((width - inner_pad * 2) * ratio))
    if fill_width > 0:
        fill_rect = pygame.Rect(rect.x + inner_pad, rect.y + inner_pad,
                                fill_width, max(1, height - inner_pad * 2))
        pygame.draw.rect(surface, color, fill_rect, border_radius=max(6, height // 2 - 3))
        highlight = pygame.Rect(fill_rect.x, fill_rect.y, fill_rect.width, max(3, fill_rect.height // 3))
        pygame.draw.rect(surface, glow or tuple(min(255, c + 35) for c in color),
                         highlight, border_radius=max(5, height // 3))
    pygame.draw.rect(surface, border, rect, 3, border_radius=height // 2)



def draw_vignette(surface, width, height, alpha=110):
    """Aplica uma vinheta simples para escurecer as bordas da cena."""
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    steps = 8
    for i in range(steps):
        inset_x = int(i * width * 0.018)
        inset_y = int(i * height * 0.025)
        rect = pygame.Rect(inset_x, inset_y, width - inset_x * 2, height - inset_y * 2)
        current_alpha = max(0, alpha - i * (alpha // steps))
        pygame.draw.rect(overlay, (0, 0, 0, current_alpha), rect, width=27, border_radius=27)
    surface.blit(overlay, (0, 0))



def _split_long_word(word, font, max_width):
    """Fatia uma palavra maior que a largura disponível em pedaços que cabem nela."""
    pieces = []
    current = ""
    for char in word:
        if current and font.size(current + char)[0] > max_width:
            pieces.append(current)
            current = char
        else:
            current += char
    if current:
        pieces.append(current)
    return pieces


def wrap_text(text, font, max_width):
    """Quebra textos longos em múltiplas linhas respeitando a largura máxima.

    Quebras explícitas (\\n) são preservadas e palavras isoladas mais largas
    que a área disponível são fatiadas, garantindo que nenhuma linha ultrapasse
    ``max_width``.
    """
    lines = []

    for paragraph in str(text).split("\n"):
        current_line = ""
        for word in paragraph.split():
            if font.size(word)[0] > max_width:
                pieces = _split_long_word(word, font, max_width)
                word = pieces.pop()
                for piece in pieces:
                    if current_line:
                        lines.append(current_line.strip())
                        current_line = ""
                    lines.append(piece)

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


def truncate_text(text, font, max_width, ellipsis="…"):
    """Encurta uma linha única com reticências para que caiba em ``max_width``."""
    text = str(text)
    if font.size(text)[0] <= max_width:
        return text
    while text and font.size(text + ellipsis)[0] > max_width:
        text = text[:-1]
    return text.rstrip() + ellipsis



def ease(t):
    """Função de interpolação suave (Smoothstep) para movimentações e animações."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)
