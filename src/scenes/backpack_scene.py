"""Preparação: seis tipos de cartas e uma ultimate independente do deck."""
import pygame
from src.config.colors import WHITE, GOLD, GRAY
from src.scenes.base_scene import BaseScene
from src.systems.deck_loadout import (SLOT_COUNT, COPIES_PER_SLOT,
    normalize_collection_and_slots, equip_card_type, equip_ultimate)
from src.systems.card_catalog import CARD_POOL, CARD_BY_NAME
from src.models.effects.ultimate_effect import ULTIMATE_METADATA, DEFAULT_ULTIMATE_ID
from src.ui import dark_fantasy_theme as theme
from src.ui.helpers import draw_text, wrap_text


class BackpackScene(BaseScene):
    PAGE_SIZE = 6

    def __init__(self, scene_manager, window_manager, asset_manager, save_manager, save_data):
        super().__init__(scene_manager, window_manager, asset_manager)
        self.save_manager, self.save_data = save_manager, save_data
        normalize_collection_and_slots(save_data['progresso'])
        self.tab, self.selected_slot, self.owned_only = 'deck', 0, False
        self.selected_card = next(name for name in save_data['progresso']['deck_slots'] if name)
        self.back_rect = pygame.Rect(1012, 43, 220, 43)
        self.deck_tab_rect = pygame.Rect(48, 118, 180, 39)
        self.ultimate_tab_rect = pygame.Rect(242, 118, 180, 39)
        self.clear_rect = pygame.Rect(48, 644, 286, 35)
        self.equip_rect = pygame.Rect(946, 625, 268, 39)
        self.filter_rect = pygame.Rect(790, 181, 100, 27)
        self.previous_page_rect = pygame.Rect(352, 644, 110, 35)
        self.next_page_rect = pygame.Rect(796, 644, 110, 35)
        self.slots = [pygame.Rect(62, 223+i*64, 258, 59) for i in range(SLOT_COUNT)]
        self.ultimate_rects = {uid: pygame.Rect(48+i*402, 178, 372, 492)
                              for i, uid in enumerate(ULTIMATE_METADATA)}
        self.ultimate_buttons = {uid: pygame.Rect(r.x+22, 608, r.width-44, 42)
                                for uid, r in self.ultimate_rects.items()}
        self._thumbs = {}
        self._set_page(0)
        self.notice = 'Escolha um espaço, selecione uma carta e equipe no painel à direita.'
        self.notice_color = GRAY

    def _set_page(self, page):
        owned = self.save_data['progresso']['cartas_colecao']
        collection = [c for c in CARD_POOL if not self.owned_only or c.name in owned]
        self.page_count = max(1, (len(collection)+self.PAGE_SIZE-1)//self.PAGE_SIZE)
        self.page = max(0, min(page, self.page_count-1))
        visible = collection[self.page*self.PAGE_SIZE:(self.page+1)*self.PAGE_SIZE]
        self.cards = {c.name: pygame.Rect(377+(i%3)*179, 216+(i//3)*208, 125, 183)
                      for i, c in enumerate(visible)}

    def update(self, dt):
        pass

    def _image(self, surface, name, rect, ultimate=False, dim=False):
        key = (name, rect.size, ultimate, dim)
        if key not in self._thumbs:
            source = (self.asset_manager.get_ultimate_image(name) if ultimate
                      else self.asset_manager.get_card_image(name))
            if source is None:
                return
            image = pygame.transform.smoothscale(source, rect.size)
            if dim:
                image.fill((100, 100, 100), special_flags=pygame.BLEND_RGB_MULT)
            self._thumbs[key] = image
        surface.blit(self._thumbs[key], rect)

    def _button(self, surface, rect, label, enabled=True, prominent=False):
        theme.button(surface, rect, label, self.asset_manager.small_font,
                     hover=rect.collidepoint(self.window_manager.get_virtual_mouse_pos()),
                     enabled=enabled, prominent=prominent)

    def draw(self, surface):
        a, p = self.asset_manager, self.save_data['progresso']
        theme.backdrop(surface, a.background, opacity=217)
        theme.eyebrow(surface, 'PREPARAÇÃO / ARSENAL ANCESTRAL', a.small_font, 50, 24)
        draw_text(surface, 'MOCHILA DO GUERREIRO', a.big_font, WHITE, 48, 48)
        draw_text(surface, 'Prepare seu deck e escolha o poder que vai levar para a batalha.', a.small_font, GRAY, 50, 91)
        self._button(surface, self.back_rect, 'VOLTAR AO MAPA')
        self._button(surface, self.deck_tab_rect, 'DECK E COLEÇÃO', prominent=self.tab == 'deck')
        self._button(surface, self.ultimate_tab_rect, 'ULTIMATES', prominent=self.tab == 'ultimates')
        uid = p.get('ultimate_equipada', DEFAULT_ULTIMATE_ID)
        meta = ULTIMATE_METADATA[uid]
        label = 'PODER EQUIPADO  ·  '+meta['name'].upper()
        draw_text(surface, label, a.small_font, meta['accent_color'], 1226-a.small_font.size(label)[0], 130)
        theme.divider(surface, 48, 1230, 166)
        if self.tab == 'deck': self._draw_deck(surface)
        else: self._draw_ultimates(surface)
        draw_text(surface, self.notice, a.small_font, self.notice_color, 50, 692)

    def _draw_deck(self, surface):
        a, p = self.asset_manager, self.save_data['progresso']
        count = sum(n is not None for n in p['deck_slots'])
        theme.panel(surface, (48, 178, 286, 454))
        theme.panel(surface, (352, 178, 554, 454))
        theme.panel(surface, (928, 178, 304, 501), highlighted=True)
        draw_text(surface, f'DECK  ·  {count}/6 TIPOS  ·  {count*COPIES_PER_SLOT} CARTAS', a.small_font, GOLD, 66, 193)
        draw_text(surface, f'COLEÇÃO  ·  {len(p["cartas_colecao"])}/{len(CARD_POOL)}', a.small_font, GOLD, 371, 188)
        self._button(surface, self.filter_rect, 'OBTIDAS' if self.owned_only else 'TODAS')
        for i, rect in enumerate(self.slots):
            selected = i == self.selected_slot
            theme.panel(surface, rect, highlighted=selected,
                        fill=(34, 37, 27, 245) if selected else (12, 21, 20, 230))
            draw_text(surface, str(i+1), a.small_font, GOLD if selected else GRAY, rect.x+11, rect.y+21)
            name = p['deck_slots'][i]
            if name:
                self._image(surface, name, pygame.Rect(rect.x+31, rect.y+5, 34, 49))
                for row, text in enumerate(wrap_text(name, a.small_font, 146)):
                    draw_text(surface, text, a.small_font, WHITE, rect.x+77, rect.y+10+row*18)
                draw_text(surface, '×3', a.small_font, GOLD, rect.right-21, rect.centery, center=True)
            else:
                draw_text(surface, 'ESPAÇO VAZIO', a.small_font, GRAY, rect.x+38, rect.y+21)
        for name, rect in self.cards.items():
            owned = name in p['cartas_colecao']
            self._image(surface, name, rect, dim=not owned)
            if self.selected_card == name:
                pygame.draw.rect(surface, (238, 198, 112), rect.inflate(6, 6), 2, border_radius=5)
            label = 'EM USO' if name in p['deck_slots'] else 'DISPONÍVEL' if owned else 'NA LOJA'
            color = GOLD if name in p['deck_slots'] else (137, 179, 150) if owned else GRAY
            draw_text(surface, label, a.small_font, color, rect.centerx, rect.bottom+12, center=True)
        self._button(surface, self.clear_rect, 'ESVAZIAR ESPAÇO '+str(self.selected_slot+1))
        self._button(surface, self.previous_page_rect, 'ANTERIOR', enabled=self.page > 0)
        self._button(surface, self.next_page_rect, 'PRÓXIMA', enabled=self.page+1 < self.page_count)
        draw_text(surface, f'PÁGINA {self.page+1} / {self.page_count}', a.small_font, GRAY, 629, 662, center=True)
        self._draw_detail(surface)

    def _draw_detail(self, surface):
        a, p = self.asset_manager, self.save_data['progresso']
        card = CARD_BY_NAME.get(self.selected_card)
        draw_text(surface, 'CARTA SELECIONADA', a.small_font, GOLD, 1080, 195, center=True)
        if card is None: return
        self._image(surface, card.name, pygame.Rect(1000, 215, 160, 235))
        kind = {'attack': 'ATAQUE', 'skill': 'HABILIDADE', 'power': 'PODER'}[card.card_type]
        draw_text(surface, f'{kind}  ·  {card.cost} DE ENERGIA', a.small_font, GOLD, 1080, 469, center=True)
        for row, text in enumerate(wrap_text(card.description, a.small_font, 260)):
            draw_text(surface, text, a.small_font, WHITE, 950, 482+row*18)
        owned = card.name in p['cartas_colecao']
        duplicate = card.name in p['deck_slots'] and p['deck_slots'][self.selected_slot] != card.name
        label = ('ADQUIRA NA LOJA' if not owned else 'JÁ ESTÁ EM OUTRO ESPAÇO' if duplicate
                 else f'EQUIPAR NO ESPAÇO {self.selected_slot+1}')
        self._button(surface, self.equip_rect, label, enabled=owned and not duplicate, prominent=True)

    def _draw_ultimates(self, surface):
        a, p = self.asset_manager, self.save_data['progresso']
        for (uid, rect), role in zip(self.ultimate_rects.items(), ('RENOVAÇÃO', 'FORTALECIMENTO', 'RUPTURA')):
            meta = ULTIMATE_METADATA[uid]
            equipped = p.get('ultimate_equipada', DEFAULT_ULTIMATE_ID) == uid
            theme.panel(surface, rect, highlighted=equipped, border=meta['accent_color'] if equipped else None)
            draw_text(surface, role, a.small_font, meta['accent_color'], rect.centerx, 199, center=True)
            self._image(surface, uid, pygame.Rect(rect.centerx-91, 220, 182, 267), ultimate=True)
            draw_text(surface, f'{meta["charge_requirement"]} DE CARGA  ·  CUSTO ZERO', a.small_font, GOLD, rect.centerx, 507, center=True)
            for row, text in enumerate(wrap_text(meta['description'], a.font, 322)):
                draw_text(surface, text, a.font, WHITE, rect.x+25, 522+row*20)
            self._button(surface, self.ultimate_buttons[uid], 'EQUIPADA' if equipped else 'EQUIPAR ULTIMATE',
                         enabled=not equipped, prominent=not equipped)

    def handle_event(self, event):
        if self.window_manager.handle_window_event(event): return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: self._back()
            elif event.key == pygame.K_TAB: self.tab = 'ultimates' if self.tab == 'deck' else 'deck'
            elif self.tab == 'deck':
                if pygame.K_1 <= event.key <= pygame.K_6: self.selected_slot = event.key-pygame.K_1
                elif event.key == pygame.K_LEFT: self._set_page(self.page-1)
                elif event.key == pygame.K_RIGHT: self._set_page(self.page+1)
                elif event.key == pygame.K_RETURN: self._equip_selected()
            return
        if event.type == pygame.MOUSEWHEEL and self.tab == 'deck':
            self._set_page(self.page-event.y)
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1: return
        point = self.window_manager.map_to_virtual(event.pos)
        if self.back_rect.collidepoint(point): self._back()
        elif self.deck_tab_rect.collidepoint(point): self.tab = 'deck'
        elif self.ultimate_tab_rect.collidepoint(point):
            self.tab = 'ultimates'
            self.notice = 'Escolha uma ultimate. A troca é salva e mantém sua carga atual.'
        elif self.tab == 'ultimates':
            for uid, rect in self.ultimate_buttons.items():
                if rect.collidepoint(point) and uid != self.save_data['progresso'].get('ultimate_equipada'):
                    self._notice(*equip_ultimate(self.save_manager, self.save_data, uid))
                    break
        elif self.previous_page_rect.collidepoint(point): self._set_page(self.page-1)
        elif self.next_page_rect.collidepoint(point): self._set_page(self.page+1)
        elif self.filter_rect.collidepoint(point):
            self.owned_only = not self.owned_only
            self._set_page(0)
        elif self.clear_rect.collidepoint(point): self._equip(None)
        elif self.equip_rect.collidepoint(point): self._equip_selected()
        else:
            for i, rect in enumerate(self.slots):
                if rect.collidepoint(point):
                    self.selected_slot = i
                    return
            for name, rect in self.cards.items():
                if rect.collidepoint(point):
                    self.selected_card = name
                    return

    def _equip_selected(self):
        if self.selected_card in self.save_data['progresso']['cartas_colecao']:
            self._equip(self.selected_card)

    def _equip(self, name):
        self._notice(*equip_card_type(self.save_manager, self.save_data, self.selected_slot, name))

    def _notice(self, ok, message):
        self.notice, self.notice_color = message, (139, 204, 149) if ok else (226, 135, 118)

    def _back(self):
        from src.scenes.map_scene import MapScene
        self.scene_manager.change_scene(MapScene(self.scene_manager, self.window_manager, self.asset_manager,
                                                self.save_manager, self.save_data))
