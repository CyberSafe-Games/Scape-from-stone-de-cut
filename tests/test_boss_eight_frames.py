"""Integração de todos os kits: oito poses efetivas, efeitos e jogador preservados."""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
from src.core.asset_manager import AssetManager
from src.systems.boss_animation_kits import KITS, kit_frame, STRIKE_BOUNDARIES
from src.systems.boss_ultimate_animations import BOSS_ULTIMATE_ANIMATIONS
from src.ui.entity_view import EntityView


class BossEightFramesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init();pygame.display.set_mode((1,1))
        cls.assets = AssetManager()

    def test_all_six_forms_have_eight_distinct_frames_for_every_group(self):
        for name,(_,groups) in KITS.items():
            for group in groups:
                with self.subTest(name=name,group=group):
                    frames = (self.assets.get_boss_ultimate_sprites(name) if group=='ultimate'
                              else self.assets.get_enemy_sprite_group(name,group))
                    self.assertEqual(len(frames),8)
                    # Some original ultimates begin and end in the same idle pose.
                    unique = {pygame.image.tobytes(f,'RGBA') for f in frames}
                    self.assertGreaterEqual(len(unique),7)
                    added = {pygame.image.tobytes(f,'RGBA') for f in frames[1::2]}
                    self.assertEqual(len(added),4)
                    for frame in frames:
                        bounds = frame.get_bounding_rect(min_alpha=40)
                        self.assertEqual(frame.get_at((0,0)).a,0)
                        self.assertLess(bounds.width,frame.get_width())
                        self.assertLessEqual(bounds.bottom,frame.get_height()-2)
                        self.assertGreaterEqual(bounds.bottom,frame.get_height()-5)

    def test_all_idle_frames_are_used_instead_of_static_first_pose(self):
        for name in KITS:
            view = EntityView(self.assets)
            frames = self.assets.get_enemy_sprite_group(name,'idle')
            for i in range(8):
                view.enemy_idle_timer=i*180+1
                self.assertIs(view.get_enemy_frame(SimpleNamespace(name=name)),frames[i])

    def test_regular_attacks_and_ultimate_reach_every_pose(self):
        for name in BOSS_ULTIMATE_ANIMATIONS:
            for group in ('atk1','atk2','atk3','atk4','ultimate'):
                frames = (self.assets.get_boss_ultimate_sprites(name) if group=='ultimate'
                          else self.assets.get_enemy_sprite_group(name,group))
                if not frames: continue
                view = EntityView(self.assets)
                view.trigger_attack('enemy','atk1' if group=='ultimate' else group,name,ultimate=group=='ultimate')
                seen = set()
                for i in range(1000):
                    view.attack_timer = i*view.enemy_attack_duration/1000
                    frame = view.get_enemy_frame(SimpleNamespace(name=name))
                    seen.add(next(j for j,f in enumerate(frames) if f is frame))
                self.assertEqual(seen,set(range(8)),(name,group))

    def test_melee_flash_tracks_new_strike_pose(self):
        view = EntityView(self.assets)
        view.trigger_attack('enemy','atk1','Carrasco da Vigília')
        view.trigger_flash('player')
        view.update(view.enemy_attack_duration*.51)
        self.assertEqual(view.player_flash,0)
        view.update(view.enemy_attack_duration*.02)
        self.assertGreater(view.player_flash,0)

    def test_approved_boss_magic_layers_remain_independent(self):
        for name in BOSS_ULTIMATE_ANIMATIONS:
            self.assertEqual(len(self.assets.get_boss_ultimate_sprites(name,effects=True)),4)

    def test_frame_boundaries_are_clamped(self):
        self.assertEqual(kit_frame(-1),0)
        self.assertEqual(kit_frame(5),7)
        self.assertEqual([kit_frame(p) for p in STRIKE_BOUNDARIES],list(range(8)))

    def test_all_actions_close_on_idle_without_global_clock_jump(self):
        for name,(_,groups) in KITS.items():
            idle=self.assets.get_enemy_sprite_group(name,'idle')[0]
            for group in groups:
                if group=='transition':continue
                frames=(self.assets.get_boss_ultimate_sprites(name) if group=='ultimate'
                        else self.assets.get_enemy_sprite_group(name,group))
                self.assertEqual(pygame.image.tobytes(frames[-1],'RGBA'),pygame.image.tobytes(idle,'RGBA'),(name,group))
            view=EntityView(self.assets)
            view.trigger_attack('enemy','atk1',name)
            view.update(view.enemy_attack_duration+10)
            self.assertEqual(view.enemy_idle_timer,0)
            self.assertIs(view.get_enemy_frame(SimpleNamespace(name=name)),idle)
            view.update(181)
            self.assertIs(view.get_enemy_frame(SimpleNamespace(name=name)),self.assets.get_enemy_sprite_group(name,'idle')[1])

    def test_shared_palette_and_no_alternating_idle_brightness(self):
        import json
        from pathlib import Path
        import numpy as np
        root=Path(__file__).resolve().parents[1]/'assets/bosses/eight_frames'
        for name,(slug,groups) in KITS.items():
            palette=set(map(tuple,json.loads((root/slug/'palette.json').read_text(encoding='utf8'))))
            brightness=[]
            for group in groups:
                frames=(self.assets.get_boss_ultimate_sprites(name) if group=='ultimate'
                        else self.assets.get_enemy_sprite_group(name,group))
                for frame in frames:
                    alpha=pygame.surfarray.array_alpha(frame)
                    rgb=pygame.surfarray.array3d(frame)
                    self.assertTrue(set(map(tuple,rgb[alpha>210])).issubset(palette),(name,group))
                    if group=='idle':brightness.append(float(rgb[alpha>210].mean()))
            self.assertLess(max(brightness)-min(brightness),5,name)
