"""Boss final, amuleto restaurador, projéteis e conclusão do Santuário."""
import os
import unittest
from unittest.mock import MagicMock
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
from src.systems.enemy_factory import create_zanzara, create_point_enemy, create_road_enemy, choose_next_action
from src.systems.combat_engine import CombatEngine
from src.core.asset_manager import AssetManager
from src.ui.entity_view import EntityView
from src.config.layout import ENEMY_X, PLAYER_X
from src.systems.boss_ultimate_animations import BOSS_ULTIMATE_ANIMATIONS
from src.ui.zanzara_fx import draw_zanzara_fx


class ZanzaraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.assets = AssetManager()

    def test_final_boss_occupies_only_the_final_point(self):
        boss = create_point_enemy(7)
        self.assertEqual(boss.name, 'Zanzara')
        self.assertEqual(boss.boss_id, 'zanzara')
        self.assertTrue(boss.is_final_boss)
        self.assertTrue(boss.is_miniboss)
        self.assertEqual(boss.max_hp, 190)
        self.assertEqual(boss.actions_per_turn, 2)
        for level in range(1, 7):
            self.assertNotEqual(create_point_enemy(level).name, 'Zanzara')
        self.assertNotEqual(create_road_enemy(7).name, 'Zanzara')

    def test_amulet_heals_and_refreshes_temporary_power_without_hitting_player(self):
        boss = create_zanzara()
        boss.hp -= 10
        action = next(a for a in boss.actions if a.action_type == 'buff')
        target = MagicMock()
        context = MagicMock()
        result = action.effect.apply(action, boss, target, context)
        self.assertEqual(result['heal'], 10)
        self.assertEqual(boss.hp, boss.max_hp)
        self.assertEqual(boss.statuses['aura']['potency'], 4)
        action.effect.apply(action, boss, target, context)
        self.assertEqual(boss.statuses['aura']['potency'], 4)
        self.assertEqual(boss.statuses['aura']['turns'], 2)
        target.take_damage.assert_not_called()
        context.trigger_attack.assert_not_called()
        context.trigger_enemy_action.assert_called_with('healer2')

    def test_two_ranged_attacks_stay_home_and_fly_left(self):
        for action in ('atk2', 'atk3'):
            view = EntityView(self.assets)
            view.trigger_attack('enemy', action, 'Zanzara')
            duration, release, impact = view.enemy_ranged_attack
            view.attack_timer = duration*(release+(impact-release)*.25)
            first = view.get_enemy_projectile_pose()
            self.assertEqual(view.get_attack_pose('enemy', ENEMY_X, PLAYER_X)[0], ENEMY_X)
            view.attack_timer += 50
            self.assertLess(view.get_enemy_projectile_pose()[0], first[0])
            images = [self.assets.get_enemy_projectile('Zanzara', action, i) for i in range(4)]
            self.assertTrue(all(im is not None for im in images))
            self.assertEqual(len({pygame.image.tobytes(im, 'RGBA') for im in images}), 4)
            screen = pygame.Surface((1280, 720), pygame.SRCALPHA)
            draw_zanzara_fx(screen, view)
            self.assertGreater(screen.get_bounding_rect().width, 20)

    def test_special_uses_dedicated_poses_and_ends_with_final_victory(self):
        boss = create_zanzara()
        boss.action_counter = 7
        choose_next_action(boss)
        self.assertIs(boss.current_action, boss.special_action)
        view = EntityView(self.assets)
        view.trigger_attack('enemy', 'atk3', boss.name, ultimate=True)
        self.assertIs(view.enemy_ultimate, BOSS_ULTIMATE_ANIMATIONS['zanzara'])
        self.assertEqual(len(self.assets.get_boss_ultimate_sprites('Zanzara')), 12)
        self.assertEqual(len(self.assets.get_boss_ultimate_sprites('Zanzara', effects=True)), 12)
        engine = CombatEngine()
        engine.enemy = boss
        boss.hp = 0
        engine._on_enemy_defeated()
        self.assertEqual(engine.state, 'victory')

    def test_map_resume_starts_zanzara_and_finishes_level_seven(self):
        from src.systems.save_manager import SaveManager
        saves = SaveManager()
        data = saves._new_data('Teste', 'test')
        events = []
        engine = CombatEngine(map_mode=True, on_event_callback=lambda event, **payload: events.append((event, payload)))
        engine.resume_from_save(data, saves, level=7, encounter_kind='point')
        self.assertEqual(engine.enemy.name, 'Zanzara')
        self.assertEqual(engine.level, 7)
        engine.enemy.hp = 0
        engine._on_enemy_defeated()
        engine.finish_map_phase()
        self.assertEqual(engine.state, 'phase_complete')
        self.assertIn(('phase_complete', {'level': 7}), events)
