"""O Mercado Silencioso: cura da vida atual e compras temporárias da run."""

import pygame

from src.config.colors import WHITE, GOLD, GRAY
from src.config.settings import WIDTH, HEIGHT
from src.scenes.base_scene import BaseScene
from src.systems.save_manager import player_max_hp
from src.systems.shop_system import (
    CARD_OFFERS,
    CARD_PRICES,
    HEAL_AMOUNT,
    HEAL_PRICES,
    HEAL_LIMIT,
    next_heal_price,
    purchase_card,
    purchase_heal,
)
from src.ui.helpers import draw_text, wrap_text
from src.ui import dark_fantasy_theme as theme
from src.ui.card_view import CardView
from src.ui.options_gear import draw_options_gear, options_gear_clicked


TYPE_NAMES = {
    "attack": "ATAQUE",
    "skill": "HABILIDADE",
    "power": "PODER",
}

COLUMNS = (83, 677, 1271)
ROWS = (485, 723)
TILE_W, TILE_H = 561, 210


class ShopScene(BaseScene):
    """Loja vinculada ao save atual. Cada compra é persistida na hora."""

    def __init__(
        self,
        scene_manager,
        window_manager,
        asset_manager,
        save_manager,
        save_data,
    ):
        super().__init__(scene_manager, window_manager, asset_manager)

        self.save_manager = save_manager
        self.save_data = save_data

        self.heal_button = pygame.Rect(1398, 264, 384, 68)
        self.back_button = pygame.Rect(1418, 984, 413, 65)
        self.workshop_button = pygame.Rect(85, 975, 510, 65)

        self.offer_rects = {}
        self.page = 0

        self.previous_page_rect = pygame.Rect(630, 975, 135, 45)
        self.next_page_rect = pygame.Rect(1065, 975, 135, 45)

        self._set_page(0)

        self.message = ""
        self.message_timer = 0
        self.message_positive = True

    def _set_page(self, page):
        self.page_count = (len(CARD_OFFERS) + 5) // 6
        self.page = max(0, min(page, self.page_count - 1))

        names = list(CARD_OFFERS)[self.page * 6 : (self.page + 1) * 6]

        self.offer_rects = {}

        for i, name in enumerate(names):
            x, y = COLUMNS[i % 3], ROWS[i // 3]
            self.offer_rects[name] = pygame.Rect(x + 336, y + 147, 206, 47)

    def update(self, dt):
        if self.message_timer > 0:
            self.message_timer = max(0, self.message_timer - dt)

    def _notify(self, result):
        self.message = result.message
        self.message_positive = result.success
        self.message_timer = 3600
        self.play_ui_sound("ui.confirm" if result.success else "ui.click")

    def _draw_coins(self, surface):
        rect = pygame.Rect(1497, 63, 333, 75)
        theme.panel(surface, rect)

        if self.asset_manager.coin_icon is not None:
            icon = pygame.transform.smoothscale(self.asset_manager.coin_icon, (45, 45))
            surface.blit(icon, (1523, 78))

        draw_text(
            surface,
            str(self.save_data["progresso"]["moedas"]),
            self.asset_manager.menu_font,
            GOLD,
            1593,
            77,
        )

        draw_text(
            surface,
            "MOEDAS",
            self.asset_manager.small_font,
            GRAY,
            1697,
            90,
        )

    def _draw_heal(self, surface):
        p = self.save_data["progresso"]

        rect = pygame.Rect(83, 198, 1749, 191)
        theme.panel(surface, rect, highlighted=True)

        draw_text(
            surface,
            "RECUPERAR VIDA",
            self.asset_manager.menu_font,
            WHITE,
            rect.x + 39,
            rect.y + 23,
        )

        draw_text(
            surface,
            (
                f"Recupere até {HEAL_AMOUNT} de vida atual, sem ultrapassar o máximo."
            ),
            self.asset_manager.font,
            (199, 205, 188),
            rect.x + 39,
            rect.y + 77,
        )

        draw_text(
            surface,
            f"VIDA  {p['vida']}/{player_max_hp(p)}",
            self.asset_manager.small_font,
            (145, 194, 154),
            rect.x + 39,
            rect.y + 134,
        )

        draw_text(
            surface,
            f"CURAS NESTA RUN: {p.get('curas_loja_run', 0)}/{HEAL_LIMIT}  ·  "
            + ' / '.join(str(price) for price in HEAL_PRICES) + ' OURO',
            self.asset_manager.small_font,
            GOLD,
            rect.x + 417,
            rect.y + 134,
        )
        draw_text(surface, 'VIDA MÁXIMA: MELHORE COM FRAGMENTOS ENTRE RUNS',
                  self.asset_manager.small_font, GRAY, rect.x + 417, rect.y + 159)

        hovered = self.heal_button.collidepoint(
            self.window_manager.get_virtual_mouse_pos()
        )

        amount = min(HEAL_AMOUNT, player_max_hp(p) - p['vida'])
        price = next_heal_price(p)
        enabled = price is not None and amount > 0 and p["moedas"] >= price
        label = (
            'ESGOTADO NESTA RUN' if price is None else
            "VIDA CHEIA" if amount <= 0
            else f"CURAR +{amount}  ·  {price} OURO"
        )

        theme.button(
            surface,
            self.heal_button,
            label,
            self.asset_manager.small_font,
            hover=hovered,
            prominent=enabled,
            enabled=enabled,
        )

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

            factor = min(
                126 / max(1, size[0]),
                177 / max(1, size[1]),
            )

            thumb = pygame.transform.smoothscale(
                img,
                (
                    max(1, int(size[0] * factor)),
                    max(1, int(size[1] * factor)),
                ),
            )

            surface.blit(
                thumb,
                (
                    x + 18 + (126 - thumb.get_width()) // 2,
                    y + 15,
                ),
            )

        title_x = x + 165

        draw_text(
            surface,
            name.upper(),
            self.asset_manager.small_font,
            WHITE,
            title_x,
            y + 20,
        )

        draw_text(
            surface,
            (
                f"{TYPE_NAMES.get(card.card_type, card.card_type.upper())}"
                f" · {card.cost} ENERGIA"
            ),
            self.asset_manager.small_font,
            GOLD,
            title_x,
            y + 59,
        )

        lines = wrap_text(
            card.description,
            self.asset_manager.small_font,
            372,
        )[:2]

        for idx, line in enumerate(lines):
            draw_text(
                surface,
                line,
                self.asset_manager.small_font,
                (184, 191, 182),
                title_x,
                y + 95 + idx * 24,
            )

        draw_text(
            surface,
            f"{price} moedas",
            self.asset_manager.small_font,
            GOLD,
            title_x,
            y + 162,
        )

        button = self.offer_rects[name]

        hovered = button.collidepoint(self.window_manager.get_virtual_mouse_pos())

        owned = name in self.save_data["progresso"].get("cartas_colecao", [])

        theme.button(
            surface,
            button,
            "ADQUIRIDA" if owned else "COMPRAR",
            self.asset_manager.small_font,
            hover=hovered and not owned,
            enabled=not owned,
        )

    def draw(self, surface):
        theme.backdrop(
            surface,
            self.asset_manager.background,
            opacity=221,
        )

        theme.eyebrow(
            surface,
            "POSTO AVANÇADO  /  MERCADORIAS",
            self.asset_manager.small_font,
            90,
            54,
        )

        draw_text(
            surface,
            "O MERCADO SILENCIOSO",
            self.asset_manager.big_font,
            WHITE,
            90,
            98,
        )

        self._draw_coins(surface)
        theme.button(surface, self.workshop_button, 'MATERIAIS / EVOLUIR CÓPIAS',
                     self.asset_manager.small_font,
                     hover=self.workshop_button.collidepoint(self.window_manager.get_virtual_mouse_pos()))
        draw_options_gear(surface, self.window_manager)

        theme.divider(surface, 83, 1832, 168)

        self._draw_heal(surface)

        draw_text(
            surface,
            "CARTAS DISPONÍVEIS",
            self.asset_manager.menu_font,
            WHITE,
            87,
            420,
        )

        draw_text(
            surface,
            "Novos tipos vão para a coleção; adicione cópias na mochila (até 3).",
            self.asset_manager.small_font,
            GRAY,
            701,
            429,
        )

        for index, name in enumerate(self.offer_rects):
            self._draw_offer(surface, name, index)

        if self.message and self.message_timer > 0:
            color = (132, 205, 143) if self.message_positive else (228, 145, 129)

            draw_text(
                surface,
                self.message,
                self.asset_manager.small_font,
                color,
                90,
                948,
            )

        mouse = self.window_manager.get_virtual_mouse_pos()

        theme.button(
            surface,
            self.previous_page_rect,
            "ANTERIOR",
            self.asset_manager.small_font,
            hover=self.previous_page_rect.collidepoint(mouse),
            enabled=self.page > 0,
        )

        theme.button(
            surface,
            self.next_page_rect,
            "PRÓXIMA",
            self.asset_manager.small_font,
            hover=self.next_page_rect.collidepoint(mouse),
            enabled=self.page + 1 < self.page_count,
        )

        draw_text(
            surface,
            f"{self.page + 1} / {self.page_count}",
            self.asset_manager.small_font,
            GOLD,
            915,
            998,
            center=True,
        )

        hovered = self.back_button.collidepoint(
            self.window_manager.get_virtual_mouse_pos()
        )

        theme.button(
            surface,
            self.back_button,
            "RETORNAR AO MAPA",
            self.asset_manager.small_font,
            hover=hovered,
        )

        draw_text(
            surface,
            "ESC  ·  VOLTAR    |    F11  ·  TELA CHEIA",
            self.asset_manager.small_font,
            GRAY,
            WIDTH // 2,
            HEIGHT - 15,
            center=True,
        )

        for i, name in enumerate(self.offer_rects):
            rect = pygame.Rect(
                COLUMNS[i % 3],
                ROWS[i // 3],
                TILE_W,
                TILE_H,
            )

            if rect.collidepoint(mouse):
                CardView.draw_tooltip(
                    surface,
                    CARD_OFFERS[name],
                    self.asset_manager,
                    mouse,
                )
                break

    def handle_event(self, event):
        if self.window_manager.handle_window_event(event):
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if options_gear_clicked(self.window_manager.map_to_virtual(event.pos)):
                self.open_options_modal()
                return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.play_ui_sound("ui.click")
            self._back()
            return

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        pos = self.window_manager.map_to_virtual(event.pos)
        if self.workshop_button.collidepoint(pos):
            from src.scenes.roguelite_scene import RogueliteScene
            self.scene_manager.change_scene(RogueliteScene(self.scene_manager, self.window_manager,
                self.asset_manager, self.save_manager, self.save_data))
            return

        if self.previous_page_rect.collidepoint(pos):
            if self.page > 0:
                self._set_page(self.page - 1)
                self.play_ui_sound("ui.click")

        elif self.next_page_rect.collidepoint(pos):
            if self.page < self.page_count - 1:
                self._set_page(self.page + 1)
                self.play_ui_sound("ui.click")

        elif self.back_button.collidepoint(pos):
            self.play_ui_sound("ui.click")
            self._back()

        elif self.heal_button.collidepoint(pos):
            self._notify(
                purchase_heal(
                    self.save_manager,
                    self.save_data,
                )
            )

        else:
            for name, rect in self.offer_rects.items():
                if rect.collidepoint(pos):
                    self._notify(
                        purchase_card(
                            self.save_manager,
                            self.save_data,
                            name,
                        )
                    )
                    break

    def _back(self):
        from src.scenes.map_scene import MapScene

        self.scene_manager.change_scene(
            MapScene(
                self.scene_manager,
                self.window_manager,
                self.asset_manager,
                self.save_manager,
                self.save_data,
            )
        )
