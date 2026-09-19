import pygame
from src.config.settings import HEIGHT
from src.config.colors import WHITE, BLACK, GOLD, GRAY
from src.ui.helpers import draw_text

HUD_ENERGY_X = 20
HUD_ENERGY_Y = HEIGHT - 114
HUD_ENERGY_W = 184
HUD_ENERGY_H = 94


class EnergyHUD:
    """Gerencia a exibição visual da energia atual, energia máxima e progressão até 8."""

    def __init__(self, player, x=HUD_ENERGY_X, y=HUD_ENERGY_Y):
        self.player = player
        self.x = x
        self.y = y
        self.pulse_timer = 0.0

    def update(self, dt):
        """Atualiza animações internas do HUD de energia."""
        self.pulse_timer = (self.pulse_timer + dt * 0.003) % (2 * 3.14159)

    def draw(self, surface, font, small_font=None):
        """Desenha o painel, orbe de energia, contagem atual/máxima e os 8 slots de progressão."""
        if small_font is None:
            small_font = font

        energy = self.player.energy
        energy_max = self.player.energy_max
        max_limit = getattr(self.player, "MAX_ENERGY_LIMIT", 8)

        # 1. Painel de fundo com borda estilizada e largura segura contra sobreposição
        panel = pygame.Surface((HUD_ENERGY_W, HUD_ENERGY_H), pygame.SRCALPHA)
        panel.fill((16, 14, 26, 210))
        border_color = (60, 160, 240, 190) if energy > 0 else (90, 90, 110, 140)
        pygame.draw.rect(
            panel,
            border_color,
            (0, 0, HUD_ENERGY_W, HUD_ENERGY_H),
            2,
            border_radius=12,
        )
        surface.blit(panel, (self.x, self.y))

        # 2. Orbe de Energia (Lado Esquerdo)
        orb_cx = self.x + 38
        orb_cy = self.y + HUD_ENERGY_H // 2
        orb_radius = 26

        # Halo suave do orbe
        glow_surf = pygame.Surface((orb_radius * 2 + 16, orb_radius * 2 + 16), pygame.SRCALPHA)
        glow_color = (40, 160, 255, 45) if energy > 0 else (60, 60, 80, 30)
        pygame.draw.circle(
            glow_surf,
            glow_color,
            (orb_radius + 8, orb_radius + 8),
            orb_radius + 5,
        )
        surface.blit(glow_surf, (orb_cx - orb_radius - 8, orb_cy - orb_radius - 8))

        # Círculo base e anel cristalino (sem manchas ou artefatos)
        orb_base_color = (18, 32, 54) if energy > 0 else (30, 30, 40)
        pygame.draw.circle(surface, orb_base_color, (orb_cx, orb_cy), orb_radius)
        orb_ring_color = (70, 190, 255) if energy > 0 else (80, 85, 100)
        pygame.draw.circle(surface, orb_ring_color, (orb_cx, orb_cy), orb_radius, 2)
        inner_ring_color = (35, 90, 145) if energy > 0 else (50, 55, 65)
        pygame.draw.circle(surface, inner_ring_color, (orb_cx, orb_cy), orb_radius - 3, 1)

        # Texto numérico limpo e centralizado no orbe (energia_atual / energia_máxima)
        ratio_text = f"{energy}/{energy_max}"
        tw, th = font.size(ratio_text)
        text_shadow = font.render(ratio_text, True, (10, 20, 35))
        surface.blit(text_shadow, (orb_cx - tw // 2 + 1, orb_cy - th // 2 + 1))
        text_surf = font.render(ratio_text, True, WHITE)
        surface.blit(text_surf, (orb_cx - tw // 2, orb_cy - th // 2))

        # 3. Informações de Texto e Título
        text_start_x = self.x + 74
        title_y = self.y + 12
        draw_text(surface, "ENERGIA", small_font, (160, 215, 255), text_start_x, title_y)

        # 4. Slots / Pips de Energia (8 slots demonstrando a progressão)
        pip_start_y = self.y + 36
        pip_w = 8
        pip_h = 16
        pip_spacing = 3

        for i in range(max_limit):
            px = text_start_x + i * (pip_w + pip_spacing)
            pip_rect = pygame.Rect(px, pip_start_y, pip_w, pip_h)

            if i < energy:
                # Energia disponível: aceso e vibrante
                pygame.draw.rect(surface, (45, 195, 255), pip_rect, border_radius=3)
                pygame.draw.rect(
                    surface,
                    (215, 245, 255),
                    (px + 1, pip_start_y + 1, pip_w - 2, pip_h // 3),
                    border_radius=2,
                )
                pygame.draw.rect(surface, (255, 255, 255), pip_rect, 1, border_radius=3)
            elif i < energy_max:
                # Energia gasta do turno: espaço desbloqueado, porém vazio
                pygame.draw.rect(surface, (25, 38, 55), pip_rect, border_radius=3)
                pygame.draw.rect(surface, (60, 130, 190), pip_rect, 1, border_radius=3)
            else:
                # Slot bloqueado: capacidade futura até o limite de 8
                pygame.draw.rect(surface, (20, 22, 30), pip_rect, border_radius=3)
                pygame.draw.rect(surface, (55, 60, 75), pip_rect, 1, border_radius=3)

        # 5. Legenda de limite contida com ampla margem interna de segurança
        subtext_y = self.y + 60
        if energy_max >= max_limit:
            draw_text(
                surface,
                f"Máx: {max_limit}",
                small_font,
                GOLD,
                text_start_x,
                subtext_y,
            )
        else:
            draw_text(
                surface,
                f"Limite: {max_limit}",
                small_font,
                (140, 160, 185),
                text_start_x,
                subtext_y,
            )
