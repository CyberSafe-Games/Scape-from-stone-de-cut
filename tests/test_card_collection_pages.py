"""Todas as 20 cartas ficam alcançáveis na loja e na mochila."""
import os
import unittest
from unittest.mock import MagicMock

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import pygame

from src.scenes.shop_scene import ShopScene
from src.scenes.backpack_scene import BackpackScene
from src.systems.save_manager import SaveManager
from src.systems.card_catalog import CARD_BY_NAME


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
                self.assertTrue(pygame.Rect(0, 0, 1280, 720).contains(rect))
                found.add(name)
                self.click(scene, rect)
            if scene.page == scene.page_count - 1: break
            self.click(scene, scene.next_page_rect)
        self.assertEqual(found, set(CARD_BY_NAME))
        self.assertEqual(set(self.data['progresso']['cartas_colecao']), set(CARD_BY_NAME))
        self.click(scene, scene.previous_page_rect)
        self.assertEqual(scene.page, 2)

    def test_last_page_card_can_be_equipped_and_persists_slot(self):
        self.data['progresso']['cartas_colecao'] = list(CARD_BY_NAME)
        scene = BackpackScene(MagicMock(), self.window, MagicMock(), self.saves, self.data)
        found = set(scene.cards)
        for _ in range(scene.page_count - 1):
            self.click(scene, scene.next_page_rect)
            found.update(scene.cards)
        self.assertEqual(found, set(CARD_BY_NAME))
        scene.selected_slot = 2
        self.click(scene, scene.cards['Poção Venenosa'])
        self.assertIsNone(self.data['progresso']['deck_slots'][2])
        self.click(scene, scene.equip_rect)
        self.assertEqual(self.data['progresso']['deck_slots'][2], 'Poção Venenosa')
        self.assertEqual(self.data['progresso']['cartas'].count('Poção Venenosa'), 3)
