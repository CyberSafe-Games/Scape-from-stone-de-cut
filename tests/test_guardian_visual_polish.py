"""Recortes sem matte e ciclo visual completo do Rugido Espiritual."""
import os
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import pygame
from src.ui.sprite_cleanup import remove_white_fringe
from src.ui.entity_view import EntityView
from src.ui.guardian_spirit_fx import draw_guardian_spirit


class GuardianVisualPolishTests(unittest.TestCase):
    def setUp(self):
        was_initialized = pygame.get_init()
        pygame.init()
        if pygame.display.get_surface() is None: pygame.display.set_mode((1, 1))
        if not was_initialized: self.addCleanup(pygame.quit)

    def test_cleanup_removes_exterior_gray_but_preserves_enclosed_highlights(self):
        image = pygame.Surface((15, 15), pygame.SRCALPHA)
        pygame.draw.rect(image, (180, 180, 177), (2, 2, 11, 11))
        pygame.draw.rect(image, (45, 32, 23), (3, 3, 9, 9))
        pygame.draw.rect(image, (242, 241, 238), (5, 5, 5, 5))
        original = pygame.image.tobytes(image, 'RGBA')
        cleaned = remove_white_fringe(image)
        self.assertEqual(cleaned.get_size(), image.get_size())
        self.assertEqual(cleaned.get_at((2, 7)).a, 0)
        self.assertEqual(cleaned.get_at((3, 7)), image.get_at((3, 7)))
        self.assertEqual(cleaned.get_at((7, 7)), image.get_at((7, 7)))
        self.assertEqual(pygame.image.tobytes(image, 'RGBA'), original)

    def test_cleanup_does_not_destroy_blue_spirit_or_thin_colored_details(self):
        image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.line(image, (60, 170, 255), (3, 2), (3, 17), 1)
        pygame.draw.circle(image, (140, 76, 33), (13, 10), 4)
        cleaned = remove_white_fringe(image)
        self.assertEqual(cleaned.get_at((3, 8)), image.get_at((3, 8)))
        self.assertEqual(cleaned.get_at((13, 10)), image.get_at((13, 10)))

    def test_spirit_has_charge_flight_and_impact_then_leaves_no_residual_effect(self):
        class Assets:
            def get_enemy_projectile(self, name, group):
                image = pygame.Surface((114, 120), pygame.SRCALPHA)
                pygame.draw.circle(image, (70, 175, 255), (57, 60), 42)
                return image
        view = EntityView(Assets())
        view.trigger_attack('enemy', 'atk2', 'Guardião da Pedra')
        for progress in (.25, .65, .90):
            view.attack_timer = 1400 * progress
            surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
            view.draw_enemy_projectile(surface)
            self.assertGreater(surface.get_bounding_rect().width, 0)
        view.update(2000)
        surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
        view.draw_enemy_projectile(surface)
        self.assertEqual(surface.get_bounding_rect().width, 0)

    def test_guardian_visual_does_not_appear_for_another_enemy_or_regular_attack(self):
        view = EntityView(None)
        for name, action in (('Vinimuth', 'atk2'), ('Guardião da Pedra', 'atk1')):
            view.trigger_attack('enemy', action, name)
            surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
            draw_guardian_spirit(surface, view)
            self.assertEqual(surface.get_bounding_rect().width, 0)
