"""Doze poses efetivas, oito chaves aprovadas e impactos preservados."""
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
from src.systems.animation_inbetweens import ORIGINAL_TWELVE_INDICES, NEW_TWELVE_INDICES, frame_boundaries


class BossTwelveFramesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init();pygame.display.set_mode((1,1))
        cls.assets = AssetManager()

    def test_all_eight_forms_have_twelve_distinct_frames_for_every_group(self):
        for name,(_,groups) in KITS.items():
            for group in groups:
                with self.subTest(name=name,group=group):
                    frames = (self.assets.get_boss_ultimate_sprites(name) if group=='ultimate'
                              else self.assets.get_enemy_sprite_group(name,group))
                    self.assertEqual(len(frames),12)
                    # Some original ultimates begin and end in the same idle pose.
                    unique = {pygame.image.tobytes(f,'RGBA') for f in frames}
                    self.assertGreaterEqual(len(unique),11)
                    added = {pygame.image.tobytes(frames[i],'RGBA') for i in NEW_TWELVE_INDICES}
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
            for i in range(12):
                view.enemy_idle_timer=i*120+1
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
                self.assertEqual(seen,set(range(12)),(name,group))

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
            self.assertEqual(len(self.assets.get_boss_ultimate_sprites(name,effects=True)),12)

    def test_frame_boundaries_are_clamped(self):
        self.assertEqual(kit_frame(-1),0)
        self.assertEqual(kit_frame(5),7)
        self.assertEqual([kit_frame(p) for p in STRIKE_BOUNDARIES],list(range(8)))
        self.assertEqual(kit_frame(5,12),11)
        self.assertEqual([kit_frame(p,12) for p in frame_boundaries(STRIKE_BOUNDARIES,12)],list(range(12)))

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
            view.update(121)
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

    def test_all_eight_approved_poses_remain_pixel_identical(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]/'assets/bosses/eight_frames'
        for name,(slug,groups) in KITS.items():
            for group in groups:
                frames=(self.assets.get_boss_ultimate_sprites(name) if group=='ultimate'
                        else self.assets.get_enemy_sprite_group(name,group))
                for original,index in enumerate(ORIGINAL_TWELVE_INDICES,1):
                    source=pygame.image.load(str(root/slug/f'{group}_{original}.png')).convert_alpha()
                    self.assertEqual(pygame.image.tobytes(source,'RGBA'),pygame.image.tobytes(frames[index],'RGBA'),(name,group,index))

    def test_all_duo_support_hurt_and_transition_poses_are_reachable(self):
        from src.config.layout import FLASH_DURATION
        from src.systems.alvaro_tex_animations import TRANSITION_MS
        for name,(_,groups) in KITS.items():
            for group in groups:
                if group not in ('def','healer2','dano','transition') and not name.startswith('álvaro'):continue
                if group=='idle':continue
                with self.subTest(name=name,group=group):
                    view=EntityView(self.assets)
                    frames=self.assets.get_enemy_sprite_group(name,group)
                    if group.startswith('atk'):view.trigger_attack('enemy',group,name)
                    elif group in ('def','healer2'):view.trigger_enemy_action(group,name)
                    seen=set()
                    for step in range(1000):
                        p=step/1000
                        if group.startswith('atk'):view.attack_timer=p*view.enemy_attack_duration
                        elif group=='transition':view.phase_transition_timer=p*TRANSITION_MS
                        elif group=='dano':view.enemy_flash=FLASH_DURATION*(1-p)
                        else:view.enemy_action_timer=p*view.enemy_action_duration
                        frame=view.get_enemy_frame(SimpleNamespace(name=name))
                        seen.add(next(i for i,f in enumerate(frames) if f is frame))
                    self.assertEqual(seen,set(range(12)))

    def test_original_attack_and_tremor_boundaries_keep_their_timing(self):
        from src.systems.gordofera_animations import tremor_frame
        from src.systems.alvaro_tex_animations import attack_frame
        for release in (None,.30,.42,.44,.50,.58):
            for step in range(1000):
                p=step/1000
                old=kit_frame(p,8,release)
                new=kit_frame(p,12,release)
                # Inserted poses lie after their preceding key and before its next key.
                self.assertGreaterEqual(new,ORIGINAL_TWELVE_INDICES[old])
                if old<7:self.assertLess(new,ORIGINAL_TWELVE_INDICES[old+1])
        self.assertEqual(tremor_frame(.64,12),8)
        self.assertEqual(attack_frame(.5,12),6)
