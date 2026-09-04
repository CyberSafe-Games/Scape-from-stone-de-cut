import math
import random
import pygame

HUD_COIN_X = 14
HUD_COIN_Y = 50

# Tamanho do icone desenhado na HUD (px) - aumente aqui para deixar maior
HUD_ICON_SIZE = 42
# Largura do painel de fundo da HUD
HUD_PANEL_W = 160
HUD_PANEL_H = 50

PARTICLE_DURATION = 900
PARTICLE_STAGGER = 70
MAX_PARTICLES = 10
PARTICLE_RADIUS = 7
PARTICLE_COLOR = (255, 210, 50)
PARTICLE_OUTLINE = (0, 0, 0)


def _ease_in_out_cubic(t):
    if t < 0.5:
        return 4 * t * t * t
    p = 2 * t - 2
    return 1 - (p * p * p) / 2


class CoinParticle:
    """Uma moeda animada que voa da origem ate o icone da HUD."""

    def __init__(self, origin_x, origin_y, delay_ms, coin_value):
        self.origin_x = float(origin_x)
        self.origin_y = float(origin_y)
        self.dest_x = float(HUD_COIN_X + HUD_ICON_SIZE // 2)
        self.dest_y = float(HUD_COIN_Y + HUD_ICON_SIZE // 2)
        self.delay = delay_ms
        self.elapsed = 0.0
        self.coin_value = coin_value
        self.done = False
        self.credited = False

        mid_x = (self.origin_x + self.dest_x) / 2
        arc_offset = random.uniform(-120, 120)
        self.ctrl_x = mid_x + arc_offset
        self.ctrl_y = min(self.origin_y, self.dest_y) - random.uniform(60, 160)

        self.x = self.origin_x
        self.y = self.origin_y
        self.alpha = 255

    def update(self, dt):
        self.elapsed += dt
        if self.elapsed < self.delay:
            return False
        progress = (self.elapsed - self.delay) / PARTICLE_DURATION
        progress = min(progress, 1.0)
        t = _ease_in_out_cubic(progress)
        inv = 1.0 - t
        self.x = inv * inv * self.origin_x + 2 * inv * t * self.ctrl_x + t * t * self.dest_x
        self.y = inv * inv * self.origin_y + 2 * inv * t * self.ctrl_y + t * t * self.dest_y
        if progress > 0.8:
            fade = 1.0 - (progress - 0.8) / 0.2
            self.alpha = int(255 * fade)
        else:
            self.alpha = 255
        if progress >= 1.0:
            self.done = True
        return self.done

    def draw(self, surface):
        if self.elapsed < self.delay:
            return
        radius = PARTICLE_RADIUS
        size = radius * 2 + 4
        tmp = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2
        shadow_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(shadow_surf, (0, 0, 0, 80), (cx + 1, cy + 2), radius)
        tmp.blit(shadow_surf, (0, 0))
        pygame.draw.circle(tmp, (*PARTICLE_COLOR, self.alpha), (cx, cy), radius)
        pygame.draw.circle(tmp, (*PARTICLE_OUTLINE, self.alpha), (cx, cy), radius, 2)
        pygame.draw.circle(tmp, (255, 240, 150, min(self.alpha, 180)), (cx - 2, cy - 2), radius // 3)
        surface.blit(tmp, (int(self.x) - cx, int(self.y) - cy))


class CoinHUD:
    """Gerencia o saldo de moedas e as particulas de animacao de drop."""

    def __init__(self, player):
        self._player = player
        self._particles = []

    def spawn_coins(self, amount, origin_x, origin_y):
        """Cria particulas de moeda voando de (origin_x, origin_y) ate a HUD."""
        num_particles = min(max(amount // 5, 3), MAX_PARTICLES)
        base_value = amount // num_particles
        remainder = amount - base_value * num_particles
        for i in range(num_particles):
            value = base_value + (1 if i < remainder else 0)
            ox = origin_x + random.randint(-30, 30)
            oy = origin_y + random.randint(-20, 20)
            delay = i * PARTICLE_STAGGER
            self._particles.append(CoinParticle(ox, oy, delay, value))

    def update(self, dt):
        """Atualiza particulas e credita moedas ao chegar no destino."""
        alive = []
        for p in self._particles:
            p.update(dt)
            if p.done and not p.credited:
                self._player.add_coins(p.coin_value)
                p.credited = True
            if not p.done:
                alive.append(p)
            elif not p.credited:
                self._player.add_coins(p.coin_value)
                p.credited = True
        self._particles = alive

    def draw(self, surface, font, coin_icon):
        """Desenha particulas em voo e o HUD de moedas no canto superior esquerdo."""
        for p in self._particles:
            p.draw(surface)

        # Painel de fundo semi-transparente
        panel = pygame.Surface((HUD_PANEL_W, HUD_PANEL_H), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 140))
        pygame.draw.rect(panel, (255, 200, 50, 180), (0, 0, HUD_PANEL_W, HUD_PANEL_H), 2, border_radius=10)
        surface.blit(panel, (HUD_COIN_X - 4, HUD_COIN_Y - 4))

        # Icone da moeda
        if coin_icon:
            icon_scaled = pygame.transform.smoothscale(coin_icon, (HUD_ICON_SIZE, HUD_ICON_SIZE))
            surface.blit(icon_scaled, (HUD_COIN_X, HUD_COIN_Y + (HUD_PANEL_H - HUD_ICON_SIZE) // 2 - 4))

        # Texto do saldo ao lado do icone
        coins_text = font.render(f": {self._player.coins}", True, (255, 235, 110))
        text_y = HUD_COIN_Y + (HUD_PANEL_H - coins_text.get_height()) // 2 - 4
        surface.blit(coins_text, (HUD_COIN_X + HUD_ICON_SIZE + 6, text_y))
