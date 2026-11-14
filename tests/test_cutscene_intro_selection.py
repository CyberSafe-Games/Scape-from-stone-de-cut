"""Valida a seleção de saves com e sem introdução."""

import unittest
from unittest.mock import Mock, patch

from src.config.cutscenes import INTRO_CUTSCENE
from src.scenes.save_selection_scene import SaveSelectionScene


class IntroSaveSelectionTests(unittest.TestCase):
    """Exercita somente o desvio introduzido em _select()."""

    def setUp(self):
        self.selection = SaveSelectionScene.__new__(SaveSelectionScene)
        self.selection.scene_manager = Mock()
        self.selection.window_manager = Mock()
        self.selection.asset_manager = Mock()
        self.selection.save_manager = Mock()
        self.selection.error = ""
        self.selection.play_ui_sound = Mock()

    def test_slot_vazio_abre_intro_e_conclui_para_tutorial(self):
        data = {
            "id": "slot_1",
            "progresso": {"intro_vista": False, "tutorial_concluido": False},
        }
        self.selection.slots = [("empty", None)]
        self.selection.save_manager.create_save.return_value = data
        with patch("src.scenes.cutscene_scene.CutsceneScene") as cutscene_cls, \
             patch("src.scenes.tutorial_scene.TutorialScene") as tutorial_cls:
            self.selection._select(0)
            cutscene_cls.assert_called_once()
            args = cutscene_cls.call_args.kwargs
            self.assertEqual(args["scenes"], INTRO_CUTSCENE)
            self.assertIs(self.selection.scene_manager.change_scene.call_args.args[0],
                          cutscene_cls.return_value)
            self.assertFalse(data["progresso"]["intro_vista"])
            self.selection.save_manager.save.assert_not_called()

            args["on_finish"]()
            self.assertTrue(data["progresso"]["intro_vista"])
            self.selection.save_manager.save.assert_called_once_with(data)
            self.assertIs(args["next_scene_factory"](), tutorial_cls.return_value)
            tutorial_cls.assert_called_once()
            self.assertIs(tutorial_cls.call_args.kwargs["save_data"], data)

    def test_save_existente_sem_intro_vai_direto_ao_tutorial(self):
        data = {"progresso": {"intro_vista": True, "tutorial_concluido": False}}
        self.selection.slots = [("occupied", data)]
        with patch("src.scenes.cutscene_scene.CutsceneScene") as cutscene_cls, \
             patch("src.scenes.tutorial_scene.TutorialScene") as tutorial_cls:
            self.selection._select(0)
            cutscene_cls.assert_not_called()
            self.selection.scene_manager.change_scene.assert_called_once_with(
                tutorial_cls.return_value
            )

    def test_save_existente_concluido_vai_ao_mapa(self):
        data = {"progresso": {"intro_vista": True, "tutorial_concluido": True}}
        self.selection.slots = [("occupied", data)]
        with patch("src.scenes.cutscene_scene.CutsceneScene") as cutscene_cls, \
             patch("src.scenes.map_scene.MapScene") as map_cls:
            self.selection._select(0)
            cutscene_cls.assert_not_called()
            self.selection.scene_manager.change_scene.assert_called_once_with(
                map_cls.return_value
            )

    def test_falha_ao_salvar_nao_impede_o_tutorial(self):
        data = {"id": "slot_1", "progresso": {
            "intro_vista": False, "tutorial_concluido": False,
        }}
        self.selection.slots = [("occupied", data)]
        self.selection.save_manager.save.side_effect = OSError("sem permissão")
        with patch("src.scenes.cutscene_scene.CutsceneScene") as cutscene_cls, \
             patch("src.scenes.tutorial_scene.TutorialScene") as tutorial_cls:
            self.selection._select(0)
            args = cutscene_cls.call_args.kwargs
            args["on_finish"]()
            self.assertIn("sem permissão", self.selection.error)
            self.assertIs(args["next_scene_factory"](), tutorial_cls.return_value)


if __name__ == "__main__":
    unittest.main()
