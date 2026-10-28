"""Especiais dos quatro chefes: identificação, sprites, impacto e sequência."""
import os
import unittest
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import pygame
from src.core.asset_manager import AssetManager
from src.systems.enemy_factory import create_point_enemy, choose_next_action
from src.systems.combat_engine import CombatEngine
from src.systems.boss_ultimate_animations import BOSS_ULTIMATE_ANIMATIONS, BOSS_ORIGINAL_CASTS, boss_ultimate_pose
from src.ui.entity_view import EntityView
from src.ui.boss_ultimate_fx import draw_boss_ultimate_fx
from src.scenes.battle_scene import BattleScene
from src.config.layout import ENEMY_X, PLAYER_X


class BossUltimateAnimationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.initialized = pygame.get_init()
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.assets = AssetManager()

    @classmethod
    def tearDownClass(cls):
        if not cls.initialized: pygame.quit()

    def scene(self, level):
        window = SimpleNamespace(get_virtual_mouse_pos=lambda: (-1, -1), draw_fullscreen_button=lambda *args: None)
        scene = BattleScene(None, window, self.assets, selected_level=level)
        scene.engine.enemy = create_point_enemy(level)
        scene.engine.player.hp = scene.engine.player.max_hp = 200
        return scene

    def start(self, scene):
        scene.engine.end_turn()
        boss = scene.engine.enemy
        boss.set_intent('attack', boss.special_action.value, boss.special_action)
        scene.engine.enemy_turn()

    def test_all_four_specials_are_marked_only_on_the_eighth_and_sixteenth_actions(self):
        for level in (1, 3, 5, 6):
            with self.subTest(level=level):
                events = []
                engine = CombatEngine(on_event_callback=lambda event, **data: events.append((event, data)))
                engine.enemy = create_point_enemy(level)
                engine.player.hp = engine.player.max_hp = 999
                choose_next_action(engine.enemy)
                fired = []
                for i in range(16):
                    if engine.state == 'player_turn': engine.end_turn()
                    events.clear()
                    engine.enemy_turn()
                    if any(kind == 'attack' and data.get('ultimate') for kind, data in events): fired.append(i+1)
                    engine.finish_enemy_turn()
                self.assertEqual(fired, [8, 16])

    def test_every_boss_has_four_transparent_casts_and_four_independent_effects(self):
        for name in BOSS_ULTIMATE_ANIMATIONS:
            casts = self.assets.get_boss_ultimate_sprites(name)
            effects = self.assets.get_boss_ultimate_sprites(name, effects=True)
            self.assertEqual(len(casts), 4)
            self.assertEqual(len(effects), 4)
            for frame in casts:
                self.assertEqual(frame.get_size(), (448, 320))
                bounds = frame.get_bounding_rect(min_alpha=50)
                self.assertGreaterEqual(bounds.bottom, 315)
                self.assertLess(bounds.bottom, 320)
                self.assertGreater(bounds.top, 0)
                self.assertGreater(bounds.left, 0)
                self.assertLess(bounds.right, 448)
            for frame in casts+effects:
                self.assertEqual(frame.get_at((0, 0)).a, 0)
                self.assertGreater(frame.get_bounding_rect().width, 20)

    def test_goblin_regular_shot_keeps_its_old_animation_and_ultimate_is_dedicated(self):
        view = EntityView(self.assets)
        view.trigger_attack('enemy', 'atk2', 'Goblin Nerd')
        self.assertIsNone(view.enemy_ultimate)
        self.assertEqual(view.enemy_attack_duration, 900)
        view.trigger_attack('enemy', 'atk2', 'Goblin Nerd', ultimate=True)
        self.assertIs(view.enemy_ultimate, BOSS_ULTIMATE_ANIMATIONS['goblin nerd'])
        self.assertEqual(view.enemy_attack_duration, 2400)
        self.assertIs(view.get_enemy_frame(create_point_enemy(3)), self.assets.get_boss_ultimate_sprites('Goblin Nerd')[0])

    def test_damage_flash_and_visual_health_shield_wait_for_each_impact(self):
        for level in (1, 3, 5, 6):
            with self.subTest(level=level):
                scene = self.scene(level)
                scene.engine.player.add_block(5)
                self.start(scene)
                spec = scene.entity_view.enemy_ultimate
                actual = scene.engine.player.hp
                self.assertLess(actual, 200)
                self.assertEqual(scene._visible_player().hp, 200)
                self.assertEqual(scene._visible_player().block, 5)
                self.assertFalse(scene.floating_texts.texts)
                scene.update(spec.duration*spec.impact-1)
                self.assertEqual(scene.entity_view.player_flash, 0)
                self.assertEqual(scene._visible_player().hp, 200)
                scene.update(2)
                self.assertGreater(scene.entity_view.player_flash, 0)
                self.assertEqual(scene._visible_player().hp, actual)
                self.assertEqual(scene._visible_player().block, 0)
                self.assertTrue(scene.floating_texts.texts)
                self.assertFalse(scene._boss_events)

    def test_casts_preserve_the_original_characters_pixels_and_scale(self):
        import numpy as np
        for name, references in BOSS_ORIGINAL_CASTS.items():
            casts = self.assets.get_boss_ultimate_sprites(name)
            for cast, (group, index) in zip(casts, references):
                with self.subTest(name=name, pose=(group, index)):
                    original = self.assets.get_enemy_sprite_group(name, group)[index]
                    if name == 'goblin nerd':
                        # A arma original veio de uma folha em escala menor:
                        # a normalização deve manter os mesmos pixels/cores e
                        # a altura física do personagem em idle.
                        visible = pygame.surfarray.array_alpha(cast) == 255
                        source_visible = pygame.surfarray.array_alpha(original) == 255
                        palette = set(map(tuple, pygame.surfarray.array3d(original)[source_visible]))
                        self.assertTrue(set(map(tuple, pygame.surfarray.array3d(cast)[visible])).issubset(palette))
                        height = self.assets.get_enemy_sprite_group(name, 'idle')[0].get_bounding_rect(min_alpha=50).height
                        self.assertLessEqual(abs(cast.get_bounding_rect(min_alpha=50).height-height), 2)
                        continue
                    expected = pygame.Surface((448, 320), pygame.SRCALPHA)
                    bounds = original.get_bounding_rect(min_alpha=50)
                    rect = original.get_rect(midbottom=(224, 318))
                    rect.y += original.get_height()-bounds.bottom
                    expected.blit(original, rect)
                    visible = pygame.surfarray.array_alpha(cast) > 250
                    original_visible = pygame.surfarray.array_alpha(expected) > 250
                    self.assertGreater(visible.sum(), original_visible.sum()*.85)
                    self.assertTrue(np.array_equal(pygame.surfarray.array3d(cast)[visible],
                                                   pygame.surfarray.array3d(expected)[visible]))

    def test_approved_magic_effect_files_remain_identical(self):
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads((root/'tests'/'fixtures'/'boss_ultimate_effect_hashes.json').read_text(encoding='utf-8'))
        self.assertEqual(len(manifest), 16)
        for path, digest in manifest.items():
            self.assertEqual(hashlib.sha256((root/path).read_bytes()).hexdigest(), digest, path)

    def test_projectiles_go_left_melee_bosses_advance_and_all_return_home(self):
        for name, spec in BOSS_ULTIMATE_ANIMATIONS.items():
            view = EntityView(self.assets)
            boss = create_point_enemy({'bear': 1, 'plasma': 3, 'blades': 5, 'execution': 6}[spec.mode])
            view.trigger_attack('enemy', boss.special_action.visual_effect, boss.name, ultimate=True)
            view.update(spec.duration*.60)
            if spec.mode in ('bear', 'plasma'):
                self.assertEqual(view.get_attack_pose('enemy', ENEMY_X, PLAYER_X)[0], ENEMY_X)
                start = view.get_enemy_projectile_pose()
                view.update(30)
                self.assertLess(view.get_enemy_projectile_pose()[0], start[0])
            else:
                self.assertEqual(view.get_attack_pose('enemy', ENEMY_X, PLAYER_X)[0], PLAYER_X+105)
            x, lift = boss_ultimate_pose(spec, 1, ENEMY_X, PLAYER_X+105)
            self.assertEqual(x, ENEMY_X)
            self.assertEqual(lift, 0)
            if spec.mode == 'execution':
                self.assertGreater(boss_ultimate_pose(spec, .38, ENEMY_X, PLAYER_X+105)[1], 30)

    def test_layers_render_then_clear_and_followup_action_waits_until_end(self):
        for level in (1, 3, 5, 6):
            scene = self.scene(level)
            self.start(scene)
            spec = scene.entity_view.enemy_ultimate
            scene.update(spec.duration*.6)
            for behind in (True, False):
                canvas = pygame.Surface((1280, 720), pygame.SRCALPHA)
                original = canvas.get_clip()
                draw_boss_ultimate_fx(canvas, scene.entity_view, behind)
                self.assertEqual(canvas.get_clip(), original)
                self.assertGreater(canvas.get_bounding_rect().width, 0)
                self.assertGreaterEqual(canvas.get_bounding_rect().top, 116)
                self.assertLessEqual(canvas.get_bounding_rect().bottom, 516)
            self.assertEqual(scene.engine.state, 'enemy_resolving')
            self.assertEqual(scene.engine.enemy_actions_remaining, 1)
            scene.update(spec.duration*.4+1)
            self.assertIsNone(scene.entity_view.enemy_ultimate)
            self.assertEqual(scene.engine.state, 'enemy_turn')
            canvas.fill((0, 0, 0, 0))
            draw_boss_ultimate_fx(canvas, scene.entity_view)
            self.assertEqual(canvas.get_bounding_rect().width, 0)

    def test_lethal_special_finishes_before_game_over_overlay(self):
        scene = self.scene(6)
        scene.engine.player.hp = 1
        self.start(scene)
        self.assertEqual(scene.engine.state, 'game_over')
        self.assertEqual(scene._visible_player().hp, 1)
        scene._draw_game_over = MagicMock()
        scene.draw(pygame.Surface((1280, 720)))
        scene._draw_game_over.assert_not_called()
        scene.update(2801)
        self.assertEqual(scene._visible_player().hp, 0)
        self.assertIsNone(scene.entity_view.enemy_ultimate)
        scene.draw(pygame.Surface((1280, 720)))
        scene._draw_game_over.assert_called_once()

    def test_ruins_background_is_used_by_goblin_and_regular_biome_encounters(self):
        background = self.assets.get_battle_background(3)
        self.assertEqual(background.get_size(), (1280, 720))
        self.assertIsNot(background, self.assets.background)
        self.assertIsNot(background, self.assets.get_battle_background(2))
        self.assertEqual(create_point_enemy(3).name, 'Goblin Nerd')
        self.assertIsNot(self.assets.get_battle_background(1), background)
