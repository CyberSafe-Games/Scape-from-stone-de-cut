"""Sprites, camadas e sincronização da ativação das três ultimates."""
import os
import unittest
from types import SimpleNamespace

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import pygame

from src.core.asset_manager import AssetManager
from src.config.layout import PLAYER_X, ENEMY_X, PLAYER_GROUND_Y
from src.ui.entity_view import EntityView
from src.ui.ultimate_fx import draw_ultimate_fx
from src.systems.ultimate_animations import ULTIMATE_ANIMATIONS, cast_frame, roar_projectile_pose
from src.scenes.battle_scene import BattleScene
from src.systems.enemy_factory import create_guardiao_da_pedra


class UltimateAnimationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.was_initialized = pygame.get_init()
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.assets = AssetManager()

    @classmethod
    def tearDownClass(cls):
        if not cls.was_initialized:
            pygame.quit()

    def scene(self):
        window = SimpleNamespace(get_virtual_mouse_pos=lambda: (-1, -1),
                                 draw_fullscreen_button=lambda *args: None)
        scene = BattleScene(None, window, self.assets)
        scene.engine.enemy = create_guardiao_da_pedra()
        scene.engine.enemy.hp = scene.engine.enemy.max_hp = 200
        return scene

    def test_every_ultimate_has_four_cast_poses_and_four_independent_alpha_effects(self):
        for name in ULTIMATE_ANIMATIONS:
            casts = self.assets.get_card_action_sprites(name)
            effects = self.assets.get_ultimate_effect_sprites(name)
            self.assertEqual(len(casts), 4, name)
            self.assertEqual(len(effects), 4, name)
            for frame in casts:
                self.assertEqual(frame.get_size(), (320, 260))
                bounds = frame.get_bounding_rect(min_alpha=50)
                self.assertGreaterEqual(bounds.bottom, 255)
                self.assertLess(bounds.bottom, 260)
                self.assertGreater(bounds.left, 0)
                self.assertLess(bounds.right, 320)
            for frame in casts+effects:
                self.assertEqual(frame.get_at((0, 0)).a, 0)
                self.assertGreater(frame.get_bounding_rect().width, 20)

    def test_cast_poses_stay_at_home_and_finish_in_the_idle_state(self):
        for name, spec in ULTIMATE_ANIMATIONS.items():
            for progress in (0, .23, .45, .90):
                with self.subTest(name=name, progress=progress):
                    view = EntityView(self.assets)
                    view.trigger_player_action(name)
                    view.update(spec.duration*progress)
                    x, frame = view.get_player_frame('player_turn')
                    self.assertEqual(x, PLAYER_X)
                    self.assertIs(frame, self.assets.get_card_action_sprites(name)[cast_frame(progress)])
                    self.assertIsNone(view.attacker)
            view.update(spec.duration)
            self.assertIsNone(view.player_action)
            self.assertEqual(view.get_player_frame('player_turn')[0], PLAYER_X)

    def test_layers_render_inside_arena_and_restore_clip_then_disappear(self):
        for name, spec in ULTIMATE_ANIMATIONS.items():
            view = EntityView(self.assets)
            view.trigger_player_action(name)
            view.update(spec.duration*.6)
            for behind in (True, False):
                screen = pygame.Surface((1280, 720), pygame.SRCALPHA)
                clip = screen.get_clip()
                draw_ultimate_fx(screen, view, behind)
                self.assertEqual(screen.get_clip(), clip)
                bounds = screen.get_bounding_rect()
                self.assertGreater(bounds.width, 5)
                self.assertGreaterEqual(bounds.top, 116)
                self.assertLessEqual(bounds.bottom, 516)
            view.update(spec.duration)
            screen.fill((0, 0, 0, 0))
            draw_ultimate_fx(screen, view)
            draw_ultimate_fx(screen, view, True)
            self.assertEqual(screen.get_bounding_rect().width, 0)

    def test_roar_flies_right_and_flash_waits_for_impact(self):
        view = EntityView(self.assets)
        view.trigger_player_action('Rugido da Floresta')
        view.trigger_flash('enemy')
        spec = ULTIMATE_ANIMATIONS[view.player_action]
        self.assertIsNone(roar_projectile_pose(spec.release-.001, PLAYER_X+105, ENEMY_X-18, 335))
        start = roar_projectile_pose(spec.release, PLAYER_X+105, ENEMY_X-18, 335)
        end = roar_projectile_pose(spec.impact-.001, PLAYER_X+105, ENEMY_X-18, 335)
        self.assertGreater(end[0], start[0])
        view.update(spec.duration*spec.impact-1)
        self.assertEqual(view.enemy_flash, 0)
        view.update(2)
        self.assertGreater(view.enemy_flash, 0)
        self.assertIsNone(roar_projectile_pose(spec.impact, PLAYER_X+105, ENEMY_X-18, 335))

    def test_real_scene_delays_visual_hp_and_text_until_roar_impact(self):
        scene = self.scene()
        scene.engine.equip_ultimate('rugido_da_floresta')
        scene.engine.player.ultimate_charge = 20
        self.assertTrue(scene.engine.activate_ultimate())
        self.assertEqual(scene.engine.enemy.hp, 140)
        self.assertEqual(scene._visible_enemy().hp, 200)
        self.assertEqual(len(scene.floating_texts.texts), 0)
        spec = ULTIMATE_ANIMATIONS['Rugido da Floresta']
        scene.update(spec.duration*spec.impact-1)
        self.assertEqual(scene._visible_enemy().hp, 200)
        scene.update(2)
        self.assertEqual(scene._visible_enemy().hp, 140)
        self.assertGreater(len(scene.floating_texts.texts), 0)
        self.assertFalse(scene._ultimate_events)
        scene.draw(pygame.Surface((1280, 720)))

    def test_self_cast_feedback_appears_at_peak_without_overlapping_text(self):
        for name in ('Mana Ancestral', 'Forças Ancestrais'):
            scene = self.scene()
            spec = ULTIMATE_ANIMATIONS[name]
            scene.engine.equip_ultimate(spec.ultimate_id)
            scene.engine.player.ultimate_charge = 20
            scene.engine.player.energy = 0
            scene.engine.activate_ultimate()
            self.assertTrue(scene._ultimate_events)
            self.assertFalse(scene.floating_texts.texts)
            scene.update(spec.duration*spec.impact+1)
            texts = scene.floating_texts.texts
            self.assertEqual(len(texts), 2)
            self.assertNotEqual(texts[0].y, texts[1].y)
            scene.draw(pygame.Surface((1280, 720)))

    def test_lethal_roar_keeps_victory_effects_until_hit_and_cast_ends(self):
        scene = self.scene()
        scene.engine.enemy.hp = 10
        scene.engine.equip_ultimate('rugido_da_floresta')
        scene.engine.player.ultimate_charge = 20
        scene.engine.activate_ultimate()
        self.assertEqual(scene.engine.state, 'victory')
        self.assertEqual(scene._visible_enemy().hp, 10)
        self.assertTrue(any(event == 'coin_drop' for _, event, _ in scene._ultimate_events))
        scene.update(2000)
        self.assertFalse(scene._ultimate_events)
        self.assertEqual(scene._visible_enemy().hp, 0)
        self.assertEqual(scene.entity_view.player_action, 'Rugido da Floresta')
        scene.update(600)
        self.assertIsNone(scene.entity_view.player_action)
        scene.draw(pygame.Surface((1280, 720)))
