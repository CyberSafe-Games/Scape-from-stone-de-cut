"""Testes direcionados às flags das cutscenes nos saves."""

import json
import tempfile
import unittest
from pathlib import Path

from src.systems.save_manager import (
    SAVE_VERSION,
    SaveCorruptedError,
    SaveManager,
    TEST_SAVE_ID,
)


class CutsceneSaveFlagsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.manager = SaveManager(saves_dir=self.temp_dir.name)

    def test_new_save_flags_are_false(self):
        data = self.manager.create_save('Novo')
        self.assertEqual(data['versao'], SAVE_VERSION)
        self.assertIs(data['progresso']['intro_vista'], False)
        self.assertIs(data['progresso']['pos_tutorial_visto'], False)
        loaded = self.manager.load_save('Novo')
        self.assertIs(loaded['progresso']['intro_vista'], False)
        self.assertIs(loaded['progresso']['pos_tutorial_visto'], False)

    def test_old_save_without_flags_migrates_to_true(self):
        self.manager.create_save('Antigo')
        path = Path(self.temp_dir.name) / 'antigo.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        data['versao'] = SAVE_VERSION - 1
        data['progresso'].pop('intro_vista')
        data['progresso'].pop('pos_tutorial_visto')
        path.write_text(json.dumps(data), encoding='utf-8')
        loaded = self.manager.load_save('Antigo')
        self.assertEqual(loaded['versao'], SAVE_VERSION)
        self.assertIs(loaded['progresso']['intro_vista'], True)
        self.assertIs(loaded['progresso']['pos_tutorial_visto'], True)

    def test_test_mode_flags_remain_true(self):
        data = self.manager.load_or_create_test_save()
        self.assertIs(data['progresso']['intro_vista'], True)
        self.assertIs(data['progresso']['pos_tutorial_visto'], True)
        data['progresso']['intro_vista'] = False
        data['progresso']['pos_tutorial_visto'] = False
        self.manager.save(data)
        loaded = self.manager.load_or_create_test_save()
        self.assertEqual(loaded['id'], TEST_SAVE_ID)
        self.assertIs(loaded['progresso']['intro_vista'], True)
        self.assertIs(loaded['progresso']['pos_tutorial_visto'], True)

    def test_invalid_flag_types_are_rejected(self):
        for field in ('intro_vista', 'pos_tutorial_visto'):
            with self.subTest(field=field):
                data = self.manager._new_data('Inválido', 'invalido')
                data['progresso'][field] = 1
                with self.assertRaises(SaveCorruptedError):
                    self.manager.save(data)


if __name__ == '__main__':
    unittest.main()
