"""Confere os quadros de derrota dos kits usados na campanha."""

from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

import pygame

from src.scenes.battle_scene import BattleScene
from src.systems.boss_animation_kits import KITS
from src.systems.common_animation_kits import COMMON_KITS
from src.ui.entity_view import EntityView


class EnemyDefeatTests(unittest.TestCase):
    def test_campaign_kits_have_a_defeat_pose_or_dedicated_sequence(self):
        root = Path(__file__).resolve().parents[1] / "assets" / "enemies" / "defeat"
        dedicated = {"slime", "vinimuth", "zanzara", "álvaro e tex"}
        for name, (slug, _) in (COMMON_KITS | KITS).items():
            if name in dedicated:
                continue
            with self.subTest(name=name):
                sprite = pygame.image.load(str(root / f"{slug}.png"))
                self.assertEqual(sprite.get_width(), 448)
                self.assertIn(sprite.get_height(), (260, 320))
                bounds = sprite.get_bounding_rect(min_alpha=32)
                self.assertGreater(bounds.height, 0)
                self.assertLess(bounds.height, sprite.get_height())
                self.assertGreater(bounds.bottom, sprite.get_height() - 12)

    def test_bat_landing_plays_impact_before_victory_and_only_once(self):
        scene = object.__new__(BattleScene)
        scene.entity_view = EntityView(MagicMock())
        scene.engine = SimpleNamespace(state="victory", enemy=SimpleNamespace(name="Morcego Sombrio"))
        scene.play_ui_sound = MagicMock()
        view = scene.entity_view
        scene._update_outcome(0)
        scene._update_outcome(view.BAT_FALL_MS * view.BAT_LANDING_FRACTION - 1)
        scene.play_ui_sound.assert_not_called()
        scene._update_outcome(2)
        scene.play_ui_sound.assert_called_once_with("gameplay.attack.charge_impact", volume=0.45)
        scene._update_outcome(view.BAT_FALL_MS)
        self.assertEqual([cue.args[0] for cue in scene.play_ui_sound.call_args_list],
                         ["gameplay.attack.charge_impact", "gameplay.victory"])
