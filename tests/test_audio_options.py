"""Volumes independentes e preferências locais, sem alterar saves da campanha."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import MagicMock,patch
from src.core.audio_manager import AudioManager

class VolumeCategoryTests(unittest.TestCase):
    @patch('src.core.audio_manager.pygame.mixer.get_init',return_value=(44100,-16,2))
    def test_music_combat_damage_and_interface_are_independent(self,_init):
        audio=AudioManager(master_volume=.5,sfx_volume=.8)
        audio.set_combat_volume(.25);audio.set_damage_volume(.75)
        for name,expected in [('gameplay.boss.zanzara.swing',.10),('gameplay.boss.zanzara.ferry_hit',.30),('ui.click',.40)]:
            audio.register_sound(name,'unused.ogg')
            sound=MagicMock();audio._sounds[name]=sound
            audio.play_sfx(name)
            self.assertAlmostEqual(sound.set_volume.call_args.args[0],expected)

    @patch('src.core.audio_manager.pygame.mixer.get_init',return_value=(44100,-16,2))
    def test_volume_change_updates_loaded_effect_without_replaying_it(self,_init):
        audio=AudioManager();audio.register_sound('gameplay.boss.zanzara.flesh','unused.ogg')
        sound=MagicMock();audio._sounds['gameplay.boss.zanzara.flesh']=sound
        audio.play_sfx('gameplay.boss.zanzara.flesh',volume=.5)
        audio.set_damage_volume(.4)
        sound.set_volume.assert_called_with(.2)
        self.assertEqual(sound.play.call_count,1)
        with patch('src.core.audio_manager.pygame.mixer.music'):
            audio.set_master_volume(.5)
        sound.set_volume.assert_called_with(.1)

class AudioPreferencesTests(unittest.TestCase):
    def test_defaults_roundtrip_and_invalid_values(self):
        from src.systems.audio_preferences import AudioPreferences
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'audio.json';store=AudioPreferences(path)
            self.assertEqual(store.load()['music_volume'],.45)
            audio=MagicMock(master_volume=.6,music_volume=.3,combat_volume=.4,damage_volume=.8)
            store.save(audio)
            self.assertEqual(store.load(),dict(master_volume=.6,music_volume=.3,combat_volume=.4,damage_volume=.8))
            path.write_text(json.dumps({'music_volume':2,'damage_volume':'bad','master_volume':-1}),encoding='utf-8')
            self.assertEqual(store.load(),dict(master_volume=0,music_volume=1,combat_volume=1,damage_volume=1))
            path.write_text('{invalid',encoding='utf-8')
            self.assertEqual(store.load()['music_volume'],.45)

    def test_applies_preferences_to_shared_audio_service(self):
        from src.systems.audio_preferences import AudioPreferences
        with tempfile.TemporaryDirectory() as folder:
            store=AudioPreferences(Path(folder)/'audio.json');audio=MagicMock();store.apply(audio)
            audio.set_master_volume.assert_called_once_with(1)
            audio.set_music_volume.assert_called_once_with(.45)
            audio.set_combat_volume.assert_called_once_with(1)
            audio.set_damage_volume.assert_called_once_with(1)

class AudioOptionsUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pygame
        cls.was_initialized=pygame.get_init()
        pygame.init();pygame.display.set_mode((1,1))

    @classmethod
    def tearDownClass(cls):
        import pygame
        if not cls.was_initialized:pygame.quit()

    def setUp(self):
        import pygame
        from types import SimpleNamespace
        from src.scenes.audio_options_scene import AudioOptionsScene
        from src.systems.audio_preferences import AudioPreferences
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.store=AudioPreferences(Path(self.folder.name)/'audio.json')
        self.audio=AudioManager();self.store.apply(self.audio)
        self.manager=SimpleNamespace(audio_manager=self.audio,audio_preferences=self.store,change_scene=MagicMock())
        self.window=SimpleNamespace(map_to_virtual=lambda pos:pos,get_virtual_mouse_pos=lambda:(-1,-1))
        font=pygame.font.Font(None,28)
        self.assets=SimpleNamespace(font=font,small_font=font,big_font=font,menu_font=font,background=None)
        self.return_scene=object()
        self.scene=AudioOptionsScene(self.manager,self.window,self.assets,self.return_scene)

    def test_mouse_drag_updates_music_saves_and_returns(self):
        import pygame
        rect=self.scene.sliders['music_volume']
        self.scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(rect.left+rect.width//4,rect.centery)))
        self.assertAlmostEqual(self.audio.music_volume,.25)
        self.scene.handle_event(pygame.event.Event(pygame.MOUSEMOTION,pos=(rect.right+100,rect.centery),buttons=(1,0,0)))
        self.scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP,button=1,pos=(rect.right+100,rect.centery)))
        self.assertEqual(self.store.load()['music_volume'],1)
        self.assertEqual(self.audio.master_volume,1)
        self.scene.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
        self.manager.change_scene.assert_called_once_with(self.return_scene)

    def test_restore_defaults_and_draw(self):
        import pygame
        self.audio.set_damage_volume(.2)
        point=self.scene.defaults_button.center
        self.scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=point))
        self.assertEqual(self.audio.damage_volume,1)
        self.assertEqual(self.store.load()['music_volume'],.45)
        self.scene.draw(pygame.Surface((1920,1080)))

    def test_main_menu_opens_audio_options(self):
        import pygame
        from src.scenes.menu_scene import MenuScene
        self.window.handle_window_event=lambda _event:False
        self.window.get_fullscreen_button_rect=lambda:pygame.Rect(1800,0,100,70)
        menu=MenuScene(self.manager,self.window,self.assets)
        menu.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=menu.options_button.center))
        from src.scenes.audio_options_scene import AudioOptionsScene
        self.assertIsInstance(self.manager.change_scene.call_args.args[0],AudioOptionsScene)
