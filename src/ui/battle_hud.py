"""Molduras da batalha com valores e retratos preenchidos em tempo real."""
import pygame

from src.config.colors import WHITE, GOLD
from src.config.boss_names import boss_display_name
from src.ui.helpers import draw_text
from src.ui.frames import gold_outline, horizontal_frame
from src.ui.status_badges import draw_status_badges
from src.config.combat_header import HEALTH_FRAME_REFERENCE, HEALTH_WINDOW_POLYGON


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
            self._scaled[cache_key] = (horizontal_frame(image, rect.size) if key == 'hud_health'
                                       else pygame.transform.smoothscale(image, rect.size))
        surface.blit(self._scaled[cache_key], rect)
        return True

    def portrait(self, surface, rect, name, player=False):
        portrait_name = 'jaum manel' if player else name.strip().lower()
        portrait = self.assets.get_character_portrait(portrait_name, rect.size)
        if portrait is not None:
            self._portraits[(portrait_name, rect.size)] = portrait
            surface.blit(portrait, rect)
        else:
            # Ausência do asset é visível, sem ressuscitar a moldura antiga.
            pygame.draw.rect(surface, (9,14,15), rect)
            gold_outline(surface, rect)

    def combatant(self, surface, rect, name, hp, maximum, stats, enemy=False, boss=False,
                  combatant=None, mouse=(0, 0)):
        portrait = pygame.Rect(rect.right - 132 if enemy else rect.left, rect.top, 132, 144)
        self.portrait(surface, portrait, name, player=not enemy)
        track = pygame.Rect(rect.left if enemy else portrait.right + 6, rect.top + 45,
                            rect.width - 144, 63)
        display_name = boss_display_name(name) if enemy else name
        label = display_name + ('  ·  MINIBOSS' if boss else '')
        if getattr(combatant, 'is_final_boss', False):
            label = display_name + ' · BOSS FINAL'
        if getattr(combatant, 'total_phases', 0):
            label = f'{display_name} · {combatant.phase}/{combatant.total_phases}'
        title = self.assets.menu_font
        if title.size(label)[0] > track.width:
            title = self.assets.small_font
        heading = title.render(label, True, GOLD if boss else WHITE)
        if heading.get_width() > track.width:
            height = round(heading.get_height() * track.width / heading.get_width())
            heading = pygame.transform.smoothscale(heading, (track.width, height))
        surface.blit(heading, heading.get_rect(center=(track.centerx, rect.top + 23)))
        bar = self.health_bar(surface, track, hp, maximum)
        health_label = '∞' if getattr(combatant, 'invulnerable', False) else f'{hp}/{maximum}'
        draw_text(surface, health_label, self.assets.small_font, WHITE,
                  bar.centerx, bar.centery, center=True)
        if combatant is not None:
            draw_status_badges(surface, combatant, track.x + 15, rect.top + 114,
                               track.width, self.assets, mouse)
            return
        for i, (label, value, color) in enumerate(stats[:2]):
            draw_text(surface, f'{label}: {value}', self.assets.small_font, color,
                      track.x + 20 + i * 168, rect.top + 114)

    def health_window(self, size):
        """Máscara do canal interno, preservando as cabeças e a borda dourada."""
        key = ('health-window', tuple(size))
        if key not in self._scaled:
            source = self.assets.get_ui_image('hud_health')
            if isinstance(source, pygame.Surface):
                mask = pygame.Surface(source.get_size(), pygame.SRCALPHA)
                w,h = HEALTH_FRAME_REFERENCE
                points = [(round(x*source.get_width()/w),round(y*source.get_height()/h))
                          for x,y in HEALTH_WINDOW_POLYGON]
                pygame.draw.polygon(mask,(255,255,255,255),points)
                self._scaled[key] = horizontal_frame(mask, size)
            else:
                mask = pygame.Surface(size, pygame.SRCALPHA)
                pygame.draw.rect(mask,(255,255,255,255),mask.get_rect().inflate(-6,-6))
                self._scaled[key] = mask
        return self._scaled[key]

    def health_bar(self, surface, track, hp, maximum):
        """Preenche de 0 a 100% da abertura real; não usa insets percentuais."""
        track = pygame.Rect(track)
        if not self.art(surface,'hud_health',track):
            gold_outline(surface,track)
        mask = self.health_window(track.size)
        bounds = mask.get_bounding_rect(min_alpha=128)
        layer = pygame.Surface(track.size,pygame.SRCALPHA)
        layer.fill((29,12,13,255))
        fill = bounds.copy()
        fill.width = round(bounds.width*max(0,min(1,hp/max(1,maximum))))
        if fill.width:
            pygame.draw.rect(layer,(137,32,30,255),fill)
            pygame.draw.line(layer,(203,77,52,255),fill.topleft,(fill.right-1,fill.top),2)
            pygame.draw.line(layer,(72,16,20,255),(fill.left,fill.bottom-1),(fill.right-1,fill.bottom-1),2)
        layer.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(layer,track)
        return bounds.move(track.topleft)
