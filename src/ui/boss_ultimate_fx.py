"""Efeitos em oito ou doze etapas: carga, ataque, impacto e dissipação."""
import math
import pygame
from src.config.layout import ENEMY_X, PLAYER_X, PLAYER_GROUND_Y
from src.systems.boss_ultimate_animations import boss_ultimate_pose, boss_effect_frame
from src.ui.ultimate_fx import _sprite, _particles


def draw_boss_ultimate_fx(surface, view, behind=False):
    if view.enemy_attack_name == 'zanzara':
        from src.ui.zanzara_necromancer import available
        if available():
            return
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
    surface.set_clip(previous_clip.clip(pygame.Rect(0, 174, surface.get_width(), 600)))
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
    x, lift = boss_ultimate_pose(spec, p, ENEMY_X, PLAYER_X+158)
    veil = pygame.Surface((surface.get_width(), 600), pygame.SRCALPHA)
    veil.fill((6, 5, 13, round(38*fade)))
    surface.blit(veil, (0, 174))
    seal = pygame.Surface((405, 96), pygame.SRCALPHA)
    for radius, alpha in ((165, 40), (131, 150), (104, 210)):
        pygame.draw.ellipse(seal, (*spec.color, round(alpha*fade)), (203-radius, 48-radius//5, radius*2, radius*2//5), 3)
    for i in range(10):
        angle = p*1.5+i*math.tau/10
        xx, yy = round(203+math.cos(angle)*128), round(48+math.sin(angle)*26)
        pygame.draw.polygon(seal, (*spec.color, round(200*fade)), [(xx, yy-5), (xx+5, yy), (xx, yy+5), (xx-5, yy)])
    surface.blit(seal, (round(x)-203, PLAYER_GROUND_Y-51))
    if spec.mode == 'blades' and .25 <= p < .82:
        progress = (p-.25)/.57
        if len(frames) not in (8,12) or p < spec.impact:
            index = boss_effect_frame(p, spec, len(frames)) if len(frames) in (8,12) else 2
            vortex = pygame.transform.rotate(frames[index], -progress*360)
            _sprite(surface, vortex, (x, PLAYER_GROUND_Y-120), .8+.2*math.sin(p*math.pi), 175*fade)
    elif p < spec.release:
        charge = p/spec.release
        center = (ENEMY_X, PLAYER_GROUND_Y-(308 if spec.mode == 'execution' else 135))
        index = boss_effect_frame(p, spec, len(frames)) if len(frames) in (8,12) else 0
        _sprite(surface, frames[index], center, .25+.45*charge, 200*charge)
        _particles(surface, center, spec.color, charge, 53+83*charge, 16)


def _front(surface, view, frames, p):
    spec = view.enemy_ultimate
    effect_index = boss_effect_frame(p, spec, len(frames)) if len(frames) in (8,12) else None
    if spec.mode in ('bear', 'plasma', 'sovereign'):
        pose = view.get_enemy_projectile_pose()
        if pose is not None:
            x, y, flight = pose
            frame = frames[effect_index if effect_index is not None else 1 if flight < .35 else 2]
            # Vapor/lâminas de luz permanecem à direita do projétil que voa à esquerda.
            for distance, alpha in ((113, 22), (63, 45)):
                _sprite(surface, frame, (x+distance, y), .9, alpha)
            _sprite(surface, frame, (x, y), .9+.12*math.sin(flight*math.pi))
            _particles(surface, (x+83, y), spec.color, flight, 86, 12)
            if spec.mode == 'sovereign':
                for band in range(2):
                    angle = flight*math.tau*2+band*math.pi
                    xx, yy = round(x+math.cos(angle)*87), round(y+math.sin(angle)*48)
                    pygame.draw.ellipse(surface, (255, 214, 100), (xx-8, yy-11, 15, 21), 3)
            if spec.mode == 'plasma':
                for band in range(3):
                    points = [(round(x+53+i*20), round(y+math.sin(i*.8+p*35+band)*14+(band-1)*20)) for i in range(8)]
                    pygame.draw.lines(surface, (179, 220, 255), False, points, 2)
    else:
        x, lift = boss_ultimate_pose(spec, p, ENEMY_X, PLAYER_X+158)
        if spec.mode == 'blades' and spec.release <= p < spec.impact:
            blade = pygame.transform.rotate(frames[effect_index if effect_index is not None else 1], (p-spec.release)*650)
            _sprite(surface, blade, (x-68, PLAYER_GROUND_Y-113-lift), .85, 190)
        elif spec.mode == 'execution' and .45 <= p < spec.impact:
            _sprite(surface, frames[effect_index if effect_index is not None else 1], (x-98, PLAYER_GROUND_Y-150-lift), .75, 235)
        elif spec.mode == 'tremor' and .43 <= p < spec.impact:
            _sprite(surface, frames[effect_index if effect_index is not None else 1], (x-68, PLAYER_GROUND_Y-57-lift), .68, 210)
    if p >= spec.impact:
        fade = (p-spec.impact)/(1-spec.impact)
        index = 2 if spec.mode in ('execution', 'tremor') and fade < .42 else 3
        if effect_index is not None:
            index = effect_index
        impact_y = PLAYER_GROUND_Y-68 if spec.mode == 'tremor' else PLAYER_GROUND_Y-123
        _sprite(surface, frames[index], (PLAYER_X+18, impact_y), 1+fade*.3, 255*(1-fade))
        _particles(surface, (PLAYER_X, PLAYER_GROUND_Y-113), spec.color, fade, 45+fade*150, 20)
        ring = pygame.Surface((360, 330), pygame.SRCALPHA)
        for i in range(2):
            radius = round(33+fade*117+i*21)
            pygame.draw.ellipse(ring, (*spec.color, round(200*(1-fade))),
                                (180-radius//2, 165-radius, radius, radius*2), 3)
        surface.blit(ring, (PLAYER_X-180, PLAYER_GROUND_Y-288))
