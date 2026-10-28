"""Molduras da batalha com valores e retratos preenchidos em tempo real."""
import pygame

from src.config.colors import WHITE, GOLD
from src.ui.helpers import draw_text
from src.ui.status_badges import draw_status_badges


class BattleHUD:
    def __init__(self, assets):
        self.assets = assets
        self._scaled = {}
        self._portraits = {}

    def art(self, surface, key, rect):
        image = self.assets.get_ui_image(key)
        if image is None:
            return False
        cache_key = (key, rect.size)
        if cache_key not in self._scaled:
            self._scaled[cache_key] = pygame.transform.smoothscale(image, rect.size)
        surface.blit(self._scaled[cache_key], rect)
        return True

    def portrait(self, surface, rect, name, player=False):
        inner = pygame.Rect(rect.x + round(rect.width * 0.17),
                            rect.y + round(rect.height * 0.18),
                            round(rect.width * 0.66), round(rect.height * 0.64))
        pygame.draw.rect(surface, (9, 14, 15), inner)
        key = ('player' if player else name.lower(), inner.size)
        if key not in self._portraits:
            sprites = (self.assets.get_player_sprite_group('idle') if player
                       else self.assets.get_enemy_sprite_group(name, 'idle'))
            source = sprites[0] if sprites else self.assets.get_fallback_sprite()
            bounds = source.get_bounding_rect(min_alpha=40)
            if bounds.width and bounds.height:
                side = max(1, round(bounds.height * 0.48))
                head = pygame.Rect(bounds.centerx - side // 2, bounds.top, side, side)
                head = head.clip(source.get_rect())
                self._portraits[key] = pygame.transform.smoothscale(source.subsurface(head), inner.size)
        if key in self._portraits:
            surface.blit(self._portraits[key], inner)
        if not self.art(surface, 'hud_portrait', rect):
            pygame.draw.rect(surface, (153, 119, 65), rect, 3)

    def combatant(self, surface, rect, name, hp, maximum, stats, enemy=False, boss=False,
                  combatant=None, mouse=(0, 0)):
        portrait = pygame.Rect(rect.right - 88 if enemy else rect.left, rect.top, 88, 96)
        self.portrait(surface, portrait, name, player=not enemy)
        track = pygame.Rect(rect.left if enemy else portrait.right + 4, rect.top + 30,
                            rect.width - 96, 42)
        label = name + ('  ·  MINIBOSS' if boss else '')
        title = self.assets.menu_font
        if title.size(label)[0] > track.width:
            title = self.assets.small_font
        draw_text(surface, label, title, GOLD if boss else WHITE,
                  track.centerx, rect.top + 15, center=True)
        if not self.art(surface, 'hud_health', track):
            pygame.draw.rect(surface, (119, 92, 50), track, 2)
        bar = pygame.Rect(track.x + round(track.width * 0.18), track.y + round(track.height * 0.30),
                          round(track.width * 0.64), round(track.height * 0.34))
        pygame.draw.rect(surface, (29, 12, 13), bar)
        ratio = max(0, min(1, hp / max(1, maximum)))
        filled = bar.copy()
        filled.width = round(bar.width * ratio)
        if filled.width:
            pygame.draw.rect(surface, (137, 32, 30), filled)
            pygame.draw.line(surface, (203, 77, 52), filled.topleft,
                             (filled.right - 1, filled.top), 2)
            pygame.draw.line(surface, (72, 16, 20), filled.bottomleft,
                             (filled.right - 1, filled.bottom), 2)
        draw_text(surface, f'{hp}/{maximum}', self.assets.small_font, WHITE,
                  track.centerx, track.centery, center=True)
        if combatant is not None:
            draw_status_badges(surface, combatant, track.x + 10, rect.top + 76,
                               track.width, self.assets, mouse)
            return
        for i, (label, value, color) in enumerate(stats[:2]):
            draw_text(surface, f'{label}: {value}', self.assets.small_font, color,
                      track.x + 13 + i * 112, rect.top + 76)
