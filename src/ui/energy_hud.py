import math
import pygame
from src.config.settings import HEIGHT
from src.config.colors import WHITE, GOLD
from src.ui.helpers import draw_text, draw_panel

HUD_ENERGY_X = 30
HUD_ENERGY_Y = HEIGHT - 189
HUD_ENERGY_W = 321
HUD_ENERGY_H = 159


class EnergyHUD:
    """Gerencia a exibição visual da energia atual, energia máxima e progressão até 8."""

    def __init__(self, player, x=HUD_ENERGY_X, y=HUD_ENERGY_Y):
        self.player = player
        self.x = x
        self.y = y
        self.pulse_timer = 0.0

    def update(self, dt):
        """Atualiza animações internas do HUD de energia."""
        self.pulse_timer = (self.pulse_timer + dt * 0.0036) % (2 * math.pi)

    def draw(self, surface, font, small_font=None):
        """Desenha o painel, orbe de energia e os slots de progressão."""
        if small_font is None:
            small_font = font

        energy = self.player.energy
        energy_max = self.player.energy_max
        max_limit = getattr(self.player, "MAX_ENERGY_LIMIT", 8)

        draw_panel(surface, pygame.Rect(self.x, self.y, HUD_ENERGY_W, HUD_ENERGY_H),
                   fill=(14, 18, 28, 226), border=(58, 150, 210), radius=24)

        orb_cx = self.x + 63
        orb_cy = self.y + HUD_ENERGY_H // 2 + 6
        orb_radius = 42
        pulse = 3 if energy > 0 else 0
        if energy > 0:
            pulse += int((math.sin(self.pulse_timer) + 1) * 2.25)

        glow_size = (orb_radius + 21) * 2
        glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        glow_color = (50, 175, 255, 42 if energy > 0 else 18)
        pygame.draw.circle(glow, glow_color, (glow_size // 2, glow_size // 2), orb_radius + 15 + pulse)
        surface.blit(glow, (orb_cx - glow_size // 2, orb_cy - glow_size // 2))

        orb_base = (18, 40, 66) if energy > 0 else (29, 33, 42)
        ring = (90, 205, 255) if energy > 0 else (86, 93, 108)
        inner_ring = (150, 228, 255) if energy > 0 else (65, 70, 80)
        pygame.draw.circle(surface, orb_base, (orb_cx, orb_cy), orb_radius)
        pygame.draw.circle(surface, ring, (orb_cx, orb_cy), orb_radius, 5)
        pygame.draw.circle(surface, inner_ring, (orb_cx, orb_cy), orb_radius - 8, 2)
        pygame.draw.circle(surface, (255, 255, 255, 40), (orb_cx - 12, orb_cy - 14), 11)

        ratio_text = f"{energy}/{energy_max}"
        draw_text(surface, ratio_text, font, WHITE, orb_cx, orb_cy, center=True)

        text_start_x = self.x + 123
        draw_text(surface, "ENERGIA", small_font, (162, 219, 255), text_start_x, self.y + 21)
        draw_text(surface, "Canalize poder para jogar cartas", small_font,
                  (115, 137, 162), text_start_x, self.y + 51)

        pip_start_y = self.y + 90
        pip_w = 17
        pip_h = 27
        pip_spacing = 6

        for i in range(max_limit):
            px = text_start_x + i * (pip_w + pip_spacing)
            pip_rect = pygame.Rect(px, pip_start_y, pip_w, pip_h)
            if i < energy:
                pygame.draw.rect(surface, (40, 196, 255), pip_rect, border_radius=6)
                pygame.draw.rect(surface, (215, 248, 255), (px + 2, pip_start_y + 2, pip_w - 3, 8), border_radius=5)
                pygame.draw.rect(surface, (255, 255, 255), pip_rect, 2, border_radius=6)
            elif i < energy_max:
                pygame.draw.rect(surface, (21, 40, 59), pip_rect, border_radius=6)
                pygame.draw.rect(surface, (74, 130, 175), pip_rect, 2, border_radius=6)
            else:
                pygame.draw.rect(surface, (18, 22, 30), pip_rect, border_radius=6)
                pygame.draw.rect(surface, (56, 61, 74), pip_rect, 2, border_radius=6)

        limit_text = f"Máximo: {energy_max}/{max_limit}" if energy_max < max_limit else f"Máximo atingido: {max_limit}"
        draw_text(surface, limit_text, small_font,
                  GOLD if energy_max >= max_limit else (138, 152, 176),
                  text_start_x, self.y + 126)
