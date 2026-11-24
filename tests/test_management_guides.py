"""Primeira visita, migração, rollback e cliques dos guias reais."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import pygame
from src.core.asset_manager import AssetManager
from src.scenes.shop_scene import ShopScene
from src.scenes.backpack_scene import BackpackScene
from src.scenes.roguelite_scene import RogueliteScene
from src.systems.save_manager import SaveManager, SaveError, SaveCorruptedError, SAVE_VERSION
from src.systems.management_tutorials import GUIDE_IDS, complete_guide
from src.config.combat_header import PLAYER_PANEL, ENEMY_PANEL, MENU_BUTTON, ARENA_TITLE
from src.config.settings import WIDTH, HEIGHT
from src.ui.frames import nine_slice, horizontal_frame
from src.ui.options_gear import OPTIONS_GEAR_RECT
from src.ui.helpers import wrap_text


class ManagementGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))
        cls.assets = AssetManager.__new__(AssetManager)
        cls.assets._fonts, cls.assets._ui_images, cls.assets._card_images = {}, {}, {}
        cls.assets._background, cls.assets._coin_icon = None, None
        cls.assets._init_fonts()
        cls.canvas = pygame.Surface((WIDTH,HEIGHT))

    def setUp(self):
        folder=tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.manager=SaveManager(folder.name)
        self.data=self.manager.create_save('slot_1')
        self.window=MagicMock()
        self.window.handle_window_event.return_value=False
        self.window.get_virtual_mouse_pos.return_value=(-1,-1)
        self.window.map_to_virtual.side_effect=lambda p:(round(p[0]*1.5),round(p[1]*1.5))

    def scene(self,cls,data=None,**kwargs):
        return cls(MagicMock(),self.window,self.assets,self.manager,data or self.data,**kwargs)

    def click(self,scene,rect):
        pos=(rect.centerx/1.5,rect.centery/1.5)
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos))

    def test_first_visit_is_independent_per_screen_and_manual_help_reopens(self):
        for cls,key in ((ShopScene,'shop'),(BackpackScene,'backpack'),(RogueliteScene,'workshop')):
            scene=self.scene(cls)
            self.assertTrue(scene.management_guide.active)
            self.assertTrue(scene.management_guide.finish())
            reopened=self.scene(cls)
            self.assertFalse(reopened.management_guide.active)
            self.click(reopened,reopened.management_guide.HELP_RECT)
            self.assertTrue(reopened.management_guide.active)
            self.assertEqual(reopened.management_guide.index,0)
            self.assertTrue(self.manager.load_save('slot_1')['perfil']['tutoriais_gerenciamento'][key])

    def test_flags_survive_new_run_and_remain_isolated_by_slot(self):
        self.assertTrue(complete_guide(self.manager,self.data,'shop')[0])
        self.assertTrue(self.manager.end_run(self.data,1)[0])
        self.assertTrue(self.manager.new_run(self.data)[0])
        flags=self.manager.load_save('slot_1')['progresso']['tutoriais_gerenciamento']
        self.assertEqual(flags,dict(shop=True,backpack=False,workshop=False))
        other=self.manager.create_save('slot_2')
        self.assertFalse(any(other['perfil']['tutoriais_gerenciamento'].values()))

    def test_migration_from_v14_keeps_inventory_profile_and_flags(self):
        old=deepcopy(self.data)
        old['versao']=14
        old['perfil'].pop('tutoriais_gerenciamento')
        old['progresso'].pop('tutoriais_gerenciamento')
        old.pop('run',None)
        before=deepcopy(old['progresso']['copies'])
        migrated=self.manager._normalize(old,'slot_1')
        self.assertEqual(migrated['versao'],SAVE_VERSION)
        self.assertEqual(migrated['progresso']['copies'],before)
        self.assertEqual(migrated['perfil']['fragmentos'],self.data['perfil']['fragmentos'])
        self.assertEqual(migrated['progresso']['tutoriais_gerenciamento'],dict.fromkeys(GUIDE_IDS,False))

    def test_serialized_profile_flags_reload_and_reject_non_booleans(self):
        self.assertTrue(complete_guide(self.manager,self.data,'workshop')[0])
        disk=json.loads(Path(self.manager._path('slot_1')).read_text(encoding='utf-8'))
        self.assertTrue(disk['perfil']['tutoriais_gerenciamento']['workshop'])
        self.assertNotIn('tutoriais_gerenciamento',disk['run'])
        disk['perfil']['tutoriais_gerenciamento']['shop']='false'
        with self.assertRaises(SaveCorruptedError):
            self.manager._normalize(disk,'slot_1')

    def test_guide_consumes_underlying_buy_equip_upgrade_and_wheel_events(self):
        for cls in (ShopScene,BackpackScene,RogueliteScene):
            scene=self.scene(cls)
            scene.draw(self.canvas)
            before=deepcopy(self.data)
            targets=([scene.heal_button,*scene.offer_rects.values()] if cls is ShopScene else
                     [scene.slots[0],scene.add_rect] if cls is BackpackScene else
                     [scene.material_button,scene.upgrade_button])
            for rect in targets:
                # Clique fora do painel do guia permanece sem efeito na economia/deck.
                if not scene.management_guide.layout()[0].collidepoint(rect.center):
                    self.click(scene,rect)
            scene.handle_event(pygame.event.Event(pygame.MOUSEWHEEL,y=-1))
            self.assertEqual(self.data,before,cls.__name__)

    def test_failed_save_rolls_back_and_keeps_guide_open_for_retry(self):
        scene=self.scene(ShopScene)
        before=deepcopy(self.data)
        with patch.object(self.manager,'save',side_effect=SaveError('falha simulada')):
            self.assertFalse(scene.management_guide.finish())
        self.assertEqual(self.data,before)
        self.assertTrue(scene.management_guide.active)
        self.assertTrue(scene.management_guide.finish())
        self.assertFalse(scene.management_guide.active)

    def test_scaled_mouse_navigation_finishes_without_buying(self):
        scene=self.scene(ShopScene)
        coins=self.data['progresso']['moedas']
        for i in range(len(scene.management_guide.steps)):
            self.assertEqual(scene.management_guide.index,i)
            self.click(scene,scene.management_guide.layout()[2])
        self.assertFalse(scene.management_guide.active)
        self.assertEqual(self.data['progresso']['moedas'],coins)

    def test_workshop_preparation_does_not_show_upgrade_guide(self):
        scene=self.scene(RogueliteScene,preparation=True)
        self.assertIsNone(scene.management_guide)

    def test_all_steps_fit_canvas_and_help_avoids_options_and_navigation(self):
        bounds=self.canvas.get_rect()
        for cls in (ShopScene,BackpackScene,RogueliteScene):
            scene=self.scene(cls)
            scene.draw(self.canvas)
            guide=scene.management_guide
            self.assertFalse(guide.HELP_RECT.colliderect(OPTIONS_GEAR_RECT))
            if cls is BackpackScene:self.assertFalse(guide.HELP_RECT.colliderect(scene.back_rect))
            for i,step in enumerate(guide.steps):
                guide.index=i
                scene.draw(self.canvas)
                box,*buttons=guide.layout()
                self.assertTrue(bounds.contains(box))
                self.assertTrue(bounds.contains(guide.target_rect()))
                self.assertTrue(all(box.contains(b) for b in buttons))
                lines=wrap_text(step.text,self.assets.small_font,box.width-52)
                self.assertLessEqual(box.y+113+len(lines)*self.assets.small_font.get_linesize(),box.bottom-75)

    def test_hud_panels_are_mirrored_and_menu_is_centered_without_overlap(self):
        player,enemy,menu,title=map(pygame.Rect,(PLAYER_PANEL,ENEMY_PANEL,MENU_BUTTON,ARENA_TITLE))
        self.assertEqual(player.size,enemy.size)
        self.assertEqual(player.left,WIDTH-enemy.right)
        self.assertEqual(menu.centerx,WIDTH//2)
        self.assertFalse(menu.colliderect(title))
        for r in (menu,title):
            self.assertGreater(r.left,player.right)
            self.assertLess(r.right,enemy.left)

    def test_nine_slice_preserves_colored_corners_for_every_slot_proportion(self):
        source=pygame.Surface((60,90),pygame.SRCALPHA)
        colors=('red','green','blue','yellow')
        for rect,color in zip(((0,0,15,15),(45,0,15,15),(0,75,15,15),(45,75,15,15)),colors):
            source.fill(color,rect)
        for size in ((100,150),(206,88),(378,546)):
            image=nine_slice(source,size,margin=15,edge=12)
            for point,color in zip(((4,4),(size[0]-5,4),(4,size[1]-5),(size[0]-5,size[1]-5)),colors):
                self.assertTrue(all(abs(a-b)<=3 for a,b in zip(image.get_at(point),pygame.Color(color))))
        health=horizontal_frame(source,(500,90))
        self.assertEqual(health.get_at((4,4)),pygame.Color('red'))


if __name__=='__main__':unittest.main()
