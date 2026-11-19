"""Composição ilustrada e feedback das telas do mercador e do altar."""
import math
import pygame

from src.config.colors import GOLD, WHITE
from src.config.settings import WIDTH, HEIGHT
from src.ui import dark_fantasy_theme as theme
from src.ui.helpers import draw_text, wrap_text

MUTED = (174, 174, 147)
JADE = (150, 212, 173)


def text_in_rect(surface, text, font, color, rect, centered=False):
    """Ajusta um rótulo de uma linha ao espaço sem mudar a fonte do jogo."""
    rect = pygame.Rect(rect)
    image = font.render(text, True, color)
    ratio = min(1, rect.width / max(1, image.get_width()),
                rect.height / max(1, image.get_height()))
    if ratio < 1:
        image = pygame.transform.smoothscale(
            image, (max(1, round(image.get_width() * ratio)),
                    max(1, round(image.get_height() * ratio))))
    target = image.get_rect(centery=rect.centery)
    target.centerx = rect.centerx if centered else rect.left + target.width // 2
    surface.blit(image, target)


def paragraph(surface, text, font, color, rect):
    rect = pygame.Rect(rect)
    lines = wrap_text(text, font, rect.width)
    for i, line in enumerate(lines):
        draw_text(surface, line, font, color, rect.x, rect.y + i * font.get_linesize())


