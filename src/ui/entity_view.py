import math
import pygame

from src.config.colors import WHITE
from src.config.layout import (
    PLAYER_X,
    PLAYER_Y,
    ENEMY_X,
    ENEMY_Y,
    PLAYER_GROUND_Y,
    APPROACH_GAP,
    ATTACK_DURATION,
    APPROACH_FRAC,
    STRIKE_FRAC,
    FLASH_DURATION,
)
from src.ui.helpers import ease
from src.systems.animation_timing import animation_duration, frame_index, dash_distance
from src.systems.card_definitions import SPECS_BY_NAME
from src.ui.guardian_spirit_fx import draw_guardian_spirit
from src.ui.crimson_cast_fx import draw_crimson_cast


class EntityView:
    """Responsável por gerenciar os timers de animação, calcular poses de combate

    e renderizar o Jogador e o Inimigo na tela.
    """

    # duração, lançamento e impacto como frações da animação completa.
    GOBLIN_RANGED_ATTACKS = {"atk1": (1100, 0.30, 0.74), "atk2": (900, 0.30, 0.58)}
    RANGED_ATTACKS = {
        "goblin nerd": GOBLIN_RANGED_ATTACKS,
        "vinimuth": {"atk2": (1200, 0.54, 0.87)},
        'guardião da pedra': {'atk2': (1400, 0.50, 0.84)},
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

    def trigger_attack(self, attacker, action=None, enemy_name=None):
        self.attacker = attacker
        self.attack_timer = 0
        self.pending_player_hit_at = None
        self.enemy_ranged_attack = None
        self.enemy_attack_name = (enemy_name or "").strip().lower()
        if attacker == "player":
            self.player_action = action
            self.player_action_timer = 0
            spec = SPECS_BY_NAME.get(action)
            self.player_attack_duration = 1200 if spec and spec[6] == 'ranged' else 900 if spec else ATTACK_DURATION
            self.player_action_duration = self.player_attack_duration
            self.pending_enemy_hit_at = None
        elif attacker == "enemy":
            self.enemy_action = action
            self.enemy_attack_duration = animation_duration(action, ATTACK_DURATION)
            if self.enemy_attack_name == 'carrasco da vigília':
                self.enemy_attack_duration = {'atk1': 1050, 'atk2': 1150, 'atk3': 1500}.get(action, ATTACK_DURATION)
            self.enemy_ranged_attack = self.RANGED_ATTACKS.get(self.enemy_attack_name, {}).get(action)
            if self.enemy_ranged_attack:
                self.enemy_attack_duration = self.enemy_ranged_attack[0]
            self.enemy_action_timer = 0

    def trigger_enemy_action(self, action, enemy_name=None):
        if enemy_name is not None:
            self.enemy_attack_name = enemy_name.strip().lower()
        self.enemy_action = action
        self.enemy_action_duration = animation_duration(action, 600)
        if self.enemy_attack_name == 'carrasco da vigília' and action == 'healer2':
            self.enemy_action_duration = 1500
        self.enemy_action_timer = 0

    def trigger_flash(self, target):
        if target == "player":
            if self.attacker == "enemy":
                impact = self.enemy_ranged_attack[2] if self.enemy_ranged_attack else 0.49
                self.pending_player_hit_at = self.enemy_attack_duration * impact
            else:
                self.player_flash = FLASH_DURATION
        elif target == "enemy":
            if self.attacker == 'player' and self.player_action in SPECS_BY_NAME:
                fraction = 0.90 if SPECS_BY_NAME[self.player_action][6] == 'ranged' else 0.52
                self.pending_enemy_hit_at = self.player_attack_duration * fraction
            else:
                self.enemy_flash = FLASH_DURATION

    def trigger_player_action(self, action):
        self.player_action = action
        self.player_action_timer = 0
        self.player_action_duration = 1100 if action in SPECS_BY_NAME else 700

    def update(self, dt):
        """Atualiza todos os timers de animação visual."""
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
            duration = self.enemy_attack_duration if self.attacker == "enemy" else self.player_attack_duration
            if self.attack_timer >= duration:
                was_enemy = self.attacker == "enemy"
                self.attacker = None
                self.attack_timer = 0
                if was_enemy:
                    self.enemy_action = None
                    self.enemy_action_timer = 0
                    self.enemy_ranged_attack = None
                    self.pending_player_hit_at = None

        if self.enemy_action is not None and self.attacker != "enemy":
            self.enemy_action_timer += dt
            if self.enemy_action_timer >= self.enemy_action_duration:
                self.enemy_action = None
                self.enemy_action_timer = 0

        if self.player_action is not None:
            self.player_action_timer += dt
            if self.player_action_timer >= self.player_action_duration:
                self.player_action = None
                self.player_action_timer = 0

        self.post_enemy_pause = max(0, self.post_enemy_pause - dt)

    def is_enemy_resolving_done(self):
        # O segundo ataque só começa depois de terminar a animação do primeiro.
        return (self.attacker is None and self.enemy_action is None
                and self.post_enemy_pause <= 0)

    def get_attack_pose(self, attacker, home_x, target_x):
        """Calcula a posição interpolada X e extensão de braço para um ataque corpo-a-corpo."""
        if self.attacker != attacker:
            return home_x, 0.0
        if attacker == "enemy" and self.enemy_ranged_attack:
            return home_x, 0.0
        if attacker == 'player' and self.player_action in SPECS_BY_NAME and SPECS_BY_NAME[self.player_action][6] != 'melee':
            return home_x, 0.0

        duration = self.enemy_attack_duration if attacker == "enemy" else self.player_attack_duration
        progress = min(1.0, self.attack_timer / max(1, duration))

        # 1. Aproximação
        if progress < APPROACH_FRAC:
            local = ease(progress / APPROACH_FRAC)
            x = home_x + (target_x - home_x) * local
            return x, 0.0

        strike_end = APPROACH_FRAC + STRIKE_FRAC

        # 2. Golpe
        if progress < strike_end:
            local = (progress - APPROACH_FRAC) / STRIKE_FRAC
            arm_extend = math.sin(local * math.pi)
            return target_x, arm_extend

        # 3. Retorno
        local = (progress - strike_end) / (1 - APPROACH_FRAC - STRIKE_FRAC)
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
        start_x, end_x = ENEMY_X - 66, PLAYER_X + 12
        start_y = PLAYER_GROUND_Y - (78 if self.enemy_attack_name == "vinimuth" else 58)
        if self.enemy_attack_name == 'guardião da pedra':
            start_x = ENEMY_X - 135
            start_y = PLAYER_GROUND_Y - 95
        end_y = PLAYER_GROUND_Y - 65
        x = start_x + (end_x - start_x) * flight
        y = start_y + (end_y - start_y) * flight
        if self.enemy_action == "atk1":
            y -= 65 * math.sin(math.pi * flight)
        return x, y, flight

    def draw_enemy_projectile(self, surface):
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
        if self.enemy_attack_name in ('vinimuth', 'guardião da pedra'):
            wave = self.asset_manager.get_enemy_projectile(self.enemy_attack_name, self.enemy_action)
            if wave is not None:
                surface.blit(wave, wave.get_rect(center=(round(x), round(y))))
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
            tool = pygame.transform.rotate(self._screwdriver_sprite, flight * 720)
            surface.blit(tool, tool.get_rect(center=(round(x), round(y))))
        else:
            # Descarga azul, na mesma paleta da arma nos frames de atk2.
            glow = pygame.Surface((90, 40), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (35, 133, 255, 45), (0, 4, 87, 32))
            pygame.draw.ellipse(glow, (55, 170, 255, 95), (2, 10, 66, 20))
            pygame.draw.lines(glow, (63, 182, 255), False,
                              [(80, 20), (55, 14), (45, 23), (28, 13), (5, 20)], 5)
            pygame.draw.lines(glow, (215, 249, 255), False,
                              [(70, 20), (50, 18), (39, 23), (26, 17), (5, 20)], 2)
            pygame.draw.circle(glow, (235, 253, 255), (8, 20), 4)
            surface.blit(glow, (round(x) - 8, round(y) - 20))

    def get_player_frame(self, game_state):
        """Determina o sprite e a posição X exata do jogador com base no estado e nos timers."""
        now = pygame.time.get_ticks()

        # Vitória
        if game_state == "victory" and self.player_action is None and self.attacker != 'player':
            sprites = self.asset_manager.get_player_sprite_group("vitoria")
            if sprites:
                frame = sprites[(now // 300) % len(sprites)]
                return PLAYER_X, frame

        # Ação específica da carta
        if self.player_action is not None:
            sprites = self.asset_manager.get_card_action_sprites(self.player_action)
            if sprites:
                progress = min(
                    1.0, self.player_action_timer / self.player_action_duration
                )
                spec = SPECS_BY_NAME.get(self.player_action)
                if spec and spec[6] == 'melee':
                    index = 0 if progress < 0.4 else 1 if progress < 0.5 else 2 if progress < 0.68 else 3
                elif spec and spec[6] == 'ranged':
                    index = 0 if progress < 0.2 else 1 if progress < 0.4 else 2 if progress < 0.64 else 3
                else:
                    index = min(len(sprites) - 1, int(progress * len(sprites)))
                frame = sprites[min(len(sprites) - 1, index)]
            else:
                frame = self.asset_manager.get_player_sprite("idle", now // 120)

            if self.attacker == "player":
                x, _ = self.get_attack_pose("player", PLAYER_X, ENEMY_X - APPROACH_GAP)
                return x, frame
            return PLAYER_X, frame

        # Ataque
        if self.attacker == "player":
            target_x = ENEMY_X - APPROACH_GAP
            x, _ = self.get_attack_pose("player", PLAYER_X, target_x)
            progress = min(1.0, self.attack_timer / ATTACK_DURATION)

            if progress < APPROACH_FRAC:
                sprites = self.asset_manager.get_player_sprite_group("idle")
                frame = sprites[(now // 120) % len(sprites)] if sprites else self.asset_manager.get_fallback_sprite()
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

        # Dano sofrido
        if self.player_flash > 0:
            sprites = self.asset_manager.get_player_sprite_group("dano")
            if sprites:
                progress = 1 - (self.player_flash / FLASH_DURATION)
                index = min(len(sprites) - 1, int(progress * len(sprites)))
                return PLAYER_X, sprites[index]

        # Idle normal
        sprites = self.asset_manager.get_player_sprite_group("idle")
        if sprites:
            frame = sprites[(now // 400) % len(sprites)]
            return PLAYER_X, frame

        return PLAYER_X, self.asset_manager.get_fallback_sprite()

    def draw_player(self, surface, game_state):
        """Renderiza o jogador e seu efeito de impacto (flash)."""
        player_x, player_frame = self.get_player_frame(game_state)
        player_rect = player_frame.get_rect(midbottom=(int(player_x), PLAYER_GROUND_Y))
        surface.blit(player_frame, player_rect)

        if self.player_flash > 0:
            alpha = self.player_flash / FLASH_DURATION
            pygame.draw.circle(
                surface,
                WHITE,
                (int(player_x), PLAYER_Y - 15),
                70 + int(8 * alpha),
                3,
            )

    def get_enemy_frame(self, enemy):
        """Retorna o frame animado do inimigo com base em seu estado atual (atk, def, idle)."""
        now = pygame.time.get_ticks()
        enemy_name = getattr(enemy, "name", "").lower()

        # 1. Ataque físico
        if self.attacker == "enemy":
            preferred_group = self.enemy_action if self.enemy_action else "atk"
            sprites = self.asset_manager.get_enemy_sprite_group(enemy_name, preferred_group)
            attack_group = preferred_group
            if not sprites:
                attack_group = self.enemy_action if self.enemy_action in ("atk1", "atk2", "atk3", "atk4") else "atk"
                sprites = self.asset_manager.get_enemy_sprite_group(enemy_name, attack_group)
            if sprites:
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
                index = frame_index(group, self.enemy_action_timer,
                                    self.enemy_action_duration, len(sprites))
                return sprites[index]

        # 3. Reação de dano exclusiva quando o sprite fornece a animação.
        if self.enemy_flash > 0:
            sprites = self.asset_manager.get_enemy_sprite_group(enemy_name, "dano")
            if sprites:
                progress = max(0.0, min(0.999, 1 - self.enemy_flash / FLASH_DURATION))
                return sprites[int(progress * len(sprites))]

        sprites = self.asset_manager.get_enemy_sprite_group(enemy_name, "idle")
        if sprites:
            if enemy_name in ('vinimuth', 'carrasco da vigília'):
                # Respiração lenta sobre uma pose estável: evita alternar
                # bruscamente braços e cabeça a cada 220 ms. Os pés mantêm o pivô.
                frame = sprites[0]
                breath = (1 - math.cos(now * math.tau / 2800)) / 2
                width, height = frame.get_size()
                return pygame.transform.smoothscale(frame, (width, height + round(2 * breath)))
            idle_ms = {"corpo seco": 800, "goblin nerd": 320, 'guardião da pedra': 400}.get(enemy_name, 220)
            index = (now // idle_ms) % len(sprites)
            if enemy_name == 'guardião da pedra' and len(sprites) == 4:
                index = (0, 1, 2, 3, 2, 1)[(now // idle_ms) % 6]
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

        enemy_target_x = PLAYER_X + APPROACH_GAP
        is_corpo = enemy is not None and enemy.name.lower() == "corpo seco"
        if is_corpo and self.attacker == "enemy":
            distance = dash_distance(self.enemy_action, True)
            enemy_target_x = ENEMY_X - distance
        enemy_x, enemy_arm = self.get_attack_pose("enemy", ENEMY_X, enemy_target_x)

        # Se houver sprite para o inimigo, renderiza o sprite animado
        if enemy is not None and self.asset_manager.has_enemy_sprites(enemy.name):
            frame = self.get_enemy_frame(enemy)
            if frame is not None:
                rect = frame.get_rect(midbottom=(int(enemy_x), PLAYER_GROUND_Y))
                # Eco visual discreto acompanha o giro, sem piscar frames nem
                # trocar artificialmente a posição do personagem.
                if is_corpo and self.attacker == "enemy" and self.enemy_action == "atk4":
                    trail = frame.copy()
                    trail.set_alpha(48)
                    surface.blit(trail, rect.move(18, -3))
                    trail.set_alpha(28)
                    surface.blit(trail, rect.move(-17, 3))
                surface.blit(frame, rect)

                # Efeito de flash de dano
                if self.enemy_flash > 0:
                    alpha = self.enemy_flash / FLASH_DURATION
                    pygame.draw.circle(
                        surface,
                        WHITE,
                        (int(enemy_x), ENEMY_Y - 15),
                        55 + int(8 * alpha),
                        3,
                    )
                return

        # Fallback procedural: boneco palito
        x = int(enemy_x)
        y = int(ENEMY_Y)
        facing = -1

        # Cabeça
        pygame.draw.circle(surface, color, (x, y - 46), 13, 4)

        # Corpo
        pygame.draw.line(surface, color, (x, y - 33), (x, y + 8), 4)

        # Pernas
        pygame.draw.line(surface, color, (x, y + 8), (x - 15, y + 40), 4)
        pygame.draw.line(surface, color, (x, y + 8), (x + 15, y + 40), 4)

        # Braço traseiro
        back_dx = -14 * facing
        pygame.draw.line(surface, color, (x, y - 18), (x + back_dx, y - 2), 4)

        # Braço dianteiro
        arm_length = 16 + 26 * enemy_arm
        front_dx = arm_length * facing
        front_dy = -18 + 10 * enemy_arm
        pygame.draw.line(surface, color, (x, y - 18), (x + front_dx, y + front_dy), 4)

        if enemy_arm > 0.15:
            pygame.draw.circle(surface, color, (int(x + front_dx), int(y + front_dy)), 6)

        # Efeito de flash de dano
        if self.enemy_flash > 0:
            alpha = self.enemy_flash / FLASH_DURATION
            pygame.draw.circle(
                surface,
                WHITE,
                (int(enemy_x), ENEMY_Y - 15),
                55 + int(8 * alpha),
                3,
            )
