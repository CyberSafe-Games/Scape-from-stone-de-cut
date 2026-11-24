from tests.management_fixtures import guides_seen
"""Integração da mesa de expedição com cartas reais, mouse e saves temporários."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import pygame
from PIL import Image

from src.core.asset_manager import AssetManager
from src.scenes.backpack_scene import BackpackScene
from src.systems.card_catalog import AVAILABLE_CARD_NAMES, CARD_BY_NAME
from src.systems.deck_loadout import DECK_MIN_CARDS, DECK_SLOT_LIMIT
from src.systems.roguelite import upgrade_copy
from src.systems.save_manager import SaveManager, SaveError


class BackpackVisualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.assets = AssetManager()

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.saves = SaveManager(self.folder.name)
        self.data = self.saves.create_save("slot_1")
        p = self.data["progresso"]
        p["cartas_colecao"] = list(AVAILABLE_CARD_NAMES)
        p["moedas"] = 9999
        p["materials"] = {name: 6 for name in AVAILABLE_CARD_NAMES}
        self.saves.save(self.data)
        copy = next(c for c in p["copies"] if c["name"] == "Soco Simples")
        self.assertTrue(upgrade_copy(self.saves, self.data, copy["id"])[0])
        self.window = MagicMock()
        self.window.handle_window_event.return_value = False
        self.window.get_virtual_mouse_pos.return_value = (-1, -1)
        self.window.map_to_virtual.side_effect = lambda point: point
        self.scene = BackpackScene(MagicMock(), self.window, self.assets, self.saves, guides_seen(self.data))
        self.canvas = pygame.Surface((1920, 1080))

    def click(self, rect):
        self.scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                                  button=1, pos=rect.center))

    def test_lv2_hover_uses_real_cost_and_description_without_changing_loadout(self):
        scene = self.scene
        p = scene._inventory_preview()
        index = next(i for i, cid in enumerate(p["copy_slots"])
                     if cid and next(c for c in p["copies"] if c["id"] == cid)["level"] == 2)
        self.window.get_virtual_mouse_pos.return_value = scene.slots[index].center
        before = deepcopy(self.data)
        with patch.object(self.assets, "get_card_image", wraps=self.assets.get_card_image) as render:
            scene.draw(self.canvas)
        lv2 = [c for c in render.call_args_list if c.args[0] == "Soco Simples"
               and c.kwargs.get("level") == 2]
        self.assertTrue(lv2)
        self.assertEqual(lv2[-1].kwargs["cost"], 1)
        self.assertIn("9", lv2[-1].kwargs["description"])
        self.assertEqual(self.data, before)

    def test_filters_use_real_type_level_and_cost_and_reset_pagination(self):
        scene = self.scene
        scene._set_page(3)
        self.click(scene.filter_buttons["type"])
        self.assertEqual(scene.page, 0)
        self.assertTrue(all(CARD_BY_NAME[n].card_type == "attack" for n in scene.cards))
        self.click(scene.filter_buttons["level"])
        self.click(scene.filter_buttons["level"])
        self.assertEqual(list(scene.cards), ["Soco Simples"])
        self.click(scene.filter_buttons["cost"])  # 0 energia
        self.assertFalse(scene.cards)
        scene.draw(self.canvas)  # Resultado vazio mantém filtros/navegação funcionais.
        self.click(scene.filter_buttons["cost"])  # 1 energia
        self.assertEqual(list(scene.cards), ["Soco Simples"])

    def test_preview_is_fixed_outside_action_controls_and_hover_cannot_equip(self):
        scene = self.scene
        preview = scene.visuals.PREVIEW_RECT.inflate(24, 28)
        for rect in [scene.add_rect, scene.back_rect, scene.previous_page_rect,
                     scene.next_page_rect, *scene.filter_buttons.values(),
                     scene.clear_deck_rect, scene.random_deck_rect]:
            self.assertFalse(preview.colliderect(rect))
        before = list(scene.draft_slots)
        for rect in [*scene.cards.values(), *scene.slots]:
            self.window.get_virtual_mouse_pos.return_value = rect.center
            scene.update(16)
            scene.draw(self.canvas)
        self.assertEqual(scene.draft_slots, before)

    def test_equip_remove_feedback_and_disk_save_preserve_upgraded_copy(self):
        scene = self.scene
        before = deepcopy(self.data["progresso"]["copies"])
        scene._add("Investida")
        self.assertGreater(scene.visuals.effect_age, 0)
        index = scene.draft_slots.index("Investida")
        self.assertEqual(self.saves.load_save("slot_1")["progresso"]["deck_slots"][index], "Investida")
        scene._remove_slot(index)
        loaded = self.saves.load_save("slot_1")["progresso"]
        self.assertIsNone(loaded["deck_slots"][index])
        self.assertEqual(loaded["copies"], before)

    def test_failed_save_does_not_play_acquisition_effect(self):
        scene = self.scene
        before = self.saves.load_save("slot_1")["progresso"]
        with patch.object(self.saves, "save", side_effect=SaveError("Falha simulada")):
            scene._add("Investida")
        self.assertEqual(scene.visuals.effect_age, 0)
        self.assertEqual(self.saves.load_save("slot_1")["progresso"]["deck_slots"], before["deck_slots"])

    def test_empty_full_and_ultimate_tabs_render_within_virtual_screen(self):
        scene = self.scene
        official = list(self.data["progresso"]["deck_slots"])
        scene._confirm_clear_deck()
        scene.draw(self.canvas)
        self.click(scene.back_rect)
        self.assertEqual(self.data["progresso"]["deck_slots"], official)
        scene._apply_random_deck()
        self.assertGreaterEqual(sum(bool(n) for n in scene.draft_slots), DECK_MIN_CARDS)
        self.assertLessEqual(sum(bool(n) for n in scene.draft_slots), DECK_SLOT_LIMIT)
        scene.draw(self.canvas)
        scene.tab = "ultimates"
        scene.draw(self.canvas)
        self.click(scene.ultimate_buttons["forcas_ancestrais"])
        self.assertEqual(self.saves.load_save("slot_1")["progresso"]["ultimate_equipada"], "forcas_ancestrais")
        bounds = self.canvas.get_rect()
        for rect in [*scene.slots, *scene.cards.values(), *scene.ultimate_buttons.values()]:
            self.assertTrue(bounds.contains(rect))

    def test_filters_do_not_misrepresent_the_level_that_will_be_equipped(self):
        scene = self.scene
        # Libera a cópia LV2, preservando os dois exemplares LV1 no rascunho.
        draft = scene._inventory_preview()
        lv2 = next(c for c in draft['copies'] if c['name'] == 'Soco Simples' and c['level'] == 2)
        index = draft['copy_slots'].index(lv2['id'])
        scene._remove_slot(index)
        scene.level_filter = 1
        scene._set_page(0)
        names = []
        for page in range(scene.page_count):
            scene._set_page(page)
            names.extend(scene.cards)
        self.assertNotIn('Soco Simples', names)
        scene.level_filter = 2
        scene._set_page(0)
        self.assertIn('Soco Simples', scene.cards)
        scene._add('Soco Simples')
        final = scene._inventory_preview()
        self.assertIn(lv2['id'], final['copy_slots'])

    def test_filter_refreshes_after_equipping_its_last_free_level_two_copy(self):
        scene = self.scene
        draft = scene._inventory_preview()
        lv2 = next(c for c in draft['copies'] if c['name'] == 'Soco Simples' and c['level'] == 2)
        scene._remove_slot(draft['copy_slots'].index(lv2['id']))
        scene._remove_slot(next(i for i,n in enumerate(scene.draft_slots) if n == 'Soco Simples'))
        scene.level_filter = 2
        scene._set_page(0)
        self.click(scene.cards['Soco Simples'])
        self.assertNotIn('Soco Simples', scene.cards)  # próxima cópia agora é LV1
        self.assertIsNone(scene.selected_card)

    def test_acquisition_effect_marks_the_hole_actually_filled(self):
        scene = self.scene
        scene._remove_slot(0)
        scene._add('Soco Simples')
        self.assertEqual(scene.visuals.effect_rect, scene.slots[0])

    def test_new_assets_load_and_leather_compartment_has_transparent_center(self):
        for key in ("expedition_background", "leather_slot"):
            self.assertIsNotNone(self.assets.get_service_image("backpack/"+key))
        path = Path(__file__).resolve().parents[1]/"assets/ui/backpack/leather_slot.png"
        with Image.open(path) as image:
            self.assertEqual(image.mode, "RGBA")
            self.assertEqual(image.getpixel((image.width//2, image.height//2))[3], 0)


if __name__ == "__main__":
    unittest.main()
