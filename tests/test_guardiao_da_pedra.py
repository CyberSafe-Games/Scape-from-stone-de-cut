"""Chefe do primeiro território, animações e cenários próprios dos biomas."""
import os
from pathlib import Path
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import pygame

from src.core.asset_manager import AssetManager
from src.systems.combat_engine import CombatEngine
from src.systems.enemy_factory import (create_point_enemy, create_guardiao_da_pedra,
                                       create_road_enemy, choose_next_action)
from src.ui.entity_view import EntityView
from src.config.layout import ENEMY_X, PLAYER_X


class GuardiaoDaPedraTests(unittest.TestCase):
    def test_first_point_has_guardian_but_normal_encounters_keep_their_pool(self):
        boss = create_point_enemy(1)
        self.assertEqual(boss.name, 'Guardião da Pedra')
        self.assertTrue(boss.is_miniboss)
        self.assertEqual(boss.max_hp, 78)
        self.assertEqual(boss.actions_per_turn, 2)
        self.assertEqual(boss.special_interval, 8)
        self.assertEqual({a.visual_effect for a in boss.actions}, {'atk1', 'def', 'healer2'})
        self.assertEqual(boss.special_action.visual_effect, 'atk2')
        for name in ('Slime', 'Vinimuth'):
            with patch('src.systems.enemy_factory.random.choice', return_value=name):
                self.assertEqual(create_road_enemy(1).name, name)
        self.assertEqual(create_point_enemy(2).name, 'Goblin Nerd')
        self.assertEqual(create_point_enemy(5).name, 'Corpo Seco')

    def test_special_occurs_on_eighth_and_sixteenth_actions(self):
        engine = CombatEngine()
        engine.enemy = create_guardiao_da_pedra()
        engine.player.hp = engine.player.max_hp = 999
        choose_next_action(engine.enemy)
        names = []
        for i in range(16):
            if engine.state == 'player_turn': engine.end_turn()
            names.append(engine.enemy.current_action.name)
            engine.enemy_turn()
            self.assertEqual(engine.enemy.action_counter, i + 1)
            engine.finish_enemy_turn()
        self.assertEqual(names[7], 'Rugido Espiritual')
        self.assertEqual(names[15], 'Rugido Espiritual')
        self.assertTrue(all(name != 'Rugido Espiritual' for i, name in enumerate(names) if (i + 1) % 8))
        self.assertEqual(engine.player.turn_count, 9)

    def test_healing_caps_at_maximum_and_defense_uses_dedicated_animation(self):
        events = []
        engine = CombatEngine(on_event_callback=lambda event, **kw: events.append((event, kw)))
        engine.enemy = create_guardiao_da_pedra()
        heal = next(a for a in engine.enemy.actions if a.action_type == 'heal')
        engine.enemy.hp = 76
        engine.enemy.set_intent('heal', heal.value, heal)
        engine.end_turn()
        engine.enemy_turn()
        self.assertEqual(engine.enemy.hp, 78)
        self.assertIn(('enemy_action', {'action': 'healer2'}), events)
        engine.finish_enemy_turn()
        defend = next(a for a in engine.enemy.actions if a.action_type == 'defend')
        engine.enemy.set_intent('defend', defend.value, defend)
        engine.enemy_turn()
        self.assertEqual(engine.enemy.block, 8)
        self.assertIn(('enemy_action', {'action': 'def'}), events)

    def test_spirit_is_ranged_and_hit_flash_waits_for_arrival(self):
        view = EntityView(None)
        view.trigger_attack('enemy', 'atk2', 'Guardião da Pedra')
        view.trigger_flash('player')
        self.assertEqual(view.enemy_attack_duration, 1400)
        self.assertIsNone(view.get_enemy_projectile_pose())
        view.update(1400 * .6)
        start = view.get_enemy_projectile_pose()
        self.assertEqual(view.get_attack_pose('enemy', ENEMY_X, PLAYER_X)[0], ENEMY_X)
        view.update(1400 * .2)
        self.assertLess(view.get_enemy_projectile_pose()[0], start[0])
        self.assertEqual(view.player_flash, 0)
        view.update(1400 * .05)
        self.assertIsNone(view.get_enemy_projectile_pose())
        self.assertGreater(view.player_flash, 0)
        self.assertFalse(view.is_enemy_resolving_done())
        view.update(1400)
        self.assertTrue(view.is_enemy_resolving_done())

    def test_24_frames_are_rgba_uniform_and_aligned_at_feet(self):
        from PIL import Image
        root = Path(__file__).resolve().parents[1] / 'assets' / 'guardiao_da_pedra'
        for group in ('idle', 'atk1', 'atk2', 'def', 'healer2', 'dano'):
            for i in range(1, 5):
                with self.subTest(group=group, frame=i), Image.open(root / f'{group}_{i}.png') as frame:
                    self.assertEqual(frame.mode, 'RGBA')
                    self.assertEqual(frame.size, (448, 280))
                    self.assertEqual(frame.getpixel((0, 0))[3], 0)
                    alpha = frame.getchannel('A').point(lambda a: 255 if a > 60 else 0)
                    self.assertGreaterEqual(alpha.getbbox()[3], 274)
                    self.assertLessEqual(alpha.getbbox()[3], 280)
        with Image.open(root / 'urso_espiritual.png') as wave:
            self.assertEqual(wave.mode, 'RGBA')
            self.assertEqual(wave.size, (114, 120))

    def test_assets_load_correct_biomes_and_animate_guardian_without_affecting_player(self):
        was_initialized = pygame.get_init()
        pygame.init()
        if pygame.display.get_surface() is None: pygame.display.set_mode((1, 1))
        if not was_initialized: self.addCleanup(pygame.quit)
        assets = AssetManager()
        for level in (1, 2, 5):
            bg = assets.get_battle_background(level)
            self.assertEqual(bg.get_size(), (1280, 720))
            self.assertIsNot(bg, assets.background)
        self.assertNotEqual(pygame.image.tobytes(assets.get_battle_background(1), 'RGB'),
                            pygame.image.tobytes(assets.get_battle_background(5), 'RGB'))
        self.assertIs(assets.get_battle_background(7), assets.background)
        boss = create_guardiao_da_pedra()
        view = EntityView(assets)
        screen = pygame.Surface((1280, 720), pygame.SRCALPHA)
        for group in ('atk1', 'atk2'):
            view.trigger_attack('enemy', group, boss.name)
            view.update(view.enemy_attack_duration * .6)
            view.draw_enemy(screen, boss)
            view.draw_enemy_projectile(screen)
            self.assertIsNotNone(view.get_enemy_frame(boss))
            view.update(3000)
        frames = assets.get_enemy_sprite_group(boss.name, 'atk2')
        view.trigger_attack('enemy', 'atk2', boss.name)
        view.update(1400 * .6)
        self.assertIs(view.get_enemy_frame(boss), frames[3])
        view.update(3000)
        x, frame = view.get_player_frame('victory')
        self.assertEqual(x, PLAYER_X)
        self.assertIsInstance(frame, pygame.Surface)
