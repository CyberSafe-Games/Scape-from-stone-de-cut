"""Abertura real da moldura: HP cheio, parcial, vazio e simetria da HUD."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from pathlib import Path
from types import SimpleNamespace
import unittest
import pygame
from src.ui.battle_hud import BattleHUD
from src.config.combat_header import PLAYER_PANEL,ENEMY_PANEL


class HealthBarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))
        path=Path(__file__).resolve().parents[1]/'assets/ui/hud_health.png'
        cls.frame=pygame.image.load(str(path)).convert_alpha()
        font=pygame.font.Font(None,26)
        cls.assets=SimpleNamespace(get_ui_image=lambda key:cls.frame,
            get_character_portrait=lambda *args,**kwargs:None,menu_font=font,small_font=font)

    def setUp(self):self.hud=BattleHUD(self.assets)

    def render(self,hp,maximum=76):
        image=pygame.Surface((536,63),pygame.SRCALPHA)
        self.hud.health_bar(image,image.get_rect(),hp,maximum)
        return image

    def test_full_hp_fills_every_opaque_window_pixel_including_both_ends(self):
        full,empty=self.render(76),self.render(0)
        window=self.hud.health_window(full.get_size())
        checked=0
        for x in range(full.get_width()):
            for y in range(full.get_height()):
                if window.get_at((x,y)).a>=224:
                    self.assertGreater(full.get_at((x,y)).r,empty.get_at((x,y)).r+25,(x,y))
                    checked+=1
        self.assertGreater(checked,8000)
        bounds=window.get_bounding_rect(min_alpha=128)
        # O antigo inset de 18% deixava dezenas de pixels pretos em cada ponta.
        self.assertLess(bounds.left,60)
        self.assertGreater(bounds.right,476)

    def test_fill_never_changes_eagle_heads_or_gold_outside_the_window(self):
        full,empty=self.render(76),self.render(0)
        mask=self.hud.health_window(full.get_size())
        for x in range(full.get_width()):
            for y in range(full.get_height()):
                if mask.get_at((x,y)).a==0:
                    self.assertEqual(full.get_at((x,y)),empty.get_at((x,y)),(x,y))

    def test_partial_hp_uses_proportional_cutoff_and_zero_has_no_red(self):
        mask=self.hud.health_window((536,63))
        bounds=mask.get_bounding_rect(min_alpha=128)
        y=bounds.centery
        for hp in (76,57,38,19,0):
            image=self.render(hp)
            cutoff=bounds.left+round(bounds.width*hp/76)
            for x in range(bounds.left,bounds.right):
                if mask.get_at((x,y)).a<224:continue
                r,g,b,a=image.get_at((x,y))
                if x<cutoff:self.assertGreater(r,2*g,(hp,x))
                else:self.assertLess(r,55,(hp,x))

    def test_player_and_enemy_have_identical_full_health_channels(self):
        canvas=pygame.Surface((1920,1080))
        player,enemy=pygame.Rect(PLAYER_PANEL),pygame.Rect(ENEMY_PANEL)
        self.hud.combatant(canvas,player,'Jaum Manel',76,76,[])
        self.hud.combatant(canvas,enemy,'Álvaro e Tex',76,76,[],enemy=True)
        left=pygame.Rect(player.x+138,player.y+45,player.width-144,63)
        right=pygame.Rect(enemy.x,enemy.y+45,enemy.width-144,63)
        self.assertEqual(pygame.image.tobytes(canvas.subsurface(left),'RGB'),
                         pygame.image.tobytes(canvas.subsurface(right),'RGB'))

    def test_limits_and_missing_art_keep_a_safe_non_negative_fill(self):
        self.assertEqual(pygame.image.tobytes(self.render(-5),'RGBA'),pygame.image.tobytes(self.render(0),'RGBA'))
        self.assertEqual(pygame.image.tobytes(self.render(200),'RGBA'),pygame.image.tobytes(self.render(76),'RGBA'))
        self.assertEqual(pygame.image.tobytes(self.render(0,0),'RGBA'),pygame.image.tobytes(self.render(0),'RGBA'))
        hud=BattleHUD(SimpleNamespace(get_ui_image=lambda key:None))
        canvas=pygame.Surface((536,63),pygame.SRCALPHA)
        bounds=hud.health_bar(canvas,canvas.get_rect(),1,1)
        self.assertEqual(bounds,pygame.Rect(3,3,530,57))


if __name__=='__main__':unittest.main()
