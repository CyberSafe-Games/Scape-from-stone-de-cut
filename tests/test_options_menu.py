"""Preferências globais, abas de Opções e pausa da batalha por modal."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from src.config.preferences import (
    DEFAULT_PREFERENCES,
    ENEMY_SPEED_FAST,
    ENEMY_SPEED_NORMAL,
    TAB_AUDIO,
    TAB_GAME,
    TAB_VIDEO,
)
from src.systems.game_preferences import GamePreferences, enemy_windup_ms


class PreferencesPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "audio.json"

    def test_defaults_match_previous_game_behavior(self):
        preferences = GamePreferences(self.path)
        self.assertEqual(preferences.load(), DEFAULT_PREFERENCES)
        self.assertEqual(preferences.get("master_volume"), 1.0)
        self.assertEqual(preferences.get("music_volume"), 0.45)
        self.assertEqual(preferences.get("combat_volume"), 1.0)
        self.assertEqual(preferences.get("damage_volume"), 1.0)
        self.assertFalse(preferences.get("fullscreen"))
        self.assertEqual(preferences.get("window_size"), "legacy")
        self.assertFalse(preferences.get("show_fps"))
        self.assertEqual(preferences.get("enemy_speed"), ENEMY_SPEED_NORMAL)
        self.assertTrue(preferences.get("damage_numbers"))

    def test_save_and_load_every_setting(self):
        preferences = GamePreferences(self.path)
        preferences.set("master_volume", 0.2)
        preferences.set("music_volume", 0.3)
        preferences.set("combat_volume", 0.4)
        preferences.set("damage_volume", 0.5)
        preferences.set("fullscreen", True)
        preferences.set("window_size", "large")
        preferences.set("show_fps", True)
        preferences.set("enemy_speed", ENEMY_SPEED_FAST)
        preferences.set("damage_numbers", False)
        preferences.save()

        loaded = GamePreferences(self.path)
        self.assertEqual(loaded.get("master_volume"), 0.2)
        self.assertEqual(loaded.get("music_volume"), 0.3)
        self.assertEqual(loaded.get("combat_volume"), 0.4)
        self.assertEqual(loaded.get("damage_volume"), 0.5)
        self.assertTrue(loaded.get("fullscreen"))
        self.assertEqual(loaded.get("window_size"), "large")
        self.assertTrue(loaded.get("show_fps"))
        self.assertEqual(loaded.get("enemy_speed"), ENEMY_SPEED_FAST)
        self.assertFalse(loaded.get("damage_numbers"))

    def test_missing_corrupt_and_out_of_range_use_defaults(self):
        self.assertEqual(GamePreferences(self.path).load(), DEFAULT_PREFERENCES)

        self.path.write_text("{invalid", encoding="utf-8")
        self.assertEqual(GamePreferences(self.path).load(), DEFAULT_PREFERENCES)

        self.path.write_text("[]", encoding="utf-8")
        self.assertEqual(GamePreferences(self.path).load(), DEFAULT_PREFERENCES)

        self.path.write_text(
            json.dumps(
                {
                    "master_volume": -0.1,
                    "music_volume": 1.1,
                    "combat_volume": "0.5",
                    "damage_volume": True,
                    "fullscreen": 1,
                    "window_size": "gigante",
                    "show_fps": "sim",
                    "enemy_speed": "turbo",
                    "damage_numbers": None,
                }
            ),
            encoding="utf-8",
        )
        loaded = GamePreferences(self.path).load()
        self.assertEqual(loaded, DEFAULT_PREFERENCES)

    def test_legacy_audio_only_file_gets_defaults_for_new_keys(self):
        self.path.write_text(
            json.dumps(
                {
                    "master_volume": 0.4,
                    "music_volume": 0.2,
                    "combat_volume": 0.8,
                    "damage_volume": 0.6,
                }
            ),
            encoding="utf-8",
        )
        loaded = GamePreferences(self.path).load()
        self.assertEqual(loaded["master_volume"], 0.4)
        self.assertEqual(loaded["music_volume"], 0.2)
        self.assertEqual(loaded["combat_volume"], 0.8)
        self.assertEqual(loaded["damage_volume"], 0.6)
        for key in (
            "fullscreen",
            "window_size",
            "show_fps",
            "enemy_speed",
            "damage_numbers",
        ):
            self.assertEqual(loaded[key], DEFAULT_PREFERENCES[key])

    def test_restore_tab_affects_only_that_tab(self):
        preferences = GamePreferences(self.path)
        preferences.set("master_volume", 0.1)
        preferences.set("fullscreen", True)
        preferences.set("window_size", "large")
        preferences.set("show_fps", True)
        preferences.set("enemy_speed", ENEMY_SPEED_FAST)
        preferences.set("damage_numbers", False)

        preferences.restore_tab(TAB_AUDIO)
        self.assertEqual(preferences.get("master_volume"), 1.0)
        self.assertTrue(preferences.get("fullscreen"))
        self.assertTrue(preferences.get("show_fps"))
        self.assertEqual(preferences.get("enemy_speed"), ENEMY_SPEED_FAST)
        self.assertFalse(preferences.get("damage_numbers"))

        preferences.restore_tab(TAB_VIDEO)
        self.assertEqual(preferences.get("master_volume"), 1.0)
        self.assertFalse(preferences.get("fullscreen"))
        self.assertEqual(preferences.get("window_size"), "legacy")
        self.assertFalse(preferences.get("show_fps"))
        self.assertEqual(preferences.get("enemy_speed"), ENEMY_SPEED_FAST)

        preferences.restore_tab(TAB_GAME)
        self.assertEqual(preferences.get("enemy_speed"), ENEMY_SPEED_NORMAL)
        self.assertTrue(preferences.get("damage_numbers"))


class EnemySpeedTests(unittest.TestCase):
    def test_normal_keeps_exact_original_windups(self):
        self.assertEqual(enemy_windup_ms(ENEMY_SPEED_NORMAL, False), 800)
        self.assertEqual(enemy_windup_ms(ENEMY_SPEED_NORMAL, True), 270)

    def test_fast_only_shortens_windups(self):
        self.assertLess(enemy_windup_ms(ENEMY_SPEED_FAST, False), 800)
        self.assertLess(enemy_windup_ms(ENEMY_SPEED_FAST, True), 270)
        self.assertGreater(enemy_windup_ms(ENEMY_SPEED_FAST, False), 0)
        self.assertGreater(enemy_windup_ms(ENEMY_SPEED_FAST, True), 0)

    def test_invalid_speed_falls_back_to_normal(self):
        self.assertEqual(enemy_windup_ms("turbo", False), 800)
        self.assertEqual(enemy_windup_ms("turbo", True), 270)


class OptionsSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pygame

        cls.was_initialized = pygame.get_init()
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        import pygame

        if not cls.was_initialized:
            pygame.quit()

    def setUp(self):
        import pygame

        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "audio.json"
        self.preferences = GamePreferences(self.path)
        self.audio = MagicMock()
        self.audio.master_volume = 1.0
        self.audio.music_volume = 0.45
        self.audio.combat_volume = 1.0
        self.audio.damage_volume = 1.0

        def set_volume(key):
            def setter(value):
                setattr(self.audio, key, max(0.0, min(1.0, value)))

            return setter

        for key in (
            "master_volume",
            "music_volume",
            "combat_volume",
            "damage_volume",
        ):
            setattr(self.audio, "set_" + key, set_volume(key))

        self.scene_manager = SimpleNamespace(
            audio_manager=self.audio,
            audio_preferences=self.preferences,
            change_scene=MagicMock(),
            push_modal=MagicMock(),
            pop_modal=MagicMock(),
        )
        self.window_manager = SimpleNamespace(
            is_fullscreen=False,
            is_large_window=False,
            map_to_virtual=lambda pos: pos,
            get_virtual_mouse_pos=lambda: (-1, -1),
        )

        def set_fullscreen(enabled):
            self.window_manager.is_fullscreen = bool(enabled)
            self.window_manager.is_large_window = False

        def set_window_size(large):
            self.window_manager.is_fullscreen = False
            self.window_manager.is_large_window = bool(large)

        self.window_manager.set_fullscreen = set_fullscreen
        self.window_manager.set_window_size = set_window_size
        self.window_manager.apply_display_preferences = (
            lambda fullscreen=False, large_window=False: set_fullscreen(fullscreen)
            if fullscreen
            else set_window_size(large_window)
        )

        font = pygame.font.Font(None, 28)
        self.assets = SimpleNamespace(
            font=font,
            small_font=font,
            big_font=font,
            menu_font=font,
            background=None,
        )
        from src.scenes.options_scene import OptionsScene

        self.scene = OptionsScene(
            self.scene_manager,
            self.window_manager,
            self.assets,
            modal=True,
        )

    @staticmethod
    def click(rect):
        import pygame

        return pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center
        )

    def test_restore_defaults_restores_only_current_tab(self):
        self.scene._set_audio("master_volume", 0.2)
        self.preferences.set("fullscreen", True)
        self.preferences.set("enemy_speed", ENEMY_SPEED_FAST)

        self.scene._switch_tab(TAB_VIDEO)
        self.scene._restore_defaults()
        self.assertEqual(self.audio.master_volume, 0.2)
        self.assertFalse(self.preferences.get("fullscreen"))
        self.assertEqual(self.preferences.get("enemy_speed"), ENEMY_SPEED_FAST)

        self.scene._switch_tab(TAB_GAME)
        self.scene._restore_defaults()
        self.assertEqual(self.audio.master_volume, 0.2)
        self.assertEqual(self.preferences.get("enemy_speed"), ENEMY_SPEED_NORMAL)

        self.scene._switch_tab(TAB_AUDIO)
        self.scene._restore_defaults()
        self.assertEqual(self.audio.master_volume, 1.0)
        self.assertEqual(self.audio.music_volume, 0.45)

    def test_video_tab_applies_and_persists_immediately(self):
        self.scene._switch_tab(TAB_VIDEO)
        self.scene.handle_event(self.click(self.scene.fullscreen_button))
        self.assertTrue(self.window_manager.is_fullscreen)
        self.assertTrue(GamePreferences(self.path).get("fullscreen"))

        self.scene.handle_event(
            self.click(self.scene.window_size_buttons["large"])
        )
        self.assertFalse(self.window_manager.is_fullscreen)
        self.assertTrue(self.window_manager.is_large_window)
        self.assertEqual(GamePreferences(self.path).get("window_size"), "large")

        self.scene.handle_event(self.click(self.scene.fps_button))
        self.assertTrue(GamePreferences(self.path).get("show_fps"))

    def test_setting_buttons_stay_on_their_own_rows(self):
        self.scene._switch_tab(TAB_VIDEO)
        first_size = self.scene.window_size_buttons["legacy"]
        self.assertGreaterEqual(first_size.top, self.scene.fullscreen_button.bottom)
        self.assertGreaterEqual(self.scene.fps_button.top, first_size.bottom)

        self.scene._switch_tab(TAB_GAME)
        first_speed = self.scene.enemy_speed_buttons[ENEMY_SPEED_NORMAL]
        self.assertGreaterEqual(
            self.scene.damage_numbers_button.top, first_speed.bottom
        )

    def test_game_tab_applies_and_persists_immediately(self):
        self.scene._switch_tab(TAB_GAME)
        self.scene.handle_event(
            self.click(self.scene.enemy_speed_buttons[ENEMY_SPEED_FAST])
        )
        self.scene.handle_event(self.click(self.scene.damage_numbers_button))
        loaded = GamePreferences(self.path)
        self.assertEqual(loaded.get("enemy_speed"), ENEMY_SPEED_FAST)
        self.assertFalse(loaded.get("damage_numbers"))

    def test_escape_closes_modal(self):
        import pygame

        self.scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.scene_manager.pop_modal.assert_called_once()
        self.scene_manager.change_scene.assert_not_called()


class PauseLogicTests(unittest.TestCase):
    def test_modal_freezes_scene_timer_and_resumes_after_close(self):
        from src.core.scene_manager import SceneManager

        class BattleLikeScene:
            def __init__(self):
                self.enemy_turn_timer = 0
                self.updates = 0

            def update(self, dt):
                self.enemy_turn_timer += dt
                self.updates += 1

        class ModalLikeScene:
            def __init__(self):
                self.timer = 0

            def update(self, dt):
                self.timer += dt

        manager = SceneManager()
        battle = BattleLikeScene()
        manager.change_scene(battle)
        manager.update(100)
        self.assertEqual(battle.enemy_turn_timer, 100)

        modal = ModalLikeScene()
        manager.push_modal(modal)
        manager.update(800)
        self.assertEqual(battle.enemy_turn_timer, 100)
        self.assertEqual(battle.updates, 1)
        self.assertEqual(modal.timer, 800)

        manager.pop_modal()
        manager.update(50)
        self.assertEqual(battle.enemy_turn_timer, 150)
        self.assertEqual(battle.updates, 2)

    def test_battle_reads_enemy_speed_preference(self):
        from src.scenes.battle_scene import BattleScene

        with tempfile.TemporaryDirectory() as folder:
            preferences = GamePreferences(Path(folder) / "audio.json")
            scene = object.__new__(BattleScene)
            scene.preferences = preferences
            self.assertEqual(scene._enemy_windup_ms(False), 800)
            self.assertEqual(scene._enemy_windup_ms(True), 270)

            preferences.set("enemy_speed", ENEMY_SPEED_FAST)
            self.assertEqual(scene._enemy_windup_ms(False), 400)
            self.assertEqual(scene._enemy_windup_ms(True), 135)

    def test_battle_menu_and_escape_open_pause_modal(self):
        import pygame
        from src.scenes.battle_scene import BattleScene
        from src.scenes.pause_menu_modal import PauseMenuModal

        for interaction in ("menu", "escape"):
            with self.subTest(interaction=interaction):
                manager = MagicMock()
                window = MagicMock()
                window.handle_window_event.return_value = False
                window.get_fullscreen_button_rect.return_value = pygame.Rect(
                    -1000, -1000, 1, 1
                )
                scene = object.__new__(BattleScene)
                scene.scene_manager = manager
                scene.window_manager = window
                scene.asset_manager = MagicMock()
                scene.engine = MagicMock()
                scene.engine.state = "enemy_turn"
                scene.map_mode = True

                if interaction == "menu":
                    scene.menu_button_rect = pygame.Rect(0, 0, 20, 20)
                    window.map_to_virtual.return_value = scene.menu_button_rect.center
                    scene.handle_event(
                        pygame.event.Event(
                            pygame.MOUSEBUTTONDOWN,
                            button=1,
                            pos=scene.menu_button_rect.center,
                        )
                    )
                else:
                    scene.handle_event(
                        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
                    )

                modal = manager.push_modal.call_args.args[0]
                self.assertIsInstance(modal, PauseMenuModal)
                self.assertEqual(modal.exit_label, "VOLTAR AO MAPA")

    def test_pause_modal_buttons_follow_layout_and_receive_clicks(self):
        import pygame
        from src.scenes.pause_menu_modal import PauseMenuModal

        manager = MagicMock()
        window = MagicMock()
        window.map_to_virtual.side_effect = lambda pos: pos
        assets = MagicMock()
        on_options = MagicMock()
        on_exit = MagicMock()
        modal = PauseMenuModal(
            manager,
            window,
            assets,
            on_options=on_options,
            on_exit=on_exit,
        )

        self.assertEqual(
            modal.panel_rect, pygame.Rect(modal.layout.panel)
        )
        for button, expected in zip(
            (modal.continue_button, modal.options_button, modal.exit_button),
            modal.layout.buttons,
        ):
            self.assertEqual(button, pygame.Rect(expected))

        modal.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=1,
                pos=modal.continue_button.center,
            )
        )
        manager.pop_modal.assert_called_once()
        on_options.assert_not_called()
        on_exit.assert_not_called()

        modal.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=1,
                pos=modal.options_button.center,
            )
        )
        on_options.assert_called_once()

        modal.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=1,
                pos=modal.exit_button.center,
            )
        )
        on_exit.assert_called_once()


class PreferencesPygameIndependenceTests(unittest.TestCase):
    def test_preferences_module_does_not_import_pygame(self):
        project_root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import sys; import src.systems.game_preferences; "
                    "print('pygame' in sys.modules)"
                ),
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result.stdout.strip().splitlines()[-1], "False")


if __name__ == "__main__":
    unittest.main()
