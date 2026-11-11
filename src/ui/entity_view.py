import math
import pygame

from src.config.colors import WHITE
from src.config.layout import (
    PLAYER_X,
    ENEMY_X,
    ENEMY_Y,
    PLAYER_GROUND_Y,
    APPROACH_GAP,
    ATTACK_DURATION,
    APPROACH_FRAC,
    STRIKE_FRAC,
    FLASH_DURATION,
    MELEE_MIN_DURATION,
    POSE_RECOVERY_MS,
    PLAYER_IDLE_FRAME_MS,
    BOSS_IDLE_FRAME_MS,
    COMMON_IDLE_FRAME_MS,
    VICTORY_FRAME_MS,
    LEGACY_VICTORY_FRAME_MS,
)
from src.ui.helpers import ARENA_ACTOR_LIGHT, ease, scale_to_display
from src.ui.pose_playback import UNIFORM_TWELVE, align_stance, display_pose, loop_pose, sample_pose
from src.systems.animation_timing import animation_duration, frame_index
from src.systems.animation_inbetweens import action_boundaries, frame_boundaries, recovery_progress, timed_frame
from src.systems.card_definitions import SPECS_BY_NAME
from src.ui.guardian_spirit_fx import draw_guardian_spirit
from src.ui.crimson_cast_fx import draw_crimson_cast
from src.systems.normal_enemy_catalog import NORMAL_RANGED, NORMAL_SPRITES
from src.systems.ultimate_animations import ULTIMATE_ANIMATIONS, cast_frame
from src.systems.boss_ultimate_animations import BOSS_ULTIMATE_ANIMATIONS, boss_cast_frame, boss_ultimate_pose
from src.systems.alvaro_tex_animations import (
    ATTACK_BOUNDARIES as DUO_BOUNDARIES,
    ATTACK_MS as DUO_ATTACK_MS,
    NAMES as DUO_NAMES,
    RANGED as DUO_RANGED,
    TRANSITION_MS,
    attack_frame,
)
from src.systems.gordofera_animations import TREMOR_BOUNDARIES, tremor_frame
from src.ui.alvaro_tex_fx import draw_alvaro_tex_fx
from src.systems.boss_animation_kits import KITS, kit_frame
from src.systems.player_animation_kits import player_frame
from src.systems.common_animation_kits import COMMON_KITS, PROJECTILE_ORIGINS

NORMAL_IDLE_NAMES = frozenset(name.lower() for name in NORMAL_SPRITES) - {'morcego sombrio'}
MELEE_RETURN_FRACTION = APPROACH_FRAC + STRIKE_FRAC
HURT_BOUNDARIES = (0, .07, .15, .25, .40, .54, .68, .84)
BOSS_BODY_LIGHT = {
    'goblin nerd': (189, 177, 164),
    'corpo seco': (199, 184, 169),
    'guardião da pedra': (186, 173, 160),
    'carrasco da vigília': (188, 174, 163),
    **dict.fromkeys(DUO_NAMES, (194, 181, 165)),
}


def hurt_pose(frames, ready, remaining, align):
    if align and ready:
        frames = align_stance(tuple(frames), ready[0])
    return frames[timed_frame(1 - remaining / FLASH_DURATION, HURT_BOUNDARIES, 8)]


def recoil_amount(remaining):
    """Impacto curto e retorno longo, com velocidade zero nos extremos."""
    progress = 1 - max(0, min(FLASH_DURATION, remaining)) / FLASH_DURATION
    if progress < .23:
        return ease(progress / .23)
    return 1 - ease((progress - .23) / .77)


def draw_recoiling_actor(surface, frame, rect, remaining, direction, blend_flags=0):
    amount = recoil_amount(remaining)
    if amount <= 0:
        surface.blit(frame, rect, special_flags=blend_flags)
        return

    bounds = frame.get_bounding_rect()
    if not bounds.width or not bounds.height:
        return
    body = frame.subsurface(bounds)
    height = max(1, round(bounds.height * (1 - .04 * amount)))
    body = pygame.transform.scale(body, (bounds.width, height))
    angle = direction * -9 * amount
    rotated = pygame.transform.rotate(body, angle)
    rotated.fill((255, round(255 - 44 * amount), round(255 - 48 * amount)),
                 special_flags=pygame.BLEND_RGB_MULT)
    back_foot = direction * bounds.width / 4
    pivot_offset = pygame.Vector2(back_foot, height / 2).rotate(-angle)
    foot = pygame.Vector2(rect.x + bounds.centerx + back_foot, rect.y + bounds.bottom)
    surface.blit(rotated, rotated.get_rect(center=foot - pivot_offset), special_flags=blend_flags)


