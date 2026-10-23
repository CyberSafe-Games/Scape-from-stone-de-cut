"""Regressão de temporização, direção e transparência do Corpo Seco."""
from pathlib import Path
import unittest

from src.systems.animation_timing import frame_index, animation_duration, dash_distance


ASSETS = Path(__file__).resolve().parents[1] / 'assets' / 'corpo_seco'


class CorpoSecoAnimationTests(unittest.TestCase):
    def test_all_animation_sets_exist(self):
        for group in ('idle', 'atk1', 'atk3', 'atk4', 'dano', 'healer2'):
            files = sorted(ASSETS.glob(f'{group}_*.png'))
            self.assertEqual(len(files), 4, group)

    def test_attack_timing_is_action_specific(self):
        self.assertGreater(animation_duration('atk4'), animation_duration('atk3'))
        self.assertGreater(animation_duration('atk3'), animation_duration('atk1'))
        self.assertEqual(animation_duration('atk', 700), 700)

    def test_spin_cycles_through_frames_without_out_of_range(self):
        indexes = [frame_index('atk4', t, 1290, 4) for t in range(0,1290,80)]
        self.assertTrue(all(0 <= i < 4 for i in indexes))
        self.assertGreaterEqual(indexes.count(2), 2)
        self.assertIn(3, indexes)

    def test_regular_action_reaches_last_frame(self):
        self.assertEqual(frame_index('atk1', 810, 810, 4), 3)
        self.assertEqual(frame_index('atk1', 0, 810, 4), 0)

    def test_special_does_not_dash_entire_arena(self):
        self.assertLess(dash_distance('atk4', True), dash_distance('atk1', True))
        self.assertIsNone(dash_distance('atk1', False))

    def test_pngs_use_alpha_channel(self):
        for path in ASSETS.glob('*.png'):
            with self.subTest(name=path.name), path.open('rb') as fh:
                header = fh.read(26)
                self.assertEqual(header[:8], b'\x89PNG\r\n\x1a\n')
                self.assertEqual(header[25], 6, 'Esperado PNG RGBA')

    def test_checkerboard_removed_at_corners(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest('Pillow opcional não instalado')
        for group in ('atk1','atk3','healer2'):
            for path in ASSETS.glob(f'{group}_*.png'):
                with self.subTest(name=path.name):
                    image=Image.open(path).convert('RGBA')
                    w,h=image.size
                    # Bordas não devem mais conter o quadriculado branco opaco.
                    corners=[image.getpixel(pt)[3] for pt in ((0,0),(w-1,0),(0,h-1),(w-1,h-1))]
                    self.assertLess(max(corners),30)


if __name__ == '__main__':
    unittest.main()
