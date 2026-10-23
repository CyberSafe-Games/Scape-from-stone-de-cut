"""Testes de checkpoints e integração com o motor de combate (sem Pygame)."""
import os
import tempfile
import unittest

from src.systems.combat_engine import CombatEngine
from src.systems.save_manager import SaveManager, SaveCorruptedError


class TestSaveIntegration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.manager = SaveManager(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_three_fixed_slot_identifiers(self):
        self.assertEqual([self.manager.slot_id(i) for i in range(1, 4)],
                         ["slot_1", "slot_2", "slot_3"])
        with self.assertRaises(ValueError):
            self.manager.slot_id(4)
        with self.assertRaises(ValueError):
            self.manager.slot_id(0)

    def test_two_slots_persist_distinct_combat_progress(self):
        first = self.manager.create_save("slot_1", display_name="Jornada 01")
        second = self.manager.create_save("slot_2", display_name="Jornada 02")

        run = CombatEngine()
        run.player.add_coins(125)
        run.player.hp = 34
        run.player.energy_max = 5
        run.player.ultimate_charge = 6
        run.deck_manager.deck.append(run.deck_manager.deck[0].copy())
        self.manager.update_from_game(first, run.player, run.deck_manager, level=4)
        self.manager.save(first)

        loaded_engine = CombatEngine()
        loaded_engine.resume_from_save(self.manager.load_save("slot_1"), self.manager)
        self.assertEqual(loaded_engine.level, 4)
        self.assertEqual(loaded_engine.player.coins, 125)
        self.assertEqual(loaded_engine.player.hp, 34)
        self.assertEqual(loaded_engine.player.energy_max, 2)  # Reinicia por luta
        self.assertEqual(loaded_engine.player.ultimate_charge, 6)
        self.assertEqual(len(loaded_engine.deck_manager.deck), 6)
        self.assertEqual(loaded_engine.state, "player_turn")
        self.assertEqual(self.manager.load_save("slot_2")["progresso"]["moedas"], 0)
        self.assertEqual(second["progresso"]["andar"], 1)

    def test_next_floor_emits_checkpoint(self):
        events = []
        engine = CombatEngine(on_event_callback=lambda evt, **kw: events.append((evt, kw)))
        engine.next_level()
        self.assertIn(("checkpoint", {"level": 2}), events)

    def test_repeated_reload_does_not_inflate_turn_counter(self):
        data = self.manager.create_save("slot_1")
        game = CombatEngine()
        self.manager.update_from_game(data, game.player, game.deck_manager, level=2)
        self.manager.save(data)
        for _ in range(3):
            restored = CombatEngine()
            restored.resume_from_save(self.manager.load_save("slot_1"), self.manager)
            self.assertEqual(restored.player.turn_count, game.player.turn_count)
            self.manager.update_from_game(data, restored.player, restored.deck_manager, level=2)
            self.manager.save(data)

    def test_invalid_json_and_invalid_metadata_are_detected(self):
        for contents in (b'\xff', b'{"nome": 42, "progresso": {}}', b'{garbage'):
            with open(os.path.join(self.temp.name, "slot_3.json"), "wb") as file:
                file.write(contents)
            with self.assertRaises(SaveCorruptedError):
                self.manager.load_save("slot_3")

    def test_save_id_cannot_escape_directory(self):
        data = self.manager.create_save("slot_1")
        data["id"] = "../fora"
        with self.assertRaises(SaveCorruptedError):
            self.manager.save(data)


if __name__ == "__main__":
    unittest.main()
