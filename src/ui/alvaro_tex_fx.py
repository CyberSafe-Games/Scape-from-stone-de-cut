"""Complementos nativos: estrela em voo, sinais de cura e rastros dos especiais."""
import math
import pygame
from src.config.layout import ENEMY_X, PLAYER_X, PLAYER_GROUND_Y, APPROACH_GAP
from src.systems.alvaro_tex_animations import DUO
from src.ui.helpers import scale_to_display


def draw_alvaro_tex_fx(surface, view):
    duo = view.enemy_attack_name == DUO
    action = view.enemy_action
    healing = duo and action == 'healer2'
    progress = (view.enemy_action_timer / max(1, view.enemy_action_duration) if healing
                else view.attack_timer / max(1, view.enemy_attack_duration))
    old_clip = surface.get_clip()
    surface.set_clip(pygame.Rect(0, 180, surface.get_width(), 578))
    try:
        if healing:
            if .20 < progress < .95:
                glow = pygame.Surface((345, 375), pygame.SRCALPHA)
                opacity = round(210*math.sin((progress-.20)/.75*math.pi))
                for i in range(7):
                    angle = i*math.tau/7+progress*4
                    x = round(173+math.cos(angle)*99)
                    y = round(308-((progress*203+i*39)%270))
                    color = (172, 220, 101, opacity)
                    pygame.draw.line(glow,color,(x-6,y),(x+6,y),3)
                    pygame.draw.line(glow,color,(x,y-6),(x,y+6),3)
                surface.blit(glow,(ENEMY_X-173,PLAYER_GROUND_Y-360))
            return
        pose = view.get_enemy_projectile_pose()
        if pose:
            x, y, flight = pose
            sprite = scale_to_display(view.asset_manager.get_enemy_projectile(view.enemy_attack_name, action))
            if sprite:
                sprite = pygame.transform.rotate(sprite, flight*900)
                for offset, alpha in ((38,45), (20,85), (0,255)):
                    trail = sprite.copy()
                    trail.set_alpha(alpha)
                    surface.blit(trail, trail.get_rect(center=(round(x+offset),round(y))))
        special = (duo and action == 'atk4') or (not duo and action == 'atk3')
        if special and .24 < progress < .87:
            intensity = math.sin((progress-.24)/.63*math.pi)
            x, _ = view.get_attack_pose('enemy', ENEMY_X, PLAYER_X+APPROACH_GAP)
            glow = pygame.Surface((405, 345), pygame.SRCALPHA)
            color = (191, 211, 126, round(130*intensity))
            for i in range(3):
                angle = progress*math.tau*3 + i*math.tau/3
                rect = pygame.Rect(30+i*11, 90-i*18, 345-i*21, 158+i*15)
                pygame.draw.arc(glow, color, rect, angle, angle+3.2, 5)
            surface.blit(glow, (round(x)-203, PLAYER_GROUND_Y-330))
            if progress > .53:
                for i in range(12):
                    t = (progress-.53)/.34
                    angle = i*2.4
                    px = PLAYER_X+math.cos(angle)*t*135
                    py = PLAYER_GROUND_Y-30-abs(math.sin(angle))*t*113+68*t*t
                    pygame.draw.circle(surface, (157,134,76), (round(px),round(py)), max(2,6-round(5*t)))
    finally:
        surface.set_clip(old_clip)
