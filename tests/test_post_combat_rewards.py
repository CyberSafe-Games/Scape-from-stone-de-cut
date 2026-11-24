"""Exercita a escolha de espólios e a persistência de um encontro real."""

import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pygame

from src.scenes.battle_scene import BattleScene
from src.scenes.cutscene_scene import CutsceneScene
from src.systems.save_manager import SaveManager
from src.systems.territory_map import ROAD_FIGHTS, TERRITORIES, complete


class PostCombatRewardTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.manager = SaveManager(folder.name)
        self.data = self.manager.create_save("slot_1")
        self.window = MagicMock()
        self.window.handle_window_event.return_value = False
        self.window.map_to_virtual.side_effect = lambda position: position
        self.scenes = MagicMock()
        self.scene = BattleScene(self.scenes, self.window, MagicMock(), self.manager,
                                 self.data, map_mode=True, selected_level=1,
                                 encounter_kind="road", encounter_index=0)
        self.scenes.current_scene = self.scene
        self.scene._return_to_map = MagicMock()
        self.initial_gold = self.scene.engine.player.coins
        self.scene.engine.enemy.hp = 0
        self.scene.engine._on_enemy_defeated()
        self.scene._outcome_elapsed = self.scene.VICTORY_POSE_MS
        self.view = self.scene.reward_view

    def click(self, rect):
        self.scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                                   pos=rect.center))

    def finish(self):
        self.scene.update(self.view.CONFIRM_MS)
        return self.manager.load_save("slot_1")["progresso"]

    def test_card_selection_saves_once_after_pulse(self):
        (_, index), rect = next(self.view.offers(self.scene.engine, self.data["progresso"]))
        card = self.scene.engine.reward_cards[index]
        self.click(rect)
        self.assertEqual(self.view.selected, ("card", index))
        self.assertIsNone(self.view.pending)
        self.click(self.view.CONFIRM)
        self.click(self.view.SKIP)
        self.scene.update(self.view.CONFIRM_MS - 1)
        self.assertEqual(self.scene.engine.state, "victory")
        self.scene._return_to_map.assert_not_called()

        progress = self.finish()
        self.assertIn(card.name, progress["cartas_colecao"])
        self.assertEqual(sum(copy["name"] == card.name for copy in progress["copies"]), 3)
        self.assertIsNone(progress["combat_snapshot"])
        self.assertEqual(progress["moedas"], self.initial_gold + self.scene._reward_gold)
        self.scene._return_to_map.assert_called_once()

    def test_material_respects_capacity_and_preserves_copies(self):
        progress = self.data["progresso"]
        full, receivable = progress["cartas_colecao"][:2]
        progress["materials"][full] = 9
        copies = len(progress["copies"])
        self.click(self.view.MATERIALS)
        tiles = dict(self.view.offers(self.scene.engine, progress))
        self.click(tiles[("material", full)])
        self.assertIsNone(self.view.selected)
        self.click(tiles[("material", receivable)])
        self.click(self.view.CONFIRM)
        saved = self.finish()
        self.assertEqual(saved["materials"][full], 9)
        self.assertEqual(saved["materials"][receivable], 1)
        self.assertEqual(len(saved["copies"]), copies)
        self.scene._return_to_map.assert_called_once()

    def test_skip_preserves_collection_and_gold(self):
        owned = self.data["progresso"]["cartas_colecao"][:]
        self.click(self.view.SKIP)
        saved = self.finish()
        self.assertEqual(saved["cartas_colecao"], owned)
        self.assertEqual(saved["moedas"], self.initial_gold + self.scene._reward_gold)
        self.scene._return_to_map.assert_called_once()

    def test_quitting_during_confirmation_persists_selection(self):
        (_, index), rect = next(self.view.offers(self.scene.engine, self.data["progresso"]))
        name = self.scene.engine.reward_cards[index].name
        self.click(rect)
        self.click(self.view.CONFIRM)
        self.scene._return_to_map.side_effect = lambda: setattr(self.scenes, "current_scene", None)
        self.assertTrue(self.scene.save_on_exit())
        self.assertIn(name, self.manager.load_save("slot_1")["progresso"]["cartas_colecao"])
        self.scene._return_to_map.assert_called_once()

    def test_resuming_victory_recovers_gold_label_without_crediting_again(self):
        self.assertTrue(self.scene._persist_logical_state())
        restored = self.manager.load_save("slot_1")
        scene = BattleScene(self.scenes, self.window, MagicMock(), self.manager,
                            restored, map_mode=True, selected_level=1,
                            encounter_kind="road", encounter_index=0)
        self.assertEqual(scene.engine.state, "victory")
        self.assertEqual(scene._reward_gold, self.scene._reward_gold)
        self.assertEqual(scene.engine.player.coins, self.initial_gold + scene._reward_gold)

    def test_final_victory_saves_and_opens_epilogue_without_an_offer(self):
        self.data["progresso"]["combat_snapshot"] = None
        for territory in TERRITORIES[:-1]:
            complete(self.data, territory.id)
        final = TERRITORIES[-1]
        self.data["progresso"]["encontros_por_territorio"][final.id] = ROAD_FIGHTS
        initial = self.data["progresso"]
        owned = list(initial["cartas_colecao"])
        gold = initial["moedas"]
        self.scenes.reset_mock()
        scene = BattleScene(self.scenes, self.window, MagicMock(), self.manager,
                            self.data, map_mode=True, selected_level=final.level,
                            encounter_kind="point")
        scene.boss_dialogue = None
        scene.engine.enemy.hp = 0
        scene.engine._on_enemy_defeated()
        scene._outcome_elapsed = 0
        scene.reward_view = MagicMock()
        scene.update(scene.VICTORY_POSE_MS - 1)
        self.scenes.change_scene.assert_not_called()
        with patch.object(CutsceneScene, "_build_layer"):
            scene.update(1)
        self.assertFalse(scene._victory_ready)
        scene.reward_view.update.assert_not_called()
        self.scenes.change_scene.assert_called_once()
        self.assertIsInstance(self.scenes.change_scene.call_args.args[0], CutsceneScene)
        saved = self.manager.load_save("slot_1")
        self.assertEqual(saved["progresso"]["estado"], "concluida")
        self.assertEqual(saved["progresso"]["cartas_colecao"], owned)
        self.assertEqual(saved["progresso"]["moedas"], gold + scene._reward_gold)
        self.assertIsNone(saved["progresso"]["combat_snapshot"])
        self.assertEqual(saved["perfil"]["campanhas_concluidas"], 1)
