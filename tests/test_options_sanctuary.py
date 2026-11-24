"""Integração da arte, controles, retorno da pausa e consulta dos guias."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from copy import deepcopy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock,patch
import pygame
from src.core.asset_manager import AssetManager
from src.core.audio_manager import AudioManager
from src.core.scene_manager import SceneManager
from src.systems.game_preferences import GamePreferences
from src.scenes.options_scene import OptionsScene
from src.scenes.pause_menu_modal import PauseMenuModal
from src.scenes.battle_scene import BattleScene
from src.scenes.menu_scene import MenuScene
from src.scenes.guide_library_scene import GuideLibraryScene
from src.config.preferences import TAB_GAME,OPTIONS_TABS
from src.config.options_layout import OPTIONS_MESSAGE_Y


class OptionsSanctuaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))
        cls.assets=AssetManager.__new__(AssetManager)
        cls.assets._fonts,cls.assets._ui_images={},{}
        cls.assets._background=None
        cls.assets._init_fonts()
        cls.canvas=pygame.Surface((1920,1080))

    def setUp(self):
        folder=tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path=Path(folder.name)/'preferences.json'
        self.prefs=GamePreferences(self.path)
        self.audio=AudioManager()
        self.prefs.apply_audio(self.audio)
        self.manager=SceneManager(self.audio,self.prefs)
        self.window=SimpleNamespace(map_to_virtual=lambda p:(round(p[0]*1.5),round(p[1]*1.5)),
            get_virtual_mouse_pos=lambda:(-1,-1),is_fullscreen=False,is_large_window=False)
        self.options=OptionsScene(self.manager,self.window,self.assets,modal=True)

    def click(self,rect):
        self.options.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(rect.centerx/1.5,rect.centery/1.5)))

    def battle(self):
        battle=object.__new__(BattleScene)
        battle.engine=SimpleNamespace(state='enemy_turn')
        battle.save_on_exit=MagicMock(return_value=True)
        self.manager.current_scene=battle
        return battle

    def test_asset_loads_and_all_four_tabs_render_without_mutating_preferences(self):
        self.assertIsInstance(self.options.visuals.source,pygame.Surface)
        self.assertGreater(self.options.visuals.source.get_width(),1000)
        before=deepcopy(self.prefs.values)
        for key,_ in OPTIONS_TABS:
            self.options.tab=key
            self.options.draw(self.canvas)
        self.assertEqual(self.prefs.values,before)
        for rect in [self.options.back_button,self.options.defaults_button,self.options.review_button,self.options.exit_button,*self.options.sliders.values()]:
            self.assertTrue(self.options.panel_rect.contains(rect))
        self.assertGreater(OPTIONS_MESSAGE_Y,self.options.exit_button.bottom)
        self.assertLess(OPTIONS_MESSAGE_Y,self.options.back_button.top)

    def test_scaled_drag_clamps_and_persists_on_release(self):
        rect=self.options.sliders['music_volume']
        self.click(rect)
        self.options.handle_event(pygame.event.Event(pygame.MOUSEMOTION,pos=((rect.right+90)/1.5,rect.centery/1.5)))
        self.options.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP,button=1,pos=(0,0)))
        self.assertEqual(self.audio.music_volume,1)
        self.assertEqual(GamePreferences(self.path).get('music_volume'),1)
        self.assertIsNone(self.options.dragging)

    def test_switching_tab_persists_an_active_slider(self):
        rect=self.options.sliders['music_volume']
        self.click(rect)
        self.options._switch_tab(TAB_GAME)
        self.assertAlmostEqual(GamePreferences(self.path).get('music_volume'),.5,places=2)
        self.assertIsNone(self.options.dragging)

    def test_return_to_combat_pops_options_and_pause_without_recreating_battle(self):
        battle=self.battle()
        pause=PauseMenuModal(self.manager,self.window,self.assets)
        self.manager.modal_stack=[pause,self.options]
        self.click(self.options.back_button)
        self.assertFalse(self.manager.modal_stack)
        self.assertIs(self.manager.current_scene,battle)
        battle.save_on_exit.assert_not_called()

    def test_review_library_does_not_change_campaign_or_mark_guides_seen(self):
        battle=self.battle()
        battle.save_data={'progresso':{'tutoriais_gerenciamento':dict(shop=False,backpack=False,workshop=False)}}
        before=deepcopy(battle.save_data)
        self.options.tab=TAB_GAME
        self.manager.modal_stack=[self.options]
        self.click(self.options.review_button)
        library=self.manager.modal_stack[-1]
        self.assertIsInstance(library,GuideLibraryScene)
        for key in library.tabs:
            library.key=key
            library.draw(self.canvas)
        self.assertEqual(battle.save_data,before)
        battle.save_on_exit.assert_not_called()
        library.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
        self.assertIs(self.manager.modal_stack[-1],self.options)

    def test_exit_confirmation_preserves_battle_when_save_fails_then_exits_safely(self):
        battle=self.battle()
        self.manager.modal_stack=[self.options]
        battle.save_on_exit.return_value=False
        self.options._request_exit()
        self.manager.modal_stack[-1]._confirm()
        self.assertIs(self.manager.current_scene,battle)
        self.assertIs(self.manager.modal_stack[-1],self.options)
        self.assertIn('cancelada',self.options.message)
        battle.save_on_exit.return_value=True
        self.options._request_exit()
        self.manager.modal_stack[-1]._confirm()
        self.assertIsInstance(self.manager.current_scene,MenuScene)
        self.assertFalse(self.manager.modal_stack)

    def test_uncollected_victory_cannot_be_bypassed_by_exit(self):
        battle=self.battle()
        self.manager.modal_stack=[self.options]
        for state in ('victory','phase_complete','boss_transition'):
            battle.engine.state=state
            self.options._request_exit()
            self.assertEqual(self.manager.modal_stack,[self.options])
        battle.save_on_exit.assert_not_called()

    def test_preference_failure_is_reported_without_discarding_session_value(self):
        self.options._set_audio('music_volume',.2)
        with patch.object(self.prefs,'save',side_effect=OSError('disco indisponível')):
            self.options._persist()
        self.assertAlmostEqual(self.audio.music_volume,.2)
        self.assertIn('sessão',self.options.message)
        self.assertFalse(self.path.exists())


if __name__=='__main__':unittest.main()
