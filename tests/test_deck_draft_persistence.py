"""Rascunho da Mochila x último deck válido persistido no save."""
import json
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
    commit_deck,
    deck_copy_count,
    deck_is_ready_for_exit,
    empty_deck_slots,
)
from src.systems.save_manager import SAVE_VERSION, SaveError, SaveManager

VALID_A = ["Soco Simples"] * 3 + ["Esfera Protetora"] * 3


class DraftPersistenceTests(unittest.TestCase):
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

    def _set_official_deck(self, names):
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

    def _load(self):
        return self.saves.load_save("slot_1")["progresso"]

    def _write_raw_save(self, save_id, progress, versao):
        path = os.path.join(self.folder.name, save_id + ".json")
        data = {
            "versao": versao,
            "id": save_id,
            "nome": save_id,
            "criado_em": "2026-11-01T00:00:00",
            "atualizado_em": "2026-11-01T00:00:00",
            "progresso": progress,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return self.saves.load_save(save_id)

    def test_valid_deck_is_saved_and_loaded_unchanged(self):
        self._set_official_deck(VALID_A)

        loaded = self._load()

        self.assertEqual(loaded["deck_slots"], VALID_A + [None] * 12)
        self.assertEqual(loaded["cartas"], VALID_A)
        self.assertTrue(deck_is_ready_for_exit(loaded["deck_slots"]))

    def test_each_valid_edit_is_promoted_immediately(self):
        self._set_official_deck(VALID_A)
        self.data["progresso"]["cartas_colecao"].append("Investida")
        self.saves.save(self.data)
        scene = self._make_scene()

        self._click(scene, scene.cards["Investida"])

        self.assertEqual(deck_copy_count(scene.draft_slots), 7)
        loaded = self._load()
        self.assertEqual(loaded["cartas"].count("Investida"), 1)
        self.assertEqual(loaded["deck_slots"], scene.draft_slots)

    def test_invalid_draft_on_save_on_exit_keeps_last_valid_deck(self):
        self._set_official_deck(VALID_A)
        scene = self._make_scene()
        for _ in range(5):
            index = next(
                i for i, name in enumerate(scene.draft_slots) if name
            )
            scene._remove_slot(index)

        self.assertEqual(deck_copy_count(scene.draft_slots), 1)
        self.assertEqual(self.data["progresso"]["cartas"], VALID_A)

        self.assertTrue(scene.save_on_exit())

        loaded = self._load()
        self.assertEqual(loaded["deck_slots"], VALID_A + [None] * 12)
        self.assertEqual(loaded["cartas"], VALID_A)

    def test_any_invalid_draft_size_on_save_on_exit_keeps_last_valid_deck(self):
        for count in range(DECK_MIN_CARDS):
            with self.subTest(count=count):
                self._set_official_deck(VALID_A)
                scene = self._make_scene()
                scene.draft_slots = VALID_A[:count] + [None] * (
                    DECK_SLOT_LIMIT - count
                )

                self.assertTrue(scene.save_on_exit())

                loaded = self._load()
                self.assertEqual(loaded["cartas"], VALID_A)
                self.assertEqual(
                    loaded["deck_slots"], VALID_A + [None] * 12
                )

    def test_clear_deck_then_close_keeps_last_valid_deck(self):
        self._set_official_deck(VALID_A)
        scene = self._make_scene()

        self._click(scene, scene.clear_deck_rect)
        modal = self.scene_manager.push_modal.call_args.args[0]
        modal._confirm()

        self.assertEqual(scene.draft_slots, empty_deck_slots())
        self.assertTrue(scene.save_on_exit())

        loaded = self._load()
        self.assertEqual(loaded["cartas"], VALID_A)
        self.assertEqual(loaded["deck_slots"], VALID_A + [None] * 12)

    def test_last_valid_deck_is_the_most_recent_valid_edit(self):
        self._set_official_deck(VALID_A)
        self.data["progresso"]["cartas_colecao"].append("Investida")
        self.saves.save(self.data)
        scene = self._make_scene()

        # A -> rascunho inválido (5) -> B válido (6, com Investida).
        index = scene.draft_slots.index("Esfera Protetora")
        scene._remove_slot(index)
        self.assertEqual(deck_copy_count(scene.draft_slots), 5)
        self.assertEqual(self.data["progresso"]["cartas"], VALID_A)

        scene._add("Investida")
        deck_b = list(scene.draft_slots)
        self.assertEqual(deck_copy_count(deck_b), 6)
        self.assertIn("Investida", deck_b)
        self.assertEqual(self.data["progresso"]["deck_slots"], deck_b)

        # B -> rascunho inválido (5); fechar deve preservar B, não A.
        index = next(i for i, name in enumerate(scene.draft_slots) if name)
        scene._remove_slot(index)
        self.assertEqual(deck_copy_count(scene.draft_slots), 5)
        self.assertEqual(self.data["progresso"]["deck_slots"], deck_b)

        self.assertTrue(scene.save_on_exit())

        loaded = self._load()
        self.assertEqual(loaded["deck_slots"], deck_b)
        self.assertEqual(loaded["cartas"], [name for name in deck_b if name])
        self.assertNotEqual(loaded["cartas"], VALID_A)

    def test_new_player_starts_with_valid_deck_and_keeps_it(self):
        progress = self.data["progresso"]
        self.assertEqual(progress["deck_slots"], list(INITIAL_SLOTS))
        self.assertTrue(deck_is_ready_for_exit(progress["deck_slots"]))
        self.assertEqual(deck_copy_count(progress["deck_slots"]), DECK_MIN_CARDS)
        scene = self._make_scene()
        # Edição extrema na sessão: sobra só 1 carta no rascunho.
        scene.draft_slots = ["Soco Simples"] + [None] * (DECK_SLOT_LIMIT - 1)

        self.assertTrue(scene.save_on_exit())

        loaded = self._load()
        self.assertEqual(loaded["deck_slots"], list(INITIAL_SLOTS))
        self.assertEqual(loaded["cartas"], VALID_A)
        self.assertEqual(loaded["cartas_colecao"], ["Soco Simples", "Esfera Protetora"])

    def test_saving_before_opening_backpack_keeps_initial_deck(self):
        # Fechar antes de abrir a Mochila (menu/mapa) não altera o deck inicial.
        self.data["progresso"]["moedas"] = 10

        self.saves.save(self.data)

        loaded = self._load()
        self.assertEqual(loaded["deck_slots"], list(INITIAL_SLOTS))
        self.assertEqual(loaded["cartas"], VALID_A)
        self.assertEqual(
            loaded["cartas_colecao"], ["Soco Simples", "Esfera Protetora"]
        )

    def test_invalid_official_deck_is_restored_to_initial_on_save(self):
        # Sem caso de "nenhum deck válido": salvar um deck oficial inválido
        # restaura o deck inicial do tutorial.
        progress = self.data["progresso"]
        progress["deck_slots"] = ["Soco Simples"] + [None] * (DECK_SLOT_LIMIT - 1)
        progress["cartas"] = ["Soco Simples"]

        self.saves.save(self.data)

        loaded = self._load()
        self.assertEqual(loaded["deck_slots"], list(INITIAL_SLOTS))
        self.assertEqual(loaded["cartas"], VALID_A)

    def test_old_valid_save_becomes_last_valid_deck(self):
        legacy = self._write_raw_save(
            "legacy",
            {
                "moedas": 5,
                "curas_compradas_run": 0,
                "cartas_colecao": [
                    "Soco Simples",
                    "Esfera Protetora",
                    "Investida",
                ],
                "deck_slots": [
                    "Soco Simples",
                    "Esfera Protetora",
                    "Investida",
                    None,
                    None,
                    None,
                ],
                "cartas": ["Soco Simples"] * 3
                + ["Esfera Protetora"] * 3
                + ["Investida"] * 3,
            },
            versao=8,
        )
        self.assertEqual(legacy["versao"], SAVE_VERSION)
        self.assertTrue(deck_is_ready_for_exit(legacy["progresso"]["deck_slots"]))
        migrated = list(legacy["progresso"]["deck_slots"])

        self.scene_manager.current_scene = BackpackScene(
            self.scene_manager,
            self.window,
            self.assets,
            self.saves,
            legacy,
        )
        scene = self.scene_manager.current_scene
        scene.draft_slots = ["Soco Simples"] + [None] * (DECK_SLOT_LIMIT - 1)
        self.assertTrue(scene.save_on_exit())

        loaded = self.saves.load_save("legacy")["progresso"]
        self.assertEqual(loaded["deck_slots"], migrated)
        self.assertEqual(
            loaded["cartas"], ["Soco Simples"] * 3
            + ["Esfera Protetora"] * 3
            + ["Investida"] * 3,
        )

    def test_old_invalid_save_migrates_to_initial_deck_without_changing_collection(self):
        invalid_slots = ["Soco Simples"] + [None] * (DECK_SLOT_LIMIT - 1)
        collection = ["Soco Simples", "Esfera Protetora"]
        legacy = self._write_raw_save(
            "legacy",
            {
                "moedas": 5,
                "curas_compradas_run": 0,
                "cartas_colecao": list(collection),
                "deck_slots": invalid_slots,
                "cartas": ["Soco Simples"],
            },
            versao=9,
        )

        progress = legacy["progresso"]
        # O deck inválido não quebra a carga: vira o deck inicial do tutorial.
        self.assertEqual(progress["deck_slots"], list(INITIAL_SLOTS))
        self.assertEqual(progress["cartas"], VALID_A)
        self.assertTrue(deck_is_ready_for_exit(progress["deck_slots"]))
        # A coleção do jogador é preservada exatamente como estava.
        self.assertEqual(progress["cartas_colecao"], collection)

        scene = BackpackScene(
            self.scene_manager,
            self.window,
            self.assets,
            self.saves,
            legacy,
        )
        self.assertTrue(deck_is_ready_for_exit(scene.draft_slots))
        self.assertTrue(scene.save_on_exit())

        loaded = self.saves.load_save("legacy")["progresso"]
        self.assertEqual(loaded["deck_slots"], list(INITIAL_SLOTS))
        self.assertEqual(loaded["cartas_colecao"], collection)

    def test_missing_cards_are_dropped_on_load_without_exception(self):
        slots = (
            ["Soco Simples"] * 3
            + ["Esfera Protetora"] * 3
            + ["Carta Fantasma"] * 2
        )
        legacy = self._write_raw_save(
            "legacy",
            {
                "moedas": 5,
                "curas_compradas_run": 0,
                "cartas_colecao": ["Soco Simples", "Esfera Protetora"],
                "deck_slots": slots,
                "cartas": slots,
            },
            versao=9,
        )

        progress = legacy["progresso"]
        self.assertNotIn("Carta Fantasma", progress["deck_slots"])
        self.assertNotIn("Carta Fantasma", progress["cartas"])
        self.assertEqual(deck_copy_count(progress["deck_slots"]), 6)
        self.assertTrue(deck_is_ready_for_exit(progress["deck_slots"]))

    def test_missing_cards_below_minimum_fall_back_to_initial_deck(self):
        slots = (
            ["Soco Simples"] * 3
            + ["Esfera Protetora"] * 2
            + ["Carta Fantasma"]
            + [None] * (DECK_SLOT_LIMIT - 6)
        )
        collection = ["Soco Simples", "Esfera Protetora"]
        legacy = self._write_raw_save(
            "legacy",
            {
                "moedas": 5,
                "curas_compradas_run": 0,
                "cartas_colecao": list(collection),
                "deck_slots": slots,
                "cartas": [name for name in slots if name],
            },
            versao=9,
        )

        progress = legacy["progresso"]
        self.assertNotIn("Carta Fantasma", progress["deck_slots"])
        self.assertEqual(progress["deck_slots"], list(INITIAL_SLOTS))
        self.assertEqual(progress["cartas"], VALID_A)
        self.assertEqual(progress["cartas_colecao"], collection)

    def test_all_missing_cards_fall_back_to_initial_deck(self):
        collection = ["Soco Simples", "Esfera Protetora"]
        legacy = self._write_raw_save(
            "legacy",
            {
                "moedas": 5,
                "curas_compradas_run": 0,
                "cartas_colecao": list(collection),
                "deck_slots": ["Carta Fantasma"] * DECK_SLOT_LIMIT,
                "cartas": ["Carta Fantasma"] * DECK_SLOT_LIMIT,
            },
            versao=9,
        )

        progress = legacy["progresso"]
        self.assertEqual(progress["deck_slots"], list(INITIAL_SLOTS))
        self.assertEqual(progress["cartas"], VALID_A)
        self.assertEqual(progress["cartas_colecao"], collection)

    def test_other_progress_saves_with_invalid_draft_keep_last_valid_deck(self):
        self._set_official_deck(VALID_A)
        scene = self._make_scene()
        for _ in range(5):
            index = next(
                i for i, name in enumerate(scene.draft_slots) if name
            )
            scene._remove_slot(index)
        self.assertEqual(deck_copy_count(scene.draft_slots), 1)

        self.data["progresso"]["moedas"] = 123
        self.saves.save(self.data)

        loaded = self._load()
        self.assertEqual(loaded["moedas"], 123)
        self.assertEqual(loaded["cartas"], VALID_A)
        self.assertEqual(loaded["deck_slots"], VALID_A + [None] * 12)

    def test_save_on_exit_promotes_a_valid_draft(self):
        self._set_official_deck(VALID_A)
        scene = self._make_scene()
        deck_b = VALID_A[:-1] + ["Investida"]
        self.data["progresso"]["cartas_colecao"].append("Investida")
        scene.draft_slots = deck_b

        self.assertTrue(scene.save_on_exit())

        loaded = self._load()
        self.assertEqual(loaded["deck_slots"], deck_b + [None] * 12)
        self.assertEqual(loaded["cartas"], deck_b)

    def test_commit_deck_tolerates_save_error_and_restores_official(self):
        self._set_official_deck(VALID_A)
        deck_b = VALID_A[:-1] + ["Investida"]
        self.data["progresso"]["cartas_colecao"].append("Investida")
        self.saves.save = MagicMock(side_effect=SaveError("disco indisponível"))

        saved, message = commit_deck(self.saves, self.data, deck_b)

        self.assertFalse(saved)
        self.assertIn("Falha ao gravar", message)
        self.assertEqual(self.data["progresso"]["deck_slots"], VALID_A + [None] * 12)
        self.assertEqual(self.data["progresso"]["cartas"], VALID_A)

    def test_save_on_exit_never_raises_when_saving_fails(self):
        self._set_official_deck(VALID_A)
        scene = self._make_scene()
        scene.draft_slots = empty_deck_slots()
        self.saves.save = MagicMock(side_effect=OSError("disco cheio"))

        self.assertFalse(scene.save_on_exit())

        scene.draft_slots = list(VALID_A)
        self.assertFalse(scene.save_on_exit())


class DraftPersistenceWithoutPygameTests(unittest.TestCase):
    def test_deck_persistence_imports_without_pygame(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        code = """
import sys
sys.modules['pygame'] = None
from src.systems.deck_loadout import (
    add_card_to_slots,
    commit_deck,
    deck_is_ready_for_exit,
    empty_deck_slots,
)
class FakeSaveManager:
    def __init__(self):
        self.saved = 0
    def save(self, data):
        self.saved += 1
collection = ['Soco Simples', 'Esfera Protetora']
slots = empty_deck_slots()
for name in ['Soco Simples'] * 3 + ['Esfera Protetora'] * 3:
    ok, message, slots = add_card_to_slots(slots, collection, name)
    assert ok
assert deck_is_ready_for_exit(slots)
data = {'progresso': {'deck_slots': empty_deck_slots(), 'cartas': [], 'cartas_colecao': collection}}
manager = FakeSaveManager()
ok, message = commit_deck(manager, data, slots)
assert ok and manager.saved == 1
invalid = slots[:5]
ok, message = commit_deck(manager, data, invalid)
assert not ok and manager.saved == 1
assert data['progresso']['deck_slots'] == slots
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
