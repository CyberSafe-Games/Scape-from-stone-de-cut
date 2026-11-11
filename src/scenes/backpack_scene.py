"""Preparação: seis tipos de cartas e uma ultimate independente do deck."""

import pygame
from src.config.colors import WHITE, GOLD, GRAY
from src.scenes.base_scene import BaseScene
from src.systems.deck_loadout import (
    SLOT_COUNT,
    COPIES_PER_SLOT,
    normalize_collection_and_slots,
    equip_card_type,
    equip_ultimate,
)
from src.systems.card_catalog import AVAILABLE_CARD_NAMES, CARD_POOL, CARD_BY_NAME
from src.models.effects.ultimate_effect import ULTIMATE_METADATA, DEFAULT_ULTIMATE_ID
from src.ui import dark_fantasy_theme as theme
from src.ui.helpers import draw_text, wrap_text


class BackpackScene(BaseScene):
    PAGE_SIZE = 6

    def __init__(
        self, scene_manager, window_manager, asset_manager, save_manager, save_data
    ):
        super().__init__(scene_manager, window_manager, asset_manager)
        self.save_manager, self.save_data = save_manager, save_data
        normalize_collection_and_slots(save_data["progresso"])
        self.tab, self.selected_slot, self.owned_only = "deck", 0, False
        self.selected_card = next(
            name for name in save_data["progresso"]["deck_slots"] if name
        )
        self.back_rect = pygame.Rect(1518, 65, 330, 65)
        self.deck_tab_rect = pygame.Rect(72, 177, 270, 59)
        self.ultimate_tab_rect = pygame.Rect(363, 177, 270, 59)
        self.clear_rect = pygame.Rect(72, 966, 429, 53)
        self.equip_rect = pygame.Rect(1419, 938, 402, 59)
        self.filter_rect = pygame.Rect(1185, 272, 150, 41)
        self.previous_page_rect = pygame.Rect(528, 966, 165, 53)
        self.next_page_rect = pygame.Rect(1194, 966, 165, 53)
        self.slots = [pygame.Rect(93, 335 + i * 96, 387, 89) for i in range(SLOT_COUNT)]
        self.ultimate_rects = {
            uid: pygame.Rect(72 + i * 603, 267, 558, 738)
            for i, uid in enumerate(ULTIMATE_METADATA)
        }
        self.ultimate_buttons = {
            uid: pygame.Rect(r.x + 33, 912, r.width - 66, 63)
            for uid, r in self.ultimate_rects.items()
        }
        self._thumbs = {}
        self._set_page(0)
        self.notice = (
            "Escolha um espaço, selecione uma carta e equipe no painel à direita."
        )
        self.notice_color = GRAY

    def _set_page(self, page):
        owned = self.save_data["progresso"]["cartas_colecao"]
        collection = [c for c in CARD_POOL if not self.owned_only or c.name in owned]
        self.page_count = max(
            1, (len(collection) + self.PAGE_SIZE - 1) // self.PAGE_SIZE
        )
        self.page = max(0, min(page, self.page_count - 1))
        visible = collection[
            self.page * self.PAGE_SIZE : (self.page + 1) * self.PAGE_SIZE
        ]
        self.cards = {
            c.name: pygame.Rect(566 + (i % 3) * 269, 324 + (i // 3) * 312, 188, 275)
            for i, c in enumerate(visible)
        }

    def update(self, dt):
        pass

    def _image(self, surface, name, rect, ultimate=False, dim=False):
        key = (name, rect.size, ultimate, dim)
        if key not in self._thumbs:
            source = (
                self.asset_manager.get_ultimate_image(name)
                if ultimate
                else self.asset_manager.get_card_image(name)
            )
            if source is None:
                return
            image = pygame.transform.smoothscale(source, rect.size)
            if dim:
                image.fill((100, 100, 100), special_flags=pygame.BLEND_RGB_MULT)
            self._thumbs[key] = image
        surface.blit(self._thumbs[key], rect)

    def _button(self, surface, rect, label, enabled=True, prominent=False):
        theme.button(
            surface,
            rect,
            label,
            self.asset_manager.small_font,
            hover=rect.collidepoint(self.window_manager.get_virtual_mouse_pos()),
            enabled=enabled,
            prominent=prominent,
        )

    def draw(self, surface):
        a, p = self.asset_manager, self.save_data["progresso"]
        theme.backdrop(surface, a.background, opacity=217)
        theme.eyebrow(surface, "PREPARAÇÃO / ARSENAL ANCESTRAL", a.small_font, 75, 36)
        draw_text(surface, "MOCHILA DO GUERREIRO", a.big_font, WHITE, 72, 72)
        draw_text(
            surface,
            "Prepare seu deck e escolha o poder que vai levar para a batalha.",
            a.small_font,
            GRAY,
            75,
            137,
        )
        self._button(surface, self.back_rect, "VOLTAR AO MAPA")
        self._button(
            surface, self.deck_tab_rect, "DECK E COLEÇÃO", prominent=self.tab == "deck"
        )
        self._button(
            surface,
            self.ultimate_tab_rect,
            "ULTIMATES",
            prominent=self.tab == "ultimates",
        )
        uid = p.get("ultimate_equipada", DEFAULT_ULTIMATE_ID)
        meta = ULTIMATE_METADATA[uid]
        label = "PODER EQUIPADO  ·  " + meta["name"].upper()
        draw_text(
            surface,
            label,
            a.small_font,
            meta["accent_color"],
            1839 - a.small_font.size(label)[0],
            195,
        )
        theme.divider(surface, 72, 1845, 249)
        if self.tab == "deck":
            self._draw_deck(surface)
        else:
            self._draw_ultimates(surface)
        draw_text(surface, self.notice, a.small_font, self.notice_color, 75, 1038)

    def _draw_deck(self, surface):
        a, p = self.asset_manager, self.save_data["progresso"]
        count = sum(n is not None for n in p["deck_slots"])
        theme.panel(surface, (72, 267, 429, 681))
        theme.panel(surface, (528, 267, 831, 681))
        theme.panel(surface, (1392, 267, 456, 752), highlighted=True)
        draw_text(
            surface,
            f"DECK  ·  {count}/6 TIPOS  ·  {count * COPIES_PER_SLOT} CARTAS",
            a.small_font,
            GOLD,
            99,
            290,
        )
        owned_count = len(AVAILABLE_CARD_NAMES.intersection(p["cartas_colecao"]))
        draw_text(
            surface,
            f"COLEÇÃO  ·  {owned_count}/{len(AVAILABLE_CARD_NAMES)}",
            a.small_font,
            GOLD,
            557,
            282,
        )
        self._button(
            surface, self.filter_rect, "OBTIDAS" if self.owned_only else "TODAS"
        )
        for i, rect in enumerate(self.slots):
            selected = i == self.selected_slot
            theme.panel(
                surface,
                rect,
                highlighted=selected,
                fill=(34, 37, 27, 245) if selected else (12, 21, 20, 230),
            )
            draw_text(
                surface,
                str(i + 1),
                a.small_font,
                GOLD if selected else GRAY,
                rect.x + 17,
                rect.y + 32,
            )
            name = p["deck_slots"][i]
            if name:
                self._image(surface, name, pygame.Rect(rect.x + 47, rect.y + 8, 51, 74))
                for row, text in enumerate(wrap_text(name, a.small_font, 219)):
                    draw_text(
                        surface,
                        text,
                        a.small_font,
                        WHITE,
                        rect.x + 116,
                        rect.y + 15 + row * 27,
                    )
                draw_text(
                    surface,
                    "×3",
                    a.small_font,
                    GOLD,
                    rect.right - 32,
                    rect.centery,
                    center=True,
                )
            else:
                draw_text(
                    surface,
                    "ESPAÇO VAZIO",
                    a.small_font,
                    GRAY,
                    rect.x + 57,
                    rect.y + 32,
                )
        for name, rect in self.cards.items():
            if name not in AVAILABLE_CARD_NAMES:
                theme.panel(surface, rect)
                for row, line in enumerate(wrap_text(name, a.small_font, rect.width - 20)):
                    draw_text(surface, line, a.small_font, WHITE,
                              rect.centerx, rect.y + 45 + row * 26, center=True)
                draw_text(surface, "Indisponível", a.small_font, GRAY,
                          rect.centerx, rect.bottom - 66, center=True)
                draw_text(surface, "no momento", a.small_font, GRAY,
                          rect.centerx, rect.bottom - 40, center=True)
                continue
            owned = name in p["cartas_colecao"]
            self._image(surface, name, rect, dim=not owned)
            if self.selected_card == name:
                pygame.draw.rect(
                    surface, (238, 198, 112), rect.inflate(9, 9), 3, border_radius=8
                )
            label = (
                "EM USO"
                if name in p["deck_slots"]
                else "DISPONÍVEL"
                if owned
                else "NA LOJA"
            )
            color = (
                GOLD if name in p["deck_slots"] else (137, 179, 150) if owned else GRAY
            )
            draw_text(
                surface,
                label,
                a.small_font,
                color,
                rect.centerx,
                rect.bottom + 18,
                center=True,
            )
        self._button(
            surface, self.clear_rect, "ESVAZIAR ESPAÇO " + str(self.selected_slot + 1)
        )
        self._button(
            surface, self.previous_page_rect, "ANTERIOR", enabled=self.page > 0
        )
        self._button(
            surface,
            self.next_page_rect,
            "PRÓXIMA",
            enabled=self.page + 1 < self.page_count,
        )
        draw_text(
            surface,
            f"PÁGINA {self.page + 1} / {self.page_count}",
            a.small_font,
            GRAY,
            944,
            993,
            center=True,
        )
        self._draw_detail(surface)

    def _draw_detail(self, surface):
        a, p = self.asset_manager, self.save_data["progresso"]
        card = CARD_BY_NAME.get(self.selected_card)
        draw_text(
            surface, "CARTA SELECIONADA", a.small_font, GOLD, 1620, 293, center=True
        )
        if card is None:
            return
        self._image(surface, card.name, pygame.Rect(1500, 323, 240, 353))
        kind = {"attack": "ATAQUE", "skill": "HABILIDADE", "power": "PODER"}[
            card.card_type
        ]
        draw_text(
            surface,
            f"{kind}  ·  {card.cost} DE ENERGIA",
            a.small_font,
            GOLD,
            1620,
            704,
            center=True,
        )
        for row, text in enumerate(wrap_text(card.description, a.small_font, 390)):
            draw_text(surface, text, a.small_font, WHITE, 1425, 723 + row * 27)
        owned = card.name in p["cartas_colecao"]
        duplicate = (
            card.name in p["deck_slots"]
            and p["deck_slots"][self.selected_slot] != card.name
        )
        label = (
            "ADQUIRA NA LOJA"
            if not owned
            else "JÁ ESTÁ EM OUTRO ESPAÇO"
            if duplicate
            else f"EQUIPAR NO ESPAÇO {self.selected_slot + 1}"
        )
        self._button(
            surface,
            self.equip_rect,
            label,
            enabled=owned and not duplicate,
            prominent=True,
        )

    def _draw_ultimates(self, surface):
        a, p = self.asset_manager, self.save_data["progresso"]
        for (uid, rect), role in zip(
            self.ultimate_rects.items(), ("RENOVAÇÃO", "FORTALECIMENTO", "RUPTURA")
        ):
            meta = ULTIMATE_METADATA[uid]
            equipped = p.get("ultimate_equipada", DEFAULT_ULTIMATE_ID) == uid
            theme.panel(
                surface,
                rect,
                highlighted=equipped,
                border=meta["accent_color"] if equipped else None,
            )
            draw_text(
                surface,
                role,
                a.small_font,
                meta["accent_color"],
                rect.centerx,
                299,
                center=True,
            )
            self._image(
                surface,
                uid,
                pygame.Rect(rect.centerx - 137, 330, 273, 401),
                ultimate=True,
            )
            draw_text(
                surface,
                f"{meta['charge_requirement']} DE CARGA  ·  CUSTO ZERO",
                a.small_font,
                GOLD,
                rect.centerx,
                761,
                center=True,
            )
            for row, text in enumerate(wrap_text(meta["description"], a.font, 483)):
                draw_text(surface, text, a.font, WHITE, rect.x + 38, 783 + row * 30)
            self._button(
                surface,
                self.ultimate_buttons[uid],
                "EQUIPADA" if equipped else "EQUIPAR ULTIMATE",
                enabled=not equipped,
                prominent=not equipped,
            )

    def handle_event(self, event):
        if self.window_manager.handle_window_event(event):
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.play_ui_sound("ui.click")
                self._back()
            elif event.key == pygame.K_TAB:
                self.tab = "ultimates" if self.tab == "deck" else "deck"
                self.play_ui_sound("ui.click")
            elif self.tab == "deck":
                if pygame.K_1 <= event.key <= pygame.K_6:
                    self.selected_slot = event.key - pygame.K_1
                    self.play_ui_sound("ui.click")

                elif event.key == pygame.K_LEFT:
                    if self.page > 0:
                        self._set_page(self.page - 1)
                        self.play_ui_sound("ui.click")

                elif event.key == pygame.K_RIGHT:
                    if self.page < self.page_count - 1:
                        self._set_page(self.page + 1)
                        self.play_ui_sound("ui.click")

                elif event.key == pygame.K_RETURN:
                    self._equip_selected()
            return

        if event.type == pygame.MOUSEWHEEL and self.tab == "deck":
            previous_page = self.page
            self._set_page(self.page - event.y)

            if self.page != previous_page:
                self.play_ui_sound("ui.click")

            return

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        point = self.window_manager.map_to_virtual(event.pos)
        if self.back_rect.collidepoint(point):
            self.play_ui_sound("ui.click")
            self._back()
        elif self.deck_tab_rect.collidepoint(point):
            if self.tab != "deck":
                self.tab = "deck"
                self.play_ui_sound("ui.click")
        elif self.ultimate_tab_rect.collidepoint(point):
            if self.tab != "ultimates":
                self.tab = "ultimates"
                self.play_ui_sound("ui.click")
                self.notice = (
                    "Escolha uma ultimate. A troca é salva e mantém sua carga atual."
                )

        elif self.tab == "ultimates":
            for uid, rect in self.ultimate_buttons.items():
                if rect.collidepoint(point) and uid != self.save_data["progresso"].get(
                    "ultimate_equipada"
                ):
                    success, message = equip_ultimate(
                        self.save_manager,
                        self.save_data,
                        uid,
                    )

                    self._notice(success, message)

                    if success:
                        self.play_ui_sound("ui.confirm")

                    break

        elif self.previous_page_rect.collidepoint(point):
            if self.page > 0:
                self._set_page(self.page - 1)
                self.play_ui_sound("ui.click")
        elif self.next_page_rect.collidepoint(point):
            if self.page < self.page_count - 1:
                self._set_page(self.page + 1)
                self.play_ui_sound("ui.click")
        elif self.filter_rect.collidepoint(point):
            self.owned_only = not self.owned_only
            self._set_page(0)
            self.play_ui_sound("ui.click")
        elif self.clear_rect.collidepoint(point):
            self._equip(None)
        elif self.equip_rect.collidepoint(point):
            self._equip_selected()
        else:
            for i, rect in enumerate(self.slots):
                if rect.collidepoint(point):
                    self.selected_slot = i
                    self.play_ui_sound("ui.click")
                    return
            for name, rect in self.cards.items():
                if rect.collidepoint(point):
                    if name not in AVAILABLE_CARD_NAMES:
                        self._notice(False, "Carta indisponível no momento.")
                        return
                    self.selected_card = name
                    self.play_ui_sound("ui.click")
                    return

    def _equip_selected(self):
        if self.selected_card in self.save_data["progresso"]["cartas_colecao"]:
            self._equip(self.selected_card)

    def _equip(self, name):
        success, message = equip_card_type(
            self.save_manager,
            self.save_data,
            self.selected_slot,
            name,
        )

        self._notice(success, message)

        if success:
            self.play_ui_sound("ui.confirm")

    def _notice(self, ok, message):
        self.notice, self.notice_color = (
            message,
            (139, 204, 149) if ok else (226, 135, 118),
        )

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
