"""Esvaziar o deck, rascunho inválido e mínimo de 6 para sair da Mochila."""
import inspect
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from src.scenes.backpack_scene import BackpackScene
from src.systems.deck_loadout import (
    DECK_MIN_CARDS,
    DECK_SLOT_LIMIT,
    INITIAL_SLOTS,
    add_card_to_slots,
    commit_deck,
    deck_cards,
    deck_copy_count,
    deck_is_ready_for_exit,
    empty_deck_slots,
    remove_card_from_slots,
)
from src.systems.save_manager import SaveManager


class DeckClearAndMinimumRulesTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.saves = SaveManager(self.folder.name)
        self.data = self.saves.create_save("slot_1")

    def _set_deck(self, names):
        progress = self.data["progresso"]
        progress["deck_slots"] = list(names) + [None] * (
            DECK_SLOT_LIMIT - len(names)
        )
        progress["cartas"] = list(names)
        self.saves.save(self.data)

    def test_minimum_is_six_and_counts_copies_not_card_types(self):
        self.assertEqual(DECK_MIN_CARDS, 6)
        five_copies_of_two_types = (
            ["Soco Simples"] * 3 + ["Esfera Protetora"] * 2
        )
        six_copies_of_two_types = five_copies_of_two_types + ["Esfera Protetora"]
        self.assertEqual(deck_copy_count(five_copies_of_two_types), 5)
        self.assertFalse(deck_is_ready_for_exit(five_copies_of_two_types))
        self.assertEqual(deck_copy_count(six_copies_of_two_types), 6)
        self.assertTrue(deck_is_ready_for_exit(six_copies_of_two_types))

    def test_empty_deck_slots_are_all_none(self):
        slots = empty_deck_slots()

        self.assertEqual(slots, [None] * DECK_SLOT_LIMIT)
        self.assertEqual(deck_copy_count(slots), 0)
        self.assertFalse(deck_is_ready_for_exit(slots))

    def test_clear_and_manual_removal_produce_the_same_empty_draft(self):
        deck = ["Soco Simples"] * 3 + ["Esfera Protetora"] * 3
        cleared = empty_deck_slots()

        slots = list(deck)
        while deck_copy_count(slots) > 0:
            index = next(
                i for i, name in enumerate(slots) if name
            )
            ok, message, slots = remove_card_from_slots(slots, index)
            self.assertTrue(ok)

        self.assertEqual(slots, cleared)
        self.assertFalse(deck_is_ready_for_exit(slots))

    def test_remove_last_copy_succeeds_in_draft_without_overwriting_official(self):
        valid = ["Soco Simples"] * 3 + ["Esfera Protetora"] * 3
        self._set_deck(valid)
        draft = ["Soco Simples"] + [None] * (DECK_SLOT_LIMIT - 1)

        ok, message, slots = remove_card_from_slots(draft, 0)

        self.assertTrue(ok)
        self.assertEqual(message, "Soco Simples removida do deck.")
        self.assertEqual(deck_cards(slots), [])
        self.assertFalse(commit_deck(self.saves, self.data, slots)[0])
        loaded = self.saves.load_save("slot_1")["progresso"]
        self.assertEqual(loaded["deck_slots"], valid + [None] * 12)
        self.assertEqual(loaded["cartas"], valid)

    def test_add_after_manual_zero_builds_a_valid_draft(self):
        slots = empty_deck_slots()
        collection = ["Soco Simples", "Esfera Protetora"]
        for name in ["Soco Simples"] * 3 + ["Esfera Protetora"] * 3:
            ok, message, slots = add_card_to_slots(slots, collection, name)
            self.assertTrue(ok)

        self.assertTrue(deck_is_ready_for_exit(slots))
        self.assertTrue(commit_deck(self.saves, self.data, slots)[0])
        loaded = self.saves.load_save("slot_1")["progresso"]
        self.assertEqual(deck_copy_count(loaded["deck_slots"]), 6)
        self.assertEqual(
            loaded["cartas"],
            ["Soco Simples"] * 3 + ["Esfera Protetora"] * 3,
        )

    def test_no_minimum_one_card_rule_remains(self):
        import src.systems.deck_loadout as deck_loadout

        self.assertFalse(hasattr(deck_loadout, "MIN_DECK_COPIES"))
        source = inspect.getsource(deck_loadout.remove_card_from_slots)
        self.assertNotIn("pelo menos uma carta", source)

    def test_empty_saved_deck_migrates_to_initial_deck(self):
        self._set_deck([])

        loaded = self.saves.load_save("slot_1")["progresso"]

        self.assertEqual(loaded["deck_slots"], list(INITIAL_SLOTS))
        self.assertEqual(
            loaded["cartas"],
            ["Soco Simples"] * 3 + ["Esfera Protetora"] * 3,
        )
        self.assertTrue(deck_is_ready_for_exit(loaded["deck_slots"]))

    def test_new_player_already_has_six_copies_available(self):
        progress = self.data["progresso"]
        self.assertEqual(deck_copy_count(progress["deck_slots"]), 6)
        self.assertTrue(deck_is_ready_for_exit(progress["deck_slots"]))
        self.assertGreaterEqual(len(set(progress["cartas_colecao"])), 2)


