"""Kit visual aprovado, recuperado dos originais em resolução detalhada.

Ações em oito quadros; estados de dano/derrota em faixas 384x280.
Preserva as artes aprovadas e usa poses dedicadas nos novos estados.
Não altera regras de combate. Coordenadas lógicas preservam os movimentos.
"""
import json
from functools import lru_cache
from pathlib import Path
import pygame
from src.config.settings import ASSETS_DIR
from src.config.layout import ENEMY_X, PLAYER_X, APPROACH_GAP, PLAYER_GROUND_Y, FLASH_DURATION

DEFEAT_DURATION = 1800

ROOT = Path(ASSETS_DIR) / 'bosses/zanzara_necromancer_v2'
FILES = {'atk1': 'foice-sombria.png', 'atk2': 'passo-do-barqueiro.png',
         'atk3': 'grilhoes-das-almas.png', 'ultimate': 'travessia-final.png'}


@lru_cache(maxsize=1)
def available():
    return all((ROOT / name).is_file() for name in FILES.values())


@lru_cache(maxsize=1)
def load_kit():
    result = {}
    for action, filename in FILES.items():
        sheet = pygame.image.load(str(ROOT / filename)).convert_alpha()
        width, height = (768, 512) if action == 'ultimate' else (256, 256)
        if sheet.get_size() != (width * 8, height):
            raise ValueError(f'Faixa inválida: {filename}: {sheet.get_size()}')
        result[action] = tuple(sheet.subsurface((i*width, 0, width, height)).copy() for i in range(8))
    return result


def frame_index(progress, impact=.8):
    # Quadro de contato coincide com o flash/dano já definido pelo combate.
    stops = (0, .12, .24, .34, impact-.10, impact, max(.90, impact+.06), .97)
    return max(i for i, start in enumerate(stops) if progress >= start) if progress >= 0 else 0


def action_frame(action, progress, impact):
    if action == 'atk1':
        if progress < .06:
            return 0
        if progress < impact-.09:
            return 3  # preparação sustentada, antes de aproximar
        if progress < impact:
            return 4
        if progress < .65:
            return 5
        return 6 if progress < .97 else 7
    return frame_index(progress, impact)


@lru_cache(maxsize=1)
def windup_sprite():
    image = pygame.image.load(str(Path(ASSETS_DIR) / 'bosses/zanzara_necromancer_v7/foice-preparacao-original.png')).convert_alpha()
    return pygame.transform.smoothscale(image, (280, 280))


@lru_cache(maxsize=1)
def ferry_sprite():
    source = pygame.image.load(str(Path(ASSETS_DIR) / 'bosses/zanzara_necromancer_v4/barco-isolado-original.png')).convert_alpha()
    boat = pygame.transform.smoothscale(source, (560, 512))
    return boat


@lru_cache(maxsize=1)
def rubra_aura_frames():
    """Chamas conectadas dos pés aos ombros, mantendo o corpo à frente."""
    image = pygame.image.load(str(Path(ASSETS_DIR) / 'bosses/zanzara_necromancer_v11/aura-corpo-inteiro-original.png')).convert_alpha()
    base = pygame.transform.smoothscale(image,(440,480))
    frames = []
    # Oito fases de pulsação suave do efeito, sem alterar escala do corpo.
    for factor in (.980,.987,.994,1.000,.996,.989,.982,.976):
        height = round(480*factor)
        frame = pygame.Surface((440,480),pygame.SRCALPHA)
        frame.blit(pygame.transform.smoothscale(base,(440,height)),(0,480-height))
        frames.append(frame)
    return tuple(frames)


def draw_rubra_style_aura(surface,progress):
    strength = max(0,min(1,progress/.16,(.97-progress)/.16))
    if strength:
        index = min(7,int(progress*8))
        frame = rubra_aura_frames()[index]
        # Campo de poder maior, ancorado nos pés. As duas passagens ficam
        # atrás do corpo e conservam a textura, a tonalidade e o centro livre.
        _blit(surface,frame,ENEMY_X,2.08,55,115,round(50*strength))
        _blit(surface,frame,ENEMY_X,2.0,55,115,round(255*strength))


