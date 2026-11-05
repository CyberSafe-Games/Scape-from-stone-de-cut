"""Oito efeitos reais, chaves originais preservadas e impacto sincronizado."""
import os
import unittest
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
from src.core.asset_manager import AssetManager
from src.systems.boss_ultimate_animations import BOSS_ULTIMATE_ANIMATIONS,boss_effect_frame
from src.ui.boss_ultimate_fx import draw_boss_ultimate_fx
from src.ui.entity_view import EntityView


class BossEightEffectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init();pygame.display.set_mode((1,1))
        cls.assets=AssetManager()

    def test_old_key_drawings_remain_identical_and_new_poses_are_distinct(self):
        root=Path(__file__).resolve().parents[1]/'assets/boss_ultimate_effects'
        for name,spec in BOSS_ULTIMATE_ANIMATIONS.items():
            frames=self.assets.get_boss_ultimate_sprites(name,effects=True)
            self.assertEqual(len(frames),8,name)
            self.assertEqual(len({pygame.image.tobytes(f,'RGBA') for f in frames}),8,name)
            for i in range(4):
                original=pygame.image.load(str(root/spec.asset_id/f'effect_{i+1}.png')).convert_alpha()
                self.assertEqual(pygame.image.tobytes(frames[i*2],'RGBA'),pygame.image.tobytes(original,'RGBA'),(name,i))
            for frame in frames:
                self.assertEqual(frame.get_size(),(384,320))
                b=frame.get_bounding_rect(min_alpha=10)
                self.assertGreater(b.left,0)
                self.assertLess(b.right,384)
                self.assertGreater(b.top,0)
                self.assertLess(b.bottom,320)

    def test_every_effect_is_reached_with_ground_impact_reserved_for_the_hit(self):
        for name,spec in BOSS_ULTIMATE_ANIMATIONS.items():
            seen={boss_effect_frame(i/1000,spec) for i in range(1000)}
            self.assertEqual(seen,set(range(8)),name)
            self.assertLess(boss_effect_frame(spec.release-.0001,spec),2)
            self.assertEqual(boss_effect_frame(spec.release,spec),2)
            if spec.mode in ('execution','tremor'):
                self.assertEqual(boss_effect_frame(spec.impact-.0001,spec),3)
                self.assertEqual(boss_effect_frame(spec.impact,spec),4)
            else:
                self.assertEqual(boss_effect_frame(spec.impact-.0001,spec),5)
                self.assertEqual(boss_effect_frame(spec.impact,spec),6)
            self.assertEqual(boss_effect_frame(1,spec),7)

    def test_all_eight_effects_render_in_arena_and_disappear_at_end(self):
        for name,spec in BOSS_ULTIMATE_ANIMATIONS.items():
            view=EntityView(self.assets)
            view.trigger_attack('enemy','atk2',name,ultimate=True)
            seen=set()
            for step in range(100):
                p=(step+.5)/100
                view.attack_timer=p*spec.duration
                seen.add(boss_effect_frame(p,spec))
                screen=pygame.Surface((1280,720),pygame.SRCALPHA)
                draw_boss_ultimate_fx(screen,view,True)
                draw_boss_ultimate_fx(screen,view)
                b=screen.get_bounding_rect()
                self.assertGreater(b.width,0)
                self.assertGreaterEqual(b.top,116)
                self.assertLessEqual(b.bottom,516)
            self.assertEqual(seen,set(range(8)),name)
            view.attack_timer=spec.duration
            screen.fill((0,0,0,0))
            draw_boss_ultimate_fx(screen,view,True)
            draw_boss_ultimate_fx(screen,view)
            self.assertEqual(screen.get_bounding_rect().width,0)
