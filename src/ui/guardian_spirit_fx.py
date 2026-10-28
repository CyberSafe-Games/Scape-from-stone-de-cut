"""Preparação, voo e dissipação do Rugido Espiritual; apenas apresentação."""
import math
import pygame
from src.config.layout import ENEMY_X, PLAYER_X, PLAYER_GROUND_Y


def _point(x, y):
    return round(x), round(y)


def _ground_seal(layer, center, radius, alpha, phase):
    x, y = center
    rect = pygame.Rect(round(x - radius), round(y - radius * .22),
                       max(1, round(radius * 2)), max(1, round(radius * .44)))
    pygame.draw.ellipse(layer, (49, 171, 255, alpha), rect, 2)
    pygame.draw.ellipse(layer, (150, 224, 255, alpha // 2), rect.inflate(-12, -5), 1)
    for i in range(8):
        angle = i * math.tau / 8 + phase
        xx, yy = x + math.cos(angle) * radius, y + math.sin(angle) * radius * .22
        pygame.draw.lines(layer, (168, 231, 255, alpha), False,
                          [_point(xx - 3, yy - 4), _point(xx, yy + 3), _point(xx + 3, yy - 3)], 1)


def draw_guardian_spirit(surface, view):
    """Desenha somente durante a animação do ataque especial do Guardião."""
    if (view.attacker != 'enemy' or view.enemy_attack_name != 'guardião da pedra'
            or view.enemy_action != 'atk2' or not view.enemy_ranged_attack):
        return
    duration, launch, impact = view.enemy_ranged_attack
    progress = view.attack_timer / max(1, duration)
    if not 0 <= progress < 1:
        return
    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    phase = progress * math.tau
    hand_x, hand_y = ENEMY_X - 72, PLAYER_GROUND_Y - 92
    if progress < launch:
        charge = progress / launch
        alpha = round(55 + charge * 140)
        _ground_seal(layer, (ENEMY_X, PLAYER_GROUND_Y - 2), 49 + charge * 34, alpha, phase)
        # Fios de energia convergem para o braço durante a formação do urso.
        for i in range(14):
            t = (charge + i / 14) % 1
            angle = i * 2.399 + phase * .45
            radius = 85 * (1 - t) + 12
            xx = hand_x + math.cos(angle) * radius
            yy = hand_y + math.sin(angle) * radius * .7
            pygame.draw.line(layer, (51, 157, 251, round(alpha * t)),
                             _point(xx, yy), _point(xx + math.cos(angle) * 8, yy + math.sin(angle) * 5), 2)
            pygame.draw.circle(layer, (177, 239, 255, round(alpha * t)), _point(xx, yy), 2)
        for i in range(3):
            radius = round(19 + charge * 14 + i * 7)
            rect = pygame.Rect(hand_x - radius, hand_y - radius, radius * 2, radius * 2)
            pygame.draw.arc(layer, (63, 177, 255, alpha // 2), rect,
                            phase + i * 2, phase + i * 2 + 1.4, 2)
    elif progress < impact:
        x, y, flight = view.get_enemy_projectile_pose()
        head = view.asset_manager.get_enemy_projectile('guardião da pedra', 'atk2')
        # A cauda fica à direita, acompanhando o voo em direção ao herói.
        for band in range(5):
            points = [_point(x + i * 8, y + (band - 2) * 8 + math.sin(i * .45 + phase * 3 + band) * 9)
                      for i in range(17)]
            pygame.draw.lines(layer, (35, 124 + band * 12, 255, 90 - band * 10), False, points, 2)
        for i in range(18):
            offset = (i * 17 + flight * 110) % 145
            xx = x + offset
            yy = y + math.sin(i * 2.399 + phase * 4) * (19 + offset * .12)
            pygame.draw.circle(layer, (109, 210, 255, round(140 * (1 - offset / 160))), _point(xx, yy), 2)
        _ground_seal(layer, (x, PLAYER_GROUND_Y - 1), 42, 60, -phase)
        surface.blit(layer, (0, 0))
        if head is not None:
            for distance, opacity in ((66, 15), (43, 28), (22, 53)):
                echo = head.copy()
                echo.set_alpha(opacity)
                surface.blit(echo, echo.get_rect(center=_point(x + distance, y)))
            surface.blit(head, head.get_rect(center=_point(x, y)))
        return
    else:
        fade = (progress - impact) / (1 - impact)
        x, y = PLAYER_X + 12, PLAYER_GROUND_Y - 65
        alpha = round(220 * (1 - fade))
        # Duas ondas de choque e fragmentos que se apagam sem esconder a HUD.
        for i in range(2):
            radius = round(18 + fade * 95 - i * 14)
            if radius > 0:
                pygame.draw.circle(layer, (80, 189, 255, alpha // (i + 1)), _point(x, y), radius, 2)
        for i in range(16):
            angle = i * math.tau / 16
            radius = 20 + fade * (62 + (i % 3) * 10)
            xx, yy = x + math.cos(angle) * radius, y + math.sin(angle) * radius * .75
            pygame.draw.line(layer, (174, 235, 255, alpha), _point(xx, yy),
                             _point(xx + math.cos(angle) * 9, yy + math.sin(angle) * 7), 2)
        _ground_seal(layer, (PLAYER_X, PLAYER_GROUND_Y - 1), 45 + fade * 60, alpha // 2, phase)
    surface.blit(layer, (0, 0))
