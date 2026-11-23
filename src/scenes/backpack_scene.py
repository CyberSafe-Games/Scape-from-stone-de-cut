"""Preparação: deck por espaços individuais e uma ultimate independente do deck."""

from collections import Counter
from copy import deepcopy
from src.systems.roguelite import normalize_inventory, instance_card
from src.ui.backpack_view import BackpackView

import pygame
from src.config.colors import WHITE, GRAY
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
from src.ui.helpers import draw_text
from src.ui.options_gear import draw_options_gear, options_gear_clicked


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
        self.visuals = BackpackView(asset_manager)
        self.type_filter = self.cost_filter = self.level_filter = None
        self.filter_buttons = {key: pygame.Rect(786+i*142, 330, 130, 42)
                               for i,key in enumerate(("owned", "type", "cost", "level"))}
        self.selected_card = next(
            (name for name in self.draft_slots if name),
            save_data["progresso"]["cartas_colecao"][0],
        )
        self.back_rect = pygame.Rect(1518, 65, 330, 65)
        self.deck_tab_rect = pygame.Rect(72, 177, 270, 59)
        self.ultimate_tab_rect = pygame.Rect(363, 177, 270, 59)
        self.add_rect = pygame.Rect(1419, 914, 402, 59)
        self.filter_rect = self.filter_buttons["owned"]
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
        draft = self._inventory_preview()
        collection = []
        for base in CARD_POOL:
            if self.owned_only and base.name not in owned:
                continue
            card = self._collection_card(base.name, draft)
            if self.type_filter is not None and card.card_type != self.type_filter:
                continue
            if self.cost_filter is not None and card.cost != self.cost_filter:
                continue
            if self.level_filter is not None and getattr(card, "level", 1) != self.level_filter:
                continue
            collection.append(base)
        if (self.type_filter is not None or self.cost_filter is not None
                or self.level_filter is not None or self.owned_only):
            if self.selected_card not in {c.name for c in collection}:
                self.selected_card = collection[0].name if collection else None
        self.filtered_count = len(collection)
        self.page_count = max(
            1, (len(collection) + self.PAGE_SIZE - 1) // self.PAGE_SIZE
        )
        self.page = max(0, min(page, self.page_count - 1))
        visible = collection[
            self.page * self.PAGE_SIZE : (self.page + 1) * self.PAGE_SIZE
        ]
        self.cards = {
            c.name: pygame.Rect(797 + (i % 3) * 187, 402 + (i // 3) * 278, 160, 226)
            for i, c in enumerate(visible)
        }

    def _inventory_preview(self):
        draft = deepcopy(self.save_data["progresso"])
        draft["deck_slots"] = list(self.draft_slots)
        normalize_inventory(draft)
        return draft

    def _collection_card(self, name, draft=None):
        base = CARD_BY_NAME.get(name)
        if base is None:
            return None
        draft = draft if draft is not None else self._inventory_preview()
        copies = [c for c in draft["copies"] if c["name"] == name]
        # Mostra a próxima cópia livre; na ausência dela, a melhor equipada.
        used = set(draft["copy_slots"])
        free = [c for c in copies if c["id"] not in used]
        copy = max(free or copies, key=lambda c: c["level"], default=None)
        return instance_card(copy) if copy else base

    def _cycle_filter(self, key):
        if key == "owned":
            self.owned_only = not self.owned_only
        else:
            choices = {"type": (None, "attack", "skill", "power"),
                       "cost": (None, *sorted({c.cost for c in CARD_POOL})),
                       "level": (None, 1, 2)}[key]
            attr = key + "_filter"
            value = getattr(self, attr)
            setattr(self, attr, choices[(choices.index(value)+1) % len(choices)])
        self._set_page(0)
        self.play_ui_sound("ui.click")

    def update(self, dt):
        self.visuals.update(dt)

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
        self.visuals.backdrop(surface)
        theme.eyebrow(surface, "ACAMPAMENTO / MESA DE EXPEDIÇÃO", a.small_font, 75, 36)
        draw_text(surface, "MOCHILA ANCESTRAL", a.big_font, WHITE, 72, 72)
        draw_text(
            surface,
            "Prepare seu deck e escolha o poder que vai levar para a batalha.",
            a.small_font,
            GRAY,
            75,
            119,
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
        draw_options_gear(surface, self.window_manager)
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
            self.visuals.deck(surface, self)
        else:
            self.visuals.ultimates(surface, self)
        self.visuals.label(surface, self.notice, (75, 1035, 1770, 32), self.notice_color)

    def _deck_counts(self):
        return Counter(name for name in self.draft_slots if name)

    def _draw_deck(self, surface):
        self.visuals.deck(surface, self)

    def _draw_ultimates(self, surface):
        self.visuals.ultimates(surface, self)

    def handle_event(self, event):
        if self.window_manager.handle_window_event(event):
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if options_gear_clicked(self.window_manager.map_to_virtual(event.pos)):
                self.open_options_modal()
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
                    "Escolha seu poder ancestral. A ultimate começa sem carga em cada combate."
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
                        self.visuals.celebrate(self.ultimate_rects[uid])
                        self.play_ui_sound("ui.confirm", volume=0.65)

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
        elif any(rect.collidepoint(point) for rect in self.filter_buttons.values()):
            key = next(k for k, r in self.filter_buttons.items() if r.collidepoint(point))
            self._cycle_filter(key)
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
        target_slot = next((i for i, value in enumerate(self.draft_slots) if value is None), None)
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
        self._set_page(self.page)
        if success:
            self.visuals.celebrate(self.slots[target_slot])
            self.play_ui_sound("ui.confirm", volume=0.65)

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
        self._set_page(self.page)
        if success:
            self.visuals.celebrate(self.slots[slot_index], healing=True)
            self.play_ui_sound("ui.confirm", volume=0.65)
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
        self._set_page(self.page)
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
        self._set_page(self.page)
        if success and play_sound:
            self.play_ui_sound("ui.confirm", volume=0.65)

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
