"""Regressões dos sprites compactos do Corpo Seco, sem dependência do Pygame.

Pillow é opcional e só é necessário para a inspeção dos pixels.
"""
from pathlib import Path
import ast
import struct
import unittest

try:
    from PIL import Image
except ImportError:
    Image = None

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets' / 'corpo_seco'
GROUPS = ('idle', 'atk1', 'atk3', 'atk4', 'healer2', 'dano')
CANVAS_SIZE = (312, 256)


class CorpoSecoVisualScaleTests(unittest.TestCase):
    def test_24_rgba_frames_share_identical_canvas(self):
        """A mesma área evita esticamentos e saltos de escala na troca de frame."""
        for group in GROUPS:
            for n in range(1, 5):
                path = ASSETS / f'{group}_{n}.png'
                with self.subTest(frame=path.name):
                    self.assertTrue(path.is_file())
                    with path.open('rb') as f:
                        header = f.read(26)
                    self.assertEqual(header[:8], b'\x89PNG\r\n\x1a\n')
                    self.assertEqual(struct.unpack('>II', header[16:24]), CANVAS_SIZE)
                    self.assertEqual(header[25], 6)  # PNG Truecolor com alfa

    def test_one_small_boss_scale_constant_controls_all_animations(self):
        source = (ROOT / 'src' / 'core' / 'asset_manager.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        values = [node.value.value for node in tree.body
                  if isinstance(node, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == 'CORPO_SECO_RENDER_SCALE'
                          for t in node.targets)
                  and isinstance(node.value, ast.Constant)]
        self.assertEqual(values, [0.74])

    @unittest.skipUnless(Image is not None, 'Pillow opcional não instalado')
    def test_all_frames_are_transparent_and_share_ground_line(self):
        for group in GROUPS:
            for n in range(1, 5):
                path = ASSETS / f'{group}_{n}.png'
                with self.subTest(frame=path.name):
                    image = Image.open(path).convert('RGBA')
                    alpha = image.getchannel('A')
                    self.assertEqual(alpha.getpixel((0, 0)), 0)
                    self.assertEqual(alpha.getpixel((311, 255)), 0)
                    bounds = alpha.point(lambda a: 255 if a > 40 else 0).getbbox()
                    self.assertIsNotNone(bounds)
                    # Pés alinhados no mesmo chão; o canvas nunca é recortado.
                    self.assertGreaterEqual(bounds[3], 250)
                    self.assertLessEqual(bounds[3], 254)

    @unittest.skipUnless(Image is not None, 'Pillow opcional não instalado')
    def test_idle_height_does_not_bounce(self):
        heights = []
        for n in range(1, 5):
            image = Image.open(ASSETS / f'idle_{n}.png').convert('RGBA')
            bb = image.getchannel('A').point(lambda a: 255 if a > 40 else 0).getbbox()
            heights.append(bb[3] - bb[1])
        self.assertLessEqual(max(heights) - min(heights), 4, heights)


if __name__ == '__main__':
    unittest.main()
