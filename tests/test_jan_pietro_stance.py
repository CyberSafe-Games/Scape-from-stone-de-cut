"""Regressões do pivô visível e do caminho real de desenho de Jan-Pietro."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
from PIL import Image

from devtools.stabilize_jan_pietro import support_anchor,BOOT_TOP
from src.core.asset_manager import AssetManager
from src.systems.jan_pietro_animation import FOOT_ANCHOR,IDLE_FRAME_MS,IDLE_SEQUENCE,idle_frame
from src.ui.entity_view import EntityView
from src.config.layout import ENEMY_X,PLAYER_GROUND_Y

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'assets/bosses/sheets_eight/corpo_seco'


class JanPietroStanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init();pygame.display.set_mode((1,1))
        cls.assets=AssetManager()

    def test_all_48_frames_have_the_same_boot_anchor(self):
        for file in FOLDER.glob('*.png'):
            with Image.open(file) as sheet:
                for i in range(8):
                    frame=sheet.convert('RGBA').crop(((i%4)*448,(i//4)*320,(i%4+1)*448,(i//4+1)*320))
                    self.assertEqual(support_anchor(frame),FOOT_ANCHOR,(file.name,i+1))

    def test_idle_boot_pixels_are_identical_and_all_eight_upper_poses_remain(self):
        frames=self.assets.get_enemy_sprite_group('Corpo Seco','idle')
        reference=pygame.image.tobytes(frames[0].subsurface((0,BOOT_TOP,448,320-BOOT_TOP)),'RGBA')
        for i,frame in enumerate(frames):
            self.assertEqual(pygame.image.tobytes(frame.subsurface((0,BOOT_TOP,448,320-BOOT_TOP)),'RGBA'),reference,i)
        self.assertEqual(len({pygame.image.tobytes(f,'RGBA') for f in frames}),8)

    def test_real_interpolated_draw_path_keeps_world_foot_pixels_fixed(self):
        view=EntityView(self.assets)
        enemy=SimpleNamespace(name='Corpo Seco')
        region=pygame.Rect(ENEMY_X-150,PLAYER_GROUND_Y-32,300,32)
        reference=None
        for elapsed in range(0,len(IDLE_SEQUENCE)*IDLE_FRAME_MS*3,37):
            view.enemy_idle_timer=elapsed
            screen=pygame.Surface((1920,1080),pygame.SRCALPHA)
            view.draw_enemy(screen,enemy)
            pixels=pygame.image.tobytes(screen.subsurface(region),'RGBA')
            if reference is None:reference=pixels
            self.assertEqual(pixels,reference,elapsed)
        self.assertTrue(any(reference))

    def test_runtime_does_not_reanchor_idle_or_hurt_using_silhouette(self):
        view=EntityView(self.assets)
        enemy=SimpleNamespace(name='Corpo Seco')
        with patch('src.ui.entity_view.align_stance',side_effect=AssertionError('Pivô já preparado')):
            view.get_enemy_frame(enemy,interpolate=True)
            view.trigger_flash('enemy','Corpo Seco')
            view.get_enemy_frame(enemy,interpolate=True)

    def test_action_endpoints_share_exactly_the_idle_pose(self):
        idle=self.assets.get_enemy_sprite_group('Corpo Seco','idle')[0]
        pixels=pygame.image.tobytes(idle,'RGBA')
        for group in ('dano','atk1','atk3','healer2','ultimate'):
            frames=self.assets.get_boss_ultimate_sprites('Corpo Seco') if group=='ultimate' else self.assets.get_enemy_sprite_group('Corpo Seco',group)
            self.assertEqual(pygame.image.tobytes(frames[0],'RGBA'),pixels,group)
            self.assertEqual(pygame.image.tobytes(frames[-1],'RGBA'),pixels,group)

    def test_idle_clock_is_6_25_fps_and_ping_pong_has_no_wrap_jump(self):
        self.assertEqual(IDLE_FRAME_MS,160)
        self.assertEqual(tuple(idle_frame(i*160) for i in range(14)),IDLE_SEQUENCE)
        self.assertEqual(idle_frame(14*160),0)
        self.assertEqual(idle_frame(-1),0)
        self.assertEqual({idle_frame(t) for t in range(0,2240,17)},set(range(8)))

    def test_coordinate_report_covers_every_frame_without_per_frame_zoom(self):
        data=json.loads((FOLDER.parent/'manifest.json').read_text(encoding='utf-8'))['bosses']['corpo_seco']['alignment']
        self.assertEqual(data['anchor'],[224,318])
        self.assertFalse(data['runtime_alignment'])
        self.assertFalse(data['scale_per_frame'])
        self.assertEqual(sum(len(rows) for rows in data['frames'].values()),48)
        for rows in data['frames'].values():
            self.assertTrue(all(row['after_anchor']==[224,318] for row in rows))

    def test_idle_head_registration_removes_large_horizontal_sway(self):
        from devtools.stabilize_jan_pietro import head_center
        with Image.open(FOLDER/'idle.png') as sheet:
            centers=[head_center(sheet.convert('RGBA').crop(((i%4)*448,(i//4)*320,(i%4+1)*448,(i//4+1)*320))) for i in range(8)]
        self.assertLessEqual(max(x for x,y in centers)-min(x for x,y in centers),2)
        self.assertLessEqual(max(y for x,y in centers)-min(y for x,y in centers),3)


if __name__=='__main__':unittest.main()