class DeckRulesWithoutPygameTests(unittest.TestCase):
    def test_deck_rules_import_and_validate_without_pygame(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        code = """
import sys
sys.modules['pygame'] = None
from src.systems.deck_loadout import (
    DECK_MIN_CARDS,
    DECK_SLOT_LIMIT,
    add_card_to_slots,
    commit_deck,
    deck_copy_count,
    deck_is_ready_for_exit,
    empty_deck_slots,
    remove_card_from_slots,
)
assert DECK_MIN_CARDS == 6
five = ['Soco Simples'] * 3 + ['Esfera Protetora'] * 2
assert deck_copy_count(five) == 5
assert not deck_is_ready_for_exit(five)
assert deck_is_ready_for_exit(five + ['Esfera Protetora'])
assert callable(commit_deck)
slots = empty_deck_slots()
assert slots == [None] * DECK_SLOT_LIMIT
ok, message, slots = remove_card_from_slots(five, 0)
assert ok and deck_copy_count(slots) == 4
ok, message, slots = add_card_to_slots(slots, ['Soco Simples', 'Esfera Protetora'], 'Soco Simples')
assert ok
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


class BackpackExitRulesTests(unittest.TestCase):
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

    def _set_deck(self, names):
        progress = self.data["progresso"]
        progress["deck_slots"] = list(names) + [None] * (
            DECK_SLOT_LIMIT - len(names)
        )
        progress["cartas"] = list(names)
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

    def test_invalid_deck_blocks_back_button_and_escape(self):
        self._set_deck(["Soco Simples"] * 3 + ["Esfera Protetora"] * 3)
        scene = self._make_scene()
        # O deck oficial é válido; o rascunho em edição tem só 5 cartas.
        scene.draft_slots = (
            ["Soco Simples"] * 3
            + ["Esfera Protetora"] * 2
            + [None] * (DECK_SLOT_LIMIT - 5)
        )

        self._click(scene, scene.back_rect)

        self.scene_manager.change_scene.assert_not_called()
        self.assertIs(self.scene_manager.current_scene, scene)
        self.assertIn("Faltam 1", scene.notice)

        scene.handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        )

        self.scene_manager.change_scene.assert_not_called()
        self.assertIs(self.scene_manager.current_scene, scene)
        self.assertIn("Faltam 1", scene.notice)

    def test_valid_deck_exits_by_button_and_escape(self):
        self._set_deck(["Soco Simples"] * 3 + ["Esfera Protetora"] * 3)
        scene = self._make_scene()

        self._click(scene, scene.back_rect)

        self.scene_manager.change_scene.assert_called_once()

        self.scene_manager.reset_mock()
        scene = self._make_scene()
        scene.handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        )

        self.scene_manager.change_scene.assert_called_once()

    def test_ultimate_tab_stays_available_with_invalid_deck(self):
        self._set_deck(["Soco Simples"] * 3 + ["Esfera Protetora"] * 3)
        scene = self._make_scene()
        scene.draft_slots = (
            ["Soco Simples"] * 3
            + ["Esfera Protetora"] * 2
            + [None] * (DECK_SLOT_LIMIT - 5)
        )

        self._click(scene, scene.ultimate_tab_rect)

        self.assertEqual(scene.tab, "ultimates")
        self.scene_manager.change_scene.assert_not_called()

    def test_clear_deck_asks_confirmation_and_leaves_draft_empty(self):
        self._set_deck(["Soco Simples"] * 3 + ["Esfera Protetora"] * 3)
        collection = list(self.data["progresso"]["cartas_colecao"])
        scene = self._make_scene()

        self._click(scene, scene.clear_deck_rect)

        self.scene_manager.push_modal.assert_called_once()
        modal = self.scene_manager.push_modal.call_args.args[0]
        self.assertEqual(modal.title, "ESVAZIAR DECK?")
        self.assertIn(str(DECK_MIN_CARDS), modal.message)
        self.assertEqual(deck_copy_count(scene.draft_slots), 6)

        modal._confirm()

        self.assertEqual(scene.draft_slots, [None] * DECK_SLOT_LIMIT)
        self.assertEqual(deck_copy_count(scene.draft_slots), 0)
        # O rascunho vazio não substitui o último deck válido.
        self.assertEqual(
            deck_copy_count(self.data["progresso"]["deck_slots"]), 6
        )
        self.assertEqual(self.data["progresso"]["cartas_colecao"], collection)
        self.assertEqual(scene.notice, "Deck esvaziado.")
        self.assertFalse(deck_is_ready_for_exit(scene.draft_slots))

    def test_clear_button_does_nothing_extra_when_draft_is_already_empty(self):
        scene = self._make_scene()
        scene.draft_slots = empty_deck_slots()

        self._click(scene, scene.clear_deck_rect)

        self.scene_manager.push_modal.assert_not_called()
        self.assertIn("já está vazio", scene.notice)

    def test_click_last_slot_removes_it_from_draft_and_shows_minimum_notice(self):
        scene = self._make_scene()
        scene.draft_slots = ["Soco Simples"] + [None] * (DECK_SLOT_LIMIT - 1)

        self._click(scene, scene.slots[0])

        self.assertEqual(scene.draft_slots, [None] * DECK_SLOT_LIMIT)
        self.assertEqual(deck_copy_count(scene.draft_slots), 0)
        self.assertIn(f"Faltam {DECK_MIN_CARDS}", scene.notice)
        self.assertNotIn("pelo menos uma carta", scene.notice)
        # O deck oficial continua sendo o último válido.
        self.assertEqual(
            deck_copy_count(self.data["progresso"]["deck_slots"]), 6
        )

        self._click(scene, scene.clear_deck_rect)

        self.scene_manager.push_modal.assert_not_called()
        self.assertIn("já está vazio", scene.notice)

    def test_backspace_removes_the_last_card_from_draft(self):
        scene = self._make_scene()
        scene.draft_slots = ["Soco Simples"] + [None] * (DECK_SLOT_LIMIT - 1)

        scene.handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE)
        )

        self.assertEqual(deck_copy_count(scene.draft_slots), 0)
        self.assertIn(f"Faltam {DECK_MIN_CARDS}", scene.notice)
        self.assertEqual(
            deck_copy_count(self.data["progresso"]["deck_slots"]), 6
        )

    def test_zero_cards_blocks_exit(self):
        scene = self._make_scene()
        scene.draft_slots = empty_deck_slots()

        self._click(scene, scene.back_rect)

        self.scene_manager.change_scene.assert_not_called()
        self.assertIn(f"Faltam {DECK_MIN_CARDS}", scene.notice)

    def test_collection_click_still_adds_after_manual_zero(self):
        scene = self._make_scene()
        scene.draft_slots = empty_deck_slots()

        self._click(scene, scene.cards["Soco Simples"])

        self.assertEqual(deck_copy_count(scene.draft_slots), 1)
        self.assertIn("adicionada ao deck", scene.notice)
        # Ainda é rascunho inválido: o oficial não muda.
        self.assertEqual(
            deck_copy_count(self.data["progresso"]["deck_slots"]), 6
        )

    def test_invalid_saved_deck_migrates_to_initial_when_reopening(self):
        self._set_deck(["Soco Simples"] * 3 + ["Esfera Protetora"] * 2)
        loaded = self.saves.load_save("slot_1")

        scene = BackpackScene(
            self.scene_manager,
            self.window,
            self.assets,
            self.saves,
            loaded,
        )

        # O deck inválido gravado vira o deck inicial do tutorial ao carregar.
        self.assertEqual(loaded["progresso"]["deck_slots"], list(INITIAL_SLOTS))
        self.assertEqual(deck_copy_count(loaded["progresso"]["deck_slots"]), 6)
        self.assertEqual(scene.draft_slots, list(INITIAL_SLOTS))
        self.assertTrue(deck_is_ready_for_exit(scene.draft_slots))

    def test_clear_button_sits_below_panel_without_overlapping_other_controls(self):
        scene = self._make_scene()
        self.assertTrue(
            pygame.Rect(0, 0, 1920, 1080).contains(scene.clear_deck_rect)
        )
        self.assertGreaterEqual(
            scene.clear_deck_rect.top, scene.deck_panel.bottom
        )
        self.assertLess(scene.clear_deck_rect.bottom, 1038)
        for rect in (
            scene.add_rect,
            scene.filter_rect,
            scene.previous_page_rect,
            scene.next_page_rect,
        ):
            self.assertFalse(scene.clear_deck_rect.colliderect(rect))
        self.assertTrue(scene.deck_panel.contains(scene.slots[-1]))


if __name__ == "__main__":
    unittest.main()
