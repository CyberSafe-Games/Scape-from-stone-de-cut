"""Testes da loja e da progressão por luta, sem interface gráfica."""
import os
import tempfile
import unittest
from unittest.mock import patch

from src.systems.combat_engine import CombatEngine
from src.models.player import Player
from src.systems.save_manager import SaveManager, SaveCorruptedError
from src.systems.shop_system import (
    purchase_healing, purchase_card, HEAL_PRICE, HEAL_PURCHASE_LIMIT,
    CARD_PRICES, CARD_OFFERS,
)


class ShopAndCombatTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.manager = SaveManager(self.folder.name)
        self.data = self.manager.create_save("slot_1")

    def tearDown(self):
        self.folder.cleanup()

    def _set_progress(self, *, coins, hp=60):
        self.data["progresso"]["moedas"] = coins
        self.data["progresso"]["vida"] = hp
        self.manager.save(self.data)

    def test_heal_restores_15_hp_and_charges_once(self):
        self._set_progress(coins=180, hp=20)
        result = purchase_healing(self.manager, self.data)
        self.assertTrue(result.success)
        self.assertEqual(result.amount, 15)
        self.assertEqual(self.manager.load_save("slot_1")["progresso"]["vida"], 35)
        self.assertEqual(self.data["progresso"]["moedas"], 180 - HEAL_PRICE)
        self.assertEqual(self.data["progresso"]["curas_compradas_run"], 1)

    def test_partial_heal_never_exceeds_max_hp(self):
        self._set_progress(coins=HEAL_PRICE, hp=52)
        result = purchase_healing(self.manager, self.data)
        self.assertEqual(result.amount, 8)
        self.assertEqual(self.data["progresso"]["vida"], 60)
        self.assertEqual(self.data["progresso"]["moedas"], 0)

    def test_full_hp_or_insufficient_funds_does_not_charge(self):
        self._set_progress(coins=500, hp=60)
        self.assertFalse(purchase_healing(self.manager, self.data).success)
        self.assertEqual(self.data["progresso"]["moedas"], 500)
        self._set_progress(coins=HEAL_PRICE - 1, hp=20)
        self.assertFalse(purchase_healing(self.manager, self.data).success)
        self.assertEqual(self.data["progresso"]["curas_compradas_run"], 0)
        self.assertEqual(self.data["progresso"]["vida"], 20)

    def test_only_three_heals_per_run_across_reloads(self):
        self._set_progress(coins=1000, hp=1)
        for i in range(HEAL_PURCHASE_LIMIT):
            self.assertTrue(purchase_healing(self.manager, self.data).success)
            self.data = self.manager.load_save("slot_1")
            self.assertEqual(self.data["progresso"]["curas_compradas_run"], i + 1)
        self.assertFalse(purchase_healing(self.manager, self.data).success)
        self.assertEqual(self.data["progresso"]["curas_compradas_run"], 3)
        self.assertEqual(self.data["progresso"]["moedas"], 1000 - 3 * HEAL_PRICE)

    def test_independent_runs_and_new_save_reset_limit(self):
        self._set_progress(coins=100, hp=20)
        purchase_healing(self.manager, self.data)
        other = self.manager.create_save("slot_2")
        self.assertEqual(other["progresso"]["curas_compradas_run"], 0)
        self.assertEqual(self.manager.load_save("slot_1")["progresso"]["curas_compradas_run"], 1)

    def test_card_purchase_adds_to_collection_and_persists(self):
        self._set_progress(coins=150)
        card_name = "Investida"
        cards_before = len(self.data["progresso"]["cartas"])
        result = purchase_card(self.manager, self.data, card_name)
        self.assertTrue(result.success)
        loaded = self.manager.load_save("slot_1")
        self.assertEqual(loaded["progresso"]["moedas"], 150 - CARD_PRICES[card_name])
        self.assertEqual(len(loaded["progresso"]["cartas"]), cards_before)
        self.assertIn(card_name, loaded["progresso"]["cartas_colecao"])
        engine = CombatEngine()
        engine.resume_from_save(loaded, self.manager)
        self.assertNotIn(card_name, [card.name for card in engine.deck_manager.deck])

    def test_card_purchase_insufficient_and_unregistered(self):
        self._set_progress(coins=0)
        original = list(self.data["progresso"]["cartas"])
        self.assertFalse(purchase_card(self.manager, self.data, "Defesa").success)
        self.assertFalse(purchase_card(self.manager, self.data, "Supercarta Inexistente").success)
        self.assertEqual(self.data["progresso"]["cartas"], original)
        self.assertEqual(self.data["progresso"]["moedas"], 0)

    def test_failed_save_rolls_back_card_and_heal(self):
        self._set_progress(coins=1000, hp=10)
        before = dict(self.data["progresso"])
        before_cards = list(self.data["progresso"]["cartas"])
        with patch.object(self.manager, "save", side_effect=OSError("Sem permissão")):
            self.assertFalse(purchase_card(self.manager, self.data, "Defesa").success)
            self.assertFalse(purchase_healing(self.manager, self.data).success)
        self.assertEqual(self.data["progresso"]["moedas"], before["moedas"])
        self.assertEqual(self.data["progresso"]["vida"], before["vida"])
        self.assertEqual(self.data["progresso"]["cartas"], before_cards)
        self.assertEqual(self.data["progresso"]["curas_compradas_run"], 0)

    def test_old_save_migrates_without_purchase_history(self):
        self.data["progresso"].pop("curas_compradas_run", None)
        self.manager.save(self.data)
        loaded = self.manager.load_save("slot_1")
        self.assertEqual(loaded["progresso"]["curas_compradas_run"], 0)

    def test_corrupt_purchase_counter_rejected(self):
        for counter in (-1, 4, "3", True):
            self.data["progresso"]["curas_compradas_run"] = counter
            with self.assertRaises(SaveCorruptedError):
                self.manager.save(self.data)

    def test_new_fight_resets_energy_hand_growth_and_strength(self):
        engine = CombatEngine()
        engine.player.energy_max = 8
        engine.player.turn_count = 30
        engine.player.strength = 9
        engine.player.coins = 99
        engine.player.hp = 32
        engine.player.ultimate_charge = 7
        engine.next_level()
        self.assertEqual(engine.player.energy_max, Player.INITIAL_ENERGY_MAX)
        self.assertEqual(engine.player.energy, Player.INITIAL_ENERGY_MAX)
        self.assertEqual(engine.player.turn_count, 1)
        self.assertEqual(engine.player.get_hand_size(), 3)
        self.assertEqual(engine.player.strength, 0)
        self.assertEqual(engine.player.coins, 99)
        self.assertEqual(engine.player.ultimate_charge, 7)
        self.assertEqual(engine.player.hp, 40)  # Cura da transição permanece.

    def test_loading_legacy_progress_starts_at_fight_baseline(self):
        self.data["progresso"].update(energia_maxima=8, turnos=30, andar=3)
        self.manager.save(self.data)
        game = CombatEngine()
        game.resume_from_save(self.manager.load_save("slot_1"), self.manager)
        self.assertEqual(game.player.energy_max, 2)
        self.assertEqual(game.player.turn_count, 1)
        self.assertEqual(game.player.get_hand_size(), 3)
        self.manager.update_from_game(self.data, game.player, game.deck_manager, level=3)
        self.assertEqual(self.data["progresso"]["energia_maxima"], 2)
        self.assertEqual(self.data["progresso"]["turnos"], 1)


if __name__ == "__main__":
    unittest.main()
