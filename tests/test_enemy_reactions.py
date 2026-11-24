"""Reações reais na arena: pivô, duração, transparência e retomada do idle."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import pygame

from src.core.asset_manager import AssetManager
from src.config.layout import FLASH_DURATION
from src.ui.entity_view import EntityView
from src.ui.enemy_reactions import (support, prepare_hurt, reaction_pose, knockback,
                                   hurt_progress, calm_idle_frames, JOZEPHINO_IDLE_MS)


class EnemyReactionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.assets = AssetManager()
        cls.names = tuple(cls.assets._enemy_sprites)

    def test_all_native_reaction_samples_keep_the_ready_anchor_and_canvas(self):
        for name in self.names:
            view = EntityView(self.assets)
            enemy = SimpleNamespace(name=name, hp=100)
            view.enemy_idle_timer = 725
            ready = view.get_enemy_frame(enemy, interpolate=True)
            expected = support(ready)[:2]
            for elapsed in range(0, FLASH_DURATION+1, 13):
                view.enemy_flash = FLASH_DURATION-elapsed
                frame = view.get_enemy_frame(enemy, interpolate=True)
                with self.subTest(name=name, elapsed=elapsed):
                    self.assertEqual(frame.get_size(), ready.get_size())
                    self.assertEqual(support(frame)[:2], expected)
            self.assertEqual(pygame.image.tobytes(frame, "RGBA"),
                             pygame.image.tobytes(ready, "RGBA"))

    def test_actual_arena_draw_never_moves_baseline_or_adds_vertical_knockback(self):
        for name in self.names:
            enemy = SimpleNamespace(name=name, hp=100)
            view = EntityView(self.assets)
            reference = None
            for elapsed in (0, 75, 160, 300, 450, 559, 560):
                view.enemy_flash = FLASH_DURATION-elapsed
                canvas = pygame.Surface((1920, 1080), pygame.SRCALPHA)
                view.draw_enemy(canvas, enemy)
                x, floor, box = support(canvas)
                with self.subTest(name=name, elapsed=elapsed):
                    self.assertTrue(box.h)
                    if reference is None:
                        reference = (x, floor)
                    self.assertLessEqual(abs(floor-reference[1]), 1)
                    self.assertLessEqual(abs(x-round(knockback(view.enemy_flash))-reference[0]), 2)

    def test_idle_clock_freezes_during_hit_then_resumes_without_reset(self):
        for name in self.names:
            view = EntityView(self.assets)
            enemy = SimpleNamespace(name=name, hp=100)
            view.enemy_idle_timer = 725
            ready = view.get_enemy_frame(enemy, interpolate=True)
            view.trigger_flash("enemy", name)
            view.update(FLASH_DURATION)
            self.assertEqual(view.enemy_idle_timer, 725, name)
            after = view.get_enemy_frame(enemy, interpolate=True)
            self.assertEqual(pygame.image.tobytes(after, "RGBA"), pygame.image.tobytes(ready, "RGBA"), name)
            view.update(16)
            self.assertEqual(view.enemy_idle_timer, 741)

    def test_hit_hold_and_recoil_have_continuous_endpoints(self):
        self.assertEqual(knockback(FLASH_DURATION), 0)
        self.assertEqual(knockback(0), 0)
        self.assertEqual(hurt_progress(FLASH_DURATION*.77), hurt_progress(FLASH_DURATION*.70))
        values = [knockback(FLASH_DURATION-t) for t in range(FLASH_DURATION+1)]
        self.assertTrue(all(0 <= x <= 12 for x in values))
        self.assertLess(max(abs(a-b) for a,b in zip(values, values[1:])), .4)

    def test_missing_or_grossly_deformed_pose_uses_intact_guard_without_scaling(self):
        ready = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.rect(ready, "green", (35, 20, 30, 70))
        deformed = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.rect(deformed, "green", (5, 5, 90, 20))
        frames, audit = prepare_hurt((deformed,), ready)
        self.assertFalse(audit[0]["accepted"])
        self.assertTrue(all(f is ready for f in frames))
        self.assertIs(reaction_pose((), ready, 250), ready)
        filtered, audit = prepare_hurt((ready, deformed, ready), ready)
        self.assertEqual([r['accepted'] for r in audit], [True, False, True])
        self.assertEqual(len(filtered), 4)  # sem inserir retorno à guarda no meio


    def test_jozephino_eight_breaths_share_boot_pixels_and_do_not_shrink(self):
        idle = self.assets.get_enemy_sprite_group("goblin nerd", "idle")
        poses = calm_idle_frames(idle[0])
        self.assertEqual(len(poses), 8)
        self.assertEqual(JOZEPHINO_IDLE_MS, 160)
        x, floor, body = support(idle[0])
        region = pygame.Rect(0, floor-max(8, body.h//7), idle[0].get_width(), max(8, body.h//7))
        boots = pygame.image.tobytes(idle[0].subsurface(region), "RGBA")
        for frame in poses:
            self.assertEqual(support(frame)[:2], (x, floor))
            self.assertEqual(pygame.image.tobytes(frame.subsurface(region), "RGBA"), boots)
            self.assertLessEqual(abs(support(frame)[2].h-body.h), 2)
        self.assertEqual(len({pygame.image.tobytes(f, "RGBA") for f in poses}), 8)

    def test_next_enemy_action_waits_for_the_visual_reaction_to_finish(self):
        from unittest.mock import MagicMock
        from src.scenes.battle_scene import BattleScene
        scene = BattleScene(MagicMock(), MagicMock(), self.assets)
        scene.boss_dialogue = None
        scene.engine.state = 'enemy_turn'
        scene.enemy_turn_timer = 5000
        scene.entity_view.enemy_flash = 200
        with patch.object(scene.engine, 'enemy_turn') as act:
            scene.update(100)
            act.assert_not_called()
            self.assertFalse(scene.entity_view.is_enemy_resolving_done())
            scene.update(101)
            act.assert_called_once()

    def test_procedural_minibosses_and_enemies_keep_ground_and_shape(self):
        from src.systems.enemy_factory import ENEMY_TYPES, MINIBOSS_TYPES
        for name, _, _ in (*ENEMY_TYPES, *MINIBOSS_TYPES):
            if self.assets.has_enemy_sprites(name):
                continue
            view = EntityView(self.assets)
            reference = None
            for elapsed in (0, 65, 150, 300, 560):
                view.enemy_flash = FLASH_DURATION-elapsed
                canvas = pygame.Surface((1920, 1080), pygame.SRCALPHA)
                view.draw_enemy(canvas, SimpleNamespace(name=name, hp=100))
                x, floor, body = support(canvas)
                if reference is None:
                    reference = (x, floor, body.size)
                self.assertEqual(floor, reference[1], name)
                self.assertEqual(body.size, reference[2], name)
                self.assertEqual(x-round(knockback(view.enemy_flash)), reference[0], name)

    def test_enemy_render_does_not_use_rotating_or_squashing_player_fallback(self):
        view = EntityView(self.assets)
        view.trigger_flash("enemy", "guardião da pedra")
        canvas = pygame.Surface((1920, 1080), pygame.SRCALPHA)
        with patch("src.ui.entity_view.draw_recoiling_actor", side_effect=AssertionError("Deformação")):
            view.draw_enemy(canvas, SimpleNamespace(name="guardião da pedra", hp=100))


if __name__ == "__main__":
    unittest.main()
