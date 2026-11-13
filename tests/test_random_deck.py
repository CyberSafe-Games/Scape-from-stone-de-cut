"""Deck aleatório: sorteio puro, persistência e integração com a Mochila."""
import os
import random
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from unittest.mock import MagicMock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from src.config.layout import (
    BACKPACK_DECK_BUTTON_GAP,
    BACKPACK_DECK_BUTTON_HEIGHT,
)
from src.scenes.backpack_scene import BackpackScene
from src.systems.card_catalog import AVAILABLE_CARD_NAMES
from src.systems.deck_loadout import (
    COPIES_PER_CARD,
    DECK_MIN_CARDS,
    DECK_SLOT_LIMIT,
    RANDOM_DECK_SIZE,
    build_random_deck,
    deck_cards,
    deck_copy_count,
    deck_is_ready_for_exit,
    empty_deck_slots,
    random_deck_capacity,
    set_random_deck,
)
from src.systems.save_manager import SaveManager

BIG_COLLECTION = sorted(AVAILABLE_CARD_NAMES)[:10]
SMALL_COLLECTION = sorted(AVAILABLE_CARD_NAMES)[:2]


class RandomDeckRulesTests(unittest.TestCase):
    def test_respects_copy_limit_and_slot_limit(self):
        slots = build_random_deck(BIG_COLLECTION, rng=random.Random(7))
        counts = Counter(deck_cards(slots))

        self.assertEqual(len(slots), DECK_SLOT_LIMIT)
        self.assertLessEqual(deck_copy_count(slots), DECK_SLOT_LIMIT)
        self.assertLessEqual(max(counts.values()), COPIES_PER_CARD)

    def test_uses_only_cards_from_the_collection(self):
        slots = build_random_deck(BIG_COLLECTION, rng=random.Random(3))
        counts = Counter(deck_cards(slots))

        self.assertLessEqual(set(counts), set(BIG_COLLECTION))
        for name, copies in counts.items():
            self.assertLessEqual(copies, COPIES_PER_CARD)

    def test_fixed_seed_is_reproducible_and_other_seeds_can_differ(self):
        first = build_random_deck(BIG_COLLECTION, rng=random.Random(42))
        again = build_random_deck(BIG_COLLECTION, rng=random.Random(42))
        other = build_random_deck(BIG_COLLECTION, rng=random.Random(43))

        self.assertEqual(first, again)
        self.assertNotEqual(first, other)

    def test_large_collection_reaches_the_target_size(self):
        self.assertEqual(RANDOM_DECK_SIZE, DECK_SLOT_LIMIT)
        slots = build_random_deck(BIG_COLLECTION, rng=random.Random(1))

        self.assertEqual(deck_copy_count(slots), RANDOM_DECK_SIZE)

    def test_small_collection_generates_only_the_possible_copies(self):
        slots = build_random_deck(SMALL_COLLECTION, rng=random.Random(5))

        self.assertEqual(deck_copy_count(slots), 6)
        self.assertEqual(deck_copy_count(slots), len(SMALL_COLLECTION) * COPIES_PER_CARD)
        self.assertGreaterEqual(deck_copy_count(slots), DECK_MIN_CARDS)
        self.assertEqual(len(slots), DECK_SLOT_LIMIT)
        self.assertEqual(slots[6:], [None] * (DECK_SLOT_LIMIT - 6))

    def test_insufficient_collection_is_signalled_and_generates_nothing(self):
        collection = ["Soco Simples"]

        self.assertEqual(random_deck_capacity(collection), 3)
        self.assertIsNone(build_random_deck(collection, rng=random.Random(1)))
        self.assertFalse(
            random_deck_capacity(collection) >= DECK_MIN_CARDS
        )

    def test_generated_deck_is_ready_for_exit(self):
        slots = build_random_deck(SMALL_COLLECTION, rng=random.Random(9))

        self.assertTrue(deck_is_ready_for_exit(slots))

    def test_building_the_deck_does_not_change_the_collection(self):
        collection = list(BIG_COLLECTION)
        before = list(collection)

        build_random_deck(collection, rng=random.Random(11))

        self.assertEqual(collection, before)

    def test_default_rng_varies_between_calls(self):
        decks = {
            tuple(build_random_deck(BIG_COLLECTION))
            for _ in range(5)
        }

        self.assertGreater(len(decks), 1)


class RandomDeckPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.saves = SaveManager(self.folder.name)
        self.data = self.saves.create_save("slot_1")

    def _set_collection(self, names):
        self.data["progresso"]["cartas_colecao"] = list(names)
        self.saves.save(self.data)

    def test_set_random_deck_persists_and_keeps_collection(self):
        self._set_collection(BIG_COLLECTION)
        collection = list(self.data["progresso"]["cartas_colecao"])

        ok, message = set_random_deck(
            self.saves, self.data, rng=random.Random(13)
        )

        self.assertTrue(ok)
        self.assertEqual(
            message, f"Deck aleatório montado: {RANDOM_DECK_SIZE} cartas."
        )
        saved_slots = list(self.data["progresso"]["deck_slots"])
        loaded = self.saves.load_save("slot_1")["progresso"]
        self.assertEqual(loaded["deck_slots"], saved_slots)
        self.assertEqual(loaded["cartas"], deck_cards(saved_slots))
        self.assertEqual(loaded["cartas_colecao"], collection)
        self.assertEqual(deck_copy_count(loaded["deck_slots"]), RANDOM_DECK_SIZE)

    def test_insufficient_collection_preserves_the_current_deck(self):
        self._set_collection(["Soco Simples"])
        before = list(self.data["progresso"]["deck_slots"])

        ok, message = set_random_deck(
            self.saves, self.data, rng=random.Random(1)
        )

        self.assertFalse(ok)
        self.assertIn(str(DECK_MIN_CARDS), message)
        self.assertEqual(self.data["progresso"]["deck_slots"], before)


class BackpackRandomDeckButtonTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.saves = SaveManager(self.folder.name)
        self.data = self.saves.create_save("slot_1")
        self.window = MagicMock()
        self.window.handle_window_event.return_value = False
        self.window.get_virtual_mouse_pos.return_value = (-1, -1)
        self.assets = MagicMock()
        self.assets.background = None
        self.scene_manager = MagicMock()
        self.scene_manager.audio_manager = None

    def _set_collection(self, names):
        self.data["progresso"]["cartas_colecao"] = list(names)
        self.saves.save(self.data)

    def _make_scene(self):
        scene = BackpackScene(
            self.scene_manager,
            self.window,
            self.assets,
            self.saves,
            self.data,
        )
        self.scene_manager.current_scene = scene
        return scene

    def _click(self, scene, rect):
        self.window.map_to_virtual.return_value = rect.center
        scene.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center
            )
        )

    def test_buttons_sit_side_by_side_below_panel_and_above_footer(self):
        scene = self._make_scene()
        clear_rect, random_rect = scene.clear_deck_rect, scene.random_deck_rect

        self.assertEqual(clear_rect.size, random_rect.size)
        self.assertEqual(clear_rect.top, random_rect.top)
        self.assertEqual(clear_rect.height, BACKPACK_DECK_BUTTON_HEIGHT)
        self.assertEqual(
            clear_rect.right + BACKPACK_DECK_BUTTON_GAP, random_rect.left
        )
        moved_down = clear_rect.top - (scene.deck_panel.bottom + 10)
        self.assertGreaterEqual(moved_down, 10)
        self.assertLessEqual(moved_down, 20)
        self.assertLess(random_rect.bottom, 1038)
        self.assertAlmostEqual(
            (clear_rect.left + random_rect.right) / 2,
            scene.deck_panel.centerx,
        )
        for rect in (
            scene.add_rect,
            scene.filter_rect,
            scene.previous_page_rect,
            scene.next_page_rect,
        ):
            self.assertFalse(random_rect.colliderect(rect))

    def test_empty_deck_generates_without_confirmation(self):
        self._set_collection(BIG_COLLECTION)
        scene = self._make_scene()
        scene.draft_slots = empty_deck_slots()

        self._click(scene, scene.random_deck_rect)

        self.scene_manager.push_modal.assert_not_called()
        progress = self.data["progresso"]
        self.assertEqual(deck_copy_count(progress["deck_slots"]), RANDOM_DECK_SIZE)
        self.assertTrue(deck_is_ready_for_exit(progress["deck_slots"]))
        self.assertEqual(deck_copy_count(scene.draft_slots), RANDOM_DECK_SIZE)
        self.assertEqual(scene.notice, "Deck aleatório montado: 18 cartas.")

    def test_manual_removal_to_zero_then_random_deck_still_works(self):
        self._set_collection(BIG_COLLECTION)
        scene = self._make_scene()
        while deck_copy_count(scene.draft_slots) > 0:
            index = next(
                i
                for i, name in enumerate(scene.draft_slots)
                if name
            )
            scene._remove_slot(index)
        self.assertEqual(deck_copy_count(scene.draft_slots), 0)

        self._click(scene, scene.random_deck_rect)

        self.scene_manager.push_modal.assert_not_called()
        self.assertEqual(
            deck_copy_count(self.data["progresso"]["deck_slots"]),
            RANDOM_DECK_SIZE,
        )
        self.assertEqual(deck_copy_count(scene.draft_slots), RANDOM_DECK_SIZE)
        self.assertIn("Deck aleatório montado", scene.notice)

    def test_non_empty_deck_asks_confirmation_before_replacing(self):
        self._set_collection(BIG_COLLECTION)
        scene = self._make_scene()
        before = list(self.data["progresso"]["deck_slots"])

        self._click(scene, scene.random_deck_rect)

        self.scene_manager.push_modal.assert_called_once()
        modal = self.scene_manager.push_modal.call_args.args[0]
        self.assertEqual(modal.title, "DECK ALEATÓRIO?")
        self.assertIn("Substituir o deck atual", modal.message)
        self.assertEqual(self.data["progresso"]["deck_slots"], before)

        modal._confirm()

        self.scene_manager.pop_modal.assert_called_once()
        self.assertEqual(
            deck_copy_count(self.data["progresso"]["deck_slots"]),
            RANDOM_DECK_SIZE,
        )
        self.assertIn("Deck aleatório montado", scene.notice)

    def test_button_is_disabled_when_collection_cannot_reach_the_minimum(self):
        self._set_collection(["Soco Simples"])
        scene = self._make_scene()
        before = list(self.data["progresso"]["deck_slots"])

        self.assertFalse(scene._random_deck_ready())
        self._click(scene, scene.random_deck_rect)

        self.scene_manager.push_modal.assert_not_called()
        self.assertEqual(self.data["progresso"]["deck_slots"], before)
        self.assertIn("Coleção insuficiente", scene.notice)

    def test_each_empty_deck_generation_can_produce_a_different_deck(self):
        self._set_collection(BIG_COLLECTION)
        seen = set()
        for _ in range(5):
            scene = self._make_scene()
            scene.draft_slots = empty_deck_slots()
            self._click(scene, scene.random_deck_rect)
            seen.add(tuple(scene.draft_slots))

        self.assertGreater(len(seen), 1)


class RandomDeckWithoutPygameTests(unittest.TestCase):
    def test_random_deck_rules_import_without_pygame(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        code = """
import sys
sys.modules['pygame'] = None
from src.systems.deck_loadout import (
    build_random_deck,
    random_deck_capacity,
    RANDOM_DECK_SIZE,
)
assert RANDOM_DECK_SIZE == 18
small = ['Soco Simples', 'Esfera Protetora']
assert len([name for name in build_random_deck(small) if name]) == 6
assert random_deck_capacity(['Soco Simples']) == 3
assert build_random_deck(['Soco Simples']) is None
print('ok')
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ok", result.stdout)


if __name__ == "__main__":
    unittest.main()
