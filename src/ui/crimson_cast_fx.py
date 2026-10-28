"""Estrela vermelha e partículas sincronizadas com o Vigor Escarlate."""
import math
import pygame
from src.config.layout import ENEMY_X, PLAYER_GROUND_Y


def draw_crimson_cast(surface, view):
    if (view.enemy_attack_name != 'carrasco da vigília'
            or view.enemy_action != 'healer2' or view.attacker == 'enemy'):
        return
    progress = view.enemy_action_timer / max(1, view.enemy_action_duration)
    if not .12 <= progress < .94:
        return
    local = (progress - .12) / .82
    strength = min(1.0, local * 5, (1 - local) * 5)
    alpha = round(235 * strength)
    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    x, y = ENEMY_X, PLAYER_GROUND_Y - 195
    radius = 18 + 3 * math.sin(local * math.pi)
    pygame.draw.circle(layer, (225, 24, 44, round(45 * strength)), (x, y), round(radius + 9))
    points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        length = radius if i % 2 == 0 else radius * .42
        points.append((round(x + math.cos(angle) * length), round(y + math.sin(angle) * length)))
    pygame.draw.polygon(layer, (205, 19, 43, alpha), points)
    pygame.draw.lines(layer, (255, 110, 120, alpha), True, points, 2)
    pygame.draw.circle(layer, (255, 178, 167, alpha), (x, y), 3)
    pygame.draw.ellipse(layer, (205, 30, 52, round(100 * strength)),
                        (x - 65, PLAYER_GROUND_Y - 15, 130, 22), 2)
    for i in range(12):
        t = (local + i / 12) % 1
        xx = x + math.sin(i * 2.399 + local * 4) * 60
        yy = PLAYER_GROUND_Y - 12 - t * 150
        pygame.draw.line(layer, (242, 60, 82, round(alpha * (1 - t))),
                         (round(xx), round(yy)), (round(xx + 2), round(yy - 6)), 2)
    surface.blit(layer, (0, 0))