def ultimate_cast_index(progress):
    if progress < .22: return 0
    if progress < .34: return 3
    if progress < .44: return 4
    if progress < .58: return 5
    return 6 if progress < .94 else 0


@lru_cache(maxsize=48)
def pose_aura(frame):
    padding = 12
    mask = pygame.mask.from_surface(frame, 45)
    aura = pygame.Surface((frame.get_width()+24,frame.get_height()+24),pygame.SRCALPHA)
    for radius,alpha in ((9,20),(5,45),(2,105)):
        layer = mask.to_surface(setcolor=(43,225,83,alpha),unsetcolor=(0,0,0,0))
        for dx,dy in ((-radius,0),(radius,0),(0,-radius),(0,radius),
                      (-radius,-radius),(radius,radius),(-radius,radius),(radius,-radius)):
            aura.blit(layer,(padding+dx,padding+dy),special_flags=pygame.BLEND_RGBA_MAX)
    inside = mask.to_surface(setcolor=(255,255,255,255),unsetcolor=(0,0,0,0))
    aura.blit(inside,(padding,padding),special_flags=pygame.BLEND_RGBA_SUB)
    return aura


def draw_pose_aura(surface,frame,x,scale,anchor_x,anchor_y,alpha=220):
    _blit(surface,pose_aura(frame),x,scale,anchor_x+3,anchor_y+3,alpha)


def passo_strike_phase(progress,impact):
    if progress < impact-.045: return 'windup'
    return 'release' if progress < impact else 'hit'


@lru_cache(maxsize=2)
def conjure_sprite(index):
    body = load_kit()['atk3'][index].copy()
    body.fill((0,0,0,0),(0,156,104,100))
    for px in range(104,136):
        for py in range(156,256):
            c = body.get_at((px,py))
            if c.a and c.g > c.r*1.25 and c.g > c.b*1.15:
                body.set_at((px,py),(0,0,0,0))
    return body


@lru_cache(maxsize=1)
def portal_sprite():
    image = pygame.image.load(str(Path(ASSETS_DIR) / 'bosses/zanzara_necromancer_v5/portal-maos-original.png')).convert_alpha()
    return image.subsurface(image.get_bounding_rect(min_alpha=15)).copy()


def portal_pose(progress, feet):
    rise = max(0, min(1, (progress-.12)/.35, (.97-progress)/.13))
    width = max(1, round(260*rise))
    height = max(1, round(200*rise))
    rect = pygame.Rect(0,0,width,height)
    rect.midbottom = (round(feet[0]),round(feet[1]+height*.25))
    return rect, round(255*rise)


def draw_target_effect(surface, view):
    if (getattr(view,'_zanzara_defeat_timer',None) is not None
            or view.attacker != 'enemy' or view.enemy_ultimate or view.enemy_action != 'atk3'):
        return
    progress = view.attack_timer/max(1,view.enemy_attack_duration)
    feet = getattr(view, 'player_ground_anchor', (PLAYER_X,PLAYER_GROUND_Y))
    rect, alpha = portal_pose(progress, feet)
    if alpha:
        effect = pygame.transform.smoothscale(portal_sprite(), rect.size)
        effect.set_alpha(alpha)
        surface.blit(effect,rect)


def ferry_pose(progress):
    flight = max(0, min(1, (progress-.44)/.36))
    x = (ENEMY_X-220)*(1-flight) + PLAYER_X*flight
    alpha = max(0, min(1, (progress-.44)/.10, (.97-progress)/.17))
    return x, round(alpha*255)


def actor_x(action, progress, index):
    target = PLAYER_X + APPROACH_GAP
    if action == 'atk2':
        return target if 4 <= index <= 6 else ENEMY_X
    if action == 'atk1':
        if progress < .22:
            t = 0
        elif progress < .48:
            t = (progress-.22)/.26
            t = t*t*(3-2*t)
        elif progress < .65:
            t = 1
        else:
            t = max(0, (1-progress)/.35)
        return ENEMY_X + (target-ENEMY_X)*t
    return ENEMY_X


