
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pygame

from src.core.audio_manager import AudioManager


class TestAudioManager(unittest.TestCase):
    @patch("src.core.audio_manager.pygame.mixer.get_init", return_value=(44100, -16, 2))
    @patch("src.core.audio_manager.pygame.mixer.Sound")
    def test_per_sound_volume_combines_with_existing_controls(self, mock_sound, mock_get_init):
        manager = AudioManager(master_volume=0.5, sfx_volume=0.8)
        manager.register_sound("gameplay.attack.punch", "punch.ogg")
        manager.set_sound_volume("gameplay.attack.punch", 0.5)
        manager.play_sfx("gameplay.attack.punch", volume=0.5)
        mock_sound.return_value.set_volume.assert_called_once_with(0.1)

    @patch("src.core.audio_manager.pygame.mixer.get_init", return_value=(44100, -16, 2))
    @patch("src.core.audio_manager.pygame.mixer.Sound")
    def test_per_sound_volume_is_clamped_and_does_not_affect_other_sounds(self, mock_sound, mock_get_init):
        manager = AudioManager()
        manager.register_sounds({"punch": "punch.ogg", "click": "click.ogg"})
        for value, expected in ((-1, 0.0), (2, 1.0)):
            manager.set_sound_volume("punch", value)
            manager.play_sfx("punch")
            mock_sound.return_value.set_volume.assert_called_with(expected)
        manager.set_sound_volume("punch", 0.25)
        manager.play_sfx("click")
        mock_sound.return_value.set_volume.assert_called_with(1.0)

    @patch("src.core.audio_manager.pygame.mixer.get_init", return_value=(44100, -16, 2))
    @patch("src.core.audio_manager.pygame.mixer.Sound")
    def test_limits_playback_to_collision_window(self, mock_sound, mock_get_init):
        manager = AudioManager()
        manager.register_sound("gameplay.attack.fireball", "bola_de_fogo.ogg")
        manager.play_sfx("gameplay.attack.fireball", maxtime=312)
        mock_sound.return_value.play.assert_called_once_with(maxtime=312)

    @patch("src.core.audio_manager.pygame.mixer.get_init")
    @patch("src.core.audio_manager.pygame.mixer.init")
    def test_initializes_mixer_when_not_available(self, mock_init, mock_get_init):
        mock_get_init.side_effect = [None, (44100, -16, 2), (44100, -16, 2)]

        manager = AudioManager()

        mock_init.assert_called_once()
        self.assertTrue(manager.available)

    @patch("src.core.audio_manager.pygame.mixer.get_init", return_value=(44100, -16, 2))
    def test_register_sound(self, mock_get_init):
        manager = AudioManager(assets_dir="assets/audio")

        manager.register_sound("ui.click", "ui/click.ogg")

        self.assertIn("ui.click", manager._sound_paths)
        self.assertEqual(
            manager._sound_paths["ui.click"],
            Path("assets/audio") / "ui/click.ogg"
        )

    @patch("src.core.audio_manager.pygame.mixer.get_init", return_value=(44100, -16, 2))
    @patch("src.core.audio_manager.pygame.mixer.Sound")
    def test_play_registered_sound(self, mock_sound, mock_get_init):
        manager = AudioManager()
        fake_sound = MagicMock()
        mock_sound.return_value = fake_sound

        manager.register_sound("ui.click", "ui/click.ogg")
        manager.play_sfx("ui.click")

        mock_sound.assert_called_once()
        fake_sound.set_volume.assert_called_once_with(1.0)
        fake_sound.play.assert_called_once()

    @patch("src.core.audio_manager.pygame.mixer.get_init", return_value=(44100, -16, 2))
    @patch("src.core.audio_manager.pygame.mixer.Sound")
    def test_applies_combined_volume(self, mock_sound, mock_get_init):
        manager = AudioManager(master_volume=0.5, sfx_volume=0.8)
        fake_sound = MagicMock()
        mock_sound.return_value = fake_sound

        manager.register_sound("ui.confirm", "ui/confirm.ogg")
        manager.play_sfx("ui.confirm", volume=0.5)

        fake_sound.set_volume.assert_called_once_with(0.2)

    @patch("src.core.audio_manager.pygame.mixer.get_init", return_value=None)
    def test_does_not_play_when_mixer_is_unavailable(self, mock_get_init):
        manager = AudioManager()

        manager.register_sound("ui.click", "ui/click.ogg")

        self.assertIsNone(manager.play_sfx("ui.click"))

    @patch("src.core.audio_manager.pygame.mixer.get_init", return_value=(44100, -16, 2))
    @patch("src.core.audio_manager.pygame.mixer.Sound", side_effect=pygame.error("Arquivo ausente"))
    def test_handles_missing_audio_file(self, mock_sound, mock_get_init):
        manager = AudioManager()
        manager.register_sound("ui.click", "ui/inexistente.ogg")

        self.assertIsNone(manager.play_sfx("ui.click"))
        self.assertIn("ui.click", manager._failed_sounds)


if __name__ == "__main__":
    unittest.main()
