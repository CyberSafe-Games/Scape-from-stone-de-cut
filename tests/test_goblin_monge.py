"""Integração do inimigo comum e da onda de energia."""
import os
from pathlib import Path
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import pygame

from src.core.asset_manager import AssetManager
from src.systems.enemy_factory import create_road_enemy, create_enemy
from src.systems.normal_enemy_catalog import biome_enemy_names
from src.ui.entity_view import EntityView
from src.config.layout import ENEMY_X, PLAYER_X, APPROACH_GAP


class GoblinMongeTests(unittest.TestCase):
    def test_biome_encounters_can_be_selected_at_every_level(self):
        for level in (1, 2, 5, 7):
            for name in biome_enemy_names(level):
                with self.subTest(level=level, name=name):
                    with patch('src.systems.enemy_factory.random.choice', return_value=name):
                        enemy = create_road_enemy(level)
                    self.assertEqual(enemy.name, name)
                    self.assertFalse(enemy.is_miniboss)
                    self.assertEqual(enemy.max_energy, 3)
                    self.assertTrue(enemy.actions)
                    if name == 'Vinimuth':
                        self.assertEqual({a.visual_effect for a in enemy.actions}, {'atk1', 'atk2'})

    def test_legacy_normal_pool_has_animated_actions_too(self):
        with patch('src.systems.enemy_factory.random.choice', return_value=('Vinimuth', 22, 5)):
            enemy = create_enemy(2)
        self.assertEqual(enemy.max_hp, 32)
        self.assertEqual(len(enemy.actions), 2)

    def test_melee_approaches_but_wave_waits_for_release_and_impact(self):
        view = EntityView(None)
        view.trigger_attack('enemy', 'atk1', 'Vinimuth')
        view.update(view.enemy_attack_duration / 2)
        self.assertEqual(view.get_attack_pose('enemy', ENEMY_X, PLAYER_X + APPROACH_GAP)[0], PLAYER_X + APPROACH_GAP)
        view.trigger_attack('enemy', 'atk2', 'Vinimuth')
        view.trigger_flash('player')
        duration, launch, impact = view.enemy_ranged_attack
        view.update(duration * launch - 1)
        self.assertIsNone(view.get_enemy_projectile_pose())
        view.update(2)
        start = view.get_enemy_projectile_pose()
        self.assertEqual(view.get_attack_pose('enemy', ENEMY_X, PLAYER_X)[0], ENEMY_X)
        view.update(duration * (impact - launch) - 2)
        end = view.get_enemy_projectile_pose()
        self.assertGreater(start[0], end[0])
        self.assertEqual(view.player_flash, 0)
        view.update(2)
        self.assertIsNone(view.get_enemy_projectile_pose())
        self.assertGreater(view.player_flash, 0)
        self.assertFalse(view.is_enemy_resolving_done())
        view.update(duration)
        self.assertTrue(view.is_enemy_resolving_done())

    def test_assets_load_with_alpha_and_render_wave_in_battle(self):
        was_initialized = pygame.get_init()
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((1, 1))
        if not was_initialized:
            self.addCleanup(pygame.quit)
        assets = AssetManager()
        root = Path(__file__).resolve().parents[1] / 'assets' / 'goblin_monge'
        for group in ('idle', 'dano', 'atk1', 'atk2'):
            frames = assets.get_enemy_sprite_group('Vinimuth', group)
            self.assertEqual(len(frames), 4)
            for frame in frames:
                self.assertEqual(frame.get_size(), (240, 180))
                self.assertEqual(frame.get_at((0, 0)).a, 0)
                bounds = frame.get_bounding_rect(min_alpha=50)
                self.assertLessEqual(bounds.bottom, 177)
                self.assertGreaterEqual(bounds.bottom, 170)
            self.assertEqual(len(list(root.glob(f'{group}_*.png'))), 4)
        with patch('src.systems.enemy_factory.random.choice', return_value='Vinimuth'):
            enemy = create_road_enemy(7)
        view = EntityView(assets)
        view.trigger_attack('enemy', 'atk2', enemy.name)
        view.update(1200 * 0.7)
        screen = pygame.Surface((1280, 720), pygame.SRCALPHA)
        view.draw_enemy(screen, enemy)
        pose = view.get_enemy_projectile_pose()
        before = screen.copy()
        view.draw_enemy_projectile(screen)
        area = pygame.Rect(round(pose[0]) - 40, round(pose[1]) - 45, 80, 90)
        self.assertNotEqual(pygame.image.tobytes(before.subsurface(area), 'RGBA'),
                            pygame.image.tobytes(screen.subsurface(area), 'RGBA'))
        view.update(1200)
        self.assertIsNone(view.get_enemy_projectile_pose())
