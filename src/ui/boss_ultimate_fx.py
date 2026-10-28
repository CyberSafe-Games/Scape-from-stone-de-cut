"""Camadas próprias dos quatro especiais: carga, deslocamento e impacto."""
import math
import pygame
from src.config.layout import ENEMY_X, PLAYER_X, PLAYER_GROUND_Y
from src.systems.boss_ultimate_animations import boss_ultimate_pose
from src.ui.ultimate_fx import _sprite, _particles


def draw_boss_ultimate_fx(surface, view, behind=False):
    spec = view.enemy_ultimate
    if spec is None or view.attacker != 'enemy':
        return
    p = view.attack_timer/max(1, spec.duration)
    if not 0 <= p < 1:
        return
    frames = view.asset_manager.get_boss_ultimate_sprites(view.enemy_attack_name, effects=True)
    if not frames:
        return
    previous_clip = surface.get_clip()
    surface.set_clip(previous_clip.clip(pygame.Rect(0, 116, surface.get_width(), 400)))
    try:
        if behind:
            _back(surface, view, frames, p)
        else:
            _front(surface, view, frames, p)
    finally:
        surface.set_clip(previous_clip)


def _back(surface, view, frames, p):
    spec = view.enemy_ultimate
    fade = min(1, p/.12, (1-p)/.18)
    x, lift = boss_ultimate_pose(spec, p, ENEMY_X, PLAYER_X+105)
    veil = pygame.Surface((surface.get_width(), 400), pygame.SRCALPHA)
    veil.fill((6, 5, 13, round(38*fade)))
    surface.blit(veil, (0, 116))
    seal = pygame.Surface((270, 64), pygame.SRCALPHA)
    for radius, alpha in ((110, 40), (87, 150), (69, 210)):
        pygame.draw.ellipse(seal, (*spec.color, round(alpha*fade)), (135-radius, 32-radius//5, radius*2, radius*2//5), 2)
    for i in range(10):
        angle = p*1.5+i*math.tau/10
        xx, yy = round(135+math.cos(angle)*85), round(32+math.sin(angle)*17)
        pygame.draw.polygon(seal, (*spec.color, round(200*fade)), [(xx, yy-3), (xx+3, yy), (xx, yy+3), (xx-3, yy)])
    surface.blit(seal, (round(x)-135, PLAYER_GROUND_Y-34))
    if spec.mode == 'blades' and .25 <= p < .82:
        progress = (p-.25)/.57
        vortex = pygame.transform.rotate(frames[2], -progress*360)
        _sprite(surface, vortex, (x, PLAYER_GROUND_Y-80), .8+.2*math.sin(p*math.pi), 175*fade)
    elif p < spec.release:
        charge = p/spec.release
        center = (ENEMY_X, PLAYER_GROUND_Y-(205 if spec.mode == 'execution' else 90))
        _sprite(surface, frames[0], center, .25+.45*charge, 200*charge)
        _particles(surface, center, spec.color, charge, 35+55*charge, 16)


def _front(surface, view, frames, p):
    spec = view.enemy_ultimate
    if spec.mode in ('bear', 'plasma'):
        pose = view.get_enemy_projectile_pose()
        if pose is not None:
            x, y, flight = pose
            frame = frames[1 if flight < .35 else 2]
            # Vapor/lâminas de luz permanecem à direita do projétil que voa à esquerda.
            for distance, alpha in ((75, 22), (42, 45)):
                _sprite(surface, frame, (x+distance, y), .9, alpha)
            _sprite(surface, frame, (x, y), .9+.12*math.sin(flight*math.pi))
            _particles(surface, (x+55, y), spec.color, flight, 57, 12)
            if spec.mode == 'plasma':
                for band in range(3):
                    points = [(round(x+35+i*13), round(y+math.sin(i*.8+p*35+band)*9+(band-1)*13)) for i in range(8)]
                    pygame.draw.lines(surface, (179, 220, 255), False, points, 1)
    else:
        x, lift = boss_ultimate_pose(spec, p, ENEMY_X, PLAYER_X+105)
        if spec.mode == 'blades' and spec.release <= p < spec.impact:
            blade = pygame.transform.rotate(frames[1], (p-spec.release)*650)
            _sprite(surface, blade, (x-45, PLAYER_GROUND_Y-75-lift), .85, 190)
        elif spec.mode == 'execution' and .45 <= p < spec.impact:
            _sprite(surface, frames[1], (x-65, PLAYER_GROUND_Y-100-lift), .75, 235)
    if p >= spec.impact:
        fade = (p-spec.impact)/(1-spec.impact)
        index = 2 if spec.mode == 'execution' and fade < .42 else 3
        _sprite(surface, frames[index], (PLAYER_X+12, PLAYER_GROUND_Y-82), 1+fade*.3, 255*(1-fade))
        _particles(surface, (PLAYER_X, PLAYER_GROUND_Y-75), spec.color, fade, 30+fade*100, 20)
        ring = pygame.Surface((240, 220), pygame.SRCALPHA)
        for i in range(2):
            radius = round(22+fade*78+i*14)
            pygame.draw.ellipse(ring, (*spec.color, round(200*(1-fade))),
                                (120-radius//2, 110-radius, radius, radius*2), 2)
        surface.blit(ring, (PLAYER_X-120, PLAYER_GROUND_Y-192))
