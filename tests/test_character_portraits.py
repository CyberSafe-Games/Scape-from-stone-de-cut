import os
import unittest
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
from src.core.asset_manager import AssetManager
from src.systems.character_portraits import PORTRAITS
from src.ui.battle_hud import BattleHUD


class CharacterPortraitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init();pygame.display.set_mode((1,1))
        cls.assets = AssetManager()

    def test_all_supplied_portraits_load_in_the_hud_and_are_cached(self):
        hud = BattleHUD(self.assets)
        surface = pygame.Surface((1280,720))
        for name in PORTRAITS:
            with self.subTest(name=name):
                portrait = self.assets.get_character_portrait(name,(58,61))
                self.assertIsInstance(portrait,pygame.Surface)
                self.assertEqual(portrait.get_size(),(58,61))
                self.assertIs(self.assets.get_character_portrait(name.upper(),(58,61)),portrait)
                hud.portrait(surface,pygame.Rect(20,20,88,96),name)
                self.assertIs(hud._portraits[(name,(58,61))],portrait)

    def test_phase_two_has_its_own_crop_and_missing_portraits_keep_the_sprite_fallback(self):
        duo = self.assets.get_character_portrait('Álvaro e Tex',(58,61))
        small = self.assets.get_character_portrait('Álvaro e Tex · Pequeno',(58,61))
        self.assertNotEqual(pygame.image.tobytes(duo,'RGB'),pygame.image.tobytes(small,'RGB'))
        hud = BattleHUD(self.assets)
        surface = pygame.Surface((1280,720))
        for name in ('Slime','Macaco Selvagem'):
            self.assertIsNone(self.assets.get_character_portrait(name,(58,61)))
            hud.portrait(surface,pygame.Rect(20,20,88,96),name)
            self.assertIsInstance(hud._portraits[(name.lower(),(58,61))],pygame.Surface)
        hud.portrait(surface,pygame.Rect(20,20,88,96),'Jaum Manel',player=True)
        self.assertIn(('player',(58,61)),hud._portraits)
