"""Artes por nível e composição global de custo das cartas dos packs."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import pygame
import numpy as np
from PIL import Image

from src.core.asset_manager import AssetManager
from src.systems.card_catalog import AVAILABLE_CARD_POOL
from src.systems.roguelite import instance_card
from src.ui.card_rules import with_player_rules
from src.ui.card_view import CardView
from src.ui.merchant_workshop_view import MerchantWorkshopView


class PlayerCardArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1280, 720))
        cls.root = Path(__file__).resolve().parents[1] / "assets/cards"
        cls.manifest = json.loads((cls.root / "art_manifest.json").read_text(encoding="utf-8"))["cards"]
        cls.assets = AssetManager.__new__(AssetManager)
        cls.assets._card_images = {}
        cls.assets._ui_images = {}

    def test_all_twenty_cards_have_two_complete_transparent_sprites(self):
        self.assertEqual(len(self.manifest), 40)
        for card in AVAILABLE_CARD_POOL:
            slug = self.assets.CARD_IMAGE_FILES[card.name].removesuffix(".png")
            for level in (1, 2):
                with self.subTest(card=card.name, level=level):
                    metadata = self.manifest[f"{slug}:{level}"]
                    image = Image.open(self.root / metadata["file"])
                    self.assertEqual(image.mode, "RGBA")
                    self.assertEqual(list(image.size), metadata["size"])
                    self.assertGreater(image.width, 280)
                    self.assertGreater(image.height, 400)
                    self.assertEqual(image.getchannel("A").getextrema(), (0, 255))
                    self.assertEqual(image.getpixel((0, 0))[3], 0)

    def test_swapped_pack_names_are_mapped_by_card_identity(self):
        self.assertEqual(self.manifest["lanca_perfurante:1"]["sheet"], "Cartas/Cards pack 1 Lv 1.png")
        self.assertEqual(self.manifest["lanca_perfurante:2"]["sheet"], "Cartas/Cards pack 2 Lv 2.png")
        self.assertEqual(self.manifest["machados_gemeos:1"]["sheet"], "Cartas/Cards pack 2 Lv 1.png")
        self.assertEqual(self.manifest["machados_gemeos:2"]["sheet"], "Cartas/Cards pack 1 Lv 2.png")

    def test_composition_preserves_all_art_outside_the_cost_diamond(self):
        for card in AVAILABLE_CARD_POOL:
            slug = self.assets.CARD_IMAGE_FILES[card.name].removesuffix(".png")
            for level in (1, 2):
                with self.subTest(card=card.name, level=level):
                    metadata = self.manifest[f"{slug}:{level}"]
                    source = pygame.image.load(str(self.root / metadata["file"])).convert_alpha()
                    model = instance_card({"id": "test", "name": card.name, "level": level})
                    result = self.assets.get_card_image(card.name, level=level)
                    self.assertIsNotNone(result)
                    footprint = pygame.Surface(source.get_size(), pygame.SRCALPHA)
                    pygame.draw.polygon(footprint, (255, 255, 255, 255), metadata["cost_polygon"])
                    mask = pygame.surfarray.array_alpha(footprint) == 0
                    self.assertTrue(np.array_equal(
                        pygame.surfarray.array3d(source)[mask],
                        pygame.surfarray.array3d(result)[mask]))
                    self.assertEqual(metadata["description"], model.description)

    def test_cost_can_be_changed_without_leaving_the_previous_number(self):
        for level in (1, 2):
            for card in AVAILABLE_CARD_POOL:
                with self.subTest(card=card.name, level=level):
                    slug = self.assets.CARD_IMAGE_FILES[card.name].removesuffix(".png")
                    metadata = self.manifest[f"{slug}:{level}"]
                    source = pygame.image.load(str(self.root / metadata["file"])).convert_alpha()
                    desc = metadata["description"]
                    zero = with_player_rules(source, metadata, 0, desc, level)
                    direct = with_player_rules(source, metadata, 7, desc, level)
                    recomposed = with_player_rules(zero, metadata, 7, desc, level)
                    self.assertEqual(pygame.image.tobytes(direct, "RGBA"),
                                     pygame.image.tobytes(recomposed, "RGBA"))
                    self.assertNotEqual(pygame.image.tobytes(zero, "RGBA"),
                                        pygame.image.tobytes(direct, "RGBA"))

    def test_shared_card_view_requests_the_actual_copy_level_and_cost(self):
        model = instance_card({"id": "test", "name": "Totem Protetor", "level": 2})
        model.cost = 1
        surface = pygame.Surface((420, 650))
        with patch.object(self.assets, "get_card_image", wraps=self.assets.get_card_image) as load:
            CardView.draw_card(surface, surface.get_rect(), model, self.assets)
            load.assert_called_once_with(model.name, level=2, cost=1, description=model.description)
        view = MerchantWorkshopView(self.assets, "shop/market_background")
        with patch.object(self.assets, "get_card_image", wraps=self.assets.get_card_image) as load:
            view.card(surface, model, surface.get_rect())
            load.assert_called_once_with(model.name, level=2, cost=1, description=model.description)

    def test_cache_separates_levels_and_runtime_costs(self):
        base = self.assets.get_card_image("Soco Simples")
        upgraded = self.assets.get_card_image("Soco Simples", level=2)
        free = self.assets.get_card_image("Soco Simples", level=2, cost=0)
        self.assertIsNot(base, upgraded)
        self.assertIsNot(upgraded, free)
        self.assertIs(upgraded, self.assets.get_card_image("Soco Simples", level=2))
        self.assertNotEqual(pygame.image.tobytes(upgraded, "RGBA"),
                            pygame.image.tobytes(free, "RGBA"))


    def test_detected_contours_fit_all_original_badges(self):
        from devtools.prepare_player_card_packs import detect_cost_diamond
        for key, metadata in self.manifest.items():
            with self.subTest(card=key):
                with Image.open(self.root / metadata["file"]) as image:
                    detected = detect_cost_diamond(image)
                    self.assertEqual(detected["cost_polygon"], metadata["cost_polygon"])
                    self.assertEqual(detected["cost_center"], metadata["cost_center"])
                    rgba = np.array(image)
                    # Cada vértice do recobrimento está no fundo escuro do badge.
                    for x, y in detected["cost_polygon"]:
                        self.assertLess(int(rgba[y, x, :3].max()), 55)
                        self.assertEqual(int(rgba[y, x, 3]), 255)

    def test_aura_rubra_alignment_uses_its_own_center_in_both_levels(self):
        # A posição anterior era x=59 no LV1 e deixava uma segunda ponta visível.
        for level in (1, 2):
            with self.subTest(level=level):
                cx, cy = self.manifest[f"aura_rubra:{level}"]["cost_center"]
                self.assertLessEqual(abs(cx - 50), 2)
                self.assertLessEqual(abs(cy - 50), 3)
