"""Camadas das ultimates: selos no chão, espíritos e projétil independente."""
import math
import pygame

from src.config.layout import PLAYER_X, ENEMY_X, PLAYER_GROUND_Y
from src.systems.ultimate_animations import ULTIMATE_ANIMATIONS, roar_projectile_pose


def _sprite(surface, image, center, scale=1, alpha=255):
    if image is None or alpha <= 0:
        return
    size = (max(1, round(image.get_width()*scale)), max(1, round(image.get_height()*scale)))
    sprite = pygame.transform.smoothscale(image, size) if size != image.get_size() else image.copy()
    sprite.set_alpha(max(0, min(255, round(alpha))))
    surface.blit(sprite, sprite.get_rect(center=(round(center[0]), round(center[1]))))


def _particles(surface, center, color, progress, radius, amount=18):
    for i in range(amount):
        angle = i*math.tau/amount+progress*2.1
        spread = radius*(.65+.35*math.sin(progress*math.pi+i*.7))
        x = round(center[0]+math.cos(angle)*spread)
        y = round(center[1]+math.sin(angle)*spread*.65)
        size = 1+(i % 3)
        pygame.draw.line(surface, color, (x-size, y), (x+size, y), 1)
        pygame.draw.line(surface, color, (x, y-size), (x, y+size), 1)


def draw_ultimate_fx(surface, view, behind=False):
    spec = ULTIMATE_ANIMATIONS.get(view.player_action)
    if spec is None:
        return
    progress = min(1, view.player_action_timer/max(1, view.player_action_duration))
    if progress >= 1:
        return
    frames = view.asset_manager.get_ultimate_effect_sprites(view.player_action)
    if not frames:
        return
    fade = min(1, progress/.12, (1-progress)/.18)
    # A magia ocupa a arena, preservando retratos, cartas e botões.
    previous_clip = surface.get_clip()
    surface.set_clip(previous_clip.clip(pygame.Rect(0, 116, surface.get_width(), 400)))
    try:
        if behind:
            _draw_back(surface, view, spec, progress, frames, fade)
        else:
            _draw_front(surface, view, spec, progress, frames, fade)
    finally:
        surface.set_clip(previous_clip)


def _draw_back(surface, view, spec, p, frames, fade):
    veil = pygame.Surface((surface.get_width(), 400), pygame.SRCALPHA)
    veil.fill((3, 12, 17, round(45*fade)))
    surface.blit(veil, (0, 116))
    seal = pygame.Surface((240, 72), pygame.SRCALPHA)
    pulse = 1+math.sin(p*math.tau*2)*.06
    for radius, opacity in ((100, 35), (79, 110), (65, 200)):
        rect = pygame.Rect(120-round(radius*pulse), 36-round(radius*.20),
                           round(radius*2*pulse), round(radius*.4))
        pygame.draw.ellipse(seal, (*spec.color, round(opacity*fade)), rect, 2)
    for i in range(10):
        angle = i*math.tau/10+p*.8
        x, y = round(120+math.cos(angle)*84), round(36+math.sin(angle)*17)
        pygame.draw.polygon(seal, (*spec.color, round(200*fade)), [(x, y-3), (x+3, y), (x, y+3), (x-3, y)])
    surface.blit(seal, (PLAYER_X-120, PLAYER_GROUND_Y-38))
    if spec.ultimate_id == 'forcas_ancestrais':
        index = 0 if p < .24 else 1 if p < .43 else 2 if p < .81 else 3
        scale = .55+p*1.2 if p < .43 else 1 if p < .81 else 1+(p-.81)*.6
        _sprite(surface, frames[min(index, len(frames)-1)], (PLAYER_X, PLAYER_GROUND_Y-129), scale, 235*fade)
        _particles(surface, (PLAYER_X, PLAYER_GROUND_Y-95), (245, 216, 139), p, 103, 24)


def _draw_front(surface, view, spec, p, frames, fade):
    if spec.ultimate_id == 'mana_ancestral':
        index = 0 if p < .24 else 1 if p < .45 else 2 if p < .79 else 3
        rise = min(1, p/.38)
        y = PLAYER_GROUND_Y-100-110*rise
        scale = .85 if p < .45 else 1+math.sin(p*math.tau*3)*.035 if p < .79 else 1+(p-.79)*1.5
        _sprite(surface, frames[min(index, len(frames)-1)], (PLAYER_X+4, y), scale, 255*fade)
        _particles(surface, (PLAYER_X+4, y), (174, 236, 255), p, 91*min(1, p*3), 20)
        if .45 <= p < .80:
            for i in range(3):
                angle = p*math.tau+i*math.tau/3
                point = (round(PLAYER_X+math.cos(angle)*78), round(y+math.sin(angle)*31))
                pygame.draw.circle(surface, (210, 249, 255), point, 3)
    elif spec.ultimate_id == 'forcas_ancestrais':
        if .43 <= p < .88:
            _particles(surface, (PLAYER_X, PLAYER_GROUND_Y-64), (255, 228, 160), p, 52, 12)
    else:
        pose = roar_projectile_pose(p, PLAYER_X+105, ENEMY_X-18, PLAYER_GROUND_Y-85)
        if pose is not None:
            x, y, flight = pose
            index = 1 if flight < .40 else 2
            _sprite(surface, frames[min(index, len(frames)-1)], (x, y), 1+.10*math.sin(flight*math.pi), 255)
            _particles(surface, (x-65, y), (190, 238, 126), flight, 55, 12)
        elif p < spec.release:
            charge = p/spec.release
            _sprite(surface, frames[0], (PLAYER_X+85, PLAYER_GROUND_Y-91), .35+.50*charge, 210*charge)
        else:
            impact = (p-spec.impact)/(1-spec.impact)
            _sprite(surface, frames[-1], (ENEMY_X-10, PLAYER_GROUND_Y-85), 1+impact*.35, 255*(1-impact))
            ring = pygame.Surface((240, 210), pygame.SRCALPHA)
            for i in range(3):
                radius = round(23+impact*83+i*13)
                color = (134, 247, 151, round(180*(1-impact)))
                pygame.draw.ellipse(ring, color, (120-radius//2, 105-radius, radius, radius*2), 2)
            surface.blit(ring, (ENEMY_X-120, PLAYER_GROUND_Y-190))
