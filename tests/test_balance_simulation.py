"""Assegura que a simulação usa recursos reais e não altera sorteios do jogo."""
from collections import Counter
import random
import tempfile
import unittest

from devtools.simulate_roguelite_balance import prepared_slots, prepare_shop, play_turn, upgrade_targets
from src.systems.save_manager import SaveManager
from src.systems.combat_engine import CombatEngine


class BalanceSimulationTests(unittest.TestCase):
    def test_every_strategy_keeps_starter_attack_when_only_support_owned(self):
        p = {'cartas_colecao': ['Soco Simples', 'Esfera Protetora', 'Poção de Cura']}
        for strategy in ('dano_aura', 'defesa_cura', 'veneno_sangramento'):
            slots = prepared_slots(p, strategy)
            self.assertEqual(len(slots), 18)
            self.assertIn('Soco Simples', slots)
            self.assertGreaterEqual(sum(n is not None for n in slots), 6)
            self.assertTrue(all(n in p['cartas_colecao'] for n in slots if n))
            self.assertTrue(all(v <= 3 for n, v in Counter(slots).items() if n))

    def test_preparation_pays_for_healing_and_does_not_grant_permanent_bonus(self):
        with tempfile.TemporaryDirectory() as folder:
            manager = SaveManager(folder)
            data = manager.create_save('bot')
            data['progresso'].update(moedas=30, vida=20)
            purchases = prepare_shop(manager, data, 'dano_aura', 1, False)
            self.assertEqual(data['progresso']['vida'], 40)
            self.assertEqual(data['progresso']['moedas'], 0)
            self.assertEqual(purchases, [{'tipo': 'cura', 'valor': 20, 'ouro': 30}])
            self.assertEqual(data['perfil']['vida'], 0)
            self.assertEqual(data['perfil']['energia'], 0)
            self.assertEqual(data['progresso']['upgrades_purchased'], 0)

    def test_exploratory_turns_do_not_consume_future_randomness(self):
        engine = CombatEngine()
        engine.player.energy = 0
        engine.deck_manager.hand = []
        engine.enemy.hp = engine.enemy.max_hp = 999
        engine.player.hp = engine.player.max_hp = 999
        before = random.getstate()
        play_turn(engine)
        self.assertEqual(random.getstate(), before)
        self.assertEqual(engine.state, 'enemy_turn')

    def test_upgrade_targets_do_not_waste_materials_on_unequipped_aura(self):
        with tempfile.TemporaryDirectory() as folder:
            manager = SaveManager(folder)
            data = manager.create_save('bot')
            p = data['progresso']
            p['cartas_colecao'].append('Aura Rubra')
            manager.save(data)
            aura = next(c for c in p['copies'] if c['name'] == 'Aura Rubra')
            aura['level'] = 2
            p['upgrades_purchased'] = 1
            manager.save(data)
            self.assertFalse(any(c['name'] == 'Aura Rubra' for c in upgrade_targets(p, 'dano_aura')))
