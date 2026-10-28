"""Cobertura do chefe exclusivo das Ruínas Ancestrais e dos recursos existentes."""
from pathlib import Path
import tempfile
import unittest

from src.systems.combat_engine import CombatEngine
from src.systems.enemy_factory import create_goblin_nerd, create_point_enemy
from src.systems.save_manager import SaveManager


class RuinasAncestraisBossTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.saves = SaveManager(self.folder.name)
        self.data = self.saves.create_save('slot_1')
        self.data['progresso']['andar'] = 3

    def tearDown(self):
        self.folder.cleanup()

    def test_level_three_point_encounter_uses_goblin_nerd(self):
        engine = CombatEngine(map_mode=True)
        engine.resume_from_save(self.data, self.saves, level=3, encounter_kind='point')
        self.assertEqual(engine.enemy.name, 'Goblin Nerd')
        self.assertEqual(engine.enemy.actions_per_turn, 2)
        self.assertEqual(create_point_enemy(3).name, 'Goblin Nerd')

    def test_mata_sombria_no_longer_uses_goblin_nerd(self):
        self.assertNotEqual(create_point_enemy(2).name, 'Goblin Nerd')

    def test_goblin_special_triggers_every_eight_actions(self):
        engine = CombatEngine(map_mode=True)
        engine.resume_from_save(self.data, self.saves, level=3, encounter_kind='point')
        engine.player.hp = 999
        engine.player.max_hp = 999
        names = []
        for i in range(8):
            if engine.state == 'player_turn':
                engine.end_turn()
            names.append(engine.enemy.current_action.name)
            engine.enemy_turn()
            engine.finish_enemy_turn()
        self.assertEqual(names[7], 'Descarga Sobrecarregada')

    def test_assets_for_goblin_and_mata_background_exist(self):
        assets = Path(__file__).resolve().parents[1] / 'assets'
        self.assertTrue((assets / 'background_mata_sombria.png').is_file())
        goblin_dir = assets / 'goblin_nerd'
        for group in ('idle', 'dano', 'atk1', 'atk2', 'atk3', 'healer2'):
            files = sorted(goblin_dir.glob(f'{group}_*.png'))
            self.assertEqual(len(files), 4, group)

    def test_create_goblin_nerd_stats(self):
        boss = create_goblin_nerd(3)
        self.assertTrue(boss.is_miniboss)
        self.assertEqual(boss.max_energy, 4)
        self.assertEqual(boss.special_interval, 8)


if __name__ == '__main__':
    unittest.main()
