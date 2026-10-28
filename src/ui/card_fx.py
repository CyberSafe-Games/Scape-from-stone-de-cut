"""Projéteis independentes dos quadros do personagem."""
import math
import pygame
from src.config.layout import PLAYER_X, ENEMY_X, PLAYER_GROUND_Y
from src.systems.card_definitions import SPECS_BY_NAME


def projectile_pose(view):
    spec = SPECS_BY_NAME.get(view.player_action)
    if view.attacker != 'player' or not spec or spec[6] != 'ranged':
        return None
    progress = view.attack_timer / max(1, view.player_attack_duration)
    if not 0.64 <= progress < 0.90:
        return None
    t = (progress - 0.64) / 0.26
    muzzle = 90 if spec[1] in ('Disparo de Arco', 'Zarabatana Venenosa') else 60
    x = PLAYER_X + muzzle + (ENEMY_X - PLAYER_X - muzzle - 15) * t
    y = PLAYER_GROUND_Y - 72
    if spec[5] in ('poison', 'vulnerable'):
        y -= 60 * math.sin(math.pi * t)
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
            xx, yy = round(x - n * 13), round(y + (n - 1) * 11 if darts else y)
            color = (120, 223, 69) if darts else (224, 192, 128)
            pygame.draw.line(surface, (76, 43, 22), (xx - 33, yy), (xx + 13, yy), 4)
            pygame.draw.line(surface, color, (xx - 29, yy - 1), (xx + 13, yy - 1), 2)
            pygame.draw.polygon(surface, color, [(xx + 21, yy), (xx + 10, yy - 4), (xx + 10, yy + 4)])
            pygame.draw.lines(surface, color, False, [(xx - 25, yy - 6), (xx - 17, yy), (xx - 25, yy + 6)], 2)
    elif name == 'Bola de Fogo':
        sprite = view.asset_manager.get_projectile_image('fireball')
        if sprite is not None:
            surface.blit(sprite, sprite.get_rect(midright=(round(x) + 20, round(y))))
            return
        flame = pygame.Surface((100, 58), pygame.SRCALPHA)
        pygame.draw.ellipse(flame, (255, 99, 16, 50), (0, 0, 100, 58))
        pygame.draw.polygon(flame, (200, 40, 10), [(4, 17), (48, 14), (27, 6), (77, 12), (94, 29), (72, 47), (21, 48), (43, 36), (0, 33), (42, 25)])
        pygame.draw.circle(flame, (255, 124, 16), (73, 29), 18)
        pygame.draw.circle(flame, (255, 219, 73), (76, 28), 12)
        pygame.draw.circle(flame, (255, 251, 199), (80, 27), 6)
        surface.blit(flame, (round(x) - 73, round(y) - 29))
    elif name in ('Poção Venenosa', 'Poção Fragilizante'):
        potion = pygame.Surface((28, 34), pygame.SRCALPHA)
        color = (113, 217, 54) if name == 'Poção Venenosa' else (244, 155, 40)
        pygame.draw.ellipse(potion, (25, 19, 29), (2, 10, 24, 23))
        pygame.draw.ellipse(potion, color, (5, 15, 18, 15))
        pygame.draw.rect(potion, (173, 201, 179), (10, 5, 8, 13), 2)
        pygame.draw.rect(potion, (119, 74, 36), (9, 2, 10, 5))
        pygame.draw.arc(potion, (221, 247, 232), (4, 11, 21, 20), 0, 1.4, 2)
        potion = pygame.transform.rotate(potion, -t * 540)
        surface.blit(potion, potion.get_rect(center=(round(x), round(y))))
    else:
        for radius, color in ((24, (71, 174, 120)), (17, (226, 192, 93)), (8, (216, 253, 224))):
            pygame.draw.circle(surface, color, (round(x), round(y)), radius, 2)
        for i in range(4):
            angle = t * math.tau * 2 + i * math.pi / 2
            pygame.draw.circle(surface, (244, 222, 139), (round(x + math.cos(angle) * 22), round(y + math.sin(angle) * 22)), 3)
