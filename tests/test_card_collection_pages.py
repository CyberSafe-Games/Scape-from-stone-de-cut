"""A coleção exibe o catálogo e só libera seleção e compra de cartas disponíveis."""
import os
import unittest
from unittest.mock import MagicMock

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import pygame

from src.scenes.shop_scene import ShopScene
from src.scenes.backpack_scene import BackpackScene
from src.systems.save_manager import SaveManager
from src.systems.card_catalog import AVAILABLE_CARD_NAMES, AVAILABLE_CARD_POOL, CARD_BY_NAME, UNAVAILABLE_CARD_NAMES
from src.systems.deck_loadout import equip_card_type
from src.systems.shop_system import purchase_card


class CardCollectionPageTests(unittest.TestCase):
    def setUp(self):
        self.window = MagicMock()
        self.window.handle_window_event.return_value = False
        self.saves = MagicMock()
        self.data = SaveManager()._new_data('Teste', 'test')
        self.data['progresso']['moedas'] = 9999

    def click(self, scene, rect):
        self.window.map_to_virtual.return_value = rect.center
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center))

    def test_buy_cards_on_all_pages_and_no_offscreen_buttons(self):
        scene = ShopScene(MagicMock(), self.window, MagicMock(), self.saves, self.data)
        found = set()
        while True:
            for name, rect in scene.offer_rects.items():
                self.assertTrue(pygame.Rect(0, 0, 1920, 1080).contains(rect))
                found.add(name)
                self.click(scene, rect)
            if scene.page == scene.page_count - 1: break
            self.click(scene, scene.next_page_rect)
        self.assertEqual(found, AVAILABLE_CARD_NAMES)
        self.assertEqual(set(self.data['progresso']['cartas_colecao']), AVAILABLE_CARD_NAMES)
        page_count = scene.page_count
        self.click(scene, scene.previous_page_rect)
        self.assertEqual(scene.page, page_count - 2)

    def test_last_page_card_can_be_equipped_and_persists_slot(self):
        self.data['progresso']['cartas_colecao'] = list(CARD_BY_NAME)
        scene = BackpackScene(MagicMock(), self.window, MagicMock(), self.saves, self.data)
        found = set(scene.cards)
        for _ in range(scene.page_count - 1):
            self.click(scene, scene.next_page_rect)
            found.update(scene.cards)
        self.assertEqual(found, set(CARD_BY_NAME))
        last_card_name = AVAILABLE_CARD_POOL[-1].name
        scene._set_page((len(AVAILABLE_CARD_POOL) - 1) // scene.PAGE_SIZE)
        scene.selected_slot = 2
        self.click(scene, scene.cards[last_card_name])
        self.assertIsNone(self.data['progresso']['deck_slots'][2])
        self.click(scene, scene.equip_rect)
        self.assertEqual(self.data['progresso']['deck_slots'][2], last_card_name)
        self.assertEqual(self.data['progresso']['cartas'].count(last_card_name), 3)

    def test_only_available_cards_can_be_selected_without_equipping(self):
        self.data['progresso']['cartas_colecao'] = list(CARD_BY_NAME)
        scene = BackpackScene(MagicMock(), self.window, MagicMock(), self.saves, self.data)
        original_slots = list(self.data['progresso']['deck_slots'])
        selected = set()
        for page in range(scene.page_count):
            scene._set_page(page)
            for name, rect in scene.cards.items():
                with self.subTest(page=page, card=name):
                    scene.selected_card = None
                    self.click(scene, rect)
                    self.assertEqual(scene.selected_card, name if name in AVAILABLE_CARD_NAMES else None)
                    self.assertEqual(self.data['progresso']['deck_slots'], original_slots)
                    if scene.selected_card:
                        selected.add(scene.selected_card)
        self.assertEqual(selected, AVAILABLE_CARD_NAMES)

    def test_unavailable_card_cannot_be_bought_or_equipped_from_an_old_save(self):
        name = sorted(UNAVAILABLE_CARD_NAMES)[0]
        progress = self.data['progresso']
        progress['cartas_colecao'] = [name]
        progress['deck_slots'] = [name]
        progress['cartas'] = [name] * 3
        coins = progress['moedas']

        self.assertFalse(purchase_card(self.saves, self.data, name).success)
        self.assertFalse(equip_card_type(self.saves, self.data, 0, name)[0])
        self.assertEqual(progress['moedas'], coins)
        self.saves.save.assert_not_called()

        BackpackScene(MagicMock(), self.window, MagicMock(), self.saves, self.data)
        self.assertIn(name, progress['cartas_colecao'])
        self.assertNotIn(name, progress['cartas'])
        self.assertTrue(progress['cartas'])
