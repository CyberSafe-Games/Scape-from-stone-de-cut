"""Altar de espólios, prévia e confirmação de recompensas."""

import math
from collections import Counter

import pygame

from src.config.colors import GOLD, WHITE
from src.systems.card_catalog import CARD_BY_NAME
from src.systems.roguelite import FRAGMENTS, instance_card
from src.ui import dark_fantasy_theme as theme
from src.ui.merchant_workshop_view import (
    JADE, MUTED, MerchantWorkshopView, paragraph, text_in_rect,
)


class PostCombatRewardView(MerchantWorkshopView):
    CONFIRM_MS = 440
    PREVIEW = pygame.Rect(1200, 233, 554, 620)
    MATERIALS = pygame.Rect(166, 921, 480, 64)
    SKIP = pygame.Rect(685, 921, 433, 64)
    CONFIRM = pygame.Rect(1200, 921, 554, 64)

    def __init__(self, assets):
        super().__init__(assets, "rewards/victory_altar_background")
        self.show_materials = False
        self.selected = None
        self.pending = None
        self.remaining = 0

    @staticmethod
    def material_amount(engine):
        return 3 if engine.enemy.is_miniboss else 1

    def offers(self, engine, progress):
        if self.show_materials:
            for index, name in enumerate(progress["cartas_colecao"]):
                row, column = divmod(index, 3)
                yield ("material", name), pygame.Rect(166 + column * 338, 264 + row * 78, 315, 62)
        else:
            count = len(engine.reward_cards)
            start = 647 - (count * 300 + max(0, count - 1) * 38) // 2
            for index in range(count):
                yield ("card", index), pygame.Rect(start + index * 338, 298, 300, 464)

    def enabled(self, option, engine, progress):
        return (option[0] == "card" or
                progress["materials"].get(option[1], 0) + self.material_amount(engine) <= 9)

    def click(self, position, engine, progress):
        """Processa a seleção e retorna a ação que deve ser confirmada pela cena."""
        if self.pending:
            return None
        if progress is not None and not engine.is_replay and self.MATERIALS.collidepoint(position):
            self.show_materials = not self.show_materials
            self.selected = None
        elif self.SKIP.collidepoint(position):
            return ("skip", None)
        elif self.CONFIRM.collidepoint(position) and self.selected:
            return self.selected
        else:
            for option, rect in self.offers(engine, progress):
                if rect.collidepoint(position) and self.enabled(option, engine, progress):
                    self.selected = option
                    break
        return None

    def confirm(self, option):
        self.pending = option
        self.remaining = self.CONFIRM_MS

    def take_confirmation(self):
        result = self.pending
        self.pending = None
        return result

    def update(self, dt):
        super().update(dt)
        self.remaining = max(0, self.remaining - dt)
        if self.pending and not self.remaining:
            return self.take_confirmation()
        return None

    def draw(self, surface, engine, progress, gold, position):
        self.backdrop(surface)
        self._embers(surface)
        assets = self.assets
        text_in_rect(surface, "Espólios da vitória", assets.title_font, GOLD, (164, 39, 1080, 90))
        if gold:
            self._gold(surface, gold)
        if progress is not None and engine.enemy.is_miniboss and not engine.is_replay:
            amount = FRAGMENTS[engine.level - 1]
            self.panel(surface, (1255, 57, 245, 58))
            text_in_rect(surface, f"+{amount} fragmentos", assets.small_font, JADE,
                         (1265, 63, 225, 45), True)

        self.panel(surface, (166, 188, 275, 55))
        text_in_rect(surface, "Materiais" if self.show_materials else "Cartas novas",
                     assets.menu_font, GOLD, (182, 197, 245, 36))
        offers = list(self.offers(engine, progress))
        hovered = next((option for option, rect in offers if rect.collidepoint(position)), None)
        counts = Counter(copy["name"] for copy in progress["copies"]) if progress else Counter()
        for option, rect in offers:
            active = option == hovered or option == self.selected
            if option[0] == "card":
                self.framed_card(surface, engine.reward_cards[option[1]], rect, active)
                self.panel(surface, (rect.x + 29, rect.bottom + 31, rect.width - 58, 43), active)
                text_in_rect(surface, "CARTA NOVA", assets.small_font, GOLD,
                             (rect.x + 36, rect.bottom + 36, rect.width - 72, 33), True)
            else:
                self._material_tile(surface, rect, option, engine, progress, counts, active)
            if active:
                self._sparks(surface, rect, 10)
            if self.pending == option:
                self._sparks(surface, rect, 26, 1 - self.remaining / self.CONFIRM_MS)

        if not offers:
            message = ("Esta revanche não concede recompensas." if engine.is_replay else
                       "Não há cartas novas disponíveis neste encontro.")
            self.panel(surface, (166, 301, 956, 180))
            text_in_rect(surface, message, assets.font, WHITE, (196, 324, 896, 75), True)
        self._preview(surface, hovered or self.selected, engine, progress, counts)

        locked = self.pending is not None
        if progress is not None and not engine.is_replay:
            label = "Ver cartas novas" if self.show_materials else "Escolher materiais"
            theme.button(surface, self.MATERIALS, label, assets.font,
                         hover=self.MATERIALS.collidepoint(position), enabled=not locked)
        label = "Pular recompensa" if offers or (progress and not engine.is_replay) else "Continuar"
        theme.button(surface, self.SKIP, label, assets.font,
                     hover=self.SKIP.collidepoint(position), enabled=not locked)
        theme.button(surface, self.CONFIRM, "Confirmar escolha", assets.font,
                     hover=self.CONFIRM.collidepoint(position), prominent=True,
                     enabled=self.selected is not None and not locked)
        if self.pending and self.pending[0] == "skip":
            self._sparks(surface, self.SKIP, 14, 1 - self.remaining / self.CONFIRM_MS)

    def _material_tile(self, surface, rect, option, engine, progress, counts, active):
        name = option[1]
        reserve = progress["materials"].get(name, 0)
        enabled = self.enabled(option, engine, progress)
        self.panel(surface, rect, active and enabled)
        color = GOLD if active and enabled else WHITE if enabled else MUTED
        text_in_rect(surface, name, self.assets.small_font, color, rect.inflate(-20, -35))
        text_in_rect(surface, f"{counts[name]} cópias · {reserve}/9 materiais",
                     self.assets.small_font, JADE if enabled else MUTED,
                     (rect.x + 10, rect.y + 36, rect.width - 20, 20))

    def _preview(self, surface, option, engine, progress, counts):
        rect = self.PREVIEW
        self.panel(surface, rect, option is not None)
        if option is None:
            paragraph(surface, "Passe o mouse sobre uma oferta para ver os detalhes.",
                      self.assets.font, MUTED, rect.inflate(-52, -80))
            return
        if option[0] == "card":
            card = engine.reward_cards[option[1]]
            label = f"Carta nova · LV{card.level}"
        else:
            name = option[1]
            copies = [copy for copy in progress["copies"] if copy["name"] == name]
            card = (instance_card(max(copies, key=lambda copy: copy["level"]))
                    if copies else CARD_BY_NAME[name])
            label = (f"Material · +{self.material_amount(engine)} na reserva · LV{card.level}"
                     if self.enabled(option, engine, progress) else "Limite da reserva")
        text_in_rect(surface, label, self.assets.small_font, JADE if option[0] == "material" else GOLD,
                     (rect.x + 25, rect.y + 22, rect.width - 50, 26))
        text_in_rect(surface, card.name, self.assets.menu_font, WHITE,
                     (rect.x + 25, rect.y + 56, rect.width - 50, 51))
        self.framed_card(surface, card, pygame.Rect(rect.centerx - 100, rect.y + 137, 200, 304))
        theme.divider(surface, rect.x + 25, rect.right - 25, rect.y + 464)
        if option[0] == "material":
            reserve = progress["materials"].get(card.name, 0)
            text_in_rect(surface, f"{counts[card.name]} cópias no acervo · {reserve}/9 materiais",
                         self.assets.small_font, JADE, (rect.x + 25, rect.y + 477, rect.width - 50, 25))
            description_y = rect.y + 518
        else:
            description_y = rect.y + 488
        paragraph(surface, card.description, self.assets.small_font, WHITE,
                  pygame.Rect(rect.x + 28, description_y, rect.width - 56, rect.bottom - description_y))

    def _embers(self, surface):
        for index in range(42):
            phase = (self.elapsed / (2700 + (index % 9) * 160) + index * .173) % 1
            x = (64 + index * 283) % 1856 + math.sin(phase * math.tau + index) * 24
            y = 908 - phase * (350 + (index % 6) * 54)
            glow = math.sin(phase * math.pi)
            color = (round(112 + 129 * glow), round(61 + 102 * glow), 32)
            pygame.draw.circle(surface, color, (round(x), round(y)), 1 + index % 3)

    def _sparks(self, surface, rect, count, pulse=None):
        overlay = pygame.Surface((rect.width + 104, rect.height + 104), pygame.SRCALPHA)
        inner = pygame.Rect(52, 52, rect.width, rect.height)
        for index in range(count):
            phase = ((self.elapsed / 1350 + index / count) % 1) if pulse is None else pulse
            angle = index * 2.4
            x = inner.centerx + math.cos(angle) * (inner.width * .46 + phase * 45)
            y = inner.centery + math.sin(angle) * (inner.height * .46 + phase * 45)
            alpha = round(195 * (1 - phase))
            pygame.draw.circle(overlay, (*GOLD, alpha), (round(x), round(y)), 2 + index % 3)
        swell = round(30 * pulse) if pulse is not None else 4
        pygame.draw.rect(overlay, (*GOLD, 160 if pulse is None else round(210 * (1 - pulse))),
                         inner.inflate(swell * 2, swell * 2), 2, border_radius=11)
        if pulse is None:
            for x, y in (inner.topleft, inner.topright, inner.bottomleft, inner.bottomright):
                pygame.draw.polygon(overlay, (*JADE, 205),
                                    ((x, y - 8), (x + 5, y), (x, y + 8), (x - 5, y)), 2)
        surface.blit(overlay, (rect.x - 52, rect.y - 52))

    def _gold(self, surface, amount):
        rect = pygame.Rect(1521, 49, 233, 74)
        self.panel(surface, rect, True)
        if not hasattr(self, "_gold_icon"):
            source = self.assets.get_service_image("rewards/coin_pouch")
            bounds = source.get_bounding_rect(min_alpha=32) if source is not None else None
            if bounds:
                scale = min(65 / bounds.width, 68 / bounds.height)
                self._gold_icon = pygame.transform.smoothscale(
                    source.subsurface(bounds),
                    (round(bounds.width * scale), round(bounds.height * scale)),
                )
            else:
                self._gold_icon = self.assets.coin_icon
        icon = self._gold_icon
        if icon is not None:
            surface.blit(icon, icon.get_rect(center=(rect.x + 35, rect.centery)))
        text_in_rect(surface, f"+{amount} ouro", self.assets.font, GOLD,
                     (rect.x + 73, rect.y + 14, rect.width - 88, 46))
