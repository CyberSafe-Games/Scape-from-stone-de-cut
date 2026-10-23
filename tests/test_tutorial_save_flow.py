"""Regressões do save/tutorial e custo do Cemitério, sem Pygame."""
import tempfile
import unittest

from src.systems.save_manager import SaveManager, SaveCorruptedError
from src.systems.combat_engine import CombatEngine


class TutorialSaveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.manager = SaveManager(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_new_save_starts_with_tutorial_pending(self):
        data = self.manager.create_save("slot_1")
        self.assertFalse(data["progresso"]["tutorial_concluido"])
        self.assertFalse(self.manager.load_save("slot_1")["progresso"]["tutorial_concluido"])

    def test_old_save_without_flag_bypasses_tutorial(self):
        data = self.manager.create_save("slot_1")
        del data["progresso"]["tutorial_concluido"]
        self.manager.save(data)
        self.assertTrue(self.manager.load_save("slot_1")["progresso"]["tutorial_concluido"])

    def test_flag_persists_and_invalid_type_is_rejected(self):
        data = self.manager.create_save("slot_1")
        data["progresso"]["tutorial_concluido"] = True
        self.manager.save(data)
        self.assertTrue(self.manager.load_save("slot_1")["progresso"]["tutorial_concluido"])
        data["progresso"]["tutorial_concluido"] = 1
        with self.assertRaises(SaveCorruptedError):
            self.manager.save(data)

    def test_cemetery_discard_requires_one_energy_without_spending_on_failure(self):
        game = CombatEngine()
        self.assertEqual(game.cemetery_cost, 1)
        game.player.energy = 0
        count = len(game.hand)
        self.assertFalse(game.use_cemetery(0))
        self.assertEqual(len(game.hand), count)
        self.assertEqual(game.energy, 0)

    def test_cemetery_swap_remains_free_once_per_turn(self):
        game = CombatEngine()
        game.player.energy = 0
        self.assertTrue(game.swap_cemetery(0))
        self.assertEqual(game.energy, 0)
        self.assertFalse(game.swap_cemetery(0))

    def test_discard_does_not_replenish_hand_automatically(self):
        game = CombatEngine()
        initial = len(game.hand)
        self.assertTrue(game.use_cemetery(0))
        self.assertEqual(len(game.hand), initial - 1)
        self.assertEqual(game.energy, 1)
        self.assertEqual(len(game.discard_pile), 1)


if __name__ == "__main__":
    unittest.main()
