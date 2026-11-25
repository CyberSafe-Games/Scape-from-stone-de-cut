"""Preparação entre runs e altar ilustrado de evolução de cópias."""
import re
import pygame

from src.scenes.base_scene import BaseScene
from src.ui.management_guide import ManagementGuide
from src.config.colors import WHITE, GOLD, GRAY
from src.ui import dark_fantasy_theme as theme
from src.ui.helpers import draw_text, wrap_text
from src.ui.merchant_workshop_view import MerchantWorkshopView, text_in_rect, paragraph, MUTED, JADE
from src.systems.roguelite import (
    PREPARATION, MATERIAL_PRICE, MATERIAL_LIMIT, UPGRADE_PRICES, UPGRADE_LIMIT,
    instance_card, purchase_material, upgrade_copy, purchase_permanent, transact,
)
from src.ui.options_gear import draw_options_gear, options_gear_clicked


def upgrade_changes(before, after):
    """Extrai valores e efeitos da descrição das instâncias reais LV1 e LV2."""
    changes = []
    if before.cost != after.cost:
        changes.append(f"Energia {before.cost} → {after.cost}")
    if before.value != after.value:
        noun = {"damage": "Dano", "shield": "Escudo", "heal": "Cura",
                "mask": "Cura", "darts": "Dano", "bleed": "Dano",
                "fire": "Dano", "energy": "Energia extra"}.get(before.effect.spec[5], "Valor")
        changes.append(f"{noun} {before.value} → {after.value}")
    old_shield = re.search(r"(\d+) de Escudo", before.description)
    new_shield = re.search(r"(\d+) de Escudo", after.description)
    if old_shield and new_shield and old_shield[1] != new_shield[1] and before.effect.spec[5] != "shield":
        changes.append(f"Escudo {old_shield[1]} → {new_shield[1]}")
    for phrase in after.description.split(". "):
        if phrase.startswith(("Receba também ", "Recupere 6 ")):
            changes.append(phrase)
    if not changes:
        changes.append("Mesmo efeito em LV2." if before.description == after.description
                       else after.description)
    return changes


