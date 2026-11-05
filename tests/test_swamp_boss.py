"""Guardião do Pântano, guarda, sangramento e ultimate corpo a corpo."""
import os
import unittest
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
from src.core.asset_manager import AssetManager
from src.systems.enemy_factory import create_gordofera, create_point_enemy, create_road_enemy, choose_next_action
from src.systems.combat_engine import CombatEngine
from src.systems.boss_ultimate_animations import boss_ultimate_pose
from src.ui.entity_view import EntityView
from src.config.layout import ENEMY_X, PLAYER_X


class SwampBossTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.assets = AssetManager()

    def engine(self):
        engine = CombatEngine(map_mode=True)
        engine.enemy = create_gordofera()
        engine.player.hp = engine.player.max_hp = 250
        return engine

    def test_last_missing_boss_is_assigned_to_swamp_only(self):
        boss = create_point_enemy(4)
        self.assertEqual(boss.boss_id, 'gordofera')
        self.assertTrue(boss.is_miniboss)
        self.assertEqual(boss.max_hp, 116)
        self.assertEqual(boss.actions_per_turn, 2)
        self.assertFalse(getattr(boss, 'is_final_boss', False))
        self.assertEqual(create_point_enemy(7).name, 'Zanzara')
        self.assertNotEqual(create_road_enemy(4).name, boss.name)
        for level in range(1, 8):
            self.assertTrue(create_point_enemy(level).is_miniboss, level)

    def test_crossed_guard_adds_shield_without_attacking(self):
        engine = self.engine()
        engine.end_turn()
        boss = engine.enemy
        guard = next(a for a in boss.actions if a.action_type == 'defend')
        boss.set_intent(guard.action_type, guard.value, guard)
        hp = engine.player.hp
        engine.enemy_turn()
        self.assertEqual(engine.player.hp, hp)
        self.assertEqual(boss.block, 10)
        self.assertEqual(boss.block_turns, 2)

    def test_claws_apply_bleed_once_per_attack_turn(self):
        engine = self.engine()
        engine.end_turn()
        attack = engine.enemy.actions[0]
        engine.enemy.set_intent('attack', attack.damage, attack)
        engine.enemy_turn()
        self.assertEqual(engine.player.statuses['bleed'], {'turns': 2, 'potency': 4})
        hp = engine.player.hp
        self.assertEqual(engine.player.on_attack(), 4)
        self.assertEqual(engine.player.on_attack(), 0)
        self.assertEqual(engine.player.hp, hp-4)

    def test_ultimate_leaps_toward_player_and_closes_on_ready(self):
        boss = create_gordofera()
        boss.action_counter = 7
        choose_next_action(boss)
        self.assertIs(boss.current_action, boss.special_action)
        view = EntityView(self.assets)
        view.trigger_attack('enemy', boss.special_action.visual_effect, boss.name, ultimate=True)
        spec = view.enemy_ultimate
        self.assertEqual(spec.mode, 'tremor')
        view.attack_timer = spec.duration*spec.impact
        self.assertIs(view.get_enemy_frame(boss), self.assets.get_boss_ultimate_sprites(boss.name)[5])
        view.attack_timer = 0
        x, lift = boss_ultimate_pose(spec, .38, ENEMY_X, PLAYER_X+105)
        self.assertLess(x, ENEMY_X)
        self.assertGreater(lift, 40)
        self.assertIsNone(view.enemy_ranged_attack)
        view.update(spec.duration+1)
        self.assertIs(view.get_enemy_frame(boss), self.assets.get_enemy_sprite_group(boss.name, 'idle')[0])

    def test_real_guard_animation_uses_all_eight_frames(self):
        boss = create_gordofera()
        view = EntityView(self.assets)
        view.trigger_enemy_action('def', boss.name)
        frames = self.assets.get_enemy_sprite_group(boss.name, 'def')
        self.assertEqual(len(frames), 8)
        for i, frame in enumerate(frames):
            view.enemy_action_timer = view.enemy_action_duration*(i+.1)/8
            self.assertIs(view.get_enemy_frame(boss), frame)