def _blit(surface, frame, x, scale, anchor_x, anchor_y, alpha=255):
    # Mesma reamostragem suave dos personagens existentes. Coordenadas lógicas
    # mantidas para preservar os movimentos aprovados, com fontes 4x mais densas.
    scale = scale * 1.25 / 4
    anchor_x *= 4
    anchor_y *= 4
    size = (round(frame.get_width()*scale), round(frame.get_height()*scale))
    enlarged = pygame.transform.smoothscale(frame, size)
    if alpha < 255:
        enlarged.set_alpha(alpha)
    surface.blit(enlarged, (round(x-anchor_x*scale), round(PLAYER_GROUND_Y-anchor_y*scale)))


@lru_cache(maxsize=2)
def state_sprite(name):
    folder = Path(ASSETS_DIR) / 'bosses/zanzara_necromancer_v12'
    metadata = json.loads((folder/'estados.json').read_text(encoding='utf-8'))
    image = pygame.image.load(str(folder/(name+'.png'))).convert_alpha()
    anchor = metadata[name]['anchor']
    return image,anchor[0]/4,anchor[1]/4


@lru_cache(maxsize=2)
def state_frames(name):
    path = Path(ASSETS_DIR) / 'bosses/zanzara_necromancer_v12' / (name+'-faixa.png')
    sheet = pygame.image.load(str(path)).convert_alpha()
    if sheet.get_size() != (3072,280):
        raise ValueError(f'Faixa de estado inválida: {path.name}')
    return tuple(sheet.subsurface((i*384,0,384,280)).copy() for i in range(8))


def draw_hit_reaction(surface,view):
    p = max(0,min(1,1-view.enemy_flash/FLASH_DURATION))
    frame = state_frames('dano')[min(7,int(p*8))]
    _blit(surface,frame,ENEMY_X,4,48,69.5)


def draw_defeat(surface,view):
    p = min(1,view._zanzara_defeat_timer/DEFEAT_DURATION)
    if p < 1:
        _blit(surface,state_frames('derrota')[min(7,int(p*8))],ENEMY_X,4,48,69.5)


def draw(surface, view):
    if getattr(view,'_zanzara_defeat_timer',None) is not None:
        draw_defeat(surface,view)
        return
    if view.enemy_flash > 0:
        draw_hit_reaction(surface,view)
        return
    kit = load_kit()
    active = view.attacker == 'enemy'
    action = ('ultimate' if view.enemy_ultimate else view.enemy_action) if active else None
    if action not in kit:
        _blit(surface, kit['atk1'][0], ENEMY_X, 4, 38, 62)
        return
    progress = min(1, view.attack_timer/max(1, view.enemy_attack_duration))
    index = action_frame(action, progress, view.enemy_impact_fraction)
    # O último quadro é sempre o mesmo repouso, sem variação de escala entre ações.
    if index == 7:
        _blit(surface, kit['atk1'][0], ENEMY_X, 4, 38, 62)
        return
    frame = kit[action][index]
    x = actor_x(action, progress, index)
    if action == 'atk1' and index == 3:
        _blit(surface, windup_sprite(), x, 4, 38.25, 64)
    elif action == 'atk2' and index == 4:
        phase = passo_strike_phase(progress,view.enemy_impact_fraction)
        if phase == 'windup':
            body, ax, ay = windup_sprite(),38.25,64
        else:
            body, ax, ay = kit['atk1'][4],38,62
        draw_pose_aura(surface,body,x,4,ax,ay)
        _blit(surface,body,x,4,ax,ay)
    elif action == 'atk3':
        body = conjure_sprite(2 if index else 0)
        if index:
            draw_rubra_style_aura(surface,progress)
        _blit(surface,body,x,4,40,62)
        # O portal segue os pés do jogador, desenhado em primeiro plano.
    elif action == 'ultimate':
        cast = ultimate_cast_index(progress)
        draw_rubra_style_aura(surface,progress)
        _blit(surface, kit['atk1'][cast], ENEMY_X, 4, 38, 62)
        # Uma peça estável mantém casco, vela e barqueiro unidos, sem salto
        # de posição/tamanho ao trocar os frames compostos da imagem original.
        boat = ferry_sprite()
        boat_x, alpha = ferry_pose(progress)
        if alpha:
            _blit(surface, boat, boat_x, 2.6, 20, 124, alpha)
    else:
        _blit(surface, frame, x, 4 if action == 'atk1' else 4.2, 38, 62)
