import os
import unittest
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
from src.core.asset_manager import AssetManager
from src.systems.character_portraits import FRAMED_PORTRAITS, PORTRAITS
from src.ui.battle_hud import BattleHUD


class CharacterPortraitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init();pygame.display.set_mode((1,1))
        cls.assets = AssetManager()

    def test_all_supplied_portraits_load_in_the_hud_and_are_cached(self):
        hud = BattleHUD(self.assets)
        surface = pygame.Surface((1920,1080))
        for name in PORTRAITS:
            with self.subTest(name=name):
                portrait = self.assets.get_character_portrait(name,(58,61))
                self.assertIsInstance(portrait,pygame.Surface)
                self.assertEqual(portrait.get_size(),(58,61))
                self.assertIs(self.assets.get_character_portrait(name.upper(),(58,61)),portrait)
                hud.portrait(surface,pygame.Rect(20,20,88,96),name)
                self.assertIs(hud._portraits[(name,(88,96))],
                              self.assets.get_character_portrait(name,(88,96)))

    def test_phase_two_has_its_own_crop_and_missing_portraits_keep_the_sprite_fallback(self):
        duo = self.assets.get_character_portrait('Álvaro e Tex',(58,61))
        small = self.assets.get_character_portrait('Álvaro e Tex · Pequeno',(58,61))
        self.assertNotEqual(pygame.image.tobytes(duo,'RGB'),pygame.image.tobytes(small,'RGB'))
        hud = BattleHUD(self.assets)
        surface = pygame.Surface((1920,1080))
        for name in ('Slime','Macaco Selvagem'):
            self.assertIsInstance(self.assets.get_character_portrait(name,(58,61)),pygame.Surface)
            hud.portrait(surface,pygame.Rect(20,20,88,96),name)
            self.assertIsInstance(hud._portraits[(name.lower(),(88,96))],pygame.Surface)
        hud.portrait(surface,pygame.Rect(20,20,88,96),'Jaum Manel',player=True)
        self.assertIn(('jaum manel',(88,96)),hud._portraits)

    def test_zanzara_keeps_approved_face_inside_protagonist_frame(self):
        from pathlib import Path
        from src.systems.character_portraits import FRAMED_PORTRAITS
        root = Path(__file__).resolve().parents[1]
        frame = pygame.image.load(str(root/'assets/portraits/source/framed/manel.png')).convert_alpha()
        portrait = self.assets.get_character_portrait('Zanzara', frame.get_size())
        self.assertIn('zanzara', FRAMED_PORTRAITS)
        for point in ((5, 200), (294, 200), (150, 3), (150, 397), (14, 8)):
            self.assertEqual(portrait.get_at(point), frame.get_at(point), point)
        self.assertNotEqual(pygame.image.tobytes(portrait, 'RGBA'), pygame.image.tobytes(frame, 'RGBA'))
        self.assertEqual(PORTRAITS['zanzara'][0], 'bosses/zanzara-necromante-v8.png')

    def test_every_common_uses_pixel_identical_protagonist_frame_without_old_overlay(self):
        from pathlib import Path
        from src.systems.normal_enemy_catalog import BIOME_ENEMIES
        root=Path(__file__).resolve().parents[1]
        frame=pygame.image.load(str(root/'assets/portraits/source/framed/manel.png')).convert_alpha()
        points=((5,200),(294,200),(150,3),(150,397),(14,8))
        from src.systems.enemy_factory import ENEMY_TYPES
        names=set(name for group in BIOME_ENEMIES.values() for name in group)
        names.update(name for name,_,_ in ENEMY_TYPES)
        for name in names:
            portrait=self.assets.get_character_portrait(name,frame.get_size())
            with self.subTest(name=name):
                self.assertIsInstance(portrait,pygame.Surface)
                for point in points:self.assertEqual(portrait.get_at(point),frame.get_at(point))
                self.assertNotEqual(pygame.image.tobytes(portrait,'RGBA'),pygame.image.tobytes(frame,'RGBA'))
        self.assertFalse((root/'assets/ui/hud_portrait.png').exists())

    def test_common_registries_use_real_portrait_files_without_sprite_fallback(self):
        from src.systems.character_portraits import COMMON_PORTRAIT_SPECS
        from src.systems.normal_enemy_catalog import BIOME_ENEMIES
        from pathlib import Path
        from unittest.mock import patch
        names={name.lower() for group in BIOME_ENEMIES.values() for name in group}
        self.assertEqual(set(COMMON_PORTRAIT_SPECS),names)
        from src.systems.enemy_factory import ENEMY_TYPES
        from src.systems.character_portraits import PORTRAITS
        names.update(name.lower() for name,_,_ in ENEMY_TYPES)
        root=Path(__file__).resolve().parents[1]/'assets/portraits/source'
        with patch.object(self.assets,'get_enemy_sprite_group',side_effect=AssertionError('Recorte de sprite não permitido no retrato comum')):
            for name in names:
                filename,crop,mode=PORTRAITS[name]
                self.assertTrue((root/filename).is_file(),name)
                self.assertEqual(mode,'framed-contain')
                self.assets._character_portraits.pop((name,(132,144)),None)
                self.assertIsInstance(self.assets.get_character_portrait(name,(132,144)),pygame.Surface)

    def test_contain_composition_keeps_all_four_corners_for_wide_tall_and_square_art(self):
        colors=('red','green','blue','yellow')
        for size in ((500,80),(80,500),(300,300)):
            source=pygame.Surface(size,pygame.SRCALPHA)
            source.fill((25,22,18))
            w,h=size
            for rect,color in zip(((0,0,15,15),(w-15,0,15,15),(0,h-15,15,15),(w-15,h-15,15,15)),colors):
                source.fill(color,rect)
            result=self.assets._portrait_with_protagonist_frame(source,fit='contain')
            # A região interna contém os quatro marcadores; cover perderia dois.
            inner=result.subsurface((16,18,268,364))
            for color in colors:
                count=pygame.mask.from_threshold(inner,pygame.Color(color),(8,8,8,255)).count()
                self.assertGreater(count,0,(size,color))

    def test_slime_and_monkey_have_dedicated_unframed_portraits(self):
        from src.systems.character_portraits import COMMON_PORTRAIT_SPECS
        for name in ('slime','macaco selvagem'):
            filename,crop,mode=COMMON_PORTRAIT_SPECS[name]
            self.assertTrue(filename.startswith('dedicated/'))
            self.assertEqual(crop,(0,0,1,1))
            portrait=self.assets.get_character_portrait(name,(132,144))
            self.assertEqual(portrait.get_size(),(132,144))
