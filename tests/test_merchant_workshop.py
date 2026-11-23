"""Regressões da seleção de cópias, transações e previews do altar ilustrado."""
import os
import tempfile
import unittest
from unittest.mock import MagicMock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from src.core.asset_manager import AssetManager
from src.scenes.roguelite_scene import RogueliteScene, upgrade_changes
from src.scenes.shop_scene import ShopScene
from src.systems.roguelite import instance_card, UPGRADE_PRICES, MATERIAL_PRICE
from src.systems.save_manager import SaveManager, SaveError
from src.systems.card_catalog import AVAILABLE_CARD_NAMES


class MerchantWorkshopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1280, 720))
        cls.assets = AssetManager.__new__(AssetManager)
        cls.assets._fonts = {}
        cls.assets._ui_images = {}
        cls.assets._card_images = {}
        cls.assets._coin_icon = None
        cls.assets._background = None
        cls.assets._init_fonts()
        cls.assets._load_coin_icon()
        cls.surface = pygame.Surface((1920, 1080))

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.manager = SaveManager(self.folder.name)
        self.data = self.manager.create_save("Altar")
        p = self.data["progresso"]
        p["moedas"] = 1000
        p["cartas_colecao"] = list(AVAILABLE_CARD_NAMES)
        p["materials"] = {name: 6 for name in AVAILABLE_CARD_NAMES}
        self.manager.save(self.data)
        self.window = MagicMock()
        self.window.handle_window_event.return_value = False
        self.window.get_virtual_mouse_pos.return_value = (-1, -1)
        self.window.map_to_virtual.side_effect = lambda pos: (round(pos[0] * 1.5), round(pos[1] * 1.5))
        self.scene = RogueliteScene(MagicMock(), self.window, self.assets, self.manager, self.data)

    def click(self, rect):
        point = (round(rect.centerx / 1.5), round(rect.centery / 1.5))
        self.scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=point))

    def test_selecting_copy_upgrades_only_that_instance_and_persists(self):
        p = self.data["progresso"]
        name = p["copies"][0]["name"]
        ids = [c["id"] for c in p["copies"] if c["name"] == name]
        self.scene.draw(self.surface)
        self.click(self.scene.copy_rects[ids[1]])
        self.scene.draw(self.surface)
        before = p["moedas"]
        self.click(self.scene.upgrade_button)
        levels = {c["id"]: c["level"] for c in p["copies"]}
        self.assertEqual([levels[cid] for cid in ids], [1, 2, 1])
        self.assertEqual(p["moedas"], before - UPGRADE_PRICES[name])
        self.assertEqual(p["materials"][name], 3)
        self.assertEqual(p["upgrades_purchased"], 1)
        saved = self.manager.load_save(self.data["id"])["progresso"]
        self.assertEqual(next(c["level"] for c in saved["copies"] if c["id"] == ids[1]), 2)
        # Mesmo antes de redesenhar, um segundo clique não pode cobrar novamente.
        self.click(self.scene.upgrade_button)
        self.assertEqual(p["moedas"], before - UPGRADE_PRICES[name])

    def test_save_failure_restores_gold_materials_and_selected_copy(self):
        self.scene.draw(self.surface)
        selected = self.scene._selected_copy()
        name, cid = selected["name"], selected["id"]
        before = self.data["progresso"]["moedas"]
        self.manager.save = MagicMock(side_effect=SaveError("Falha simulada"))
        self.click(self.scene.upgrade_button)
        p = self.data["progresso"]
        self.assertEqual(p["moedas"], before)
        self.assertEqual(p["materials"][name], 6)
        self.assertEqual(next(c["level"] for c in p["copies"] if c["id"] == cid), 1)
        self.assertFalse(self.scene.message_positive)
        self.scene.draw(self.surface)

    def test_material_purchase_and_limit(self):
        self.scene.draw(self.surface)
        name = self.scene._selected_copy()["name"]
        before = self.data["progresso"]["moedas"]
        self.click(self.scene.material_button)
        self.assertEqual(self.data["progresso"]["materials"][name], 7)
        self.assertEqual(self.data["progresso"]["moedas"], before - MATERIAL_PRICE)
        self.data["progresso"]["materials"][name] = 9
        self.scene.draw(self.surface)
        self.click(self.scene.material_button)
        self.assertEqual(self.data["progresso"]["materials"][name], 9)
        self.assertEqual(self.data["progresso"]["moedas"], before - MATERIAL_PRICE)

    def test_every_card_compares_real_levels_and_additional_effects(self):
        for name in AVAILABLE_CARD_NAMES:
            with self.subTest(name=name):
                copy = next(c for c in self.data["progresso"]["copies"] if c["name"] == name)
                self.scene.selected_copy_id = copy["id"]
                before = instance_card(dict(copy, level=1))
                after = instance_card(dict(copy, level=2))
                self.assertTrue(upgrade_changes(before, after))
                self.scene.draw(self.surface)
        copy = next(c for c in self.data["progresso"]["copies"] if c["name"] == "Máscara Ancestral")
        self.assertIn("Escudo 22 → 28", upgrade_changes(
            instance_card(dict(copy, level=1)), instance_card(dict(copy, level=2))))
        copy = next(c for c in self.data["progresso"]["copies"] if c["name"] == "Totem Protetor")
        self.assertTrue(any("8 de Escudo" in text for text in upgrade_changes(
            instance_card(dict(copy, level=1)), instance_card(dict(copy, level=2)))))

    def test_empty_collection_and_all_shop_pages_draw(self):
        shop = ShopScene(MagicMock(), self.window, self.assets, self.manager, self.data)
        for page in range(shop.page_count):
            shop._set_page(page)
            for rect in shop.offer_rects.values():
                self.assertTrue(self.surface.get_rect().contains(rect))
            shop.draw(self.surface)
        self.data["progresso"]["cartas_colecao"] = []
        self.data["progresso"]["copies"] = []
        self.scene.selected_copy_id = None
        self.scene.draw(self.surface)
        self.assertIsNone(self.scene._selected_copy())

    def test_hover_preview_leaves_purchase_hit_target_active(self):
        name = next(n for n in AVAILABLE_CARD_NAMES if n not in ("Soco Simples", "Esfera Protetora"))
        p = self.data["progresso"]
        p["cartas_colecao"].remove(name)
        p["copies"] = [c for c in p["copies"] if c["name"] != name]
        p["copy_slots"] = [cid if any(c["id"] == cid for c in p["copies"]) else None for cid in p["copy_slots"]]
        p["deck_slots"] = [n if n != name else None for n in p["deck_slots"]]
        self.manager.save(self.data)
        self.scene = ShopScene(MagicMock(), self.window, self.assets, self.manager, self.data)
        from src.systems.shop_system import CARD_OFFERS
        self.scene._set_page(list(CARD_OFFERS).index(name) // self.scene.PAGE_SIZE)
        self.window.get_virtual_mouse_pos.return_value = self.scene.card_rects[name].center
        self.scene.draw(self.surface)
        self.click(self.scene.offer_rects[name])
        self.assertIn(name, self.data["progresso"]["cartas_colecao"])
        self.assertTrue(self.scene.message_positive)


    def test_cost_composition_replaces_previous_number_for_every_card(self):
        from src.ui.card_rules import with_rules
        from src.systems.card_catalog import CARD_BY_NAME
        for name in AVAILABLE_CARD_NAMES:
            with self.subTest(name=name):
                card = CARD_BY_NAME[name]
                image = self.assets.get_card_image(name)
                direct = with_rules(image, card.description, cost=7, level=2)
                previous = with_rules(image, card.description, cost=1, level=1)
                recomposed = with_rules(previous, card.description, cost=7, level=2)
                self.assertEqual(pygame.image.tobytes(direct, "RGBA"),
                                 pygame.image.tobytes(recomposed, "RGBA"))
                self.assertNotEqual(pygame.image.tobytes(previous, "RGBA"),
                                    pygame.image.tobytes(direct, "RGBA"))

    def test_framed_card_keeps_padding_and_refreshes_when_cost_changes(self):
        from src.systems.card_catalog import CARD_BY_NAME
        view = self.scene.visuals
        card = CARD_BY_NAME["Soco Simples"].copy()
        slot = pygame.Rect(600, 330, 262, 387)
        view.framed_card(self.surface, card, slot)
        first = next(iter(view.cards.values()))
        fitted = first.get_rect(center=slot.center)
        self.assertGreaterEqual(fitted.left - slot.left, 12)
        self.assertGreaterEqual(slot.right - fitted.right, 12)
        self.assertGreaterEqual(fitted.top - slot.top, 12)
        self.assertGreaterEqual(slot.bottom - fitted.bottom, 12)
        card.cost += 2
        view.framed_card(self.surface, card, slot)
        self.assertEqual(len(view.cards), 2)
        images = list(view.cards.values())
        self.assertNotEqual(pygame.image.tobytes(images[0], "RGBA"),
                            pygame.image.tobytes(images[1], "RGBA"))


    def test_upgraded_saved_copy_keeps_lv2_across_backpack_altar_and_base_shop_offer(self):
        from src.scenes.backpack_scene import BackpackScene
        from src.systems.roguelite import upgrade_copy
        from unittest.mock import patch
        p = self.data["progresso"]
        copy = next(c for c in p["copies"] if c["name"] == "Soco Simples")
        self.assertTrue(upgrade_copy(self.manager, self.data, copy["id"])[0])
        reloaded = self.manager.load_save(self.data["id"])
        backpack = BackpackScene(MagicMock(), self.window, self.assets, self.manager, reloaded)
        draft = backpack._inventory_preview()
        slot = draft["copy_slots"].index(copy["id"])
        self.window.get_virtual_mouse_pos.return_value = backpack.slots[slot].center
        with patch.object(self.assets, "get_card_image", wraps=self.assets.get_card_image) as image:
            backpack.draw(self.surface)
            requests = [c for c in image.call_args_list
                        if c.args[0] == "Soco Simples" and c.kwargs.get("level") == 2]
            self.assertTrue(requests)
            self.assertEqual(requests[-1].kwargs["cost"], 1)
            self.assertIn("9", requests[-1].kwargs["description"])
        altar = RogueliteScene(MagicMock(), self.window, self.assets, self.manager, reloaded)
        altar.selected_copy_id = copy["id"]
        self.assertEqual(altar._selected_copy()["level"], 2)
        altar.draw(self.surface)
        self.window.get_virtual_mouse_pos.return_value = (-1, -1)
        shop = ShopScene(MagicMock(), self.window, self.assets, self.manager, reloaded)
        with patch.object(self.assets, "get_card_image", wraps=self.assets.get_card_image) as image:
            shop.draw(self.surface)
            requests = [c for c in image.call_args_list if c.args[0] == "Soco Simples"]
            self.assertTrue(requests)
            self.assertTrue(all(c.kwargs.get("level") == 1 for c in requests))
        persisted = self.manager.load_save(self.data["id"])["progresso"]
        self.assertEqual(next(c["level"] for c in persisted["copies"] if c["id"] == copy["id"]), 2)