class MerchantWorkshopView:
    """Cache por tela; imagens e partículas não participam dos eventos do mouse."""
    def __init__(self, assets, background):
        self.assets = assets
        self.background = background
        self.scaled = {}
        self.cards = {}
        self.elapsed = 0
        self.effect_age = 0
        self.effect_rect = None
        self.effect_color = GOLD

    def update(self, dt):
        self.elapsed += dt
        self.effect_age = max(0, self.effect_age - dt)

    def celebrate(self, rect, healing=False):
        self.effect_rect = pygame.Rect(rect)
        self.effect_color = JADE if healing else GOLD
        self.effect_age = 1400

    def image(self, name, size):
        key = (name, tuple(size))
        if key not in self.scaled:
            source = self.assets.get_service_image(name)
            self.scaled[key] = (
                pygame.transform.smoothscale(source, size)
                if source is not None else None)
        return self.scaled[key]

    def backdrop(self, surface):
        image = self.image(self.background, (WIDTH, HEIGHT))
        if image is None:
            theme.backdrop(surface, self.assets.background, opacity=165)
        else:
            surface.blit(image, (0, 0))
            veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(veil, (3, 8, 7, 180), (0, 0, WIDTH, 160))
            pygame.draw.rect(veil, (3, 8, 7, 210), (0, 964, WIDTH, 116))
            surface.blit(veil, (0, 0))
        theme.divider(surface, 60, WIDTH - 60, 148)

    def panel(self, surface, rect, selected=False):
        rect = pygame.Rect(rect)
        layer = pygame.Surface(rect.size, pygame.SRCALPHA)
        local = layer.get_rect()
        pygame.draw.rect(layer, (5, 13, 10, 205 if rect.height < 150 else 172),
                         local, border_radius=10)
        edge = GOLD if selected else (140, 111, 64)
        pygame.draw.rect(layer, (*edge, 235), local, 2, border_radius=10)
        pygame.draw.rect(layer, (89, 75, 48, 185), local.inflate(-14, -14), 1, border_radius=7)
        surface.blit(layer, rect.topleft)

    def frame(self, surface, rect):
        image = self.image("shop/offer_frame", pygame.Rect(rect).size)
        if image is not None:
            surface.blit(image, pygame.Rect(rect).topleft)

    def framed_card(self, surface, card, rect, selected=False):
        """Reserva uma margem real entre a arte da carta e o ornamento externo."""
        rect = pygame.Rect(rect)
        padding = max(12, round(rect.width * .055))
        inner = rect.inflate(-padding * 2, -padding * 2)
        self.card(surface, card, inner, selected)
        # Desenha o ornamento por último para manter todos os seus detalhes visíveis.
        self.frame(surface, rect.inflate(24, 28))

    def rune_ring(self, surface, center):
        image = self.image("workshop/rune_ring", (260, 260))
        if image is not None:
            rotated = pygame.transform.rotate(image, self.elapsed / 90 % 360)
            rotated.set_alpha(65)
            surface.blit(rotated, rotated.get_rect(center=center))

    def card(self, surface, card, rect, selected=False):
        """Enquadra a carta completa e compõe custo e regras do modelo atual."""
        rect = pygame.Rect(rect)
        key = (card.name, card.description, card.cost, getattr(card, "level", 1), rect.size)
        if key not in self.cards:
            image = self.assets.get_card_image(
                card.name, level=getattr(card, "level", 1),
                cost=card.cost, description=card.description)
            if image is not None:
                scale = min(rect.width / image.get_width(), rect.height / image.get_height())
                self.cards[key] = pygame.transform.smoothscale(
                    image, (round(image.get_width() * scale), round(image.get_height() * scale)))
            else:
                self.cards[key] = None
        image = self.cards[key]
        if selected:
            glow = pygame.Surface((rect.width + 32, rect.height + 32), pygame.SRCALPHA)
            alpha = round(70 + 25 * math.sin(self.elapsed / 250))
            for inset in range(3, 15, 3):
                pygame.draw.rect(glow, (*GOLD, alpha // inset * 3),
                                 glow.get_rect().inflate(-inset, -inset), 3, border_radius=12)
            surface.blit(glow, (rect.x - 16, rect.y - 16))
        if image is not None:
            surface.blit(image, image.get_rect(center=rect.center))
        else:
            self.panel(surface, rect)
            paragraph(surface, card.name + "\n" + card.description,
                      self.assets.small_font, WHITE, rect.inflate(-24, -24))

    def price_button(self, surface, rect, amount, label, hover=False, enabled=True):
        rect = pygame.Rect(rect)
        theme.button(surface, rect, "", self.assets.small_font,
                     hover=hover and enabled, prominent=enabled, enabled=enabled)
        icon = self.assets.coin_icon
        if icon is not None:
            icon = self.image_coin(icon)
            surface.blit(icon, (rect.x + 18, rect.centery - 15))
        text_in_rect(surface, f"{amount}  ·  {label}", self.assets.small_font,
                     GOLD if enabled else MUTED,
                     (rect.x + 54, rect.y + 9, rect.width - 70, rect.height - 18), True)

    def image_coin(self, icon):
        key = ("coin", (30, 30))
        if key not in self.scaled:
            self.scaled[key] = pygame.transform.smoothscale(icon, (30, 30))
        return self.scaled[key]

    def balance(self, surface, amount, rect=(1520, 50, 300, 66)):
        self.panel(surface, rect)
        icon = self.assets.coin_icon
        if icon is not None:
            surface.blit(self.image_coin(icon), (rect[0] + 20, rect[1] + 18))
        text_in_rect(surface, f"{amount} OURO", self.assets.menu_font, GOLD,
                     (rect[0] + 64, rect[1] + 10, rect[2] - 80, rect[3] - 20))

    def feedback(self, surface):
        if not self.effect_age or self.effect_rect is None:
            return
        progress = 1 - self.effect_age / 1400
        rect = self.effect_rect
        layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        alpha = round(160 * (1 - progress))
        pygame.draw.rect(layer, (*self.effect_color, alpha),
                         rect.inflate(round(progress * 36), round(progress * 36)), 4, border_radius=12)
        for i in range(22):
            phase = (progress + i / 22) % 1
            x = rect.centerx + math.sin(i * 2.4) * rect.width * .6
            y = rect.bottom - phase * (rect.height + 90)
            radius = 2 + i % 3
            pygame.draw.line(layer, (*self.effect_color, alpha), (x - radius, y), (x + radius, y), 2)
            pygame.draw.line(layer, (*self.effect_color, alpha), (x, y - radius), (x, y + radius), 2)
        surface.blit(layer, (0, 0))

    def message(self, surface, text, positive=True):
        if not text:
            return
        self.panel(surface, (520, 892, 1325, 66))
        text_in_rect(surface, text, self.assets.small_font,
                     JADE if positive else (238, 155, 133), (544, 906, 1277, 38))
