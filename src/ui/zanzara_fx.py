"""Moedas e ondas independentes do corpo; aura restauradora do amuleto."""
import math
import pygame
from src.config.layout import ENEMY_X, PLAYER_GROUND_Y
from src.ui.ultimate_fx import _sprite, _particles


def draw_zanzara_fx(surface, view):
    if view.enemy_action == 'healer2':
        p = view.enemy_action_timer/max(1, view.enemy_action_duration)
        if not 0 <= p < 1:
            return
        fade = min(1, p/.18, (1-p)/.20)
        effects = view.asset_manager.get_boss_ultimate_sprites('Zanzara', effects=True)
        if effects:
            _sprite(surface, effects[0], (ENEMY_X, PLAYER_GROUND_Y-303), .22+.08*math.sin(p*math.pi), 225*fade)
        _particles(surface, (ENEMY_X, PLAYER_GROUND_Y-129), (246, 199, 83), p, 125, 18)
        for i in range(3):
            yy = round(PLAYER_GROUND_Y-39-((p*210+i*63) % 218))
            xx = round(ENEMY_X+math.sin(i*2+p*5)*98)
            color = (255, 221, 118)
            pygame.draw.line(surface, color, (xx-6, yy), (xx+6, yy), 3)
            pygame.draw.line(surface, color, (xx, yy-6), (xx, yy+6), 3)
        return
    pose = view.get_enemy_projectile_pose()
    if pose is None:
        return
    x, y, flight = pose
    projectile = view.asset_manager.get_enemy_projectile('Zanzara', view.enemy_action, min(3, int(flight*4)))
    if projectile is None:
        return
    if view.enemy_action == 'atk2':
        y -= 36*math.sin(flight*math.pi)
    _sprite(surface, projectile, (x+45, y), .90, 45)
    _sprite(surface, projectile, (x, y))
