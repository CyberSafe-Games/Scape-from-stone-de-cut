"""Chefe do Pico da Vigília, recuperação temporária e cast escarlate."""
import os
from pathlib import Path
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import pygame
from src.models.action import Action
from src.systems.combat_engine import CombatEngine
from src.systems.enemy_factory import create_point_enemy, create_carrasco_da_vigilia, choose_next_action
from src.core.asset_manager import AssetManager
from src.ui.entity_view import EntityView
from src.ui.sprite_cleanup import recolor_green_aura_red
from src.ui.crimson_cast_fx import draw_crimson_cast


class CarrascoDaVigiliaTests(unittest.TestCase):
    def test_level_six_point_uses_carrasco_with_two_actions(self):
        boss = create_point_enemy(6)
        self.assertEqual(boss.name, 'Carrasco da Vigília')
        self.assertEqual(boss.hp, 146)
        self.assertTrue(boss.is_miniboss)
        self.assertEqual(boss.actions_per_turn, 2)
        self.assertEqual({a.visual_effect for a in boss.actions}, {'atk1', 'atk2', 'healer2'})
        self.assertEqual(boss.special_action.visual_effect, 'atk3')
        self.assertEqual(boss.special_action.damage, 24)
        self.assertEqual(create_point_enemy(5).name, 'Corpo Seco')
        self.assertEqual(create_point_enemy(1).name, 'Guardião da Pedra')

    def test_special_fires_on_eighth_and_sixteenth_actions(self):
        engine = CombatEngine()
        engine.enemy = create_carrasco_da_vigilia()
        engine.player.hp = engine.player.max_hp = 999
        choose_next_action(engine.enemy)
        names = []
        for i in range(16):
            if engine.state == 'player_turn': engine.end_turn()
            names.append(engine.enemy.current_action.name)
            engine.enemy_turn()
            engine.finish_enemy_turn()
        self.assertEqual(names[7], 'Execução Escarlate')
        self.assertEqual(names[15], 'Execução Escarlate')
        self.assertTrue(all(name != 'Execução Escarlate' for i, name in enumerate(names) if (i + 1) % 8))

    def test_vigor_heals_and_bonus_lasts_turns_rather_than_actions(self):
        engine = CombatEngine()
        engine.enemy = create_carrasco_da_vigilia()
        boss = engine.enemy
        boss.hp = 100
        vigor = next(a for a in boss.actions if a.action_type == 'buff')
        boss.set_intent('buff', vigor.value, vigor)
        engine.end_turn()
        engine.enemy_turn()
        self.assertEqual(boss.hp, 114)
        self.assertEqual(boss.statuses['aura'], {'turns': 2, 'potency': 4})
        engine.finish_enemy_turn()
        self.assertEqual(boss.statuses['aura']['turns'], 2)
        zero = Action('Teste', 'attack', damage=0)
        boss.set_intent('attack', 0, zero)
        engine.enemy_turn()
        self.assertEqual(engine.player.hp, 56)
        engine.finish_enemy_turn()
        self.assertEqual(boss.statuses['aura']['turns'], 1)
        engine.end_turn()
        for _ in range(2):
            boss.set_intent('attack', 0, zero)
            engine.enemy_turn()
            engine.finish_enemy_turn()
        self.assertEqual(engine.player.hp, 48)
        self.assertNotIn('aura', boss.statuses)

    def test_vigor_caps_health_and_does_not_stack_bonus(self):
        engine = CombatEngine()
        engine.enemy = create_carrasco_da_vigilia()
        boss = engine.enemy
        boss.hp = 140
        vigor = next(a for a in boss.actions if a.action_type == 'buff')
        for _ in range(3): vigor.execute(boss, engine.player, engine)
        self.assertEqual(boss.hp, 146)
        self.assertEqual(boss.attack_bonus, 4)
        self.assertEqual(boss.statuses['aura']['turns'], 2)
        boss.cleanse(all_effects=True)
        self.assertEqual(boss.attack_bonus, 0)

    def test_all_24_frames_are_uniform_rgba_and_transparent(self):
        from PIL import Image
        root = Path(__file__).resolve().parents[1] / 'assets' / 'carrasco_da_vigilia'
        for group in ('idle', 'atk1', 'atk2', 'atk3', 'healer2', 'dano'):
            for i in range(1, 5):
                with self.subTest(group=group, frame=i), Image.open(root / f'{group}_{i}.png') as image:
                    self.assertEqual(image.size, (448, 300))
                    self.assertEqual(image.mode, 'RGBA')
                    self.assertEqual(image.getpixel((0, 0))[3], 0)
                    self.assertIsNotNone(image.getbbox())

    def test_palette_star_and_biome_load_in_the_real_view(self):
        was_initialized = pygame.get_init()
        pygame.init()
        if pygame.display.get_surface() is None: pygame.display.set_mode((1, 1))
        if not was_initialized: self.addCleanup(pygame.quit)
        sample = pygame.Surface((2, 1), pygame.SRCALPHA)
        sample.set_at((0, 0), (145, 180, 60, 255))
        sample.set_at((1, 0), (175, 155, 144, 255))
        fixed = recolor_green_aura_red(sample)
        self.assertGreater(fixed.get_at((0, 0)).r, fixed.get_at((0, 0)).g * 2)
        self.assertEqual(fixed.get_at((1, 0)), sample.get_at((1, 0)))
        assets = AssetManager()
        self.assertIsNot(assets.get_battle_background(6), assets.background)
        self.assertEqual(assets.get_battle_background(6).get_size(), (1280, 720))
        view = EntityView(assets)
        view.trigger_enemy_action('healer2', 'Carrasco da Vigília')
        self.assertEqual(view.enemy_action_duration, 1500)
        screen = pygame.Surface((1280, 720), pygame.SRCALPHA)
        view.update(900)
        draw_crimson_cast(screen, view)
        red = screen.get_at((1020, 225))
        self.assertGreater(red.r, red.g)
        self.assertGreater(red.a, 0)
        frames = assets.get_enemy_sprite_group('Carrasco da Vigília', 'healer2')
        self.assertEqual(len(frames), 4)
        for frame in frames:
            rgb = pygame.image.tobytes(frame, 'RGBA')
            greens = sum(1 for i in range(0, len(rgb), 4)
                         if rgb[i + 3] and rgb[i + 1] > rgb[i] * 1.2 and rgb[i + 1] > rgb[i + 2] * 1.2)
            self.assertEqual(greens, 0)
        view.update(2000)
        screen.fill((0, 0, 0, 0))
        draw_crimson_cast(screen, view)
        self.assertEqual(screen.get_bounding_rect().width, 0)
