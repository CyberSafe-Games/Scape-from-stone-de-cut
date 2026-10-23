"""O Mercado Silencioso: cura da RUN e compra de cartas existentes."""
import pygame

from src.config.colors import WHITE, GOLD, GRAY
from src.config.settings import WIDTH, HEIGHT
from src.scenes.base_scene import BaseScene
from src.systems.shop_system import (
    CARD_OFFERS, CARD_PRICES, HEAL_AMOUNT, HEAL_PRICE,
    HEAL_PURCHASE_LIMIT, MAX_PLAYER_HP, purchase_card, purchase_healing,
)
from src.ui.helpers import draw_text, wrap_text
from src.ui import dark_fantasy_theme as theme


TYPE_NAMES = {"attack": "ATAQUE", "skill": "HABILIDADE", "power": "PODER"}
COLUMNS = (55, 451, 847)
ROWS = (323, 482)
TILE_W, TILE_H = 374, 140


class ShopScene(BaseScene):
    """Loja vinculada ao save atual. Cada compra é persistida na hora."""

    def __init__(self, scene_manager, window_manager, asset_manager,
                 save_manager, save_data):
        super().__init__(scene_manager, window_manager, asset_manager)
        self.save_manager = save_manager
        self.save_data = save_data
        self.heal_button = pygame.Rect(932, 176, 256, 45)
        self.back_button = pygame.Rect(945, 656, 275, 43)
        self.offer_rects = {}
        names = list(CARD_OFFERS)
        for i, name in enumerate(names):
            x, y = COLUMNS[i % 3], ROWS[i // 3]
            self.offer_rects[name] = pygame.Rect(x + 224, y + 98, 137, 31)
        self.message = ""
        self.message_timer = 0
        self.message_positive = True

    def update(self, dt):
        if self.message_timer > 0:
            self.message_timer = max(0, self.message_timer - dt)

    def _notify(self, result):
        self.message = result.message
        self.message_positive = result.success
        self.message_timer = 3600

    def _draw_coins(self, surface):
        rect = pygame.Rect(998, 42, 222, 50)
        theme.panel(surface, rect)
        if self.asset_manager.coin_icon is not None:
            icon = pygame.transform.smoothscale(self.asset_manager.coin_icon, (30, 30))
            surface.blit(icon, (1015, 52))
        draw_text(surface, str(self.save_data["progresso"]["moedas"]),
                  self.asset_manager.menu_font, GOLD, 1062, 51)
        draw_text(surface, "MOEDAS", self.asset_manager.small_font, GRAY, 1131, 60)

    def _draw_healing(self, surface):
        p = self.save_data["progresso"]
        rect = pygame.Rect(55, 132, 1166, 127)
        theme.panel(surface, rect, highlighted=True)
        draw_text(surface, "RECUPERAÇÃO DE VIDA", self.asset_manager.menu_font,
                  WHITE, rect.x + 26, rect.y + 15)
        draw_text(surface, f"Recupere até {HEAL_AMOUNT} de vida, sem ultrapassar {MAX_PLAYER_HP} HP.",
                  self.asset_manager.font, (199, 205, 188), rect.x + 26, rect.y + 51)
        draw_text(surface, f"VIDA  {p['vida']}/{MAX_PLAYER_HP}", self.asset_manager.small_font,
                  (145, 194, 154), rect.x + 26, rect.y + 89)
        remaining = HEAL_PURCHASE_LIMIT - p["curas_compradas_run"]
        draw_text(surface, f"CURAS RESTANTES NESTA RUN  {remaining}/{HEAL_PURCHASE_LIMIT}",
                  self.asset_manager.small_font, GOLD, rect.x + 278, rect.y + 89)
        hovered = self.heal_button.collidepoint(self.window_manager.get_virtual_mouse_pos())
        enabled = remaining > 0 and p["vida"] < MAX_PLAYER_HP
        label = ("LIMITE ATINGIDO" if remaining <= 0 else
                 "VIDA COMPLETA" if p["vida"] >= MAX_PLAYER_HP else
                 f"CURAR +{HEAL_AMOUNT}  ·  {HEAL_PRICE} MOEDAS")
        theme.button(surface, self.heal_button, label, self.asset_manager.small_font,
                     hover=hovered, prominent=enabled, enabled=enabled)

    def _draw_offer(self, surface, name, index):
        card = CARD_OFFERS[name]
        price = CARD_PRICES[name]
        x, y = COLUMNS[index % 3], ROWS[index // 3]
        rect = pygame.Rect(x, y, TILE_W, TILE_H)
        theme.panel(surface, rect)
        img = self.asset_manager.get_card_image(name)
        if img is not None:
            # Mantém a proporção original e evita distorcer os sprites.
            size = img.get_size()
            factor = min(84 / max(1, size[0]), 118 / max(1, size[1]))
            thumb = pygame.transform.smoothscale(img, (max(1, int(size[0] * factor)),
                                                         max(1, int(size[1] * factor))))
            surface.blit(thumb, (x + 12 + (84 - thumb.get_width()) // 2, y + 10))
        title_x = x + 110
        draw_text(surface, name.upper(), self.asset_manager.small_font, WHITE, title_x, y + 13)
        draw_text(surface, TYPE_NAMES.get(card.card_type, card.card_type.upper()),
                  self.asset_manager.small_font, GOLD, title_x, y + 39)
        for idx, line in enumerate(wrap_text(card.description, self.asset_manager.small_font, 248)[:2]):
            draw_text(surface, line, self.asset_manager.small_font,
                      (184, 191, 182), title_x, y + 63 + idx * 16)
        draw_text(surface, f"{price} moedas", self.asset_manager.small_font, GOLD,
                  title_x, y + 108)
        button = self.offer_rects[name]
        hovered = button.collidepoint(self.window_manager.get_virtual_mouse_pos())
        owned = name in self.save_data["progresso"].get("cartas_colecao", [])
        theme.button(surface, button, "ADQUIRIDA" if owned else "COMPRAR",
                     self.asset_manager.small_font, hover=hovered and not owned,
                     enabled=not owned)

    def draw(self, surface):
        theme.backdrop(surface, self.asset_manager.background, opacity=221)
        theme.eyebrow(surface, "POSTO AVANÇADO  /  MERCADORIAS", self.asset_manager.small_font,
                      60, 36)
        draw_text(surface, "O MERCADO SILENCIOSO", self.asset_manager.big_font,
                  WHITE, 60, 65)
        self._draw_coins(surface)
        theme.divider(surface, 55, 1221, 112)
        self._draw_healing(surface)
        draw_text(surface, "CARTAS DISPONÍVEIS", self.asset_manager.menu_font,
                  WHITE, 58, 280)
        draw_text(surface, "Novos tipos vão para a coleção; equipe três cópias na mochila.",
                  self.asset_manager.small_font, GRAY, 467, 286)
        for index, name in enumerate(CARD_OFFERS):
            self._draw_offer(surface, name, index)
        if self.message and self.message_timer > 0:
            color = (132, 205, 143) if self.message_positive else (228, 145, 129)
            draw_text(surface, self.message, self.asset_manager.small_font,
                      color, 60, 662)
        hovered = self.back_button.collidepoint(self.window_manager.get_virtual_mouse_pos())
        theme.button(surface, self.back_button, "RETORNAR AO MAPA",
                     self.asset_manager.small_font, hover=hovered)
        theme.footer(surface, "ESC  ·  VOLTAR    |    F11  ·  TELA CHEIA", self.asset_manager.small_font)

    def handle_event(self, event):
        if self.window_manager.handle_window_event(event):
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        pos = self.window_manager.map_to_virtual(event.pos)
        if self.back_button.collidepoint(pos):
            self._back()
        elif self.heal_button.collidepoint(pos):
            self._notify(purchase_healing(self.save_manager, self.save_data))
        else:
            for name, rect in self.offer_rects.items():
                if rect.collidepoint(pos):
                    self._notify(purchase_card(self.save_manager, self.save_data, name))
                    break

    def _back(self):
        from src.scenes.map_scene import MapScene
        self.scene_manager.change_scene(MapScene(
            self.scene_manager, self.window_manager, self.asset_manager,
            self.save_manager, self.save_data,
        ))