class RogueliteScene(BaseScene):
    """O altar opera sobre a cópia escolhida, através das transações existentes."""
    PAGE_SIZE = 5

    def __init__(self, scene_manager, window_manager, asset_manager, save_manager, save_data,
                 preparation=False):
        super().__init__(scene_manager, window_manager, asset_manager)
        self.save_manager, self.save_data = save_manager, save_data
        self.preparation = preparation
        self.page = 0
        self.message = ""
        self.message_positive = True
        self.message_timer = 0
        self.buttons = []
        self.selected_copy_id = None
        self.visuals = MerchantWorkshopView(asset_manager, "workshop/altar_background")
        self.type_rects = {}
        self.copy_rects = {}
        self.material_button = pygame.Rect(558, 986, 375, 62)
        self.upgrade_button = pygame.Rect(1288, 986, 558, 62)
        self.back_button = pygame.Rect(72, 986, 400, 62)
        self.previous_page_rect = pygame.Rect(90, 870, 150, 58)
        self.next_page_rect = pygame.Rect(327, 870, 150, 58)
        self.after_rect = pygame.Rect(1430, 328, 310, 458)
        self._select_first()

        self.management_guide = None if preparation else ManagementGuide(self, "workshop")

    def _select_first(self):
        copies = self.save_data["progresso"]["copies"]
        if self.selected_copy_id not in {c["id"] for c in copies}:
            candidate = next((c for c in copies if c["level"] == 1), next(iter(copies), None))
            self.selected_copy_id = candidate["id"] if candidate else None

    def _selected_copy(self):
        return next((c for c in self.save_data["progresso"]["copies"]
                     if c["id"] == self.selected_copy_id), None)

    def update(self, dt):
        self.visuals.update(dt)
        self.message_timer = max(0, self.message_timer - dt)

    def _button(self, surface, rect, label, action, enabled=True):
        rect = pygame.Rect(rect)
        theme.button(surface, rect, label, self.asset_manager.small_font,
                     hover=enabled and rect.collidepoint(self.window_manager.get_virtual_mouse_pos()),
                     enabled=enabled)
        self.buttons.append((rect, action, enabled))

    def _notify(self, result):
        ok, self.message = result
        self.message_positive, self.message_timer = ok, 5000
        self.play_ui_sound("ui.confirm" if ok else "ui.click")
        return ok

    def _select_type(self, name):
        copies = [c for c in self.save_data["progresso"]["copies"] if c["name"] == name]
        candidate = next((c for c in copies if c["level"] == 1), next(iter(copies), None))
        self.selected_copy_id = candidate["id"] if candidate else None
        self.play_ui_sound("ui.click")

    def _purchase_material(self):
        selected = self._selected_copy()
        if selected:
            def complete(result):
                if self._notify(result):
                    self.visuals.celebrate(self.material_button)
            self.persist_command(lambda m,d:purchase_material(m,d,selected["name"]),complete)

    def _upgrade_selected(self):
        selected = self._selected_copy()
        if selected:
            def complete(result):
                if self._notify(result):
                    self.visuals.celebrate(self.after_rect)
            self.persist_command(lambda m,d:upgrade_copy(m,d,selected["id"]),complete)

    def draw(self, surface):
        self.buttons = []
        if self.preparation:
            self._draw_preparation(surface)
            return
        self._draw_workshop(surface)
        self.management_guide.draw(surface)

    def _draw_workshop(self, surface):
        self._select_first()
        a, p = self.asset_manager, self.save_data["progresso"]
        mouse = self.window_manager.get_virtual_mouse_pos()
        self.visuals.backdrop(surface)
        draw_text(surface, "O ALTAR ANCESTRAL", a.big_font, WHITE, 72, 63)
        self.visuals.balance(surface, p["moedas"])
        draw_options_gear(surface, self.window_manager)
        self.visuals.panel(surface, (60, 188, 438, 760))
        draw_text(surface, "SUAS CARTAS", a.menu_font, GOLD, 88, 217)
        names = [name for name in p["cartas_colecao"] if name in UPGRADE_PRICES]
        page_count = max(1, (len(names) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self.page = max(0, min(self.page, page_count - 1))
        selected = self._selected_copy()
        self.type_rects = {}
        for i, name in enumerate(names[self.page * self.PAGE_SIZE:(self.page + 1) * self.PAGE_SIZE]):
            rect = pygame.Rect(80, 274 + i * 113, 400, 100)
            self.type_rects[name] = rect
            active = selected is not None and selected["name"] == name
            self.visuals.panel(surface, rect, active or rect.collidepoint(mouse))
            card = next((c for c in p["copies"] if c["name"] == name), None)
            if card:
                self.visuals.card(surface, instance_card(card), (rect.x + 12, rect.y + 10, 55, 80))
            text_in_rect(surface, name, a.small_font, GOLD if active else WHITE,
                         (rect.x + 82, rect.y + 12, 300, 36))
            text_in_rect(surface, f"Materiais  {p['materials'].get(name, 0)} / {MATERIAL_LIMIT}",
                         a.small_font, MUTED, (rect.x + 82, rect.y + 54, 300, 30))
        self._button(surface, self.previous_page_rect, "ANTERIOR",
                     lambda: self._page(-1), self.page > 0)
        self._button(surface, self.next_page_rect, "PRÓXIMA",
                     lambda: self._page(1), self.page + 1 < page_count)
        draw_text(surface, f"{self.page + 1}/{page_count}", a.small_font, GOLD, 285, 900, center=True)
        self.visuals.panel(surface, (530, 188, 1325, 682))
        self.copy_rects = {}
        if selected:
            self._draw_comparison(surface, selected, mouse)
        else:
            paragraph(surface, "Adquira uma carta na loja para começar a aprimorar suas cópias.",
                      a.font, WHITE, (620, 440, 1070, 150))
        self._button(surface, self.back_button, "VOLTAR À LOJA", self._back)
        draw_text(surface, f"EVOLUÇÕES  {p['upgrades_purchased']} / {UPGRADE_LIMIT}",
                  a.small_font, GOLD, 1010, 1005)
        if self.message_timer:
            self.visuals.message(surface, self.message, self.message_positive)
        self.visuals.feedback(surface)

    def _draw_comparison(self, surface, selected, mouse):
        a, p = self.asset_manager, self.save_data["progresso"]
        name = selected["name"]
        copies = [c for c in p["copies"] if c["name"] == name]
        for i, copy in enumerate(copies):
            rect = pygame.Rect(562 + i * 422, 210, 394, 60)
            self.copy_rects[copy["id"]] = rect
            equipped = copy["id"] in p["copy_slots"]
            label = f"CÓPIA {i + 1} · LV{copy['level']} · " + ("EQUIPADA" if equipped else "LIVRE")
            theme.button(surface, rect, label, a.small_font,
                         hover=rect.collidepoint(mouse), prominent=copy["id"] == selected["id"])
        before = instance_card(dict(selected, level=1))
        after = instance_card(dict(selected, level=2))
        text_in_rect(surface, "ANTES · LV1", a.small_font, MUTED, (640, 282, 310, 34), True)
        text_in_rect(surface, "DEPOIS · LV2", a.small_font, GOLD, (1430, 282, 310, 34), True)
        before_rect = pygame.Rect(640, 328, 310, 458)
        self.visuals.framed_card(surface, before, before_rect)
        self.visuals.framed_card(surface, after, self.after_rect, selected["level"] == 1)
        self.visuals.rune_ring(surface, (1190, 590))
        draw_text(surface, "→", a.big_font, GOLD, 1190, 350, center=True)
        draw_text(surface, "APRIMORAMENTO", a.small_font, GOLD, 1190, 420, center=True)
        y = 466
        for change in upgrade_changes(before, after):
            paragraph(surface, change, a.small_font, JADE, (1004, y, 366, 200))
            y += len(wrap_text(change, a.small_font, 366)) * a.small_font.get_linesize() + 15
        text_in_rect(surface, "Cópia já aprimorada" if selected["level"] == 2 else "Evolui somente esta cópia",
                     a.small_font, MUTED, (1000, 784, 385, 52), True)
        active = p.get("estado") == "ativa" and not p.get("combat_snapshot")
        materials = p["materials"].get(name, 0)
        gold = p["moedas"]
        price = UPGRADE_PRICES[name]
        can_buy = active and materials < MATERIAL_LIMIT and gold >= MATERIAL_PRICE
        can_upgrade = (active and selected["level"] == 1 and materials >= 3
                       and gold >= price and p["upgrades_purchased"] < UPGRADE_LIMIT)
        self.visuals.price_button(surface, self.material_button, MATERIAL_PRICE,
                                  "MATERIAL +1", self.material_button.collidepoint(mouse), can_buy)
        label = "JÁ É LV2" if selected["level"] == 2 else "APRIMORAR · 3 MATERIAIS"
        self.visuals.price_button(surface, self.upgrade_button, price, label,
                                  self.upgrade_button.collidepoint(mouse), can_upgrade)
        self.buttons.extend(((self.material_button, self._purchase_material, can_buy),
                             (self.upgrade_button, self._upgrade_selected, can_upgrade)))
        reason = f"Reserva de {name}: {materials}/9. A evolução consome 3 materiais e {price} ouro."
        if selected["level"] == 2:
            reason = "Esta cópia atingiu LV2. Selecione outra cópia para continuar."
        elif p["upgrades_purchased"] >= UPGRADE_LIMIT:
            reason = "As três evoluções desta run já foram utilizadas."
        self.visuals.panel(surface, (530, 889, 1325, 68))
        paragraph(surface, reason, a.small_font, GOLD, (552, 900, 1278, 55))

    def _draw_preparation(self, surface):
        a, p = self.asset_manager, self.save_data["progresso"]
        profile = self.save_data["perfil"]
        theme.backdrop(surface, a.background, opacity=235)
        draw_text(surface, "PREPARAÇÃO DA PRÓXIMA RUN", a.big_font, WHITE, 80, 45)
        draw_text(surface, f"FRAGMENTOS PERMANENTES: {profile['fragmentos']}", a.font, GOLD, 80, 125)
        reason = "Você concluiu a campanha!" if p["estado"] == "concluida" else "A run terminou."
        draw_text(surface, reason + " Seu perfil foi preservado neste slot.", a.font, WHITE, 80, 185)
        rows = [("vida", f"Vida permanente: +{profile['vida'] * 5} (máximo +15)", (3, 5, 8)),
                ("energia", f"Energia inicial: {2 + profile['energia']} (máximo 3)", (12,)),
                ("preparacao", f"Opções de cartas iniciais: nível {profile['preparacao']}/2", (4, 6))]
        for i, (kind, label, prices) in enumerate(rows):
            y = 260 + i * 130
            draw_text(surface, label, a.menu_font, WHITE, 100, y)
            level = profile[kind]
            price = prices[level] if level < len(prices) else None
            self._button(surface, (1200, y - 5, 580, 65),
                         f"COMPRAR · {price} FRAGMENTOS" if price else "LIMITE ATINGIDO",
                         lambda k=kind: self.persist_command(lambda m,d:purchase_permanent(m,d,k),self._notify),
                         price is not None and profile["fragmentos"] >= price)
        draw_text(surface, "Escolha um tipo extra LV1 para a nova run (não ocupa espaço automaticamente).",
                  a.small_font, GRAY, 100, 660)
        choices = PREPARATION[:3 if profile["preparacao"] == 1 else 6] if profile["preparacao"] else ()
        for i, name in enumerate(choices):
            label = ("✓ " if profile.get("preparada") == name else "") + name
            self._button(surface, (100 + (i % 3) * 570, 710 + (i // 3) * 80, 540, 65), label,
                         lambda n=name: self._choose_preparation(n))
        self._button(surface, (1140, 930, 650, 70), "INICIAR NOVA RUN · VIDA CHEIA", self._new_run)
        self._button(surface, (80, 930, 400, 65), "VOLTAR AO MENU", self._back)
        text_in_rect(surface, self.message, a.small_font, GOLD, (80, 1020, 1740, 45))

    def _page(self, delta):
        self.page += delta
        self.play_ui_sound("ui.click")

    def _choose_preparation(self, name):
        def command(manager, data):
            def mutate():
                data["perfil"]["preparada"] = name
                return f"{name} preparada para a próxima run."
            return transact(manager,data,mutate)
        self.persist_command(command,self._notify)

    def _new_run(self):
        if getattr(self.save_manager,"async_commands",False) is True:
            def complete(result):
                if self._notify(result):
                    self.management_back()
            return self.persist_command(lambda m,d:m.new_run(d),complete)
        result = self.save_manager.new_run(self.save_data)
        self._notify(result)
        if result[0]:
            from src.scenes.map_scene import MapScene
            self.scene_manager.change_scene(MapScene(self.scene_manager, self.window_manager,
                self.asset_manager, self.save_manager, self.save_data))

    def _back(self):
        if self.management_back():
            return
        if self.preparation:
            from src.scenes.menu_scene import MenuScene
            scene = MenuScene(self.scene_manager, self.window_manager, self.asset_manager)
        else:
            from src.scenes.shop_scene import ShopScene
            scene = ShopScene(self.scene_manager, self.window_manager, self.asset_manager,
                              self.save_manager, self.save_data)
        self.scene_manager.change_scene(scene)

    def handle_event(self, event):
        if self.window_manager.handle_window_event(event):
            return
        if getattr(self, 'management_guide', None) and self.management_guide.handle_event(event):
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.play_ui_sound("ui.click")
            self._back()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            point = self.window_manager.map_to_virtual(event.pos)
            if not self.preparation and options_gear_clicked(point):
                self.open_options_modal()
                return
            for name, rect in self.type_rects.items():
                if rect.collidepoint(point):
                    self._select_type(name)
                    return
            for copy_id, rect in self.copy_rects.items():
                if rect.collidepoint(point):
                    self.selected_copy_id = copy_id
                    self.play_ui_sound("ui.click")
                    return
            for rect, action, enabled in self.buttons:
                if enabled and rect.collidepoint(point):
                    action()
                    break
