"""Cobertura das ações completas, retorno ao repouso e sincronia de lançamento."""
import os
import unittest
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
from src.core.asset_manager import AssetManager
from src.ui.entity_view import EntityView
from src.ui.card_fx import projectile_pose
from src.systems.card_definitions import CARD_SPECS
from src.systems.ultimate_animations import ULTIMATE_ANIMATIONS, cast_frame
from src.systems.player_animation_kits import player_frame


class PlayerEightFramesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.assets = AssetManager()

    def test_every_interaction_has_eight_complete_distinct_poses_and_ready_closure(self):
        groups = {g: self.assets.get_player_sprite_group(g) for g in ('idle', 'soco', 'dano', 'vitoria')}
        groups.update({s[1]: self.assets.get_card_action_sprites(s[1]) for s in CARD_SPECS})
        groups.update({name: self.assets.get_card_action_sprites(name) for name in ULTIMATE_ANIMATIONS})
        self.assertEqual(len(groups), 27)
        ready = pygame.image.tobytes(groups['idle'][0], 'RGBA')
        for name, frames in groups.items():
            with self.subTest(name=name):
                self.assertEqual(len(frames), 8)
                self.assertGreaterEqual(len({pygame.image.tobytes(f, 'RGBA') for f in frames}), 6)
                self.assertEqual(pygame.image.tobytes(frames[-1], 'RGBA'), ready)
                for frame in frames:
                    self.assertEqual(frame.get_size(), (320, 260))
                    b = frame.get_bounding_rect(min_alpha=50)
                    self.assertGreater(b.left, 0)
                    self.assertLess(b.right, 320)
                    self.assertGreaterEqual(b.bottom, 255)
                    self.assertLess(b.bottom, 260)
                    self.assertEqual(frame.get_at((0, 0)).a, 0)

    def test_all_card_and_ultimate_poses_are_reachable_and_return_without_global_clock_jump(self):
        for spec in CARD_SPECS:
            name = spec[1]
            view = EntityView(self.assets)
            if spec[3] == 'attack':
                view.trigger_attack('player', name)
            else:
                view.trigger_player_action(name)
            frames = self.assets.get_card_action_sprites(name)
            seen = set()
            for i in range(1000):
                view.player_action_timer = view.player_action_duration*i/1000
                seen.add(next(j for j, f in enumerate(frames) if f is view.get_player_frame('player_turn')[1]))
            self.assertEqual(seen, set(range(8)), name)
            view.update(view.player_action_duration+1000)
            self.assertIs(view.get_player_frame('player_turn')[1], self.assets.get_player_sprite_group('idle')[0])
        for name, spec in ULTIMATE_ANIMATIONS.items():
            self.assertEqual({cast_frame(i/1000, spec.release) for i in range(1000)}, set(range(8)), name)

    def test_ranged_release_matches_fifth_pose_and_projectile_start(self):
        view = EntityView(self.assets)
        view.trigger_attack('player', 'Disparo de Arco')
        view.player_action_timer = view.attack_timer = view.player_attack_duration*.64
        self.assertEqual(player_frame(.64, 'ranged'), 4)
        self.assertIsNotNone(projectile_pose(view))
        self.assertIs(view.get_player_frame('player_turn')[1], self.assets.get_card_action_sprites('Disparo de Arco')[4])

    def test_idle_and_damage_play_all_eight_poses(self):
        view = EntityView(self.assets)
        for i, frame in enumerate(self.assets.get_player_sprite_group('idle')):
            view.player_idle_timer = i*150
            self.assertIs(view.get_player_frame('player_turn')[1], frame)
        from src.config.layout import FLASH_DURATION
        view.trigger_flash('player')
        for i, frame in enumerate(self.assets.get_player_sprite_group('dano')):
            view.player_flash = FLASH_DURATION*(1-(i+.1)/8)
            self.assertIs(view.get_player_frame('player_turn')[1], frame)
