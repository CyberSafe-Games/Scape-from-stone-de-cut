"""Grade nativa, identidade das fatias, ordem, direção e cadência dos três kits."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
from src.core.asset_manager import AssetManager
from src.systems.boss_sheet_kits import SHEET_KITS, sheet_pose
from src.systems.enemy_factory import create_point_enemy
from src.ui.entity_view import EntityView

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'assets/bosses/sheets_eight'


class BossSheetUpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))
        cls.assets=AssetManager()
        cls.manifest=json.loads((FOLDER/'manifest.json').read_text(encoding='utf-8'))

    def test_all_18_sheets_have_eight_frames_and_keep_internal_identity(self):
        self.assertEqual(len(self.manifest['audit']),18)
        self.assertEqual(self.manifest['direction'],'left')
        self.assertEqual(self.manifest['grid'],[4,2])
        self.assertEqual({create_point_enemy(i).name.lower() for i in (1,5,6)},set(SHEET_KITS))
        for name,(slug,aliases) in SHEET_KITS.items():
            groups=self.manifest['bosses'][slug]['groups']
            self.assertEqual(len(groups),6)
            for group,file in groups.items():
                sheet=pygame.image.load(str(FOLDER/slug/file))
                frames=self.assets.get_boss_ultimate_sprites(name) if group=='ultimate' else self.assets.get_enemy_sprite_group(name,group)
                self.assertEqual(len(frames),8)
                self.assertEqual(sheet.get_size(),(1792,640))
                for i,frame in enumerate(frames):
                    expected=sheet.subsurface(((i%4)*448,(i//4)*320,448,320))
                    self.assertEqual(pygame.image.tobytes(frame,'RGBA'),pygame.image.tobytes(expected,'RGBA'),(name,group,i))
                    self.assertEqual(frame.get_at((0,0)).a,0)
                    self.assertLess(frame.get_bounding_rect(min_alpha=50).bottom,319)
                    self.assertGreater(frame.get_bounding_rect(min_alpha=50).width,35)
            for alias,original in aliases.items():
                frames=self.assets.get_enemy_sprite_group(name,alias)
                source=self.assets.get_boss_ultimate_sprites(name) if original=='ultimate' else self.assets.get_enemy_sprite_group(name,original)
                self.assertIs(frames,source)

    def test_each_of_144_frames_was_audited_and_repairs_are_recorded(self):
        for key,audit in self.manifest['audit'].items():
            self.assertEqual(audit['logical_order'],list(range(1,9)),key)
            self.assertEqual(audit['anatomy_checked_frames'],list(range(1,9)),key)
        expected={'Boss1/Sprite4':[4,6], 'Boss5/Sprite4':[4], 'Boss6/Sprite5':[4], 'Boss6/Sprite6':[5,6,7]}
        self.assertEqual({k:v['frames'] for k,v in self.manifest['repairs'].items()},expected)

    def test_each_native_pose_is_reachable_in_normal_attack_support_and_ultimate(self):
        for name in SHEET_KITS:
            boss=create_point_enemy({'guardião da pedra':1,'corpo seco':5,'carrasco da vigília':6}[name])
            for action in [*boss.actions,boss.special_action]:
                view=EntityView(self.assets)
                special=action is boss.special_action
                frames=self.assets.get_boss_ultimate_sprites(name) if special else self.assets.get_enemy_sprite_group(name,action.visual_effect)
                if action.action_type=='attack':
                    view.trigger_attack('enemy',action.visual_effect,name,ultimate=special)
                    duration=view.enemy_attack_duration+view.enemy_recovery_ms
                else:
                    view.trigger_enemy_action(action.visual_effect,name)
                    duration=view.enemy_action_duration+view.enemy_recovery_ms
                seen=set()
                for step in range(1000):
                    if action.action_type=='attack':view.attack_timer=step*duration/1000
                    else:view.enemy_action_timer=step*duration/1000
                    frame=view.get_enemy_frame(boss)
                    seen.add(next(i for i,candidate in enumerate(frames) if candidate is frame))
                self.assertEqual(seen,set(range(8)),(name,action.name))

    def test_native_sampler_keeps_contact_and_a_readable_hold_for_every_frame(self):
        for contact in (.42,.52,.62,.64,.78):
            seen=[0]*8
            for step in range(1000):seen[sheet_pose(step/1000,contact)]+=1
            self.assertGreater(min(seen),15)
            self.assertEqual(sheet_pose(contact,contact),4)
        self.assertEqual(sheet_pose(-1),0)
        self.assertEqual(sheet_pose(5),7)

    def test_replaced_pose_directories_are_absent_but_independent_bear_remains(self):
        for slug,_ in SHEET_KITS.values():
            for version in ('eight_frames','twelve_frames'):
                self.assertFalse((ROOT/'assets/bosses'/version/slug).exists())
            self.assertFalse(list((ROOT/'assets'/slug).glob('idle_*.png')))
        self.assertTrue((ROOT/'assets/guardiao_da_pedra/urso_espiritual.png').is_file())
        self.assertIsNotNone(self.assets.get_enemy_projectile('Guardião da Pedra','atk2'))


if __name__=='__main__':unittest.main()
