"""Escala e apoio do kit atual de Jan-Pietro, com oito poses nativas por folha."""
from pathlib import Path
import unittest
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'assets/bosses/sheets_eight/corpo_seco'
GROUPS=('idle','atk1','atk3','ultimate','healer2','dano')


class CorpoSecoVisualScaleTests(unittest.TestCase):
    def test_all_sheets_share_canvas_and_alpha(self):
        for group in GROUPS:
            with Image.open(FOLDER/f'{group}.png') as sheet:
                self.assertEqual(sheet.mode,'RGBA')
                self.assertEqual(sheet.size,(1792,640))
                for i in range(8):
                    frame=sheet.crop(((i%4)*448,(i//4)*320,(i%4+1)*448,(i//4+1)*320))
                    self.assertEqual(frame.getpixel((0,0))[3],0)
                    bounds=frame.getchannel('A').point(lambda a:255 if a>100 else 0).getbbox()
                    self.assertIsNotNone(bounds)
                    self.assertLessEqual(bounds[3],318)
                    self.assertGreaterEqual(bounds[3],314)

    def test_native_scale_is_baked_once_and_idle_does_not_bounce(self):
        import json
        manifest=json.loads((FOLDER.parent/'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['bosses']['corpo_seco']['body_height'],132)
        with Image.open(FOLDER/'idle.png') as sheet:
            heights=[]
            for i in range(8):
                frame=sheet.crop(((i%4)*448,(i//4)*320,(i%4+1)*448,(i//4+1)*320))
                b=frame.getchannel('A').point(lambda a:255 if a>100 else 0).getbbox()
                heights.append(b[3]-b[1])
            self.assertLessEqual(max(heights)-min(heights),4)

    def test_all_48_frames_keep_an_opaque_body_including_repaired_thrust(self):
        import numpy as np
        for group in GROUPS:
            with Image.open(FOLDER/f'{group}.png') as sheet:
                for i in range(8):
                    frame=sheet.crop(((i%4)*448,(i//4)*320,(i%4+1)*448,(i//4+1)*320))
                    r,g,b,a=np.array(frame).astype(int).transpose(2,0,1)
                    body=(a>210)&(r>g*1.1)&(r<g*2.2)&(g>b*1.1)&(r>45)
                    self.assertGreater(int(body.sum()),400,(group,i+1))

    def test_spin_regeneration_and_both_slashes_keep_their_own_colors(self):
        import numpy as np
        for group,color in [('ultimate','purple'),('healer2','green'),('atk1','red'),('atk3','red')]:
            with Image.open(FOLDER/f'{group}.png') as sheet:
                r,g,b,a=np.array(sheet).astype(int).transpose(2,0,1)
                if color=='purple':magic=(b>r*1.1)&(r>g*1.12)&(b>110)
                elif color=='green':magic=(g>r*1.2)&(g>b*1.2)&(g>100)
                else:magic=(r>g*1.65)&(r>b*1.65)&(r>140)
                self.assertGreater(int((magic&(a>70)).sum()),150,group)


if __name__=='__main__':unittest.main()
