"""Poses completas, transparência e sincronização dos inimigos comuns."""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
from src.core.asset_manager import AssetManager
from src.scenes.battle_scene import BattleScene
from src.systems.common_animation_kits import COMMON_KITS
from src.systems.normal_enemy_catalog import BIOME_ENEMIES
from src.systems.enemy_factory import create_road_enemy, choose_next_action
from src.ui.entity_view import EntityView
from src.config.layout import FLASH_DURATION


class CommonEightFramesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.assets = AssetManager()

    def test_all_13_kits_have_distinct_transparent_poses_and_close_on_idle(self):
        self.assertEqual(len(COMMON_KITS), 13)
        for name, (_, groups) in COMMON_KITS.items():
            idle = self.assets.get_enemy_sprite_group(name, 'idle')[0]
            for group in groups:
                with self.subTest(name=name, group=group):
                    frames = self.assets.get_enemy_sprite_group(name, group)
                    self.assertEqual(len(frames), 8)
                    self.assertGreaterEqual(len({pygame.image.tobytes(f, 'RGBA') for f in frames}), 7)
                    self.assertEqual(pygame.image.tobytes(frames[-1], 'RGBA'), pygame.image.tobytes(idle, 'RGBA'))
                    for frame in frames:
                        self.assertEqual(frame.get_size(), (448, 260))
                        bounds = frame.get_bounding_rect(min_alpha=40)
                        self.assertGreater(bounds.left, 0)
                        self.assertLess(bounds.right, 448)
                        self.assertLessEqual(bounds.bottom, 258)
                        self.assertGreater(bounds.height, 20)
                        self.assertEqual(frame.get_at((0, 0)).a, 0)

    def test_each_action_reaches_all_eight_frames_and_resets_idle(self):
        for name, (_, groups) in COMMON_KITS.items():
            enemy = SimpleNamespace(name=name)
            for group in groups:
                with self.subTest(name=name, group=group):
                    view = EntityView(self.assets)
                    frames = self.assets.get_enemy_sprite_group(name, group)
                    if group.startswith('atk'):
                        view.trigger_attack('enemy', group, name)
                    elif group in ('def', 'healer2'):
                        view.trigger_enemy_action(group, name)
                    seen = set()
                    for i in range(1000):
                        p = i / 1000
                        if group == 'idle': view.enemy_idle_timer = p * 8 * 180
                        elif group == 'dano': view.enemy_flash = FLASH_DURATION * (1-p)
                        elif group.startswith('atk'): view.attack_timer = p * view.enemy_attack_duration
                        else: view.enemy_action_timer = p * view.enemy_action_duration
                        frame = view.get_enemy_frame(enemy)
                        seen.add(next(j for j, f in enumerate(frames) if f is frame))
                    self.assertEqual(seen, set(range(8)))
                    view.update(5000)
                    if group != 'idle':
                        self.assertIs(view.get_enemy_frame(enemy), self.assets.get_enemy_sprite_group(name, 'idle')[0])

    def test_damage_and_hud_wait_for_the_actual_melee_or_projectile_impact(self):
        window = SimpleNamespace(get_virtual_mouse_pos=lambda: (-1,-1), draw_fullscreen_button=lambda *_: None)
        for level, names in BIOME_ENEMIES.items():
            for name in names:
                with patch('src.systems.enemy_factory.random.choice', return_value=name):
                    enemy = create_road_enemy(level)
                for action in enemy.actions:
                    if action.action_type != 'attack': continue
                    with self.subTest(name=name, action=action.name):
                        scene = BattleScene(None, window, self.assets)
                        scene.engine.enemy = enemy
                        scene.engine.player.hp = scene.engine.player.max_hp = 999
                        enemy.reset_energy()
                        choose_next_action(enemy)
                        scene.engine.end_turn()
                        enemy.set_intent('attack', action.value, action)
                        scene.engine.enemy_actions_remaining = 1
                        scene.engine.enemy_turn()
                        actual = scene.engine.player.hp
                        self.assertLess(actual, 999)
                        self.assertEqual(scene._visible_player().hp, 999)
                        view = scene.entity_view
                        scene.update(view.enemy_attack_duration * (view.enemy_impact_fraction-.02))
                        self.assertEqual(scene._visible_player().hp, 999)
                        self.assertFalse(scene.floating_texts.texts)
                        scene.update(view.enemy_attack_duration * .03)
                        self.assertEqual(scene._visible_player().hp, actual)
                        self.assertTrue(scene.floating_texts.texts)
