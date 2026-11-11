"""Regra de cura pós-combate: lutas comuns não curam; miniboss cura; vida persiste."""
import os
import tempfile
import unittest
from unittest.mock import MagicMock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.systems.combat_engine import CombatEngine
from src.systems.enemy_factory import create_point_enemy, create_road_enemy
from src.systems.save_manager import SaveManager
from src.core.asset_manager import AssetManager
from src.core.window import WindowManager
from src.scenes.tutorial_scene import TutorialScene


class TestLifeAfterCombat(unittest.TestCase):
    def _map_engine(self, kind="road", index=0):
        engine = CombatEngine(map_mode=True)
        if kind == "road":
            engine.enemy = create_road_enemy(1)
        else:
            engine.enemy = create_point_enemy(1)
        engine.encounter_kind = kind
        engine.encounter_index = index
        engine.reward_cards = []
        engine.state = "victory"
        return engine

    def test_common_victory_does_not_heal(self):
        engine = self._map_engine("road")
        engine.player.hp = 23
        engine.finish_map_phase()
        self.assertEqual(engine.player.hp, 23)
        self.assertEqual(engine.state, "phase_complete")

    def test_miniboss_victory_heals_30_percent_of_max_hp(self):
        engine = self._map_engine("point", None)
        self.assertTrue(engine.enemy.is_miniboss)
        engine.player.hp = 9
        engine.finish_map_phase()
        self.assertEqual(engine.player.hp, 27)  # 9 + 30% de 60 (18)
        self.assertEqual(engine.state, "phase_complete")

    def test_miniboss_heal_never_exceeds_max_hp(self):
        engine = self._map_engine("point", None)
        engine.player.hp = 55
        engine.finish_map_phase()
        self.assertEqual(engine.player.hp, engine.player.max_hp)

    def test_miniboss_heal_tracks_changed_max_hp(self):
        engine = self._map_engine("point", None)
        engine.player.max_hp = 80
        engine.player.hp = 30
        engine.finish_map_phase()
        self.assertEqual(engine.player.hp, 54)  # 30 + 30% de 80 (24)
        self.assertLessEqual(engine.player.hp, engine.player.max_hp)

    def test_life_is_saved_and_loaded_for_next_combat(self):
        with tempfile.TemporaryDirectory() as folder:
            manager = SaveManager(saves_dir=folder)
            data = manager.create_save("slot_1")
            data["progresso"]["vida"] = 23
            manager.save(data)

            engine = CombatEngine(map_mode=True)
            engine.resume_from_save(
                manager.load_save("slot_1"),
                manager,
                level=2,
                encounter_kind="road",
                encounter_index=0,
            )
            self.assertEqual(engine.player.hp, 23)

            # Simula a gravação feita ao sair da batalha: a vida atual do
            # jogador prevalece sobre o checkpoint.
            engine.player.hp = 17
            manager.update_from_game(
                data,
                engine.player,
                engine.deck_manager,
                level=2,
            )
            manager.save(data)

            loaded = manager.load_save("slot_1")
            self.assertEqual(loaded["progresso"]["vida"], 17)

            resumed = CombatEngine(map_mode=True)
            resumed.resume_from_save(
                loaded,
                manager,
                level=2,
                encounter_kind="road",
                encounter_index=0,
            )
            self.assertEqual(resumed.player.hp, 17)

    def test_legacy_save_without_life_defaults_to_full(self):
        with tempfile.TemporaryDirectory() as folder:
            manager = SaveManager(saves_dir=folder)
            path = os.path.join(folder, "slot_2.json")
            with open(path, "w", encoding="utf-8") as stream:
                import json

                json.dump(
                    {
                        "versao": 8,
                        "id": "slot_2",
                        "nome": "Legado",
                        "criado_em": "2026-01-01T00:00:00",
                        "atualizado_em": "2026-01-01T00:00:00",
                        "progresso": {"andar": 1, "tutorial_concluido": True},
                    },
                    stream,
                )
            loaded = manager.load_save("slot_2")
            self.assertEqual(loaded["progresso"]["vida"], 60)


class TestTutorialRestoresLife(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.assets = AssetManager()

    def test_completing_tutorial_saves_full_life_for_the_campaign(self):
        with tempfile.TemporaryDirectory() as folder:
            manager = SaveManager(saves_dir=folder)
            data = manager.create_save("slot_1", display_name="Jornada 01")

            scene = TutorialScene(
                MagicMock(),
                WindowManager(),
                self.assets,
                save_manager=manager,
                save_data=data,
            )
            scene.engine.player.hp = 17
            scene.engine.state = "victory"
            scene._complete_tutorial()

            loaded = manager.load_save("slot_1")
            self.assertEqual(loaded["progresso"]["vida"], 60)
            self.assertTrue(loaded["progresso"]["tutorial_concluido"])


if __name__ == "__main__":
    unittest.main()
