import ast
from pathlib import Path
import unittest

from src.config.audio_mix import SOUND_VOLUMES


class TestAudioMix(unittest.TestCase):
    def test_every_registered_effect_has_an_attenuation_setting(self):
        root = Path(__file__).resolve().parents[1]
        tree = ast.parse((root / "main.py").read_text(encoding="utf-8"))
        registrations = [
            ast.literal_eval(node.args[0])
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "register_sounds"
        ]
        self.assertEqual(len(registrations), 1)
        self.assertEqual(set(SOUND_VOLUMES), set(registrations[0]))
        for sound_id, gain in SOUND_VOLUMES.items():
            with self.subTest(sound_id=sound_id):
                self.assertGreater(gain, 0)
                self.assertLessEqual(gain, 1)
