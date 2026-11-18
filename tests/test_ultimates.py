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

    def test_mana_restores_energy_and_cleanses_without_drawing(self):
        engine = CombatEngine()
        engine.player.energy = 5
        engine.player.ultimate_charge = engine.player.ultimate_threshold
        engine.deck_manager.draw_pile.extend([engine.hand[0].copy() for _ in range(5)])
        hand_before = len(engine.hand)
        piles_before = [list(pile) for pile in (engine.deck_manager.hand,
            engine.deck_manager.draw_pile, engine.deck_manager.discard_pile)]
        engine.player.add_stacks('poison', 2)
        engine.player.add_stacks('bleed', 1)
        engine.player.apply_status('vulnerable', 2, 25)
        self.assertTrue(engine.activate_ultimate())
        self.assertEqual(engine.energy, engine.player.MAX_ENERGY_LIMIT)
        self.assertEqual(len(engine.hand), hand_before)
        self.assertEqual(piles_before, [list(pile) for pile in (engine.deck_manager.hand,
            engine.deck_manager.draw_pile, engine.deck_manager.discard_pile)])
        self.assertEqual(engine.player.poison_stacks, 0)
        self.assertEqual(engine.player.bleed_stacks, 0)
        self.assertNotIn('vulnerable', engine.player.statuses)
        self.assertEqual(engine.player.ultimate_charge, 0)

    def test_twin_axes_cost_prevents_two_hits_with_eight_energy(self):
        from src.systems.roguelite import instance_card
        for level, damage in ((1, 40), (2, 50)):
            with self.subTest(level=level):
                engine = CombatEngine()
                card = instance_card({'id': 'axes-test', 'name': 'Machados Gêmeos', 'level': level})
                self.assertEqual(card.cost, 5)
                self.assertEqual(card.value, damage)
                engine.deck_manager.hand = [card, card.copy()]
                engine.enemy.hp = engine.enemy.max_hp = 300
                engine.player.energy = 8
                self.assertTrue(engine.play_card(0))
                self.assertEqual(engine.enemy.hp, 300 - damage)
                self.assertEqual(engine.energy, 3)
                self.assertFalse(engine.play_card(0))
                self.assertEqual(engine.player.ultimate_charge, 5)

    def test_forcas_ancestrais_grants_strength_and_block(self):
        engine = CombatEngine()
        engine.player.unlock_ultimate("forcas_ancestrais")
        self.assertTrue(engine.equip_ultimate("forcas_ancestrais"))
        engine.player.energy = 8
        engine.player.ultimate_charge = engine.player.ultimate_threshold
        self.assertTrue(engine.activate_ultimate())
        self.assertEqual(engine.player.strength, 12)
        self.assertEqual(engine.player.block, 40)
        self.assertEqual(engine.energy, 3)

    def test_rugido_applies_weakness_for_three_full_enemy_turns(self):
        engine = CombatEngine()
        engine.player.unlock_ultimate("rugido_da_floresta")
        self.assertTrue(engine.equip_ultimate("rugido_da_floresta"))
        engine.player.energy = 7
        engine.player.ultimate_charge = engine.player.ultimate_threshold
        engine.enemy.hp = engine.enemy.max_hp = 200
        target_hp = engine.enemy.hp
        self.assertTrue(engine.activate_ultimate())
        self.assertEqual(engine.energy, 2)
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


    def test_insufficient_energy_preserves_charge_and_effects_for_all_specials(self):
        for ultimate in known_ultimate_ids():
            with self.subTest(ultimate=ultimate):
                engine = CombatEngine()
                engine.equip_ultimate(ultimate)
                engine.player.ultimate_charge = 20
                engine.player.energy = 4
                before = (engine.enemy.hp, engine.player.strength, engine.player.block, len(engine.hand))
                self.assertFalse(engine.activate_ultimate())
                self.assertEqual(engine.player.ultimate_charge, 20)
                self.assertEqual(engine.energy, 4)
                self.assertEqual(before, (engine.enemy.hp, engine.player.strength, engine.player.block, len(engine.hand)))
                engine.end_turn()
                while engine.state in ('enemy_turn', 'enemy_resolving'):
                    if engine.state == 'enemy_turn':
                        engine.enemy_turn()
                    else:
                        engine.finish_enemy_turn()
                self.assertEqual(engine.player.ultimate_charge, 20)
                engine.player.energy = 5
                self.assertTrue(engine.activate_ultimate())
                self.assertEqual(engine.player.ultimate_charge, 0)
                self.assertEqual(engine.energy, 8 if ultimate == 'mana_ancestral' else 0)
                self.assertFalse(engine.activate_ultimate())

    def test_incomplete_charge_or_wrong_turn_does_not_spend_energy(self):
        engine = CombatEngine()
        engine.player.energy = 8
        engine.player.ultimate_charge = 19
        self.assertFalse(engine.activate_ultimate())
        self.assertEqual(engine.energy, 8)
        engine.player.ultimate_charge = 20
        engine.state = 'enemy_turn'
        self.assertFalse(engine.activate_ultimate())
        self.assertEqual(engine.energy, 8)
        self.assertEqual(engine.player.ultimate_charge, 20)


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
