"""Ícones exclusivos dos territórios no mapa: um arquivo por território."""
import os
import unittest
from unittest.mock import MagicMock

import pygame

from src.config.settings import UI_ASSETS_DIR
from src.core.asset_manager import AssetManager
from src.scenes.map_scene import MapScene, MAP_ICON_SIZE, FINAL_BOSS_ICON_SIZE
from src.systems.save_manager import SaveManager
from src.systems.territory_map import TERRITORIES, TERRITORY_IDS

ICON_DIR = os.path.join(UI_ASSETS_DIR, "map_icons")


class MapIconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        # Só o cache de ícones é necessário; evita carregar todos os sprites do jogo.
        cls.assets = AssetManager.__new__(AssetManager)
        cls.assets._map_icons = {}

    def test_every_territory_has_its_own_square_transparent_icon(self):
        self.assertEqual(sorted(os.listdir(ICON_DIR)), sorted(i + ".png" for i in TERRITORY_IDS))
        seen = set()
        for territory_id in TERRITORY_IDS:
            with self.subTest(territory=territory_id):
                icon = pygame.image.load(os.path.join(ICON_DIR, territory_id + ".png")).convert_alpha()
                width, height = icon.get_size()
                self.assertEqual(width, height)
                for corner in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)):
                    self.assertEqual(icon.get_at(corner).a, 0)
                # O disco central (onde o estado é desenhado) permanece opaco.
                self.assertEqual(icon.get_at((width // 2, height // 2)).a, 255)
                seen.add(pygame.image.tobytes(icon, "RGBA"))
        self.assertEqual(len(seen), len(TERRITORY_IDS))

    def test_icons_are_scaled_cached_and_dimmed_without_touching_the_source(self):
        icon = self.assets.get_map_icon("mata_sombria", MAP_ICON_SIZE)
        self.assertEqual(icon.get_size(), (MAP_ICON_SIZE, MAP_ICON_SIZE))
        self.assertIs(icon, self.assets.get_map_icon("mata_sombria", MAP_ICON_SIZE))
        dimmed = self.assets.get_map_icon("mata_sombria", MAP_ICON_SIZE, dimmed=True)
        self.assertIsNot(dimmed, icon)
        point = icon.get_bounding_rect(min_alpha=255).midtop
        point = (point[0], point[1] + 12)
        self.assertLess(sum(dimmed.get_at(point)[:3]), sum(icon.get_at(point)[:3]) + 1)
        self.assertIsNone(self.assets.get_map_icon("territorio_inexistente", MAP_ICON_SIZE))

    def test_map_draws_the_icon_centered_on_each_territory(self):
        import tempfile
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        saves = SaveManager(folder.name)
        data = saves.create_save("slot_1")
        calls = []
        assets = MagicMock()
        assets.menu_font = assets.small_font = pygame.font.Font(None, 28)
        assets.get_map_icon.side_effect = lambda tid, size, dimmed=False: (
            calls.append((tid, size, dimmed)) or self.assets.get_map_icon(tid, size, dimmed)
        )
        window = MagicMock()
        window.get_virtual_mouse_pos.return_value = (-100, -100)
        scene = MapScene(MagicMock(), window, assets, saves, data)
        scene.selected, scene.selected_encounter = TERRITORY_IDS[0], 0
        surface = pygame.Surface((1920, 1080), pygame.SRCALPHA)
        scene._territories(surface)
        self.assertEqual([c[0] for c in calls], list(TERRITORY_IDS))
        self.assertEqual({c[1] for c in calls[:-1]}, {MAP_ICON_SIZE})
        self.assertEqual(calls[-1][1], FINAL_BOSS_ICON_SIZE)
        self.assertTrue(all(c[2] for c in calls))  # save novo: chefes bloqueados
        for territory in TERRITORIES:
            x, y = territory.position
            # Ponto do disco fora do losango de estado: só o ícone o preenche.
            self.assertGreater(surface.get_at((x, y - 36)).a, 240, territory.id)


if __name__ == "__main__":
    unittest.main()
