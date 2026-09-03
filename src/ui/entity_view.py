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


class EntityView:
    """Responsável por gerenciar os timers de animação, calcular poses de combate

    e renderizar o Jogador e o Inimigo na tela.
    """

    def __init__(self, asset_manager):
        self.asset_manager = asset_manager

        # Estados de animação
        self.attacker = None
        self.attack_timer = 0
        self.player_action = None
        self.player_action_timer = 0
        self.player_action_duration = 700

        self.player_flash = 0
        self.enemy_flash = 0
        self.post_enemy_pause = 0

    def trigger_attack(self, attacker, action=None):
        self.attacker = attacker
        self.attack_timer = 0
        if attacker == "player":
            self.player_action = action
            self.player_action_timer = 0

    def trigger_flash(self, target):
        if target == "player":
            self.player_flash = FLASH_DURATION
        elif target == "enemy":
            self.enemy_flash = FLASH_DURATION

    def trigger_player_action(self, action):
        self.player_action = action
        self.player_action_timer = 0

    def update(self, dt):
        """Atualiza todos os timers de animação visual."""
        if self.attacker is not None:
            self.attack_timer += dt
            if self.attack_timer >= ATTACK_DURATION:
                self.attacker = None
                self.attack_timer = 0

        if self.player_action is not None:
            self.player_action_timer += dt
            if self.player_action_timer >= self.player_action_duration:
                self.player_action = None
                self.player_action_timer = 0

        self.player_flash = max(0, self.player_flash - dt)
        self.enemy_flash = max(0, self.enemy_flash - dt)
        self.post_enemy_pause = max(0, self.post_enemy_pause - dt)

    def is_enemy_resolving_done(self):
        return self.attacker is None and self.post_enemy_pause <= 0

    def get_attack_pose(self, attacker, home_x, target_x):
        """Calcula a posição interpolada X e extensão de braço para um ataque corpo-a-corpo."""
        if self.attacker != attacker:
            return home_x, 0.0

        progress = min(1.0, self.attack_timer / ATTACK_DURATION)

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

    def get_player_frame(self, game_state):
        """Determina o sprite e a posição X exata do jogador com base no estado e nos timers."""
        now = pygame.time.get_ticks()

        # Vitória
        if game_state == "victory":
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
                frame = sprites[min(len(sprites) - 1, int(progress * len(sprites)))]
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

    def draw_enemy(self, surface, color):
        """Calcula pose e renderiza o inimigo com suas articulações e efeito de flash."""
        enemy_target_x = PLAYER_X + APPROACH_GAP
        enemy_x, enemy_arm = self.get_attack_pose("enemy", ENEMY_X, enemy_target_x)

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
