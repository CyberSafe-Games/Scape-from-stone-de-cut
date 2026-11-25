"""Contratos da prova web sem depender de navegador ou slots reais."""
import asyncio
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import MagicMock, patch
import pygame
from src.core.application import Application
from src.core.audio_manager import AudioManager
from web.poc import SessionPreferences, ProofAssets, ProofFont, ProofBattle
from devtools.build_web import selected_assets, ROOT


class WebLoopTests(IsolatedAsyncioTestCase):
    async def test_web_yields_between_frames_and_returns_without_exit(self):
        app=Application(*(MagicMock() for _ in range(5)))
        frames=[]
        def frame(web=False):
            frames.append(web)
            if len(frames)==2:
                app.running=False
        app.frame=frame
        with patch("src.core.application.asyncio.sleep", wraps=asyncio.sleep) as sleep:
            await app.run_web()
        self.assertEqual(frames,[True,True])
        self.assertEqual(sleep.await_count,2)

    async def test_desktop_keeps_synchronous_loop(self):
        app=Application(*(MagicMock() for _ in range(5)))
        app.frame=MagicMock(side_effect=lambda: setattr(app,"running",False))
        app.run_desktop()
        app.frame.assert_called_once_with()


class ProofIsolationTests(TestCase):
    def test_preferences_never_read_or_write_disk(self):
        with patch("pathlib.Path.read_text",side_effect=AssertionError("leitura")), patch("os.replace",side_effect=AssertionError("gravação")):
            preferences=SessionPreferences()
            preferences.set("show_fps",True)
            preferences.save()
        self.assertTrue(preferences.get("show_fps"))

    def test_manifest_excludes_other_enemies_and_source_art(self):
        paths=[p.relative_to(ROOT/"assets").as_posix() for p in selected_assets()]
        self.assertIn("cards/soco_simples.png",paths)
        self.assertFalse(any(p.endswith("reference.png") for p in paths))
        self.assertTrue(any(p.startswith("enemies/eight_frames/slime/") for p in paths))
        self.assertFalse(any(p.startswith(("bosses/","cutscenes/","player/twelve_frames/source/")) for p in paths))

    def test_menu_does_not_preload_combat(self):
        with patch.object(ProofAssets,"_init_fonts"), patch.object(ProofAssets,"_load_background"), patch.object(ProofAssets,"_load_enemy_sprites") as enemies, patch.object(ProofAssets,"_load_player_sprites") as player:
            assets=ProofAssets()
        enemies.assert_not_called()
        player.assert_not_called()
        self.assertEqual(assets._enemy_sprites,{})
        self.assertFalse(assets.combat_ready)

    def test_web_audio_waits_for_gesture_and_preserves_requested_music(self):
        with patch.object(AudioManager,"_initialize_mixer") as initialize:
            audio=AudioManager(defer_initialization=True)
            initialize.assert_not_called()
            self.assertFalse(audio.play_music("music/menu_floresta_v1.ogg"))
            with patch.object(audio,"play_music",return_value=True) as play:
                audio.unlock_after_interaction()
                play.assert_called_once_with("music/menu_floresta_v1.ogg",loops=-1,start=0.0,fade_ms=0)
            initialize.assert_called_once()

    def test_desktop_audio_still_initializes_immediately(self):
        with patch.object(AudioManager,"_initialize_mixer") as initialize:
            AudioManager()
        initialize.assert_called_once()



class WebRenderCacheTests(TestCase):
    def test_font_cache_does_not_share_mutable_alpha(self):
        surface=pygame.Surface((20,20),pygame.SRCALPHA)
        source=MagicMock()
        source.render.return_value=surface
        font=ProofFont(source)
        first=font.render("Texto",True,(255,255,255))
        first.set_alpha(10)
        second=font.render("Texto",True,(255,255,255))
        source.render.assert_called_once()
        self.assertEqual(second.get_alpha(),255)
        self.assertIsNot(first,second)

    def test_background_cache_preserves_original_pixels(self):
        from types import SimpleNamespace
        from src.scenes.battle_scene import BattleScene
        pygame.display.init()
        pygame.display.set_mode((64,64))
        try:
            scene=ProofBattle.__new__(ProofBattle)
            scene.selected_level=None
            scene.engine=SimpleNamespace(level=1)
            scene.asset_manager=MagicMock()
            background=pygame.Surface((1920,1080))
            background.fill((40,60,80))
            scene.asset_manager.get_battle_background.return_value=background
            scene._static_background=None
            expected=pygame.Surface((1920,1080))
            actual=pygame.Surface((1920,1080))
            BattleScene._render_background(scene,expected)
            with patch.object(BattleScene,"_draw_background",autospec=True,side_effect=BattleScene._draw_background) as draw:
                scene._draw_background(actual)
                scene._draw_background(actual)
                self.assertEqual(draw.call_count,1)
            self.assertEqual(pygame.image.tobytes(actual,"RGB"),pygame.image.tobytes(expected,"RGB"))
            scene.engine.level=7
            BattleScene._render_background(scene,expected)
            BattleScene._draw_background(scene,actual)
            self.assertEqual(pygame.image.tobytes(actual,"RGB"),pygame.image.tobytes(expected,"RGB"))
        finally:
            pygame.display.quit()
