"""Remove a luz do fundo branco que ficou presa às bordas dos recortes."""
from collections import deque
import pygame


def remove_white_fringe(image):
    """Limpa apenas o branco/cinza conectado à transparência externa.

    Olhos, dentes e reflexos cercados pela própria arte ficam intactos.
    A limpeza acontece uma vez no carregamento, sem mudar escala ou pivô.
    """
    width, height = image.get_size()
    pixels = bytearray(pygame.image.tobytes(image, 'RGBA'))
    size = width * height
    candidates = bytearray(size)
    visited = bytearray(size)
    depth = bytearray(size)
    queue = deque()
    for i in range(size):
        r, g, b, alpha = pixels[i * 4:i * 4 + 4]
        candidates[i] = alpha <= 12 or (min(r, g, b) >= 90 and max(r, g, b) - min(r, g, b) <= 55)
        if candidates[i] and (i < width or i >= size - width or i % width in (0, width - 1)):
            visited[i] = 1
            queue.append(i)
    while queue:
        i = queue.popleft()
        pixels[i * 4:i * 4 + 4] = b'\x00\x00\x00\x00'
        x = i % width
        for neighbor in (i - width, i + width, i - 1 if x else -1,
                         i + 1 if x < width - 1 else -1):
            if 0 <= neighbor < size and not visited[neighbor] and candidates[neighbor]:
                next_depth = 0 if pixels[neighbor * 4 + 3] <= 12 else depth[i] + 1
                if next_depth > 2:
                    continue
                visited[neighbor] = 1
                depth[neighbor] = next_depth
                queue.append(neighbor)
    return pygame.image.frombytes(bytes(pixels), (width, height), 'RGBA').convert_alpha()
