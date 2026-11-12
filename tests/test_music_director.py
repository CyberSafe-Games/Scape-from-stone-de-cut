"""Seleção e transições das quatro trilhas aprovadas, sem carregar sprites."""
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch
from src.core.scene_manager import SceneManager
from src.core.audio_manager import AudioManager
from src.scenes.base_scene import BaseScene
from src.scenes.battle_scene import BattleScene
from src.systems.enemy_factory import (create_guardiao_da_pedra,create_alvaro_tex,create_goblin_nerd,create_gordofera,create_corpo_seco,create_carrasco_da_vigilia,create_zanzara,create_road_enemy)

class MusicRoutingTests(unittest.TestCase):
    def scene(self,enemy,state='player_turn'):
        scene=object.__new__(BattleScene)
        scene.engine=SimpleNamespace(enemy=enemy,state=state,level=7)
        return scene

    def test_every_boss_uses_chase_except_final_boss(self):
        for factory in (create_guardiao_da_pedra,create_alvaro_tex,create_goblin_nerd,create_gordofera,create_corpo_seco,create_carrasco_da_vigilia):
            self.assertEqual(self.scene(factory()).music_context,'boss')
        self.assertEqual(self.scene(create_alvaro_tex(phase=2)).music_context,'boss')
        self.assertEqual(self.scene(create_zanzara()).music_context,'final_boss')
        self.assertEqual(self.scene(create_road_enemy(7)).music_context,'battle')

    def test_victory_and_defeat_leave_space_for_existing_stingers(self):
        for state in ('victory','game_over','phase_complete'):
            self.assertIsNone(self.scene(create_zanzara(),state).music_context)
        self.assertEqual(BaseScene.music_context.fget(None),'menu')

    def test_menu_to_map_does_not_restart_music(self):
        audio=MagicMock();manager=SceneManager(audio)
        scene=SimpleNamespace(music_context='menu',update=MagicMock())
        manager.change_scene(scene);manager.update(16)
        manager.change_scene(SimpleNamespace(music_context='menu',update=MagicMock()))
        manager.update(16)
        self.assertEqual(audio.play_music.call_count,1)
        self.assertEqual(audio.play_music.call_args.args,('music/menu_floresta_v1.ogg',))
        audio.stop_music.assert_not_called()

    def test_fade_waits_then_uses_latest_requested_context(self):
        audio=MagicMock();manager=SceneManager(audio)
        scene=SimpleNamespace(music_context='battle',update=MagicMock())
        manager.change_scene(scene)
        scene.music_context='boss';manager.update(1)
        audio.stop_music.assert_called_once_with(fade_ms=350)
        scene.music_context='final_boss';manager.update(348)
        self.assertEqual(audio.play_music.call_count,1)
        manager.update(1)
        self.assertEqual(audio.play_music.call_args.args,('music/chefes_jungle_tribe_v2.ogg',))
        self.assertEqual(audio.play_music.call_count,2)
        manager.update(1000)
        self.assertEqual(audio.play_music.call_count,2)
        audio.stop_all_sfx.assert_not_called()

    def test_phase_change_and_modal_keep_boss_track(self):
        audio=MagicMock();manager=SceneManager(audio)
        scene=self.scene(create_alvaro_tex());scene.update=MagicMock()
        manager.change_scene(scene)
        scene.engine.enemy=create_alvaro_tex(phase=2)
        manager.push_modal(SimpleNamespace(update=MagicMock()))
        manager.update(16)
        self.assertEqual(audio.play_music.call_count,1)
        self.assertEqual(audio.play_music.call_args.args,('music/chefes_jungle_chase_v2.ogg',))
        scene.engine.state='game_over';manager.update(16)
        audio.stop_music.assert_called_once_with(fade_ms=350)
        manager.update(1000)
        self.assertEqual(audio.play_music.call_count,1)

class MusicPlaybackTests(unittest.TestCase):
    @patch('src.core.audio_manager.pygame.mixer.get_init',return_value=(44100,-16,2))
    @patch('src.core.audio_manager.pygame.mixer.music')
    def test_music_fades_in_without_altering_effects(self,music,_init):
        audio=AudioManager(music_volume=.45)
        self.assertTrue(audio.play_music('music/chefes_jungle_tribe_v2.ogg',fade_ms=600))
        music.play.assert_called_once_with(loops=-1,start=0.0,fade_ms=600)
        music.set_volume.assert_called_once_with(.45)
