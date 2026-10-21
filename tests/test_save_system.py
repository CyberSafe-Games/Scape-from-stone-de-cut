import json
import os
import tempfile
import unittest

from src.models.deck import DeckManager
from src.models.player import Player
from src.systems.card_catalog import CARD_POOL, create_starting_deck
from src.systems.save_manager import (
    SaveAlreadyExistsError,
    SaveCorruptedError,
    SaveManager,
    SaveNotFoundError,
)


class TestSaveSystem(unittest.TestCase):
    """Testes do sistema de criação, carregamento e salvamento de progresso."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.manager = SaveManager(saves_dir=self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_new_save_has_initial_progress(self):
        data = self.manager.create_save("Gabriel")
        progress = data["progresso"]
        self.assertEqual(progress["moedas"], 0)
        self.assertEqual(len(progress["cartas"]), 7)
        self.assertEqual(len(progress["territorios_desbloqueados"]), 1)
        self.assertTrue(self.manager.exists("Gabriel"))

    def test_create_save_does_not_overwrite_existing(self):
        self.manager.create_save("Gabriel")
        with self.assertRaises(SaveAlreadyExistsError):
            self.manager.create_save("gabriel")

    def test_empty_name_is_rejected(self):
        with self.assertRaises(ValueError):
            self.manager.create_save("   ")

    def test_load_missing_save_raises(self):
        with self.assertRaises(SaveNotFoundError):
            self.manager.load_save("inexistente")

    def test_progress_round_trip(self):
        data = self.manager.create_save("Gabriel")
        data["progresso"]["moedas"] = 120
        data["progresso"]["cartas"].append("Fúria")
        self.manager.unlock_territory(data, "floresta")
        self.manager.save(data)

        loaded = self.manager.load_save("Gabriel")
        self.assertEqual(loaded["progresso"]["moedas"], 120)
        self.assertIn("Fúria", loaded["progresso"]["cartas"])
        self.assertIn("floresta", loaded["progresso"]["territorios_desbloqueados"])

    def test_each_save_keeps_its_own_progress(self):
        a = self.manager.create_save("A")
        b = self.manager.create_save("B")
        a["progresso"]["moedas"] = 300
        self.manager.save(a)

        self.assertEqual(self.manager.load_save("A")["progresso"]["moedas"], 300)
        self.assertEqual(self.manager.load_save("B")["progresso"]["moedas"], 0)
        self.assertEqual(b["progresso"]["moedas"], 0)

    def test_unlock_territory_does_not_duplicate(self):
        data = self.manager.create_save("Gabriel")
        self.manager.unlock_territory(data, "floresta")
        self.manager.unlock_territory(data, "floresta")
        self.assertEqual(
            data["progresso"]["territorios_desbloqueados"].count("floresta"), 1
        )

    def test_update_and_apply_with_player_and_deck(self):
        data = self.manager.create_save("Gabriel")
        player = Player("Herói", 60)
        deck = DeckManager(create_starting_deck())

        player.add_coins(75)
        deck.add_to_deck(CARD_POOL[4])  # Fúria
        self.manager.update_from_game(data, player, deck)
        self.manager.save(data)

        new_player = Player("Herói", 60)
        new_deck = DeckManager()
        self.manager.apply_to_game(self.manager.load_save("Gabriel"), new_player, new_deck)

        self.assertEqual(new_player.coins, 75)
        self.assertEqual(len(new_deck.deck), 8)
        self.assertEqual([c.name for c in new_deck.deck].count("Fúria"), 1)

    def test_unknown_cards_are_ignored_when_applying(self):
        data = self.manager.create_save("Gabriel")
        data["progresso"]["cartas"] = ["Golpe", "CartaQueNaoExiste"]
        new_deck = DeckManager()
        self.manager.apply_to_game(data, Player("Herói", 60), new_deck)
        self.assertEqual([c.name for c in new_deck.deck], ["Golpe"])

    def test_list_saves(self):
        self.manager.create_save("A")
        self.manager.create_save("B")
        names = sorted(s["nome"] for s in self.manager.list_saves())
        self.assertEqual(names, ["A", "B"])

    def test_corrupted_file_is_reported_and_skipped_in_list(self):
        self.manager.create_save("Bom")
        with open(os.path.join(self._tmp.name, "ruim.json"), "w") as f:
            f.write("{ isto não é json")

        with self.assertRaises(SaveCorruptedError):
            self.manager.load_save("ruim")
        self.assertEqual([s["nome"] for s in self.manager.list_saves()], ["Bom"])

    def test_missing_fields_are_filled_on_load(self):
        path = os.path.join(self._tmp.name, "antigo.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"nome": "Antigo", "progresso": {"moedas": 10}}, f)

        loaded = self.manager.load_save("antigo")
        self.assertEqual(loaded["progresso"]["moedas"], 10)
        self.assertTrue(loaded["progresso"]["cartas"])
        self.assertTrue(loaded["progresso"]["territorios_desbloqueados"])

    def test_delete_save(self):
        self.manager.create_save("Gabriel")
        self.manager.delete_save("Gabriel")
        self.assertFalse(self.manager.exists("Gabriel"))


if __name__ == "__main__":
    unittest.main()
