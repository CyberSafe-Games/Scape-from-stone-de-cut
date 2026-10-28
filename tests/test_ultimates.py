"""Testes das ultimates e da migração do save."""
import json
import os
import tempfile
import unittest

from src.systems.combat_engine import CombatEngine
from src.systems.save_manager import SaveManager
from src.models.effects.ultimate_effect import DEFAULT_ULTIMATE_ID, known_ultimate_ids


class TestUltimates(unittest.TestCase):
    def test_default_ultimate_is_mana_ancestral(self):
        engine = CombatEngine()
        self.assertEqual(engine.active_ultimate_id, DEFAULT_ULTIMATE_ID)
        self.assertEqual(engine.active_ultimate_name, "Mana Ancestral")
        self.assertIn(DEFAULT_ULTIMATE_ID, engine.unlocked_ultimates)

    def test_mana_ancestral_restores_energy_and_draws_cards(self):
        engine = CombatEngine()
        engine.player.use_energy(2)
        engine.player.ultimate_charge = engine.player.ultimate_threshold
        engine.deck_manager.draw_pile.extend([engine.hand[0].copy() for _ in range(5)])
        hand_before = len(engine.hand)
        self.assertTrue(engine.activate_ultimate())
        self.assertEqual(engine.energy, engine.player.MAX_ENERGY_LIMIT)
        self.assertEqual(len(engine.hand), hand_before + 5)
        self.assertEqual(engine.player.ultimate_charge, 0)

    def test_forcas_ancestrais_grants_strength_and_block(self):
        engine = CombatEngine()
        engine.player.unlock_ultimate("forcas_ancestrais")
        self.assertTrue(engine.equip_ultimate("forcas_ancestrais"))
        engine.player.ultimate_charge = engine.player.ultimate_threshold
        self.assertTrue(engine.activate_ultimate())
        self.assertEqual(engine.player.strength, 12)
        self.assertEqual(engine.player.block, 40)

    def test_rugido_applies_weakness_for_three_full_enemy_turns(self):
        engine = CombatEngine()
        engine.player.unlock_ultimate("rugido_da_floresta")
        self.assertTrue(engine.equip_ultimate("rugido_da_floresta"))
        engine.player.ultimate_charge = engine.player.ultimate_threshold
        engine.enemy.hp = engine.enemy.max_hp = 200
        target_hp = engine.enemy.hp
        self.assertTrue(engine.activate_ultimate())
        self.assertLess(engine.enemy.hp, target_hp)
        self.assertEqual(engine.enemy.weak_turns, 3)

        player_hp = engine.player.hp
        engine.end_turn()
        engine.enemy.current_action = None
        engine.enemy.intent = "attack"
        engine.enemy.intent_value = 8
        engine.enemy_turn()
        self.assertEqual(player_hp - engine.player.hp, 6)
        self.assertEqual(engine.enemy.weak_turns, 3)

        engine.finish_enemy_turn()
        self.assertEqual(engine.enemy.weak_turns, 2)
        player_hp = engine.player.hp
        engine.end_turn()
        engine.enemy.current_action = None
        engine.enemy.intent = "attack"
        engine.enemy.intent_value = 8
        engine.enemy_turn()
        self.assertEqual(player_hp - engine.player.hp, 6)
        self.assertEqual(engine.enemy.weak_turns, 2)
        engine.finish_enemy_turn()
        self.assertEqual(engine.enemy.weak_turns, 1)


class TestUltimateSaveMigration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.manager = SaveManager(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_new_save_contains_default_ultimate_fields(self):
        data = self.manager.create_save("slot_1")
        progress = data["progresso"]
        self.assertEqual(progress["ultimate_equipada"], DEFAULT_ULTIMATE_ID)
        self.assertEqual(progress["ultimates_desbloqueadas"], known_ultimate_ids())

    def test_legacy_save_receives_default_ultimate(self):
        path = os.path.join(self.temp.name, "slot_1.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "versao": 2,
                "nome": "Legado",
                "progresso": {"andar": 2, "moedas": 10, "cartas": ["Golpe"]},
            }, f)
        loaded = self.manager.load_save("slot_1")
        progress = loaded["progresso"]
        self.assertEqual(progress["ultimate_equipada"], DEFAULT_ULTIMATE_ID)
        self.assertEqual(progress["ultimates_desbloqueadas"], known_ultimate_ids())


if __name__ == "__main__":
    unittest.main()
