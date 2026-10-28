"""Distribuição, ações de combate e integração visual dos habitantes do mapa."""
import os
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import pygame

from src.systems.normal_enemy_catalog import BIOME_ENEMIES, NORMAL_SPRITES, NORMAL_RANGED
from src.systems.enemy_factory import create_road_enemy, create_point_enemy
from src.systems.combat_engine import CombatEngine
from src.core.asset_manager import AssetManager
from src.ui.entity_view import EntityView
from src.config.layout import ENEMY_X, PLAYER_X


class NormalBestiaryTests(unittest.TestCase):
    def test_thirteen_unique_types_follow_the_requested_biome_distribution(self):
        self.assertEqual([len(pool) for pool in BIOME_ENEMIES.values()], [1, 2, 2, 2, 2, 2, 2])
        names = [name for pool in BIOME_ENEMIES.values() for name in pool]
        self.assertEqual(len(set(names)), 13)
        self.assertEqual(set(names), set(NORMAL_SPRITES) | {'Slime', 'Vinimuth'})
        for level, pool in BIOME_ENEMIES.items():
            for name in pool:
                with self.subTest(level=level, name=name):
                    with patch('src.systems.enemy_factory.random.choice', return_value=name) as choose:
                        enemy = create_road_enemy(level)
                    choose.assert_called_once_with(pool)
                    self.assertEqual(enemy.name, name)
                    self.assertFalse(enemy.is_miniboss)
                    self.assertEqual(sum(a.weight for a in enemy.actions), 1)
                    self.assertTrue(all(a.energy_cost <= enemy.max_energy for a in enemy.actions))

    def test_every_new_action_resolves_in_the_real_combat_engine(self):
        for level, pool in BIOME_ENEMIES.items():
            for name in pool:
                with patch('src.systems.enemy_factory.random.choice', return_value=name):
                    enemy = create_road_enemy(level)
                for action in enemy.actions:
                    with self.subTest(name=name, action=action.name):
                        engine = CombatEngine()
                        engine.enemy = enemy
                        enemy.hp = max(1, enemy.max_hp-20)
                        enemy.reset_energy()
                        enemy.block = 0
                        engine.player.hp = engine.player.max_hp = 999
                        engine.end_turn()
                        enemy.set_intent(action.action_type, action.value, action)
                        hp, enemy_hp = engine.player.hp, enemy.hp
                        engine.enemy_turn()
                        if action.action_type == 'attack':
                            self.assertLess(engine.player.hp, hp)
                            if action.status_effect:
                                self.assertIn(action.status_effect[0], engine.player.statuses)
                        elif action.action_type == 'heal':
                            self.assertGreater(enemy.hp, enemy_hp)
                        else:
                            self.assertGreater(enemy.block, 0)

    def test_existing_territorial_bosses_are_preserved(self):
        for level, name in ((1, 'Guardião da Pedra'), (3, 'Goblin Nerd'),
                            (5, 'Corpo Seco'), (6, 'Carrasco da Vigília')):
            self.assertEqual(create_point_enemy(level).name, name)

    def test_all_sprite_groups_and_projectiles_load_and_render_without_clipping(self):
        was_initialized = pygame.get_init()
        pygame.init()
        pygame.display.set_mode((1, 1))
        if not was_initialized:
            self.addCleanup(pygame.quit)
        assets = AssetManager()
        root = Path(__file__).resolve().parents[1] / 'assets' / 'enemies'
        for name, (slug, groups, _, _) in NORMAL_SPRITES.items():
            for group in groups:
                frames = assets.get_enemy_sprite_group(name, group)
                self.assertEqual(len(frames), 4, (name, group))
                for i, frame in enumerate(frames, 1):
                    with self.subTest(name=name, group=group, frame=i):
                        self.assertTrue((root/slug/f'{group}_{i}.png').is_file())
                        rect = frame.get_bounding_rect()
                        self.assertGreater(rect.width, 20)
                        self.assertGreater(rect.height, 20)
                        self.assertGreater(rect.left, 0)
                        self.assertLess(rect.right, frame.get_width())
                        self.assertLess(rect.bottom, frame.get_height())
                        self.assertEqual(frame.get_at((0, 0)).a, 0)
        for name, attacks in NORMAL_RANGED.items():
            for group, (duration, launch, impact) in attacks.items():
                with self.subTest(name=name, action=group):
                    view = EntityView(assets)
                    view.trigger_attack('enemy', group, name)
                    view.trigger_flash('player')
                    view.update(duration*(launch+impact)/2)
                    self.assertEqual(view.get_attack_pose('enemy', ENEMY_X, PLAYER_X)[0], ENEMY_X)
                    self.assertIsNotNone(view.get_enemy_projectile_pose())
                    screen = pygame.Surface((1280, 720), pygame.SRCALPHA)
                    view.draw_enemy_projectile(screen)
                    self.assertGreater(screen.get_bounding_rect().width, 10)
                    self.assertEqual(view.player_flash, 0)
                    view.update(duration*(impact-launch)/2+1)
                    self.assertIsNone(view.get_enemy_projectile_pose())
                    self.assertGreater(view.player_flash, 0)
