"""Preparação: deck por espaços individuais e uma ultimate independente do deck."""

from collections import Counter

import pygame
from src.config.colors import WHITE, GOLD, GRAY
from src.config.layout import (
    BACKPACK_DECK_BUTTON_OFFSET_Y,
    BACKPACK_DECK_BUTTON_HEIGHT,
    BACKPACK_DECK_BUTTON_GAP,
    BACKPACK_DECK_BUTTON_INSET_X,
)
from src.scenes.base_scene import BaseScene
from src.systems.deck_loadout import (
    DECK_SLOT_LIMIT,
    DECK_MIN_CARDS,
    COPIES_PER_CARD,
    normalize_collection_and_slots,
    add_card_to_slots,
    remove_card_from_slots,
    empty_deck_slots,
    commit_deck,
    deck_copy_count,
    deck_is_ready_for_exit,
    equip_ultimate,
    random_deck_capacity,
    set_random_deck,
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
        # O deck oficial (último válido) permanece no save; a edição acontece
        # neste rascunho em memória e só é promovida quando atinge o mínimo.
        self.draft_slots = list(save_data["progresso"]["deck_slots"])
        self.tab, self.owned_only = "deck", False
        self.selected_card = next(
            (name for name in self.draft_slots if name),
            save_data["progresso"]["cartas_colecao"][0],
        )
        self.back_rect = pygame.Rect(1518, 65, 330, 65)
        self.deck_tab_rect = pygame.Rect(72, 177, 270, 59)
        self.ultimate_tab_rect = pygame.Rect(363, 177, 270, 59)
        self.add_rect = pygame.Rect(1419, 914, 402, 59)
        self.filter_rect = pygame.Rect(1192, 278, 150, 41)
        self.previous_page_rect = pygame.Rect(786, 966, 165, 53)
        self.next_page_rect = pygame.Rect(1181, 966, 165, 53)
        self.page_label_center = 1066
        self.slots = []
        cell_w, cell_h = 206, 88
        cols = 3
        rows = (DECK_SLOT_LIMIT + cols - 1) // cols
        grid_top = 345
        self.deck_panel = pygame.Rect(
            72, 267, 672, grid_top - 267 + rows * cell_h + (rows - 1) * 6 + 16
        )
        # Os botões ficam logo abaixo do painel, lado a lado e afastados do
        # rodapé. A altura dos slots já foi reduzida em 8 px para abrir espaço.
        button_width = (
            self.deck_panel.width
            - 2 * BACKPACK_DECK_BUTTON_INSET_X
            - BACKPACK_DECK_BUTTON_GAP
        ) // 2
        button_top = self.deck_panel.bottom + BACKPACK_DECK_BUTTON_OFFSET_Y
        self.clear_deck_rect = pygame.Rect(
            self.deck_panel.x + BACKPACK_DECK_BUTTON_INSET_X,
            button_top,
            button_width,
            BACKPACK_DECK_BUTTON_HEIGHT,
        )
        self.random_deck_rect = pygame.Rect(
            self.clear_deck_rect.right + BACKPACK_DECK_BUTTON_GAP,
            button_top,
            button_width,
            BACKPACK_DECK_BUTTON_HEIGHT,
        )
        for i in range(DECK_SLOT_LIMIT):
            col, row = i % cols, i // cols
            self.slots.append(
                pygame.Rect(
                    89 + col * (cell_w + 8),
                    grid_top + row * (cell_h + 6),
                    cell_w,
                    cell_h,
                )
            )
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
        if deck_is_ready_for_exit(self.draft_slots):
            self.notice = (
                "Clique em uma carta da coleção para adicionar 1 cópia; "
                "clique em um espaço preenchido para remover."
            )
            self.notice_color = GRAY
        else:
            self.notice = self._missing_cards_notice()
            self.notice_color = (226, 135, 118)

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
            c.name: pygame.Rect(786 + (i % 3) * 190, 330 + (i // 3) * 300, 176, 258)
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

    def _button(
        self, surface, rect, label, enabled=True, prominent=False, danger=False
    ):
        theme.button(
            surface,
            rect,
            label,
            self.asset_manager.small_font,
            hover=rect.collidepoint(self.window_manager.get_virtual_mouse_pos()),
            enabled=enabled,
            prominent=prominent,
            danger=danger,
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
        self._button(
            surface,
            self.back_rect,
            "VOLTAR AO MAPA",
            enabled=deck_is_ready_for_exit(self.draft_slots),
        )
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

    def _deck_counts(self):
        return Counter(name for name in self.draft_slots if name)

    def _draw_deck(self, surface):
        a, p = self.asset_manager, self.save_data["progresso"]
        counts = self._deck_counts()
        filled = sum(counts.values())
        minimum_met = deck_is_ready_for_exit(self.draft_slots)
        theme.panel(surface, self.deck_panel)
        theme.panel(surface, (768, 267, 592, 700))
        theme.panel(surface, (1392, 267, 456, 752), highlighted=True)
        counter = f"DECK  ·  {filled}/{DECK_SLOT_LIMIT}"
        if not minimum_met:
            counter += f"  ·  MÍN. {DECK_MIN_CARDS}"
        draw_text(
            surface,
            counter,
            a.small_font,
            GOLD if minimum_met else (226, 135, 118),
            99,
            282,
        )
        draw_text(
            surface,
            "Clique num espaço para remover a cópia."
            if minimum_met
            else f"Escolha pelo menos {DECK_MIN_CARDS} cartas para voltar ao mapa.",
            a.small_font,
            GRAY if minimum_met else (226, 135, 118),
            99,
            310,
        )
        owned_count = len(AVAILABLE_CARD_NAMES.intersection(p["cartas_colecao"]))
        draw_text(
            surface,
            f"COLEÇÃO  ·  {owned_count}/{len(AVAILABLE_CARD_NAMES)}",
            a.small_font,
            GOLD,
            786,
            282,
        )
        self._button(
            surface, self.filter_rect, "OBTIDAS" if self.owned_only else "TODAS"
        )
        mouse = self.window_manager.get_virtual_mouse_pos()
        for i, rect in enumerate(self.slots):
            name = self.draft_slots[i]
            hovered = rect.collidepoint(mouse)
            if name:
                theme.panel(
                    surface,
                    rect,
                    highlighted=hovered,
                    fill=(34, 37, 27, 245) if not hovered else (44, 48, 33, 245),
                )
                self._image(surface, name, pygame.Rect(rect.x + 8, rect.y + 4, 56, 80))
                lines = wrap_text(name, a.small_font, rect.width - 78)
                text_y = rect.y + rect.height // 2 - (len(lines) * 27) // 2
                for row, text in enumerate(lines):
                    draw_text(
                        surface,
                        text,
                        a.small_font,
                        WHITE,
                        rect.x + 78,
                        text_y + row * 27,
                    )
            else:
                theme.panel(
                    surface,
                    rect,
                    fill=(11, 19, 18, 215),
                    border=(46, 54, 49),
                )
                draw_text(
                    surface,
                    "VAZIO",
                    a.small_font,
                    GRAY,
                    rect.centerx,
                    rect.centery,
                    center=True,
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
            copies = counts.get(name, 0)
            maxed = copies >= COPIES_PER_CARD
            dim = not owned or maxed
            self._image(surface, name, rect, dim=dim)
            if self.selected_card == name:
                pygame.draw.rect(
                    surface, (238, 198, 112), rect.inflate(9, 9), 3, border_radius=8
                )
            if owned:
                badge = pygame.Rect(rect.right - 58, rect.y + 10, 48, 30)
                pygame.draw.rect(surface, (10, 14, 13), badge, border_radius=6)
                pygame.draw.rect(
                    surface,
                    (226, 135, 118) if maxed else GOLD,
                    badge,
                    2,
                    border_radius=6,
                )
                draw_text(
                    surface,
                    f"{copies}/{COPIES_PER_CARD}",
                    a.small_font,
                    (226, 135, 118) if maxed else GOLD,
                    badge.centerx,
                    badge.centery,
                    center=True,
                )
            if not owned:
                label, color = "NA LOJA", GRAY
            elif maxed:
                label, color = f"MÁXIMO {COPIES_PER_CARD}/{COPIES_PER_CARD}", (226, 135, 118)
            elif copies:
                label, color = f"{copies}/{COPIES_PER_CARD} NO DECK", (137, 179, 150)
            else:
                label, color = "DISPONÍVEL", (137, 179, 150)
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
            self.page_label_center,
            993,
            center=True,
        )
        self._button(
            surface,
            self.clear_deck_rect,
            "ESVAZIAR DECK",
            enabled=filled > 0,
            danger=True,
        )
        random_ready = self._random_deck_ready()
        self._button(
            surface,
            self.random_deck_rect,
            "DECK ALEATÓRIO",
            enabled=random_ready,
        )
        if not random_ready:
            draw_text(
                surface,
                f"Coleção insuficiente: mínimo de {DECK_MIN_CARDS} cópias.",
                a.small_font,
                GRAY,
                self.deck_panel.centerx,
                self.clear_deck_rect.bottom + 6,
                center=True,
            )
        self._draw_detail(surface, filled)

    def _draw_detail(self, surface, filled):
        a, p = self.asset_manager, self.save_data["progresso"]
        counts = self._deck_counts()
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
        available = card.name in AVAILABLE_CARD_NAMES
        copies = counts.get(card.name, 0)
        deck_full = filled >= DECK_SLOT_LIMIT
        maxed = copies >= COPIES_PER_CARD
        draw_text(
            surface,
            f"NO DECK  ·  {copies}/{COPIES_PER_CARD}",
            a.small_font,
            GOLD if not maxed else (226, 135, 118),
            1620,
            878,
            center=True,
        )
        if not available:
            label, enabled = "INDISPONÍVEL NO MOMENTO", False
        elif not owned:
            label, enabled = "ADQUIRA NA LOJA", False
        elif maxed:
            label, enabled = f"MÁXIMO DE {COPIES_PER_CARD} CÓPIAS", False
        elif deck_full:
            label, enabled = f"DECK CHEIO  ·  {DECK_SLOT_LIMIT}/{DECK_SLOT_LIMIT}", False
        else:
            label, enabled = f"ADICIONAR AO DECK  ·  {copies}/{COPIES_PER_CARD}", True
        self._button(
            surface,
            self.add_rect,
            label,
            enabled=enabled,
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
                if event.key == pygame.K_LEFT:
                    if self.page > 0:
                        self._set_page(self.page - 1)
                        self.play_ui_sound("ui.click")

                elif event.key == pygame.K_RIGHT:
                    if self.page < self.page_count - 1:
                        self._set_page(self.page + 1)
                        self.play_ui_sound("ui.click")

                elif event.key == pygame.K_RETURN:
                    self._add_selected()

                elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                    self._remove_last_filled_slot()
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

        elif self.clear_deck_rect.collidepoint(point):
            self._request_clear_deck()
        elif self.random_deck_rect.collidepoint(point):
            self._request_random_deck()
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
        elif self.add_rect.collidepoint(point):
            self._add_selected()
        else:
            slot_index = next(
                (i for i, rect in enumerate(self.slots) if rect.collidepoint(point)),
                None,
            )
            if slot_index is not None:
                self._remove_slot(slot_index)
                return
            for name, rect in self.cards.items():
                if rect.collidepoint(point):
                    if name not in AVAILABLE_CARD_NAMES:
                        self._notice(False, "Carta indisponível no momento.")
                        return
                    self.selected_card = name
                    self._add(name)
                    return

    def _add_selected(self):
        if self.selected_card in AVAILABLE_CARD_NAMES:
            self._add(self.selected_card)

    def _add(self, name):
        success, message, slots = add_card_to_slots(
            self.draft_slots,
            self.save_data["progresso"]["cartas_colecao"],
            name,
        )
        self.draft_slots = slots
        if success:
            saved, save_message = self._commit_draft_if_valid()
            if not saved:
                success, message = False, save_message
        self._notice(success, message)
        if success:
            self.play_ui_sound("ui.confirm")

    def _remove_slot(self, slot_index):
        success, message, slots = remove_card_from_slots(
            self.draft_slots, slot_index
        )
        self.draft_slots = slots
        if success:
            if deck_is_ready_for_exit(self.draft_slots):
                saved, save_message = commit_deck(
                    self.save_manager, self.save_data, self.draft_slots
                )
                if not saved:
                    success, message = False, save_message
            else:
                message = self._missing_cards_notice()
        self._notice(success, message)
        if success:
            self.play_ui_sound("ui.confirm")
        else:
            self.play_ui_sound("ui.click")

    def _remove_last_filled_slot(self):
        filled = [i for i, name in enumerate(self.draft_slots) if name]
        if not filled:
            self._notice(False, "O deck está vazio.")
            return
        self._remove_slot(filled[-1])

    def _commit_draft_if_valid(self):
        """Promove o rascunho quando ele já pode sair da Mochila."""
        if not deck_is_ready_for_exit(self.draft_slots):
            return True, ""
        return commit_deck(
            self.save_manager, self.save_data, self.draft_slots
        )

    def _request_clear_deck(self):
        if deck_copy_count(self.draft_slots) == 0:
            self._notice(False, "O deck já está vazio.")
            return
        self.play_ui_sound("ui.click")
        from src.scenes.confirmation_modal import ConfirmationModal

        self.scene_manager.push_modal(
            ConfirmationModal(
                self.scene_manager,
                self.window_manager,
                self.asset_manager,
                on_confirm=self._confirm_clear_deck,
                title="ESVAZIAR DECK?",
                message=(
                    f"O deck precisa de pelo menos {DECK_MIN_CARDS} cartas "
                    "para voltar ao mapa."
                ),
                confirm_label="SIM, ESVAZIAR",
            )
        )

    def _confirm_clear_deck(self):
        # O deck vazio é um rascunho: nunca sobrescreve o último deck válido.
        self.draft_slots = empty_deck_slots()
        self._notice(True, "Deck esvaziado.")

    def _random_deck_ready(self):
        collection = self.save_data["progresso"]["cartas_colecao"]
        return random_deck_capacity(collection) >= DECK_MIN_CARDS

    def _request_random_deck(self):
        if not self._random_deck_ready():
            self._notice(
                False,
                f"Coleção insuficiente: mínimo de {DECK_MIN_CARDS} cópias.",
            )
            return
        if deck_copy_count(self.draft_slots) == 0:
            self._apply_random_deck(play_sound=True)
            return
        self.play_ui_sound("ui.click")
        from src.scenes.confirmation_modal import ConfirmationModal

        self.scene_manager.push_modal(
            ConfirmationModal(
                self.scene_manager,
                self.window_manager,
                self.asset_manager,
                on_confirm=self._apply_random_deck,
                title="DECK ALEATÓRIO?",
                message="Substituir o deck atual por um deck aleatório?",
                confirm_label="SIM, SORTEAR",
            )
        )

    def _apply_random_deck(self, play_sound=False):
        success, message = set_random_deck(self.save_manager, self.save_data)
        if success:
            self.draft_slots = list(
                self.save_data["progresso"]["deck_slots"]
            )
        self._notice(success, message)
        if success and play_sound:
            self.play_ui_sound("ui.confirm")

    def _notice(self, ok, message):
        self.notice, self.notice_color = (
            message,
            (139, 204, 149) if ok else (226, 135, 118),
        )

    def _missing_cards_notice(self):
        missing = DECK_MIN_CARDS - deck_copy_count(self.draft_slots)
        return (
            f"Escolha pelo menos {DECK_MIN_CARDS} cartas para voltar ao mapa. "
            f"Faltam {missing}."
        )

    def _back(self):
        if not deck_is_ready_for_exit(self.draft_slots):
            self._notice(False, self._missing_cards_notice())
            return
        saved, message = commit_deck(
            self.save_manager, self.save_data, self.draft_slots
        )
        if not saved:
            self._notice(False, message)
            return
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

    def save_on_exit(self):
        """Grava o último deck válido; o rascunho inválido nunca é salvo.

        Se o rascunho já estiver válido, ele é promovido antes. Caso
        contrário, o deck oficial do save (o último válido) é preservado.
        Fechar a janela nunca falha: erros de gravação são apenas
        registrados no retorno, sem propagar exceção.
        """
        try:
            if deck_is_ready_for_exit(self.draft_slots):
                saved, _ = commit_deck(
                    self.save_manager, self.save_data, self.draft_slots
                )
                if saved:
                    return True
            self.save_manager.save(self.save_data)
        except Exception:
            return False
        return True
