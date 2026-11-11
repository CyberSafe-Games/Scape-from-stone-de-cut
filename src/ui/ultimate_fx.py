"""Camadas das ultimates: selos no chão, espíritos e projétil independente."""
import math
import pygame

from src.config.layout import PLAYER_X, ENEMY_X, PLAYER_GROUND_Y
from src.config.settings import UI_SCALE
from src.systems.ultimate_animations import ULTIMATE_ANIMATIONS, roar_projectile_pose, player_effect_frame


def _sprite(surface, image, center, scale=1, alpha=255):
    if image is None or alpha <= 0:
        return
    # Quadros em tamanho nativo do arquivo: amplia para a resolução de referência.
    scale *= UI_SCALE
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
        size = round(UI_SCALE*(1+(i % 3)))
        pygame.draw.line(surface, color, (x-size, y), (x+size, y), 2)
        pygame.draw.line(surface, color, (x, y-size), (x, y+size), 2)


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
    surface.set_clip(previous_clip.clip(pygame.Rect(0, 174, surface.get_width(), 600)))
    try:
        if behind:
            _draw_back(surface, view, spec, progress, frames, fade)
        else:
            _draw_front(surface, view, spec, progress, frames, fade)
    finally:
        surface.set_clip(previous_clip)


def _draw_back(surface, view, spec, p, frames, fade):
    veil = pygame.Surface((surface.get_width(), 600), pygame.SRCALPHA)
    veil.fill((3, 12, 17, round(45*fade)))
    surface.blit(veil, (0, 174))
    seal = pygame.Surface((360, 108), pygame.SRCALPHA)
    pulse = 1+math.sin(p*math.tau*2)*.06
    for radius, opacity in ((150, 35), (119, 110), (98, 200)):
        rect = pygame.Rect(180-round(radius*pulse), 54-round(radius*.20),
                           round(radius*2*pulse), round(radius*.4))
        pygame.draw.ellipse(seal, (*spec.color, round(opacity*fade)), rect, 3)
    for i in range(10):
        angle = i*math.tau/10+p*.8
        x, y = round(180+math.cos(angle)*126), round(54+math.sin(angle)*26)
        pygame.draw.polygon(seal, (*spec.color, round(200*fade)), [(x, y-5), (x+5, y), (x, y+5), (x-5, y)])
    surface.blit(seal, (PLAYER_X-180, PLAYER_GROUND_Y-57))
    if spec.ultimate_id == 'forcas_ancestrais':
        index = 0 if p < .24 else 1 if p < .43 else 2 if p < .81 else 3
        if len(frames) in (8,12):
            index = player_effect_frame(p,spec,len(frames))
        scale = .55+p*1.2 if p < .43 else 1 if p < .81 else 1+(p-.81)*.6
        _sprite(surface, frames[min(index, len(frames)-1)], (PLAYER_X, PLAYER_GROUND_Y-194), scale, 235*fade)
        _particles(surface, (PLAYER_X, PLAYER_GROUND_Y-143), (245, 216, 139), p, 155, 24)


def _draw_front(surface, view, spec, p, frames, fade):
    if spec.ultimate_id == 'mana_ancestral':
        index = 0 if p < .24 else 1 if p < .45 else 2 if p < .79 else 3
        if len(frames) in (8,12):
            index = player_effect_frame(p,spec,len(frames))
        rise = min(1, p/.38)
        y = PLAYER_GROUND_Y-150-165*rise
        scale = .85 if p < .45 else 1+math.sin(p*math.tau*3)*.035 if p < .79 else 1+(p-.79)*1.5
        _sprite(surface, frames[min(index, len(frames)-1)], (PLAYER_X+6, y), scale, 255*fade)
        _particles(surface, (PLAYER_X+6, y), (174, 236, 255), p, 137*min(1, p*3), 20)
        if .45 <= p < .80:
            for i in range(3):
                angle = p*math.tau+i*math.tau/3
                point = (round(PLAYER_X+math.cos(angle)*117), round(y+math.sin(angle)*47))
                pygame.draw.circle(surface, (210, 249, 255), point, 5)
    elif spec.ultimate_id == 'forcas_ancestrais':
        if .43 <= p < .88:
            _particles(surface, (PLAYER_X, PLAYER_GROUND_Y-96), (255, 228, 160), p, 78, 12)
    else:
        pose = roar_projectile_pose(p, PLAYER_X+158, ENEMY_X-27, PLAYER_GROUND_Y-128)
        if pose is not None:
            x, y, flight = pose
            index = 1 if flight < .40 else 2
            if len(frames) in (8,12):
                index = player_effect_frame(p,spec,len(frames))
            _sprite(surface, frames[min(index, len(frames)-1)], (x, y), 1+.10*math.sin(flight*math.pi), 255)
            _particles(surface, (x-98, y), (190, 238, 126), flight, 83, 12)
        elif p < spec.release:
            charge = p/spec.release
            index = player_effect_frame(p,spec,len(frames)) if len(frames) in (8,12) else 0
            _sprite(surface, frames[index], (PLAYER_X+128, PLAYER_GROUND_Y-137), .35+.50*charge, 210*charge)
        else:
            impact = (p-spec.impact)/(1-spec.impact)
            index = player_effect_frame(p,spec,len(frames)) if len(frames) in (8,12) else len(frames)-1
            _sprite(surface, frames[index], (ENEMY_X-15, PLAYER_GROUND_Y-128), 1+impact*.35, 255*(1-impact))
            ring = pygame.Surface((360, 315), pygame.SRCALPHA)
            for i in range(3):
                radius = round(35+impact*125+i*20)
                color = (134, 247, 151, round(180*(1-impact)))
                pygame.draw.ellipse(ring, color, (180-radius//2, 158-radius, radius, radius*2), 3)
            surface.blit(ring, (ENEMY_X-180, PLAYER_GROUND_Y-285))
