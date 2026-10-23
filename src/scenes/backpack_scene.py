"""Mochila: coleção da RUN e seis espaços de deck, sempre três cópias por tipo."""
import pygame
from src.config.settings import WIDTH, HEIGHT
from src.config.colors import WHITE, GOLD, GRAY
from src.scenes.base_scene import BaseScene
from src.systems.deck_loadout import (
    SLOT_COUNT, COPIES_PER_SLOT, normalize_collection_and_slots, equip_card_type,
)
from src.systems.card_catalog import CARD_POOL
from src.ui import dark_fantasy_theme as theme
from src.ui.helpers import draw_text, wrap_text


class BackpackScene(BaseScene):
    def __init__(self, scene_manager, window_manager, asset_manager, save_manager, save_data):
        super().__init__(scene_manager, window_manager, asset_manager)
        self.save_manager = save_manager
        self.save_data = save_data
        normalize_collection_and_slots(self.save_data['progresso'])
        self.selected_slot = 0
        self.back_rect = pygame.Rect(953, 649, 262, 43)
        self.clear_rect = pygame.Rect(730, 649, 197, 43)
        self.slots = []
        self.cards = {}
        for i in range(SLOT_COUNT):
            col, row = i % 2, i // 2
            self.slots.append(pygame.Rect(56 + col*310, 197 + row*137, 290, 124))
        for index, card in enumerate(CARD_POOL):
            col, row = index % 2, index // 2
            self.cards[card.name] = pygame.Rect(703 + col*248, 197 + row*137, 232, 124)
        self.notice = "Selecione um espaço à esquerda e um tipo adquirido à direita."
        self.notice_color = GRAY

    def update(self, dt):
        pass

    def draw(self, surface):
        theme.backdrop(surface, self.asset_manager.background, opacity=231)
        theme.eyebrow(surface, "INVENTÁRIO / PREPARAÇÃO", self.asset_manager.small_font, 57, 28)
        draw_text(surface, "MOCHILA DO GUERREIRO", self.asset_manager.big_font, WHITE, 57, 60)
        theme.divider(surface, 55, 1220, 115)
        progress = self.save_data['progresso']
        equipped = sum(name is not None for name in progress['deck_slots'])
        draw_text(surface, f"DECK ATIVO · {equipped}/6 TIPOS · {equipped*COPIES_PER_SLOT} CARTAS",
                  self.asset_manager.menu_font, GOLD, 60, 144)
        draw_text(surface, "COLEÇÃO DE TIPOS", self.asset_manager.menu_font, GOLD, 704, 144)
        for index, rect in enumerate(self.slots):
            name = progress['deck_slots'][index]
            theme.panel(surface, rect, highlighted=index == self.selected_slot)
            draw_text(surface, f"ESPAÇO {index+1:02d}", self.asset_manager.small_font, GOLD,
                      rect.x+14, rect.y+13)
            if name:
                card = next(c for c in CARD_POOL if c.name == name)
                self._thumb(surface, card.name, rect.x+16, rect.y+39, 52, 73)
                draw_text(surface, name.upper(), self.asset_manager.small_font, WHITE,
                          rect.x+81, rect.y+48)
                draw_text(surface, "3x FIXO", self.asset_manager.small_font, GOLD,
                          rect.x+81, rect.y+81)
            else:
                draw_text(surface, "VAZIO · ESCOLHA UMA CARTA", self.asset_manager.small_font,
                          GRAY, rect.x+16, rect.y+68)
        for card in CARD_POOL:
            rect = self.cards[card.name]
            owned = card.name in progress['cartas_colecao']
            is_equipped = card.name in progress['deck_slots']
            theme.panel(surface, rect, highlighted=is_equipped)
            self._thumb(surface, card.name, rect.x+12, rect.y+10, 66, 99)
            draw_text(surface, card.name.upper(), self.asset_manager.small_font,
                      WHITE if owned else GRAY, rect.x+85, rect.y+17)
            for j, line in enumerate(wrap_text(card.description, self.asset_manager.small_font, 127)[:3]):
                draw_text(surface, line, self.asset_manager.small_font, GRAY,
                          rect.x+85, rect.y+46+j*17)
            draw_text(surface, "EQUIPADA" if is_equipped else "DISPONÍVEL" if owned else "NÃO ADQUIRIDA",
                      self.asset_manager.small_font,
                      GOLD if owned else GRAY, rect.x+85, rect.y+99)
        draw_text(surface, self.notice[:102], self.asset_manager.small_font,
                  self.notice_color, 57, 617)
        hovered = self.clear_rect.collidepoint(self.window_manager.get_virtual_mouse_pos())
        theme.button(surface, self.clear_rect, "ESVAZIAR ESPAÇO", self.asset_manager.small_font, hover=hovered)
        hovered = self.back_rect.collidepoint(self.window_manager.get_virtual_mouse_pos())
        theme.button(surface, self.back_rect, "VOLTAR AO MAPA", self.asset_manager.small_font, hover=hovered)
        theme.footer(surface, "1–6 · ESCOLHER ESPAÇO     |     3 CÓPIAS FIXAS POR TIPO     |     ESC · VOLTAR", self.asset_manager.small_font)

    def _thumb(self, surface, name, x, y, width, height):
        image = self.asset_manager.get_card_image(name)
        if image is not None:
            thumb = pygame.transform.smoothscale(image, (width, height))
            surface.blit(thumb, (x, y))

    def handle_event(self, event):
        if self.window_manager.handle_window_event(event):
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._back()
                return
            if pygame.K_1 <= event.key <= pygame.K_6:
                self.selected_slot = event.key - pygame.K_1
                return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        point = self.window_manager.map_to_virtual(event.pos)
        if self.back_rect.collidepoint(point):
            self._back()
        elif self.clear_rect.collidepoint(point):
            self._equip(None)
        else:
            for i, rect in enumerate(self.slots):
                if rect.collidepoint(point):
                    self.selected_slot = i
                    return
            for name, rect in self.cards.items():
                if rect.collidepoint(point):
                    self._equip(name)
                    return

    def _equip(self, name):
        ok, message = equip_card_type(self.save_manager, self.save_data, self.selected_slot, name)
        self.notice = message
        self.notice_color = (139, 204, 149) if ok else (226, 135, 118)

    def _back(self):
        from src.scenes.map_scene import MapScene
        self.scene_manager.change_scene(MapScene(
            self.scene_manager, self.window_manager, self.asset_manager,
            self.save_manager, self.save_data,
        ))
