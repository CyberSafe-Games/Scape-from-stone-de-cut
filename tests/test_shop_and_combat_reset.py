"""Testes da loja e da progressão por luta, sem interface gráfica."""
import os
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.systems.combat_engine import CombatEngine
from src.models.player import Player
from src.systems.save_manager import SaveManager, SaveCorruptedError, player_max_hp, SAVE_VERSION
from src.systems.shop_system import (
    purchase_heal, purchase_card, HEAL_PRICES, HEAL_AMOUNT, next_heal_price,
    CARD_PRICES, CARD_OFFERS,
)

HEAL_PRICE = HEAL_PRICES[0]


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

    def test_heal_persists_without_increasing_maximum(self):
        self._set_progress(coins=180, hp=20)
        result = purchase_heal(self.manager, self.data)
        self.assertTrue(result.success)
        self.assertEqual(result.amount, HEAL_AMOUNT)
        loaded = self.manager.load_save("slot_1")
        self.assertEqual(loaded["progresso"]["vida"], 40)
        self.assertEqual(loaded["progresso"]["moedas"], 180 - HEAL_PRICE)
        self.assertEqual(loaded["progresso"]["melhorias_vida_run"], 0)
        self.assertEqual(loaded['progresso']['curas_loja_run'], 1)
        engine = CombatEngine()
        engine.resume_from_save(loaded, self.manager)
        self.assertEqual((engine.player.hp, engine.player.max_hp), (40, 60))

    def test_full_hp_refuses_without_charge(self):
        self._set_progress(coins=HEAL_PRICE)
        self.assertFalse(purchase_heal(self.manager, self.data).success)
        self.assertEqual(self.data["progresso"]["vida"], 60)
        self.assertEqual(self.data["progresso"]["moedas"], HEAL_PRICE)
        self.assertEqual(self.data['progresso']['curas_loja_run'], 0)

    def test_insufficient_funds_does_not_charge(self):
        self._set_progress(coins=HEAL_PRICE - 1, hp=20)
        self.assertFalse(purchase_heal(self.manager, self.data).success)
        self.assertEqual(self.data["progresso"]["moedas"], HEAL_PRICE - 1)
        self.assertEqual(self.data["progresso"]["melhorias_vida_run"], 0)
        self.assertEqual(self.data["progresso"]["vida"], 20)

    def test_repeated_heals_stop_at_full_hp_across_reloads(self):
        self._set_progress(coins=1000, hp=1)
        for expected in (21, 41, 60):
            self.assertTrue(purchase_heal(self.manager, self.data).success)
            self.data = self.manager.load_save("slot_1")
            self.assertEqual(self.data["progresso"]["vida"], expected)
        self.assertFalse(purchase_heal(self.manager, self.data).success)
        self.assertEqual(self.data["progresso"]["melhorias_vida_run"], 0)
        self.assertEqual(self.data["progresso"]["moedas"], 1000 - sum(HEAL_PRICES))
        self.assertEqual(self.data['progresso']['curas_loja_run'], 3)
        engine = CombatEngine()
        engine.resume_from_save(self.data, self.manager)
        self.assertEqual(engine.player.max_hp, 60)

    def test_healing_does_not_change_other_slots(self):
        self._set_progress(coins=100, hp=20)
        purchase_heal(self.manager, self.data)
        other = self.manager.create_save("slot_2")
        self.assertEqual(other["progresso"]["melhorias_vida_run"], 0)
        self.assertEqual(other['progresso']['vida'], 60)
        self.assertEqual(other['progresso']['curas_loja_run'], 0)
        self.assertEqual(self.manager.load_save('slot_1')['progresso']['curas_loja_run'], 1)
        self.assertEqual(self.manager.load_save("slot_1")["progresso"]["vida"], 40)

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
            self.assertFalse(purchase_heal(self.manager, self.data).success)
        self.assertEqual(self.data["progresso"]["moedas"], before["moedas"])
        self.assertEqual(self.data["progresso"]["vida"], before["vida"])
        self.assertEqual(self.data["progresso"]["cartas"], before_cards)
        self.assertEqual(self.data["progresso"]["melhorias_vida_run"], 0)
        self.assertEqual(self.data['progresso']['curas_loja_run'], 0)

    def test_old_heals_do_not_consume_upgrade_limit(self):
        self.data["progresso"].pop("melhorias_vida_run", None)
        self.data["progresso"]["curas_compradas_run"] = 3
        self.data["versao"] = 9
        self.manager.save(self.data)
        loaded = self.manager.load_save("slot_1")
        self.assertNotIn("curas_compradas_run", loaded["progresso"])
        self.assertEqual(loaded["progresso"]["melhorias_vida_run"], 0)
        self.assertEqual(loaded['progresso']['curas_loja_run'], 0)

    def test_corrupt_purchase_counter_rejected(self):
        for counter in (-1, 4, "3", True):
            self.data["progresso"]["melhorias_vida_run"] = counter
            with self.assertRaises(SaveCorruptedError):
                self.manager.save(self.data)

    def test_heal_clamps_to_permanent_maximum_without_spending_fragments(self):
        self.data['perfil']['vida'] = 2
        self.data['perfil']['fragmentos'] = 7
        self._set_progress(coins=100, hp=67)
        result = purchase_heal(self.manager, self.data)
        self.assertTrue(result.success)
        self.assertEqual(result.amount, 3)
        self.assertEqual(self.data['progresso']['vida'], 70)
        self.assertEqual(player_max_hp(self.data['progresso']), 70)
        self.assertEqual(self.data['perfil']['fragmentos'], 7)

    def test_legacy_health_bonus_preserved_only_until_new_run(self):
        self.data['progresso']['melhorias_vida_run'] = 2
        self._set_progress(coins=100, hp=85)
        self.assertTrue(purchase_heal(self.manager, self.data).success)
        self.data = self.manager.load_save('slot_1')
        self.assertEqual(self.data['progresso']['vida'], 90)
        self.assertEqual(player_max_hp(self.data['progresso']), 90)
        self.assertEqual(self.data['progresso']['melhorias_vida_run'], 2)
        self.assertTrue(self.manager.end_run(self.data, 1)[0])
        self.assertTrue(self.manager.new_run(self.data)[0])
        self.assertEqual(player_max_hp(self.data['progresso']), 60)
        self.assertEqual(self.data['progresso']['melhorias_vida_run'], 0)

    def test_heal_cannot_resurrect_or_change_in_progress_combat(self):
        self._set_progress(coins=100, hp=0)
        self.assertFalse(purchase_heal(self.manager, self.data).success)
        self.data['progresso']['vida'] = 20
        self.data['progresso']['combat_snapshot'] = {'locked': True}
        self.assertFalse(purchase_heal(self.manager, self.data).success)
        self.data['progresso']['combat_snapshot'] = None
        self.manager.end_run(self.data, 1)
        self.assertFalse(purchase_heal(self.manager, self.data).success)

    def test_prices_increase_and_fourth_purchase_is_blocked_when_injured(self):
        self._set_progress(coins=1000, hp=1)
        for index, price in enumerate((30, 45, 60)):
            self.assertEqual(next_heal_price(self.data['progresso']), price)
            self.assertTrue(purchase_heal(self.manager, self.data).success)
            self.data = self.manager.load_save('slot_1')
            self.assertEqual(self.data['progresso']['curas_loja_run'], index + 1)
        self._set_progress(coins=1000, hp=10)  # dano de outro encontro, não nova run
        self.assertIsNone(next_heal_price(self.data['progresso']))
        self.assertFalse(purchase_heal(self.manager, self.data).success)
        self.assertEqual(self.data['progresso']['vida'], 10)
        self.assertEqual(self.data['progresso']['moedas'], 1000)

    def test_second_purchase_requires_45_and_does_not_consume_on_failure(self):
        self._set_progress(coins=74, hp=1)
        self.assertTrue(purchase_heal(self.manager, self.data).success)
        self.assertFalse(purchase_heal(self.manager, self.data).success)
        self.assertEqual(self.data['progresso']['curas_loja_run'], 1)
        self.assertEqual(self.data['progresso']['moedas'], 44)
        self.assertEqual(self.data['progresso']['vida'], 21)

    def test_failed_write_preserves_next_price_and_counter(self):
        self._set_progress(coins=1000, hp=1)
        self.assertTrue(purchase_heal(self.manager, self.data).success)
        with patch.object(self.manager, 'save', side_effect=OSError('disco')):
            self.assertFalse(purchase_heal(self.manager, self.data).success)
        p = self.data['progresso']
        self.assertEqual((p['vida'], p['moedas'], p['curas_loja_run']), (21, 970, 1))
        self.assertEqual(next_heal_price(p), 45)

    def test_new_run_resets_counter_and_profile_survives(self):
        self._set_progress(coins=1000, hp=1)
        self.assertTrue(purchase_heal(self.manager, self.data).success)
        self.data['perfil']['fragmentos'] = 9
        self.assertTrue(self.manager.end_run(self.data, 1)[0])
        self.assertTrue(self.manager.new_run(self.data)[0])
        loaded = self.manager.load_save('slot_1')
        self.assertEqual(loaded['progresso']['curas_loja_run'], 0)
        self.assertEqual(next_heal_price(loaded['progresso']), 30)
        self.assertEqual(loaded['perfil']['fragmentos'], 9)

    def test_corrupt_heal_counter_is_rejected(self):
        for value in (-1, 4, '1', True, None):
            with self.subTest(value=value):
                self.data['progresso']['curas_loja_run'] = value
                with self.assertRaises(SaveCorruptedError):
                    self.manager.save(self.data)

    def test_v13_migration_starts_counter_zero_and_preserves_original(self):
        self._set_progress(coins=123, hp=35)
        legacy = self.manager.load_save('slot_1')
        legacy.pop('progresso')
        legacy['run'].pop('curas_loja_run')
        legacy['versao'] = 13
        path = Path(self.folder.name) / 'slot_1.json'
        path.write_text(json.dumps(legacy), encoding='utf-8')
        migrated = self.manager.load_save('slot_1')
        self.assertEqual(migrated['versao'], SAVE_VERSION)
        self.assertEqual(migrated['progresso']['curas_loja_run'], 0)
        self.assertEqual((migrated['progresso']['vida'], migrated['progresso']['moedas']), (35, 123))
        self.assertEqual(json.loads(Path(str(path) + '.v13.bak').read_text(encoding='utf-8')), legacy)

    def test_partial_heal_consumes_one_purchase_but_full_hp_does_not(self):
        self._set_progress(coins=200, hp=55)
        result = purchase_heal(self.manager, self.data)
        self.assertEqual(result.amount, 5)
        self.assertEqual(self.data['progresso']['curas_loja_run'], 1)
        self.assertFalse(purchase_heal(self.manager, self.data).success)
        self.assertEqual(self.data['progresso']['curas_loja_run'], 1)
        self.assertEqual(self.data['progresso']['moedas'], 170)
        self.assertEqual(next_heal_price(self.data['progresso']), 45)

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
        self.assertEqual(engine.player.ultimate_charge, 0)
        self.assertEqual(engine.player.hp, 32)  # Combates comuns não curam; a vida persiste.

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
