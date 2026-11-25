"""O Mercado Silencioso: mercador ilustrado e ofertas persistidas na run."""
import pygame

from src.config.colors import WHITE, GOLD
from src.scenes.base_scene import BaseScene
from src.ui.management_guide import ManagementGuide
from src.systems.save_manager import player_max_hp
from src.systems.shop_system import (
    CARD_OFFERS, CARD_PRICES, HEAL_AMOUNT, HEAL_PRICES, HEAL_LIMIT,
    next_heal_price, purchase_card, purchase_heal,
)
from src.ui import dark_fantasy_theme as theme
from src.ui.helpers import draw_text
from src.ui.merchant_workshop_view import MerchantWorkshopView, text_in_rect, paragraph, MUTED, JADE
from src.ui.options_gear import draw_options_gear, options_gear_clicked


class ShopScene(BaseScene):
    """Cada compra usa as transações da loja e é persistida imediatamente."""
    PAGE_SIZE = 4

    def __init__(self, scene_manager, window_manager, asset_manager, save_manager, save_data):
        super().__init__(scene_manager, window_manager, asset_manager)
        self.save_manager, self.save_data = save_manager, save_data
        self.visuals = MerchantWorkshopView(asset_manager, "shop/market_background")
        self.heal_button = pygame.Rect(80, 842, 380, 62)
        self.back_button = pygame.Rect(1510, 986, 335, 60)
        self.workshop_button = pygame.Rect(75, 986, 410, 60)
        self.previous_page_rect = pygame.Rect(892, 986, 180, 60)
        self.next_page_rect = pygame.Rect(1234, 986, 180, 60)
        self.page = 0
        self._set_page(0)
        self.message, self.message_timer, self.message_positive = "", 0, True

        self.management_guide = ManagementGuide(self, "shop")

    def _set_page(self, page):
        self.page_count = max(1, (len(CARD_OFFERS) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self.page = max(0, min(page, self.page_count - 1))
        names = list(CARD_OFFERS)[self.page * self.PAGE_SIZE:(self.page + 1) * self.PAGE_SIZE]
        self.card_rects = {
            name: pygame.Rect(586 + i * 310, 326, 262, 387)
            for i, name in enumerate(names)}
        self.offer_rects = {
            name: pygame.Rect(rect.x - 6, 756, 274, 64)
            for name, rect in self.card_rects.items()}

    def update(self, dt):
        self.visuals.update(dt)
        self.message_timer = max(0, self.message_timer - dt)

    def _notify(self, result):
        self.message = result.message
        self.message_positive = result.success
        self.message_timer = 3600
        self.play_ui_sound("ui.confirm" if result.success else "ui.click")

    def _draw_heal(self, surface, mouse):
        p, a = self.save_data["progresso"], self.asset_manager
        self.visuals.panel(surface, (60, 640, 420, 291))
        draw_text(surface, "BÁLSAMO ANCESTRAL", a.menu_font, GOLD, 84, 667)
        maximum = player_max_hp(p)
        text_in_rect(surface, f"VIDA  {p['vida']} / {maximum}", a.small_font, JADE,
                     (84, 709, 370, 29))
        amount = max(0, min(HEAL_AMOUNT, maximum - p["vida"]))
        price = next_heal_price(p)
        text_in_rect(surface, f"Curas usadas  {p.get('curas_loja_run', 0)} / {HEAL_LIMIT}",
                     a.small_font, MUTED, (84, 748, 370, 28))
        text_in_rect(surface, " / ".join(map(str, HEAL_PRICES)) + " ouro", a.small_font,
                     MUTED, (84, 783, 370, 28))
        enabled = self._can_trade() and price is not None and amount > 0 and p["moedas"] >= price
        label = "ESGOTADO" if price is None else "VIDA CHEIA" if not amount else f"CURAR +{amount}"
        self.visuals.price_button(surface, self.heal_button, price or 0, label,
                                  self.heal_button.collidepoint(mouse), enabled)

    def _can_trade(self):
        p = self.save_data["progresso"]
        return p.get("estado", "ativa") == "ativa" and not p.get("combat_snapshot")

    def draw(self, surface):
        a, p = self.asset_manager, self.save_data["progresso"]
        mouse = self.window_manager.get_virtual_mouse_pos()
        self.visuals.backdrop(surface)
        draw_text(surface, "O MERCADO SILENCIOSO", a.big_font, WHITE, 72, 63)
        self.visuals.balance(surface, p["moedas"])
        draw_options_gear(surface, self.window_manager)
        self.visuals.panel(surface, (540, 194, 1320, 674))
        draw_text(surface, "OS TESOUROS DO MERCADOR", a.menu_font, GOLD, 579, 223)
        text_in_rect(surface, "Adquira um tipo e equipe as cópias na mochila.", a.small_font,
                     MUTED, (580, 269, 1215, 32))
        hovered_name = None
        for name, rect in self.card_rects.items():
            price, owned = CARD_PRICES[name], name in p["cartas_colecao"]
            card = CARD_OFFERS[name]
            hovered = self.visuals.framed_card_image_rect(card, rect).collidepoint(mouse)
            self.visuals.framed_card(surface, card, rect, hovered)
            enabled = not owned and p["moedas"] >= price and self._can_trade()
            label = "ADQUIRIDA" if owned else "COMPRAR" if enabled else "SEM OURO"
            if not owned and not self._can_trade():
                label = "INDISPONÍVEL"
            button = self.offer_rects[name]
            self.visuals.price_button(surface, button, price, label, button.collidepoint(mouse), enabled)
            if hovered:
                hovered_name = name
        self._draw_heal(surface, mouse)
        self.visuals.panel(surface, (60, 518, 420, 97))
        paragraph(surface, "Toda força tem seu preço.\nEscolha o que levar às ruínas.",
                  a.small_font, (226, 209, 168), (85, 540, 370, 70))
        for rect, label, enabled in (
            (self.workshop_button, "ALTAR DE APRIMORAMENTO", True),
            (self.back_button, "RETORNAR AO MAPA", True),
            (self.previous_page_rect, "ANTERIOR", self.page > 0),
            (self.next_page_rect, "PRÓXIMA", self.page + 1 < self.page_count),
        ):
            theme.button(surface, rect, label, a.small_font,
                         hover=rect.collidepoint(mouse) and enabled, enabled=enabled)
        draw_text(surface, f"{self.page + 1} / {self.page_count}", a.small_font, GOLD,
                  1152, 1016, center=True)
        if self.message_timer:
            self.visuals.message(surface, self.message, self.message_positive)
        if hovered_name:
            veil = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            veil.fill((0, 5, 3, 115))
            surface.blit(veil, (0, 0))
            self.visuals.panel(surface, (722, 170, 476, 678))
            self.visuals.card(surface, CARD_OFFERS[hovered_name], (748, 194, 424, 630))
        self.visuals.feedback(surface)
        self.management_guide.draw(surface)

    def handle_event(self, event):
        if self.window_manager.handle_window_event(event):
            return
        if getattr(self, 'management_guide', None) and self.management_guide.handle_event(event):
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.play_ui_sound("ui.click")
            self._back()
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        pos = self.window_manager.map_to_virtual(event.pos)
        if options_gear_clicked(pos):
            self.open_options_modal()
        elif self.workshop_button.collidepoint(pos):
            from src.scenes.roguelite_scene import RogueliteScene
            self.play_ui_sound("ui.click")
            self.scene_manager.change_scene(RogueliteScene(
                self.scene_manager, self.window_manager, self.asset_manager,
                self.save_manager, self.save_data))
        elif self.previous_page_rect.collidepoint(pos) and self.page > 0:
            self._set_page(self.page - 1)
            self.play_ui_sound("ui.click")
        elif self.next_page_rect.collidepoint(pos) and self.page + 1 < self.page_count:
            self._set_page(self.page + 1)
            self.play_ui_sound("ui.click")
        elif self.back_button.collidepoint(pos):
            self.play_ui_sound("ui.click")
            self._back()
        elif self.heal_button.collidepoint(pos):
            def complete(result):
                self._notify(result)
                if result.success:
                    self.visuals.celebrate(self.heal_button, healing=True)
            self.persist_command(lambda m,d: purchase_heal(m,d), complete)
        else:
            for name, rect in self.offer_rects.items():
                if rect.collidepoint(pos):
                    def complete(result):
                        self._notify(result)
                        if result.success:
                            self.visuals.celebrate(self.card_rects[name])
                    self.persist_command(lambda m,d: purchase_card(m,d,name), complete)
                    break

    def _back(self):
        if self.management_back():
            return
        from src.scenes.map_scene import MapScene
        self.scene_manager.change_scene(MapScene(
            self.scene_manager, self.window_manager, self.asset_manager,
            self.save_manager, self.save_data))
