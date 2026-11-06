"""Projéteis independentes dos quadros do personagem."""
import math
import pygame
from src.config.layout import PLAYER_X, ENEMY_X, PLAYER_GROUND_Y
from src.systems.card_definitions import SPECS_BY_NAME
from src.ui.helpers import scale_to_display


def projectile_pose(view):
    spec = SPECS_BY_NAME.get(view.player_action)
    if view.attacker != 'player' or not spec or spec[6] != 'ranged':
        return None
    progress = view.attack_timer / max(1, view.player_attack_duration)
    if not 0.64 <= progress < 0.90:
        return None
    t = (progress - 0.64) / 0.26
    muzzle = 135 if spec[1] in ('Disparo de Arco', 'Zarabatana Venenosa') else 90
    x = PLAYER_X + muzzle + (ENEMY_X - PLAYER_X - muzzle - 23) * t
    y = PLAYER_GROUND_Y - 108
    if spec[5] in ('poison', 'vulnerable'):
        y -= 90 * math.sin(math.pi * t)
    return x, y, t


def draw_player_projectile(surface, view):
    pose = projectile_pose(view)
    if pose is None:
        return
    x, y, t = pose
    name = view.player_action
    if name in ('Disparo de Arco', 'Zarabatana Venenosa'):
        darts = name == 'Zarabatana Venenosa'
        for n in range(3 if darts else 1):
            xx, yy = round(x - n * 20), round(y + (n - 1) * 17 if darts else y)
            color = (120, 223, 69) if darts else (224, 192, 128)
            pygame.draw.line(surface, (76, 43, 22), (xx - 50, yy), (xx + 20, yy), 6)
            pygame.draw.line(surface, color, (xx - 44, yy - 2), (xx + 20, yy - 2), 3)
            pygame.draw.polygon(surface, color, [(xx + 32, yy), (xx + 15, yy - 6), (xx + 15, yy + 6)])
            pygame.draw.lines(surface, color, False, [(xx - 38, yy - 9), (xx - 26, yy), (xx - 38, yy + 9)], 3)
    elif name == 'Bola de Fogo':
        sprite = scale_to_display(view.asset_manager.get_projectile_image('fireball'))
        if sprite is not None:
            surface.blit(sprite, sprite.get_rect(midright=(round(x) + 30, round(y))))
            return
        flame = pygame.Surface((150, 87), pygame.SRCALPHA)
        pygame.draw.ellipse(flame, (255, 99, 16, 50), (0, 0, 150, 87))
        pygame.draw.polygon(flame, (200, 40, 10), [(6, 26), (72, 21), (41, 9), (116, 18), (141, 44), (108, 71), (32, 72), (65, 54), (0, 50), (63, 38)])
        pygame.draw.circle(flame, (255, 124, 16), (110, 44), 27)
        pygame.draw.circle(flame, (255, 219, 73), (114, 42), 18)
        pygame.draw.circle(flame, (255, 251, 199), (120, 41), 9)
        surface.blit(flame, (round(x) - 110, round(y) - 44))
    elif name in ('Poção Venenosa', 'Poção Fragilizante'):
        potion = pygame.Surface((42, 51), pygame.SRCALPHA)
        color = (113, 217, 54) if name == 'Poção Venenosa' else (244, 155, 40)
        pygame.draw.ellipse(potion, (25, 19, 29), (3, 15, 36, 35))
        pygame.draw.ellipse(potion, color, (8, 23, 27, 23))
        pygame.draw.rect(potion, (173, 201, 179), (15, 8, 12, 20), 3)
        pygame.draw.rect(potion, (119, 74, 36), (14, 3, 15, 8))
        pygame.draw.arc(potion, (221, 247, 232), (6, 17, 32, 30), 0, 1.4, 3)
        potion = pygame.transform.rotate(potion, -t * 540)
        surface.blit(potion, potion.get_rect(center=(round(x), round(y))))
    else:
        for radius, color in ((36, (71, 174, 120)), (26, (226, 192, 93)), (12, (216, 253, 224))):
            pygame.draw.circle(surface, color, (round(x), round(y)), radius, 3)
        for i in range(4):
            angle = t * math.tau * 2 + i * math.pi / 2
            pygame.draw.circle(surface, (244, 222, 139), (round(x + math.cos(angle) * 33), round(y + math.sin(angle) * 33)), 5)
