"""Verifica a entrada no epílogo e o retorno ao mapa."""

import os
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.scenes.battle_scene import BattleScene
from src.scenes.cutscene_scene import CutsceneScene
from src.systems.save_manager import SaveError, TEST_SAVE_ID
from src.systems.territory_map import TERRITORIES


class FinalCutsceneTests(unittest.TestCase):
    def setUp(self):
        pygame.display.init()
        pygame.font.init()
        pygame.display.set_mode((1, 1))
        self.addCleanup(pygame.quit)
        self.battle = BattleScene.__new__(BattleScene)
        self.battle.map_mode = True
        self.battle.save_data = {}
        self.battle.save_manager = Mock()
        self.battle.engine = Mock(is_replay=False)
        self.battle.coin_hud = Mock()
        self.battle.encounter_kind = "point"
        self.battle.scene_manager = Mock(current_scene=self.battle)
        self.battle.window_manager = Mock()
        self.battle.window_manager.handle_window_event.return_value = False
        self.battle.asset_manager = Mock()
        self.battle.asset_manager.get_font.return_value = pygame.font.Font(None, 32)
        self.battle._make_map_scene = Mock()
        self.level = TERRITORIES[-1].level

    def test_vitoria_final_abre_dez_imagens_em_ordem_e_volta_ao_mapa(self):
        with patch("src.scenes.battle_scene.record_victory") as record, patch(
            "src.scenes.cutscene_scene.logger.warning"
        ) as missing_image:
            self.battle._finalize_map_phase(self.level)
            record.assert_called_once()
            destination = self.battle.scene_manager.change_scene
            scene = destination.call_args.args[0]
            self.assertIsInstance(scene, CutsceneScene)
            images = [f"cutscenes/final_{number:02d}.png" for number in range(1, 11)]
            images.insert(2, None)
            self.assertEqual([frame["image"] for frame in scene.scenes], images)
            space = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
            click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1)
            for index in range(len(images)):
                scene.update(500)
                self.assertEqual(scene.index, index)
                if index in (2, 3):
                    self.assertIsNone(scene.music_context)
                if images[index] is None:
                    surface = pygame.Surface((32, 32))
                    surface.fill("white")
                    scene.draw(surface)
                    self.assertEqual(surface.get_at((16, 16)), pygame.Color("black"))
                event = space if index % 2 == 0 else click
                dialogues = scene.scenes[index]["dialogues"]
                for speaker, line in dialogues:
                    scene.update(scene.DIALOGUE_DELAY_MS)
                    if index == 3:
                        self.assertEqual(scene.music_context, "farewell")
                    self.assertEqual(scene._current_dialogue(), (speaker, line))
                    scene.update(1000 * len(line))
                    scene.handle_event(event)
                if not dialogues:
                    scene.handle_event(event)
            scene.update(500)
            destination.assert_called_with(self.battle._make_map_scene.return_value)
            missing_image.assert_not_called()

    def test_revanche_final_exibe_epilogo_sem_registrar_recompensa(self):
        self.battle.engine.is_replay = True
        for data in ({}, {"id": TEST_SAVE_ID, "modo_teste": True}):
            with self.subTest(data=data), patch("src.scenes.battle_scene.record_victory") as record:
                self.battle.save_data = data
                self.battle._finalize_map_phase(self.level)
                record.assert_not_called()
                self.assertIsInstance(
                    self.battle.scene_manager.change_scene.call_args.args[0], CutsceneScene
                )

    def test_falha_ao_salvar_mantem_a_batalha(self):
        with patch("src.scenes.battle_scene.record_victory", side_effect=SaveError):
            self.battle._finalize_map_phase(self.level)
        self.battle.scene_manager.change_scene.assert_not_called()

    def test_outros_encontros_e_revanche_voltam_ao_mapa(self):
        for level, kind, replay in [
            (self.level - 1, "point", False),
            (self.level, "road", False),
            (self.level - 1, "point", True),
        ]:
            with self.subTest(level=level, kind=kind, replay=replay), patch(
                "src.scenes.battle_scene.record_victory"
            ), patch("src.scenes.battle_scene.record_road_victory"):
                self.battle.encounter_kind = kind
                self.battle.engine.is_replay = replay
                self.battle.scene_manager.change_scene.reset_mock()
                self.battle._finalize_map_phase(level)
                self.battle.scene_manager.change_scene.assert_called_once_with(
                    self.battle._make_map_scene.return_value
                )
