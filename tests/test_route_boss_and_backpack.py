"""Regressões da campanha 3 encontros/ponto, Corpo Seco e deck 3x fixo."""
import tempfile
import unittest
from unittest.mock import patch

from src.models.player import Player
from src.systems.save_manager import SaveManager, SaveCorruptedError
from src.systems.combat_engine import CombatEngine
from src.systems.enemy_factory import create_corpo_seco, create_road_enemy
from src.systems.campaign_progress import record_road_victory, record_victory
from src.systems.territory_map import TERRITORY_IDS, status
from src.systems.deck_loadout import equip_card_type, COPIES_PER_SLOT, SLOT_COUNT
from src.systems.shop_system import purchase_card


class RouteBossDeckTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.saves = SaveManager(self.folder.name)
        self.data = self.saves.create_save('slot_1')

    def tearDown(self):
        self.folder.cleanup()

    def _road_victory(self, level=1):
        engine = CombatEngine(map_mode=True)
        engine.resume_from_save(self.data, self.saves, level=level, encounter_kind='road')
        self.assertIn(engine.enemy.name, ('Slime', 'Vinimuth'))
        engine.state = 'victory'
        engine.skip_reward()
        self.assertEqual(engine.state, 'phase_complete')
        record_road_victory(self.saves, self.data, engine, lambda: None)

    def test_new_save_starts_with_zero_road_encounters(self):
        self.assertEqual(self.data['progresso']['encontros_por_territorio'], {})
        self.assertEqual(status(self.data, TERRITORY_IDS[0]), 'available')

    def test_three_road_encounters_then_point_fight_unlock(self):
        for i in range(3):
            self._road_victory()
            self.assertEqual(self.saves.load_save('slot_1')['progresso']['encontros_por_territorio'][TERRITORY_IDS[0]], i+1)
            self.assertEqual(status(self.data, TERRITORY_IDS[1]), 'locked')
        engine = CombatEngine(map_mode=True)
        engine.resume_from_save(self.data, self.saves, level=1)
        engine.state = 'victory'
        engine.skip_reward()
        record_victory(self.saves, self.data, engine, lambda: None)
        self.assertEqual(status(self.data, TERRITORY_IDS[0]), 'completed')
        self.assertEqual(status(self.data, TERRITORY_IDS[1]), 'available')
        self.assertEqual(self.data['progresso']['encontros_por_territorio'].get(TERRITORY_IDS[1], 0), 0)

    def test_point_cannot_unlock_before_road(self):
        engine = CombatEngine(map_mode=True)
        engine.state = 'victory'
        engine.skip_reward()
        with self.assertRaises(ValueError):
            record_victory(self.saves, self.data, engine, lambda: None)

    def test_road_cannot_be_counted_four_times(self):
        for _ in range(3):
            self._road_victory()
        with self.assertRaises(ValueError):
            self._road_victory()

    def test_legacy_save_preserves_open_point_battles(self):
        old = self.saves.create_save('slot_2')
        old['progresso'].pop('encontros_por_territorio', None)
        self.saves.save(old)
        self.assertEqual(self.saves.load_save('slot_2')['progresso']['encontros_por_territorio'][TERRITORY_IDS[0]], 3)

    def test_fortress_boss_and_other_road_enemies(self):
        self.assertEqual(create_corpo_seco(5).name, 'Corpo Seco')
        self.assertIn(create_road_enemy(5).name, ('Slime', 'Vinimuth'))
        self.data['progresso']['andar'] = 5
        e = CombatEngine(map_mode=True)
        e.resume_from_save(self.data, self.saves, level=5, encounter_kind='point')
        self.assertEqual(e.enemy.name, 'Corpo Seco')
        self.assertEqual(e.enemy.actions_per_turn, 2)
        e.resume_from_save(self.data, self.saves, level=5, encounter_kind='road')
        self.assertIn(e.enemy.name, ('Slime', 'Vinimuth'))

    def test_boss_gets_two_actions_and_spins_every_eight_actions(self):
        e = CombatEngine(map_mode=True)
        e.resume_from_save(self.data, self.saves, level=5, encounter_kind='point')
        e.player.hp = 999
        e.player.max_hp = 999
        action_names = []
        for i in range(16):
            if e.state == 'player_turn':
                e.end_turn()
            action_names.append(e.enemy.current_action.name)
            e.enemy_turn()
            self.assertEqual(e.enemy.action_counter, i+1)
            if i % 2 == 0:
                self.assertEqual(e.enemy_actions_remaining, 1)
            else:
                self.assertEqual(e.enemy_actions_remaining, 0)
            e.finish_enemy_turn()
        self.assertEqual(action_names[7], 'Ataque Giratório')
        self.assertEqual(action_names[15], 'Ataque Giratório')
        self.assertEqual(e.player.turn_count, 9)
        self.assertTrue(all(name != 'Ataque Giratório' for i, name in enumerate(action_names) if (i+1) % 8 != 0))

    def test_normal_enemy_one_action(self):
        e = CombatEngine(map_mode=True)
        e.resume_from_save(self.data, self.saves, level=1, encounter_kind='road')
        e.end_turn()
        e.enemy_turn()
        self.assertEqual(e.enemy_actions_remaining, 0)
        e.finish_enemy_turn()
        self.assertEqual(e.state, 'player_turn')

    def test_initial_deck_three_copies_per_type(self):
        p = self.data['progresso']
        self.assertEqual(p['deck_slots'], ['Soco Simples', 'Esfera Protetora', None, None, None, None])
        self.assertEqual(p['cartas'].count('Soco Simples'), 3)
        self.assertEqual(p['cartas'].count('Esfera Protetora'), 3)
        self.assertEqual(len(p['deck_slots']), SLOT_COUNT)

    def test_purchase_collect_then_equip_three(self):
        self.data['progresso']['moedas'] = 1000
        self.assertTrue(purchase_card(self.saves, self.data, 'Investida').success)
        self.assertNotIn('Investida', self.data['progresso']['cartas'])
        result = equip_card_type(self.saves, self.data, 2, 'Investida')
        self.assertTrue(result[0])
        saved = self.saves.load_save('slot_1')['progresso']
        self.assertEqual(saved['cartas'].count('Investida'), COPIES_PER_SLOT)
        self.assertFalse(equip_card_type(self.saves, self.data, 3, 'Investida')[0])
        self.assertFalse(equip_card_type(self.saves, self.data, 4, 'Fúria')[0])
        self.assertTrue(equip_card_type(self.saves, self.data, 2, None)[0])
        self.assertEqual(self.data['progresso']['cartas'].count('Investida'), 0)

    def test_equip_must_leave_one_type(self):
        self.assertTrue(equip_card_type(self.saves, self.data, 1, None)[0])
        self.assertFalse(equip_card_type(self.saves, self.data, 0, None)[0])
        self.assertEqual(self.data['progresso']['cartas'], ['Soco Simples']*3)

    def test_bad_encounter_counter_rejected(self):
        for value in (4, -1, True, '3'):
            self.data['progresso']['encontros_por_territorio'] = {TERRITORY_IDS[0]: value}
            with self.assertRaises(SaveCorruptedError):
                self.saves.save(self.data)


if __name__ == '__main__':
    unittest.main()
