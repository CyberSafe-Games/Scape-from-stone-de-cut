"""Compatibilidade dos debuffs de Zanzara com os novos Totens da main."""
import unittest
from src.systems.combat_engine import CombatEngine
from src.systems.enemy_factory import create_zanzara

class TestMergedZanzaraTotems(unittest.TestCase):
    def execute(self, index, trigger=None):
        engine = CombatEngine()
        engine.enemy = create_zanzara()
        engine.player.hp = 40
        if trigger:
            engine.player.apply_status('totem', 2, 1)
            engine.player.statuses['totem']['trigger'] = trigger
        action = engine.enemy.actions[index]
        engine.enemy.set_intent('attack', action.damage, action)
        engine.enemy_actions_remaining = 1
        engine.state = 'enemy_turn'
        engine.enemy_turn()
        return engine

    def test_poison_totem_blocks_both_scythe_debuffs_and_retaliates(self):
        engine = self.execute(0, 'poison')
        self.assertEqual(engine.player.hp, 40)
        self.assertNotIn('bleed', engine.player.statuses)
        self.assertNotIn('poison', engine.player.statuses)
        self.assertEqual(engine.enemy.statuses['poison']['potency'], 5)
        self.assertNotIn('totem', engine.player.statuses)

    def test_healing_totem_still_blocks_chains_vulnerability(self):
        engine = self.execute(2, 'heal')
        self.assertEqual(engine.player.hp, 48)
        self.assertNotIn('vulnerable', engine.player.statuses)

    def test_unprotected_scythe_keeps_two_debuffs(self):
        engine = self.execute(0)
        self.assertEqual(engine.player.hp, 20)
        self.assertEqual(engine.player.statuses['bleed']['potency'], 5)
        self.assertEqual(engine.player.statuses['poison']['potency'], 3)
