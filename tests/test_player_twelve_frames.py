"""Cobertura das ações completas, retorno ao repouso e sincronia de lançamento."""
import os
import unittest
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
from src.core.asset_manager import AssetManager
from src.ui.entity_view import EntityView
from src.config.layout import PLAYER_IDLE_FRAME_MS, VICTORY_FRAME_MS
from src.ui.card_fx import projectile_pose
from src.systems.card_definitions import CARD_SPECS
from src.systems.ultimate_animations import ULTIMATE_ANIMATIONS, cast_frame
from src.systems.player_animation_kits import player_frame


class PlayerTwelveFramesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.assets = AssetManager()

    def test_idle_and_hurt_have_eight_poses_and_other_actions_have_twelve(self):
        groups = {g: self.assets.get_player_sprite_group(g) for g in ('idle', 'soco', 'dano', 'vitoria')}
        groups.update({s[1]: self.assets.get_card_action_sprites(s[1]) for s in CARD_SPECS})
        groups.update({name: self.assets.get_card_action_sprites(name) for name in ULTIMATE_ANIMATIONS})
        self.assertEqual(len(groups), 27)
        ready = pygame.image.tobytes(groups['idle'][0], 'RGBA')
        for name, frames in groups.items():
            with self.subTest(name=name):
                count = 8 if name in ('idle', 'dano') else 12
                self.assertEqual(len(frames), count)
                self.assertGreaterEqual(len({pygame.image.tobytes(f, 'RGBA') for f in frames}), count - 2)
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
                view.player_action_timer = (view.player_action_duration + view.player_recovery_ms) * i/1000
                seen.add(next(j for j, f in enumerate(frames) if f is view.get_player_frame('player_turn')[1]))
            self.assertEqual(seen, set(range(12)), name)
            view.update(view.player_action_duration+1000)
            self.assertIs(view.get_player_frame('player_turn')[1], self.assets.get_player_sprite_group('idle')[0])
        for name, spec in ULTIMATE_ANIMATIONS.items():
            self.assertEqual({cast_frame(i/1000, spec.release, 12) for i in range(1000)}, set(range(12)), name)
            view=EntityView(self.assets)
            view.trigger_player_action(name)
            frames=self.assets.get_card_action_sprites(name)
            seen=set()
            for i in range(1000):
                view.player_action_timer=spec.duration*i/1000
                seen.add(next(j for j,f in enumerate(frames) if f is view.get_player_frame('player_turn')[1]))
            self.assertEqual(seen,set(range(12)),name)

    def test_ranged_release_matches_seventh_pose_and_projectile_start(self):
        view = EntityView(self.assets)
        view.trigger_attack('player', 'Disparo de Arco')
        view.player_action_timer = view.attack_timer = view.player_attack_duration*.64
        self.assertEqual(player_frame(.64, 'ranged'), 4)
        self.assertEqual(player_frame(.64, 'ranged', count=12), 6)
        self.assertIsNotNone(projectile_pose(view))
        self.assertIs(view.get_player_frame('player_turn')[1], self.assets.get_card_action_sprites('Disparo de Arco')[6])

    def test_idle_victory_and_basic_punch_play_all_their_poses(self):
        view = EntityView(self.assets)
        for i, frame in enumerate(self.assets.get_player_sprite_group('idle')):
            view.player_idle_timer = i * PLAYER_IDLE_FRAME_MS
            self.assertIs(view.get_player_frame('player_turn')[1], frame)
        view=EntityView(self.assets)
        view.get_player_frame('victory')
        for i,frame in enumerate(self.assets.get_player_sprite_group('vitoria')):
            view.player_victory_timer=(i+.1)*VICTORY_FRAME_MS
            self.assertIs(view.get_player_frame('victory')[1],frame)
        view=EntityView(self.assets)
        view.trigger_attack('player')
        frames=self.assets.get_player_sprite_group('soco')
        seen=set()
        for i in range(1000):
            view.attack_timer=(view.player_attack_duration + view.player_recovery_ms)*i/1000
            seen.add(next(j for j,f in enumerate(frames) if f is view.get_player_frame('player_turn')[1]))
        self.assertEqual(seen,set(range(12)))

    def test_damage_plays_eight_poses_and_finishes_at_ready(self):
        from src.config.layout import FLASH_DURATION
        view = EntityView(self.assets)
        def draw():
            canvas = pygame.Surface((1920, 1080), pygame.SRCALPHA)
            view.draw_player(canvas, 'player_turn')
            return pygame.image.tobytes(canvas, 'RGBA')

        ready = draw()
        view.trigger_flash('player')
        frames = self.assets.get_player_sprite_group('dano')
        seen = []
        for _ in range(0, FLASH_DURATION, 10):
            frame = view.get_player_frame('player_turn')[1]
            if not seen or frame is not seen[-1]:
                seen.append(frame)
            view.update(10)
        self.assertEqual(seen, frames)
        self.assertEqual(draw(), ready)

    def test_all_approved_eight_poses_and_ultimate_effects_remain_pixel_identical(self):
        from pathlib import Path
        from src.systems.animation_inbetweens import ORIGINAL_TWELVE_INDICES,NEW_TWELVE_INDICES
        root=Path(__file__).resolve().parents[1]/'assets/player/eight_frames'
        groups={g:self.assets.get_player_sprite_group(g) for g in ('idle','dano','soco','vitoria')}
        groups.update({slug:self.assets.get_card_action_sprites(name) for name,slug in self.assets.CARD_ACTION_FILES.items()})
        groups.update({spec.ultimate_id:self.assets.get_card_action_sprites(name) for name,spec in ULTIMATE_ANIMATIONS.items()})
        groups.update({spec.ultimate_id+'_effect':self.assets.get_ultimate_effect_sprites(name) for name,spec in ULTIMATE_ANIMATIONS.items()})
        for group,frames in groups.items():
            with self.subTest(group=group):
                old=[]
                indices = range(8) if group in ('idle', 'dano') else ORIGINAL_TWELVE_INDICES
                for i,index in enumerate(indices,1):
                    source=pygame.image.load(str(root/f'{group}_{i}.png')).convert_alpha()
                    old.append(pygame.image.tobytes(source,'RGBA'))
                    self.assertEqual(pygame.image.tobytes(frames[index],'RGBA'),old[-1])
                if len(frames) == 12:
                    added={pygame.image.tobytes(frames[i],'RGBA') for i in NEW_TWELVE_INDICES}
                    self.assertEqual(len(added),4)
                    self.assertFalse(added.intersection(old))

    def test_palette_brightness_and_slim_idle_silhouette_remain_consistent(self):
        import json
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]/'assets/player/eight_frames'
        colors=json.loads((root/'palette.json').read_text(encoding='utf8'))
        palette={tuple(colors[i:i+3]) for i in range(0,len(colors),3)}
        import numpy as np
        widths=[];brightness=[]
        groups={g:self.assets.get_player_sprite_group(g) for g in ('idle','dano','soco','vitoria')}
        groups.update({name:self.assets.get_card_action_sprites(name) for name in self.assets.CARD_ACTION_FILES})
        groups.update({name:self.assets.get_card_action_sprites(name) for name in ULTIMATE_ANIMATIONS})
        for group,frames in groups.items():
            for frame in frames:
                rgb=pygame.surfarray.array3d(frame);alpha=pygame.surfarray.array_alpha(frame)
                self.assertTrue(set(map(tuple,rgb[alpha>210])).issubset(palette),group)
                if group=='idle':
                    brightness.append(float(rgb[alpha>210].mean()))
                    widths.append(frame.get_bounding_rect(min_alpha=100).width)
        original_width=max(pygame.image.load(str(root/f'idle_{i}.png')).get_bounding_rect(min_alpha=100).width for i in range(1,9))
        self.assertLessEqual(max(widths),original_width+6)
        self.assertLess(max(brightness)-min(brightness),5)

    def test_twelve_ultimate_effects_are_reached_and_roar_dissipation_waits_for_impact(self):
        from src.systems.ultimate_animations import player_effect_frame
        for name,spec in ULTIMATE_ANIMATIONS.items():
            seen={player_effect_frame(i/1000,spec,12) for i in range(1000)}
            self.assertEqual(seen,set(range(12)),name)
        roar=ULTIMATE_ANIMATIONS['Rugido da Floresta']
        self.assertEqual(player_effect_frame(roar.impact-.001,roar,12),9)
        self.assertEqual(player_effect_frame(roar.impact,roar,12),10)