class EntityView:
    """Responsável por gerenciar os timers de animação, calcular poses de combate

    e renderizar o Jogador e o Inimigo na tela.
    """

    # duração, lançamento e impacto como frações da animação completa.
    GOBLIN_RANGED_ATTACKS = {"atk1": (1100, 0.30, 0.74), "atk2": (900, 0.30, 0.58)}
    RANGED_ATTACKS = {
        'zanzara': {'atk2': (1600, .42, .78), 'atk3': (1900, .44, .80)},
        "goblin nerd": GOBLIN_RANGED_ATTACKS,
        "vinimuth": {"atk2": (1200, 0.54, 0.87)},
        'guardião da pedra': {'atk2': (1400, 0.50, 0.84)},
        **NORMAL_RANGED,
        **DUO_RANGED,
    }

    def __init__(self, asset_manager):
        self.asset_manager = asset_manager

        # Estados de animação
        self.attacker = None
        self.attack_timer = 0
        self.enemy_attack_duration = ATTACK_DURATION
        self.player_action = None
        self.player_action_timer = 0
        self.player_action_duration = 700
        self.player_attack_duration = ATTACK_DURATION
        self.pending_enemy_hit_at = None
        self.enemy_action = None
        self.enemy_action_timer = 0
        self.enemy_action_duration = 600

        self.player_flash = 0
        self.enemy_flash = 0
        self.post_enemy_pause = 0
        self.pending_player_hit_at = None
        self.enemy_ranged_attack = None
        self._screwdriver_sprite = None
        self.enemy_attack_name = ""
        self.enemy_ultimate = None
        self.phase_transition_timer = None
        self.enemy_idle_timer = 0
        self.player_idle_timer = 0
        self.player_victory_timer = 0
        self._player_victory_active = False
        self._zanzara_defeat_timer = None

    def trigger_attack(self, attacker, action=None, enemy_name=None, ultimate=False):
        self.attacker = attacker
        self.attack_timer = 0
        self.pending_player_hit_at = None
        self.enemy_ranged_attack = None
        self.enemy_attack_name = (enemy_name or "").strip().lower()
        self.enemy_ultimate = BOSS_ULTIMATE_ANIMATIONS.get(self.enemy_attack_name) if ultimate and attacker == 'enemy' else None
        if attacker == "player":
            self.player_idle_timer = 0
            self.player_action = action
            self.player_action_timer = 0
            spec = SPECS_BY_NAME.get(action)
            self.player_attack_duration = 1200 if spec and spec[6] == 'ranged' else 900 if spec else MELEE_MIN_DURATION
            self.player_action_duration = self.player_attack_duration
            self.pending_enemy_hit_at = None
        elif attacker == "enemy":
            self.enemy_idle_timer = 0
            self.enemy_action = action
            self.enemy_attack_duration = animation_duration(action, ATTACK_DURATION)
            if self.enemy_attack_name == 'zanzara':
                self.enemy_attack_duration = 1300
            if self.enemy_attack_name == 'gordofera':
                self.enemy_attack_duration = {'atk1': 1150, 'atk2': 1300, 'atk3': 1450}.get(action, 1300)
            if self.enemy_attack_name == 'carrasco da vigília':
                self.enemy_attack_duration = {'atk1': 1050, 'atk2': 1150, 'atk3': 1500}.get(action, ATTACK_DURATION)
            if self.enemy_attack_name in DUO_ATTACK_MS:
                self.enemy_attack_duration = DUO_ATTACK_MS[self.enemy_attack_name].get(action, 1300)
            self.enemy_ranged_attack = self.RANGED_ATTACKS.get(self.enemy_attack_name, {}).get(action)
            if self.enemy_ranged_attack:
                self.enemy_attack_duration = self.enemy_ranged_attack[0]
            elif self.enemy_attack_name in KITS or self.enemy_attack_name in COMMON_KITS:
                self.enemy_attack_duration = max(self.enemy_attack_duration, MELEE_MIN_DURATION)
            if self.enemy_ultimate:
                spec = self.enemy_ultimate
                self.enemy_attack_duration = spec.duration
                self.enemy_ranged_attack = ((spec.duration, spec.release, spec.impact)
                                           if spec.mode in ('bear', 'plasma', 'sovereign') else None)
            self.enemy_action_timer = 0

    def trigger_enemy_action(self, action, enemy_name=None):
        self.enemy_idle_timer = 0
        if enemy_name is not None:
            self.enemy_attack_name = enemy_name.strip().lower()
        self.enemy_action = action
        self.enemy_action_duration = animation_duration(action, 600)
        if self.enemy_attack_name == 'gordofera' and action == 'def':
            self.enemy_action_duration = 1400
        if self.enemy_attack_name == 'zanzara' and action == 'healer2':
            self.enemy_action_duration = 1800
        if self.enemy_attack_name == 'carrasco da vigília' and action == 'healer2':
            self.enemy_action_duration = 1500
        if self.enemy_attack_name in DUO_NAMES and action == 'healer2':
            self.enemy_action_duration = DUO_ATTACK_MS[self.enemy_attack_name].get(action, 1800)
        self.enemy_action_timer = 0

    @property
    def enemy_impact_fraction(self):
        if self.enemy_ultimate:
            return self.enemy_ultimate.impact
        if self.enemy_ranged_attack:
            return self.enemy_ranged_attack[2]
        if self.enemy_attack_name in DUO_NAMES:
            return .58 if self.enemy_attack_name==DUO_NAMES[0] else .60
        return .52 if self.enemy_attack_name in KITS or self.enemy_attack_name in COMMON_KITS else .49

    def trigger_flash(self, target, enemy_name=None):
        if target == "player":
            if self.attacker == "enemy":
                self.pending_player_hit_at = self.enemy_attack_duration * self.enemy_impact_fraction
            else:
                self.player_flash = FLASH_DURATION
        elif target == "enemy":
            if enemy_name:
                self.enemy_attack_name = enemy_name.strip().lower()
            if self.player_action in ULTIMATE_ANIMATIONS:
                self.pending_enemy_hit_at = self.player_action_duration * ULTIMATE_ANIMATIONS[self.player_action].impact
            elif self.attacker == 'player':
                spec = SPECS_BY_NAME.get(self.player_action)
                fraction = .90 if spec and spec[6] == 'ranged' else .52
                self.pending_enemy_hit_at = self.player_attack_duration * fraction
            else:
                self.enemy_flash = FLASH_DURATION

    def trigger_player_action(self, action):
        self.player_idle_timer = 0
        self.player_action = action
        self.player_action_timer = 0
        ultimate = ULTIMATE_ANIMATIONS.get(action)
        self.player_action_duration = ultimate.duration if ultimate else 1100 if action in SPECS_BY_NAME else 700
        if ultimate:
            self.pending_enemy_hit_at = None
            self.attacker = None
            self.attack_timer = 0

    def is_enemy_defeat_done(self,enemy):
        if enemy.name.lower() != 'zanzara':
            return True
        from src.ui.zanzara_necromancer import DEFEAT_DURATION
        return self._zanzara_defeat_timer is not None and self._zanzara_defeat_timer >= DEFEAT_DURATION

    @property
    def player_recovery_ms(self):
        return 0 if self.player_action in ULTIMATE_ANIMATIONS else POSE_RECOVERY_MS

    @property
    def enemy_recovery_ms(self):
        return POSE_RECOVERY_MS if self.enemy_attack_name in KITS and not self.enemy_ultimate else 0

    def update(self, dt):
        """Atualiza todos os timers de animação visual."""
        if self._zanzara_defeat_timer is not None:
            self._zanzara_defeat_timer += dt
        player_was_busy = self.attacker == 'player' or self.player_action is not None
        player_was_hurt = self.player_flash > 0
        self.player_victory_timer += dt
        enemy_was_busy = (self.attacker == 'enemy' or self.enemy_action is not None
                          or self.phase_transition_timer is not None)
        enemy_was_hurt = self.enemy_flash > 0
        if self.phase_transition_timer is not None:
            self.phase_transition_timer += dt
        self.player_flash = max(0, self.player_flash - dt)
        self.enemy_flash = max(0, self.enemy_flash - dt)
        if self.attacker is not None:
            self.attack_timer += dt
            if (self.attacker == "enemy" and self.pending_player_hit_at is not None
                    and self.attack_timer >= self.pending_player_hit_at):
                self.player_flash = max(0, FLASH_DURATION - (
                    self.attack_timer - self.pending_player_hit_at))
                self.pending_player_hit_at = None
            if (self.attacker == 'player' and self.pending_enemy_hit_at is not None
                    and self.attack_timer >= self.pending_enemy_hit_at):
                self.enemy_flash = max(0, FLASH_DURATION - (self.attack_timer - self.pending_enemy_hit_at))
                self.pending_enemy_hit_at = None
            duration = (self.enemy_attack_duration + self.enemy_recovery_ms if self.attacker == "enemy"
                        else self.player_attack_duration + self.player_recovery_ms)
            if self.attack_timer >= duration:
                was_enemy = self.attacker == "enemy"
                self.attacker = None
                self.attack_timer = 0
                if was_enemy:
                    self.enemy_action = None
                    self.enemy_action_timer = 0
                    self.enemy_ranged_attack = None
                    self.pending_player_hit_at = None
                    self.enemy_ultimate = None

        if self.enemy_action is not None and self.attacker != "enemy":
            self.enemy_action_timer += dt
            if self.enemy_action_timer >= self.enemy_action_duration + self.enemy_recovery_ms:
                self.enemy_action = None
                self.enemy_action_timer = 0

        if self.player_action is not None:
            self.player_action_timer += dt
            if self.player_action in ULTIMATE_ANIMATIONS and self.pending_enemy_hit_at is not None and self.player_action_timer >= self.pending_enemy_hit_at:
                self.enemy_flash = max(0, FLASH_DURATION-(self.player_action_timer-self.pending_enemy_hit_at))
                self.pending_enemy_hit_at = None
            if self.player_action_timer >= self.player_action_duration + self.player_recovery_ms:
                self.player_action = None
                self.player_action_timer = 0

        self.post_enemy_pause = max(0, self.post_enemy_pause - dt)
        if (enemy_was_busy or self.attacker == 'enemy' or self.enemy_action is not None
                or ((enemy_was_hurt or self.enemy_flash > 0) and self.enemy_attack_name in KITS)
                or self.phase_transition_timer is not None):
            self.enemy_idle_timer = 0
        elif not (enemy_was_hurt or self.enemy_flash > 0):
            self.enemy_idle_timer += dt
        if player_was_busy or self.attacker == 'player' or self.player_action is not None or player_was_hurt or self.player_flash > 0:
            self.player_idle_timer = 0
        else:
            self.player_idle_timer += dt

    def is_enemy_resolving_done(self):
        # O segundo ataque só começa depois de terminar a animação do primeiro.
        return (self.attacker is None and self.enemy_action is None
                and self.post_enemy_pause <= 0)

    def get_attack_pose(self, attacker, home_x, target_x):
        """Calcula a posição interpolada X e extensão de braço para um ataque corpo-a-corpo."""
        if self.attacker != attacker:
            return home_x, 0.0
        if attacker == 'enemy' and self.enemy_ultimate:
            progress = self.attack_timer/max(1, self.enemy_attack_duration)
            x, _ = boss_ultimate_pose(self.enemy_ultimate, progress, home_x, PLAYER_X+158)
            return x, 0
        if attacker == "enemy" and self.enemy_ranged_attack:
            return home_x, 0.0
        if attacker == 'player' and self.player_action in SPECS_BY_NAME and SPECS_BY_NAME[self.player_action][6] != 'melee':
            return home_x, 0.0

        duration = self.enemy_attack_duration if attacker == "enemy" else self.player_attack_duration
        extension = self.enemy_recovery_ms if attacker == "enemy" else self.player_recovery_ms
        progress = recovery_progress(self.attack_timer, duration, extension, MELEE_RETURN_FRACTION)

        # 1. Aproximação
        if progress < APPROACH_FRAC:
            local = ease(progress / APPROACH_FRAC)
            x = home_x + (target_x - home_x) * local
            return x, 0.0

        # 2. Golpe
        if progress < MELEE_RETURN_FRACTION:
            local = (progress - APPROACH_FRAC) / STRIKE_FRAC
            arm_extend = math.sin(local * math.pi)
            return target_x, arm_extend

        # 3. Retorno
        local = (progress - MELEE_RETURN_FRACTION) / (1 - MELEE_RETURN_FRACTION)
        local = ease(local)
        x = target_x + (home_x - target_x) * local
        return x, 0.0

    def get_enemy_projectile_pose(self):
        """Trajeto da mão do goblin ao tronco do jogador, apenas durante o voo."""
        if self.attacker != "enemy" or not self.enemy_ranged_attack:
            return None
        duration, launch, impact = self.enemy_ranged_attack
        progress = self.attack_timer / duration
        if not launch <= progress < impact:
            return None
        flight = (progress - launch) / (impact - launch)
        start_x, end_x = ENEMY_X - 99, PLAYER_X + 18
        start_y = PLAYER_GROUND_Y - (143 if self.enemy_attack_name == 'morcego sombrio'
                                     else 117 if self.enemy_attack_name in ('vinimuth', 'centauro vigia') else 87)
        if self.enemy_attack_name == 'guardião da pedra':
            start_x = ENEMY_X - 203
            start_y = PLAYER_GROUND_Y - 143
        origins = {'golem das ruínas': (248, 173), 'centauro vigia': (99, 126),
                   'zanzara': (135, 150),
                   'putrefato do pântano': (143, 105), 'morcego sombrio': (114, 180)}
        if self.enemy_attack_name in origins:
            offset_x, offset_y = origins[self.enemy_attack_name]
            start_x, start_y = ENEMY_X-offset_x, PLAYER_GROUND_Y-offset_y
        end_y = PLAYER_GROUND_Y - 98
        if self.enemy_attack_name in DUO_NAMES:
            start_y = PLAYER_GROUND_Y - (240 if self.enemy_attack_name == DUO_NAMES[0] else 98)
        origin = PROJECTILE_ORIGINS.get((self.enemy_attack_name, self.enemy_action))
        if origin:
            start_x, start_y, end_y = ENEMY_X-origin[0], PLAYER_GROUND_Y-origin[1], PLAYER_GROUND_Y-origin[2]
            if self.enemy_attack_name == 'morcego sombrio':
                start_y -= 42 + round(4.5*math.sin(pygame.time.get_ticks()/300))
        x = start_x + (end_x - start_x) * flight
        y = start_y + (end_y - start_y) * flight
        if self.enemy_attack_name == 'goblin nerd' and self.enemy_action == "atk1":
            y -= 98 * math.sin(math.pi * flight)
        return x, y, flight

    def draw_enemy_projectile(self, surface):
        if self.enemy_attack_name == 'zanzara':
            from src.ui.zanzara_necromancer import available, draw_target_effect
            if available():
                draw_target_effect(surface, self)
                return  # Efeitos novos são renderizados junto ao kit, sem moedas/onda antiga.
        if self.enemy_attack_name == 'zanzara' and not self.enemy_ultimate:
            from src.ui.zanzara_fx import draw_zanzara_fx
            draw_zanzara_fx(surface, self)
            return
        if self.enemy_attack_name == DUO_NAMES[0] and self.enemy_action == 'healer2':
            draw_alvaro_tex_fx(surface, self)
            return
        if self.enemy_attack_name in DUO_NAMES and self.attacker == 'enemy':
            draw_alvaro_tex_fx(surface, self)
            return
        if self.enemy_ultimate:
            return
        if self.enemy_attack_name == 'carrasco da vigília' and self.enemy_action == 'healer2':
            draw_crimson_cast(surface, self)
            return
        if self.enemy_attack_name == 'guardião da pedra' and self.enemy_action == 'atk2':
            draw_guardian_spirit(surface, self)
            return
        pose = self.get_enemy_projectile_pose()
        if pose is None:
            return
        x, y, flight = pose
        projectile = self.asset_manager.get_enemy_projectile(
            self.enemy_attack_name, self.enemy_action, min(3, int(flight * 4))
        )
        projectile = scale_to_display(projectile)
        if projectile is not None:
            surface.blit(projectile, projectile.get_rect(center=(round(x), round(y))))
            return
        if self.enemy_action == "atk1":
            if self._screwdriver_sprite is None:
                # Sprite vetorial em resolução nativa: cabo, haste e ponta chata.
                tool = pygame.Surface((44, 14), pygame.SRCALPHA)
                pygame.draw.polygon(tool, (35, 28, 24), [(0, 7), (7, 3), (25, 4), (25, 10), (7, 11)])
                pygame.draw.polygon(tool, (177, 193, 193), [(1, 7), (8, 5), (26, 5), (26, 8), (8, 8)])
                pygame.draw.rect(tool, (49, 28, 18), (24, 1, 19, 12), border_radius=3)
                pygame.draw.rect(tool, (173, 100, 38), (26, 3, 15, 8), border_radius=2)
                pygame.draw.line(tool, (239, 179, 72), (29, 4), (38, 4), 2)
                pygame.draw.line(tool, (85, 48, 24), (29, 9), (38, 9), 2)
                self._screwdriver_sprite = tool
            tool = pygame.transform.rotate(scale_to_display(self._screwdriver_sprite), flight * 720)
            surface.blit(tool, tool.get_rect(center=(round(x), round(y))))
        else:
            # Descarga azul, na mesma paleta da arma nos frames de atk2.
            glow = pygame.Surface((135, 60), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (35, 133, 255, 45), (0, 6, 131, 48))
            pygame.draw.ellipse(glow, (55, 170, 255, 95), (3, 15, 99, 30))
            pygame.draw.lines(glow, (63, 182, 255), False,
                              [(120, 30), (83, 21), (68, 35), (42, 20), (8, 30)], 8)
            pygame.draw.lines(glow, (215, 249, 255), False,
                              [(105, 30), (75, 27), (59, 35), (39, 26), (8, 30)], 3)
            pygame.draw.circle(glow, (235, 253, 255), (12, 30), 6)
            surface.blit(glow, (round(x) - 12, round(y) - 30))

    def get_player_frame(self, game_state, *, interpolate=False):
        """Determina o sprite e a posição X exata do jogador com base no estado e nos timers."""
        victory = game_state == 'victory'
        if victory and not self._player_victory_active:
            self.player_victory_timer = 0
        self._player_victory_active = victory

        # Vitória
        if game_state == "victory" and self.player_action is None and self.attacker != 'player':
            sprites = self.asset_manager.get_player_sprite_group("vitoria")
            if sprites:
                frame_ms = VICTORY_FRAME_MS if len(sprites) == 12 else LEGACY_VICTORY_FRAME_MS
                frame = loop_pose(sprites, self.player_victory_timer, frame_ms, interpolate)
                return PLAYER_X, frame

        # Ação específica da carta
        if self.player_action is not None:
            sprites = self.asset_manager.get_card_action_sprites(self.player_action)
            if sprites:
                progress = min(
                    1.0, self.player_action_timer / self.player_action_duration
                )
                spec = SPECS_BY_NAME.get(self.player_action)
                if self.player_action in ULTIMATE_ANIMATIONS:
                    release = ULTIMATE_ANIMATIONS[self.player_action].release
                    index = cast_frame(progress, release, len(sprites))
                elif len(sprites) in (8,12):
                    mode = spec[6] if spec else 'self'
                    release = .64 if mode == 'ranged' else .52
                    recovery_start = MELEE_RETURN_FRACTION if mode == 'melee' else release
                    progress = recovery_progress(self.player_action_timer, self.player_action_duration,
                                                 self.player_recovery_ms, recovery_start)
                    index = player_frame(progress, mode, release, count=len(sprites))
                elif spec and spec[6] == 'melee':
                    index = 0 if progress < 0.4 else 1 if progress < 0.5 else 2 if progress < 0.68 else 3
                elif spec and spec[6] == 'ranged':
                    index = 0 if progress < 0.2 else 1 if progress < 0.4 else 2 if progress < 0.64 else 3
                else:
                    index = min(len(sprites) - 1, int(progress * len(sprites)))
                frame = sprites[min(len(sprites) - 1, index)]
                if interpolate and len(sprites) == 12:
                    frame = sample_pose(sprites, index, progress, action_boundaries(12, release), True, cuts=(6,))
            else:
                idle = self.asset_manager.get_player_sprite_group('idle')
                frame = self._player_idle_pose(idle, interpolate)

            if self.attacker == "player":
                x, _ = self.get_attack_pose("player", PLAYER_X, ENEMY_X - APPROACH_GAP)
                return x, frame
            return PLAYER_X, frame

        # Ataque
        if self.attacker == "player":
            target_x = ENEMY_X - APPROACH_GAP
            x, _ = self.get_attack_pose("player", PLAYER_X, target_x)
            progress = min(1.0, self.attack_timer / ATTACK_DURATION)
            punches = self.asset_manager.get_player_sprite_group('soco')
            if punches and len(punches) in (8,12):
                progress = recovery_progress(self.attack_timer, self.player_attack_duration,
                                             self.player_recovery_ms, MELEE_RETURN_FRACTION)
                index = player_frame(progress, 'melee', count=len(punches))
                return x, sample_pose(punches, index, progress, action_boundaries(12, .52), interpolate, cuts=(6,))

            if progress < APPROACH_FRAC:
                sprites = self.asset_manager.get_player_sprite_group("idle")
                frame = self._player_idle_pose(sprites, interpolate)
            elif progress < (APPROACH_FRAC + STRIKE_FRAC):
                sprites = self.asset_manager.get_player_sprite_group("soco")
                if sprites:
                    local = (progress - APPROACH_FRAC) / STRIKE_FRAC
                    index = min(len(sprites) - 1, int(local * len(sprites)))
                    frame = sprites[index]
                else:
                    frame = self.asset_manager.get_fallback_sprite()
            else:
                sprites = self.asset_manager.get_player_sprite_group("soco")
                frame = sprites[0] if sprites else self.asset_manager.get_fallback_sprite()

            return x, frame

        sprites = self.asset_manager.get_player_sprite_group("idle")
        if self.player_flash > 0:
            damage = self.asset_manager.get_player_sprite_group("dano")
            if len(damage) == 8:
                return PLAYER_X, hurt_pose(damage, sprites, self.player_flash, interpolate)
        return PLAYER_X, self._player_idle_pose(sprites, interpolate)

    def _player_idle_pose(self, sprites, interpolate):
        if sprites:
            if interpolate and len(sprites) == 8:
                sprites = align_stance(tuple(sprites), sprites[0])
            return loop_pose(sprites, self.player_idle_timer, PLAYER_IDLE_FRAME_MS, interpolate)
        return self.asset_manager.get_fallback_sprite()

    def draw_player(self, surface, game_state):
        """Renderiza o jogador e seu efeito de impacto (flash)."""
        player_x, pose = self.get_player_frame(game_state, interpolate=True)
        player_frame, blend_flags = display_pose(pose)
        player_rect = player_frame.get_rect(midbottom=(int(player_x), PLAYER_GROUND_Y))
        hurt = self.player_flash if game_state != "victory" else 0
        if hurt and len(self.asset_manager.get_player_sprite_group("dano")) == 8:
            hurt = 0
        draw_recoiling_actor(surface, player_frame, player_rect, hurt, -1, blend_flags)
        ink = player_frame.get_bounding_rect(min_alpha=50).move(player_rect.topleft)
        self.player_ground_anchor = (ink.centerx, ink.bottom)

    def get_enemy_frame(self, enemy, *, interpolate=False):
        """Retorna o frame animado do inimigo com base em seu estado atual (atk, def, idle)."""
        enemy_name = getattr(enemy, "name", "").lower()

        if self.phase_transition_timer is not None and enemy_name == DUO_NAMES[0]:
            frames = self.asset_manager.get_enemy_sprite_group(enemy_name, 'transition')
            if frames:
                p = self.phase_transition_timer / TRANSITION_MS
                return sample_pose(frames, attack_frame(p, len(frames)), p,
                                   frame_boundaries(DUO_BOUNDARIES, len(frames)), interpolate)

        # 1. Ataque físico
        if self.attacker == "enemy":
            if self.enemy_ultimate:
                sprites = self.asset_manager.get_boss_ultimate_sprites(enemy_name)
                if sprites:
                    p = self.attack_timer/max(1, self.enemy_attack_duration)
                    if self.enemy_ultimate.mode == 'tremor':
                        index = tremor_frame(p, len(sprites))
                        return sample_pose(sprites, index, p, frame_boundaries(TREMOR_BOUNDARIES, len(sprites)),
                                           interpolate, cuts=(8,))
                    release = (self.enemy_ultimate.release if self.enemy_ultimate.mode in ('bear','plasma','sovereign')
                               else self.enemy_ultimate.impact)
                    index = (kit_frame(p,len(sprites),release) if len(sprites) in (8,12)
                             else boss_cast_frame(p,self.enemy_ultimate))
                    return sample_pose(sprites, min(index, len(sprites) - 1), p,
                                       action_boundaries(12, release), interpolate, cuts=(6,))
            preferred_group = self.enemy_action if self.enemy_action else "atk"
            sprites = self.asset_manager.get_enemy_sprite_group(enemy_name, preferred_group)
            attack_group = preferred_group
            if not sprites:
                attack_group = self.enemy_action if self.enemy_action in ("atk1", "atk2", "atk3", "atk4") else "atk"
                sprites = self.asset_manager.get_enemy_sprite_group(enemy_name, attack_group)
            if sprites:
                if enemy_name in DUO_NAMES:
                    accent = self.enemy_ranged_attack[1] if self.enemy_ranged_attack else MELEE_RETURN_FRACTION
                    p = recovery_progress(self.attack_timer, self.enemy_attack_duration, self.enemy_recovery_ms, accent)
                    cue = self.enemy_ranged_attack[1] if self.enemy_ranged_attack else self.enemy_impact_fraction
                    return sample_pose(sprites, attack_frame(p, len(sprites)), p,
                                       frame_boundaries(DUO_BOUNDARIES, len(sprites)), interpolate,
                                       cuts=(attack_frame(cue, len(sprites)),))
                if (enemy_name in KITS or enemy_name in COMMON_KITS) and len(sprites) in (8,12):
                    release = self.enemy_ranged_attack[1] if self.enemy_ranged_attack else self.enemy_impact_fraction
                    recovery_start = release if self.enemy_ranged_attack else MELEE_RETURN_FRACTION
                    p = recovery_progress(self.attack_timer, self.enemy_attack_duration,
                                          self.enemy_recovery_ms, recovery_start)
                    return sample_pose(sprites, kit_frame(p, len(sprites), release), p,
                                       action_boundaries(12, release), interpolate, cuts=(6,))
                if enemy_name in NORMAL_RANGED and attack_group in NORMAL_RANGED[enemy_name]:
                    progress = self.attack_timer / max(1, self.enemy_attack_duration)
                    index = 0 if progress < .22 else 1 if progress < .44 else 2 if progress < .80 else 3
                    return sprites[min(index, len(sprites) - 1)]
                if enemy_name == 'carrasco da vigília':
                    progress = self.attack_timer / max(1, self.enemy_attack_duration)
                    index = 0 if progress < 0.35 else 1 if progress < 0.49 else 2 if progress < 0.68 else 3
                    return sprites[min(index, len(sprites) - 1)]
                if enemy_name == 'guardião da pedra':
                    progress = self.attack_timer / max(1, self.enemy_attack_duration)
                    if attack_group == 'atk2':
                        if progress >= 0.92:
                            idle = self.asset_manager.get_enemy_sprite_group(enemy_name, 'idle')
                            return idle[0] if idle else sprites[-1]
                        index = 0 if progress < 0.20 else 1 if progress < 0.35 else 2 if progress < 0.50 else 3
                    else:
                        index = 0 if progress < 0.4 else 1 if progress < 0.49 else 2 if progress < 0.65 else 3
                    return sprites[min(index, len(sprites) - 1)]
                if enemy_name == "vinimuth":
                    progress = self.attack_timer / max(1, self.enemy_attack_duration)
                    if attack_group == "atk2":
                        # Carrega em três poses, lança e sustenta as mãos durante o voo.
                        if progress >= 0.87:
                            idle = self.asset_manager.get_enemy_sprite_group(enemy_name, "idle")
                            return idle[0] if idle else sprites[-1]
                        index = min(3, int(progress / 0.18))
                    else:
                        index = 0 if progress < 0.4 else 1 if progress < 0.49 else 2 if progress < 0.65 else 3
                    return sprites[min(index, len(sprites) - 1)]
                index = frame_index(attack_group, self.attack_timer,
                                    self.enemy_attack_duration, len(sprites))
                return sprites[index]

        # 2. Ação de defesa
        if self.enemy_action in ("def", "defesa", "healer2"):
            group = "healer2" if self.enemy_action == "healer2" else "def"
            sprites = self.asset_manager.get_enemy_sprite_group(enemy_name, group)
            if sprites:
                p = recovery_progress(self.enemy_action_timer, self.enemy_action_duration, self.enemy_recovery_ms, .50)
                index = frame_index(group, p, 1, len(sprites))
                return sample_pose(sprites, index, p, UNIFORM_TWELVE, interpolate)

        sprites = self.asset_manager.get_enemy_sprite_group(enemy_name, "idle")
        if self.enemy_flash > 0 and enemy_name in KITS:
            damage = self.asset_manager.get_enemy_sprite_group(enemy_name, "dano")
            if len(damage) == 8:
                return hurt_pose(damage, sprites, self.enemy_flash, interpolate)
        if sprites:
            now = self.enemy_idle_timer
            if (enemy_name in KITS or enemy_name in COMMON_KITS) and len(sprites) in (8,12):
                frame_ms = COMMON_IDLE_FRAME_MS
                if enemy_name in KITS:
                    frame_ms = BOSS_IDLE_FRAME_MS
                    if interpolate and len(sprites) == 8:
                        sprites = align_stance(tuple(sprites), sprites[0])
                return loop_pose(sprites, now, frame_ms, interpolate)
            if enemy_name in DUO_NAMES:
                sequence = (0, 1, 2, 3, 2, 1)
                return sprites[sequence[int(now // 260) % len(sequence)] % len(sprites)]
            if enemy_name in ('vinimuth', 'carrasco da vigília') or enemy_name in NORMAL_IDLE_NAMES:
                # Respiração lenta sobre uma pose estável: evita alternar
                # bruscamente braços e cabeça a cada 220 ms. Os pés mantêm o pivô.
                frame = sprites[0]
                breath = (1 - math.cos(now * math.tau / 2800)) / 2
                width, height = frame.get_size()
                return pygame.transform.smoothscale(frame, (width, height + round(2 * breath)))
            idle_ms = {"corpo seco": 800, "goblin nerd": 320, 'guardião da pedra': 400}.get(enemy_name, 360)
            index = int(now // idle_ms) % len(sprites)
            if enemy_name == 'guardião da pedra' and len(sprites) == 4:
                index = (0, 1, 2, 3, 2, 1)[int(now // idle_ms) % 6]
            return sprites[index]

        return None

    def draw_enemy(self, surface, enemy_or_color, maybe_color=None):
        """Calcula pose e renderiza o inimigo com sprite real ou fallback procedural."""
        if hasattr(enemy_or_color, "name"):
            enemy = enemy_or_color
            color = maybe_color or WHITE
        else:
            enemy = None
            color = enemy_or_color

        if enemy is not None and enemy.name.lower() == 'zanzara':
            from src.ui.zanzara_necromancer import available, draw
            if available():
                if getattr(enemy,'hp',1) <= 0:
                    # Não cair antes de o golpe do jogador chegar ao contato.
                    if self._zanzara_defeat_timer is None and self.pending_enemy_hit_at is None:
                        self._zanzara_defeat_timer = 0
                else:
                    self._zanzara_defeat_timer = None
                draw(surface, self)
                return

        enemy_target_x = PLAYER_X + APPROACH_GAP
        is_corpo = enemy is not None and enemy.name.lower() == "corpo seco"
        enemy_x, enemy_arm = self.get_attack_pose("enemy", ENEMY_X, enemy_target_x)

        # Se houver sprite para o inimigo, renderiza o sprite animado
        if enemy is not None and self.asset_manager.has_enemy_sprites(enemy.name):
            name = enemy.name.lower()
            light = BOSS_BODY_LIGHT.get(name, ARENA_ACTOR_LIGHT)
            frame, blend_flags = display_pose(self.get_enemy_frame(enemy, interpolate=True), light)
            if frame is not None:
                hover = 42 + round(4.5 * math.sin(pygame.time.get_ticks() / 300)) if enemy.name == 'Morcego Sombrio' else 0
                if self.enemy_ultimate:
                    _, hover = boss_ultimate_pose(self.enemy_ultimate, self.attack_timer/max(1, self.enemy_attack_duration), ENEMY_X, PLAYER_X+158)
                rect = frame.get_rect(midbottom=(int(enemy_x), PLAYER_GROUND_Y-hover))
                # Eco visual discreto acompanha o giro, sem piscar frames nem
                # trocar artificialmente a posição do personagem.
                if is_corpo and self.attacker == "enemy" and self.enemy_action == "atk4":
                    for opacity, offset in ((48, (27, -5)), (28, (-26, 5))):
                        trail = frame.copy()
                        if blend_flags:
                            trail.fill((opacity,) * 4, special_flags=pygame.BLEND_RGBA_MULT)
                        else:
                            trail.set_alpha(opacity)
                        surface.blit(trail, rect.move(offset), special_flags=blend_flags)
                hurt = self.enemy_flash if self.phase_transition_timer is None else 0
                if hurt and name in KITS and len(self.asset_manager.get_enemy_sprite_group(name, "dano")) == 8:
                    hurt = 0
                draw_recoiling_actor(surface, frame, rect, hurt, 1, blend_flags)
                return

        # Fallback procedural: boneco palito
        x = int(enemy_x)
        y = int(ENEMY_Y)
        facing = -1

        # Cabeça
        pygame.draw.circle(surface, color, (x, y - 69), 20, 6)

        # Corpo
        pygame.draw.line(surface, color, (x, y - 50), (x, y + 12), 6)

        # Pernas
        pygame.draw.line(surface, color, (x, y + 12), (x - 23, y + 60), 6)
        pygame.draw.line(surface, color, (x, y + 12), (x + 23, y + 60), 6)

        # Braço traseiro
        back_dx = -21 * facing
        pygame.draw.line(surface, color, (x, y - 27), (x + back_dx, y - 3), 6)

        # Braço dianteiro
        arm_length = 24 + 39 * enemy_arm
        front_dx = arm_length * facing
        front_dy = -27 + 15 * enemy_arm
        pygame.draw.line(surface, color, (x, y - 27), (x + front_dx, y + front_dy), 6)

        if enemy_arm > 0.15:
            pygame.draw.circle(surface, color, (int(x + front_dx), int(y + front_dy)), 9)

        # Efeito de flash de dano
        if self.enemy_flash > 0:
            alpha = self.enemy_flash / FLASH_DURATION
            pygame.draw.circle(
                surface,
                WHITE,
                (int(enemy_x), ENEMY_Y - 23),
                83 + int(12 * alpha),
                5,
            )
