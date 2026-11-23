"""Mesa de expedição: composição visual da mochila, sem transações de save."""
from collections import Counter
import pygame

from src.config.colors import GOLD, WHITE
from src.models.effects.ultimate_effect import ULTIMATE_METADATA, DEFAULT_ULTIMATE_ID
from src.systems.card_catalog import AVAILABLE_CARD_NAMES
from src.systems.deck_loadout import DECK_SLOT_LIMIT, DECK_MIN_CARDS, COPIES_PER_CARD
from src.systems.roguelite import instance_card
from src.ui.merchant_workshop_view import MerchantWorkshopView, text_in_rect, MUTED, JADE


class BackpackView(MerchantWorkshopView):
    PREVIEW_RECT = pygame.Rect(1431, 326, 378, 546)

    def __init__(self, assets):
        super().__init__(assets, "backpack/expedition_background")

    def slot(self, surface, rect, occupied=False, hovered=False):
        self.panel(surface, rect, hovered or occupied)
        image = self.image("backpack/leather_slot", rect.size)
        if image is not None:
            surface.blit(image, rect)
        if hovered:
            pygame.draw.rect(surface, GOLD, rect.inflate(-8, -8), 2, border_radius=5)

    def label(self, surface, text, rect, color=MUTED, centered=False):
        text_in_rect(surface, text, self.assets.small_font, color, rect, centered)

    def deck(self, surface, scene):
        p = scene.save_data["progresso"]
        draft = scene._inventory_preview()
        copies = {c["id"]: c for c in draft["copies"]}
        counts = Counter(n for n in scene.draft_slots if n)
        filled = sum(counts.values())
        mouse = scene.window_manager.get_virtual_mouse_pos()
        self.panel(surface, scene.deck_panel)
        self.panel(surface, (768, 267, 592, 755))
        self.panel(surface, (1392, 267, 456, 755), True)
        self.label(surface, f"BARALHO EQUIPADO  {filled}/{DECK_SLOT_LIMIT}",
                   (99, 280, 610, 30), GOLD if filled >= DECK_MIN_CARDS else (226, 135, 118))
        self.label(surface, f"Mínimo {DECK_MIN_CARDS} · clique no espaço para retirar",
                   (99, 312, 610, 25))
        inspected = None
        for i, rect in enumerate(scene.slots):
            name = scene.draft_slots[i]
            hovered = rect.collidepoint(mouse)
            self.slot(surface, rect, bool(name), hovered)
            if name:
                card = instance_card(copies[draft["copy_slots"][i]])
                self.card(surface, card, pygame.Rect(rect.x+13, rect.y+10, 48, 68))
                self.label(surface, name, (rect.x+70, rect.y+20, rect.width-82, 32), WHITE)
                self.label(surface, f"LV{card.level} · equipado",
                           (rect.x+70, rect.y+54, rect.width-82, 20), JADE)
                if hovered:
                    inspected = card
            else:
                self.label(surface, f"{i+1:02d}  ·  VAZIO", rect.inflate(-24, -24), centered=True)
        self.label(surface, "COLEÇÃO / RESERVA", (786, 280, 430, 30), GOLD)
        self.label(surface, "Próxima cópia livre · prioridade LV2", (786, 309, 550, 19))
        self.label(surface, f"{scene.filtered_count} tipo" + ("s" if scene.filtered_count != 1 else ""), (1210, 283, 130, 25), centered=True)
        kinds = {None: "TIPOS", "attack": "ATAQUE", "skill": "HABILIDADE", "power": "PODER"}
        for key, rect in scene.filter_buttons.items():
            label = {"owned": "OBTIDAS" if scene.owned_only else "TODAS",
                     "type": kinds[scene.type_filter],
                     "cost": "CUSTO" if scene.cost_filter is None else f"{scene.cost_filter} ENERGIA",
                     "level": "NÍVEIS" if scene.level_filter is None else f"LV{scene.level_filter}"}[key]
            active = (scene.owned_only if key == "owned" else getattr(scene, key+"_filter") is not None)
            scene._button(surface, rect, label, prominent=active)
        for name, rect in scene.cards.items():
            owned = name in p["cartas_colecao"]
            available = name in AVAILABLE_CARD_NAMES
            hovered = rect.collidepoint(mouse)
            if not available:
                self.slot(surface, rect)
                self.label(surface, name, (rect.x+15, rect.y+70, rect.width-30, 40), WHITE, True)
                self.label(surface, "INDISPONÍVEL", (rect.x+12, rect.bottom-65, rect.width-24, 30), centered=True)
                self.label(surface, "no momento", (rect.x+12, rect.bottom-38, rect.width-24, 25), centered=True)
                continue
            card = scene._collection_card(name, draft)
            self.framed_card(surface, card, rect, hovered or scene.selected_card == name)
            if not owned:
                veil = pygame.Surface(rect.size, pygame.SRCALPHA)
                veil.fill((4, 10, 8, 130))
                surface.blit(veil, rect)
            label = ("NA LOJA" if not owned else
                     f"LV{card.level} · {counts[name]}/{COPIES_PER_CARD} NO DECK")
            self.label(surface, label, (rect.x-4, rect.bottom+10, rect.width+8, 25),
                       JADE if owned else MUTED, True)
            if hovered:
                inspected = card
        if not scene.cards:
            self.label(surface, "Nenhuma carta corresponde aos filtros.",
                       (795, 540, 540, 65), centered=True)
        scene._button(surface, scene.previous_page_rect, "ANTERIOR", enabled=scene.page > 0)
        scene._button(surface, scene.next_page_rect, "PRÓXIMA", enabled=scene.page+1 < scene.page_count)
        self.label(surface, f"{scene.page+1} / {scene.page_count}",
                   (978, 973, 178, 35), centered=True)
        scene._button(surface, scene.clear_deck_rect, "ESVAZIAR DECK", enabled=filled > 0, danger=True)
        scene._button(surface, scene.random_deck_rect, "DECK ALEATÓRIO", enabled=scene._random_deck_ready())
        selected = scene._collection_card(scene.selected_card, draft)
        card = inspected or selected
        self.label(surface, "INSPEÇÃO DA CARTA", (1415, 284, 410, 30), GOLD, True)
        if card is not None and card.name in AVAILABLE_CARD_NAMES:
            self.framed_card(surface, card, self.PREVIEW_RECT)
            kind = {"attack": "ATAQUE", "skill": "HABILIDADE", "power": "PODER"}[card.card_type]
            self.label(surface, f"LV{getattr(card, 'level', 1)} · {kind} · {card.cost} ENERGIA",
                       (1418, 878, 404, 25), JADE, True)
        else:
            self.label(surface, "Selecione uma carta da coleção.",
                       (1420, 510, 400, 60), centered=True)
        owned = scene.selected_card in p["cartas_colecao"]
        if scene.selected_card is None:
            label, enabled = "SELECIONE UMA CARTA", False
        elif scene.selected_card not in AVAILABLE_CARD_NAMES:
            label, enabled = "INDISPONÍVEL NO MOMENTO", False
        elif not owned:
            label, enabled = "ADQUIRA NA LOJA", False
        elif filled >= DECK_SLOT_LIMIT:
            label, enabled = "BARALHO COMPLETO", False
        elif counts[scene.selected_card] >= COPIES_PER_CARD:
            label, enabled = "LIMITE DE CÓPIAS ATINGIDO", False
        else:
            label, enabled = "EQUIPAR CARTA SELECIONADA", True
        scene._button(surface, scene.add_rect, label, enabled=enabled, prominent=True)
        self.label(surface, "Passe o mouse para inspecionar.",
                   (1418, 982, 404, 24), centered=True)
        self.feedback(surface)

    def ultimates(self, surface, scene):
        equipped = scene.save_data["progresso"].get("ultimate_equipada", DEFAULT_ULTIMATE_ID)
        roles = ("RENOVAÇÃO", "FORTALECIMENTO", "RUPTURA")
        for (uid, rect), role in zip(scene.ultimate_rects.items(), roles):
            meta = ULTIMATE_METADATA[uid]
            self.panel(surface, rect, uid == equipped)
            self.label(surface, role, (rect.x+35, 285, rect.width-70, 30), meta["accent_color"], True)
            card_rect = pygame.Rect(rect.centerx-160, 340, 320, 495)
            image = self.assets.get_ultimate_image(uid)
            if image is not None:
                scale = min(card_rect.width/image.get_width(), card_rect.height/image.get_height())
                image = pygame.transform.smoothscale(image, (round(image.get_width()*scale), round(image.get_height()*scale)))
                surface.blit(image, image.get_rect(center=card_rect.center))
            self.frame(surface, card_rect.inflate(40, 42))
            self.label(surface, f"{meta['charge_requirement']} CARGA · {meta['energy_cost']} ENERGIA",
                       (rect.x+35, 858, rect.width-70, 30), GOLD, True)
            scene._button(surface, scene.ultimate_buttons[uid],
                          "PODER EQUIPADO" if uid == equipped else "EQUIPAR ULTIMATE",
                          enabled=uid != equipped, prominent=uid != equipped)
        self.feedback(surface)
