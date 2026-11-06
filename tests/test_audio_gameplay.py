import unittest
from unittest.mock import MagicMock, patch, call

import pygame

from src.scenes.battle_scene import BattleScene
from src.systems.combat_engine import CombatEngine
from src.scenes.tutorial_scene import TutorialScene
from src.ui.tutorial_overlay import TutorialOverlay, TutorialStep
from src.ui.entity_view import EntityView


class TestNamedCardAudio(unittest.TestCase):
    def test_remaining_player_cards_are_synchronized_and_bounded(self):
        for name, event, sound_id, start, limit in (
            ("Poção Fragilizante", "attack", "gameplay.potion.weaken", 768, 1692),
            ("Amuleto Dissipador", "attack", "gameplay.skill.dispel", 768, 720),
            ("Máscara Ancestral", "player_action", "gameplay.skill.mask", 0, 1700),
            ("Surto de Energia", "player_action", "gameplay.skill.energy", 0, 1900),
            ("Esfera Escudo", "player_action", "gameplay.skill.shield_heavy", 572, 1728),
        ):
            with self.subTest(card=name):
                scene = self.make_scene()
                scene._handle_combat_event(event, attacker="player", action=name)
                if start:
                    scene.update(start - 1)
                    scene.scene_manager.audio_manager.play_sfx.assert_not_called()
                    scene.update(1)
                else:
                    scene.update(0)
                scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(sound_id, volume=1.0, maxtime=limit)
                scene.update(3000)
                self.assertEqual(scene.scene_manager.audio_manager.play_sfx.call_count, 1)

    def test_amulet_plays_when_frame_crosses_launch(self):
        scene = self.make_scene()
        scene._handle_combat_event("attack", attacker="player", action="Amuleto Dissipador")
        scene.update(760)
        scene.scene_manager.audio_manager.play_sfx.assert_not_called()
        scene.update(16)
        scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "gameplay.skill.dispel", volume=1.0, maxtime=712,
        )

    def test_poison_potion_starts_composition_at_throw_and_keeps_glass_and_acid_tail(self):
        scene = self.make_scene()
        scene._handle_combat_event("attack", attacker="player", action="Poção Venenosa")
        scene.update(767)
        scene.scene_manager.audio_manager.play_sfx.assert_not_called()
        scene.update(1)
        scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "gameplay.potion.poison", volume=1.0, maxtime=2407,
        )
        scene.update(312)
        scene.update(1000)
        self.assertEqual(scene.scene_manager.audio_manager.play_sfx.call_count, 1)

    def make_scene(self):
        scene = object.__new__(BattleScene)
        scene.scene_manager = MagicMock()
        scene.engine = MagicMock()
        scene.engine.state = "player_turn"
        scene.engine.enemy.name = "Slime"
        scene.entity_view = EntityView(MagicMock())
        scene.floating_texts = MagicMock()
        scene.coin_hud = MagicMock()
        scene.energy_hud = MagicMock()
        scene._ultimate_clock = 0
        scene._ultimate_events = []
        scene._boss_clock = 0
        scene._boss_events = []
        return scene

    def test_revised_attacks_preserve_impact_tail(self):
        for name, sound_id, start, limit in (
            ("Lança Perfurante", "gameplay.attack.spear", 308, 592),
            ("Machados Gêmeos", "gameplay.attack.twin_axes", 368, 532),
            ("Machado Quebra-Escudo", "gameplay.attack.shield_break", 216, 2200),
            ("Bola de Fogo", "gameplay.attack.fireball", 768, 2100),
        ):
            with self.subTest(card=name):
                scene = self.make_scene()
                scene._handle_combat_event("attack", attacker="player", action=name)
                scene.update(start - 1)
                scene.scene_manager.audio_manager.play_sfx.assert_not_called()
                scene.update(1)
                scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(sound_id, volume=1.0, maxtime=limit)
                if name in ("Lança Perfurante", "Machados Gêmeos"):
                    scene.update(468 - start)
                    self.assertEqual(scene.scene_manager.audio_manager.play_sfx.call_args,
                                     call("gameplay.attack.punch", volume=0.6, maxtime=160))
                    scene.update(1000)
                    self.assertEqual(scene.scene_manager.audio_manager.play_sfx.call_count, 2)

    def test_aura_and_totem_begin_with_visual_preparation(self):
        for name, sound_id in (("Aura Rubra", "gameplay.skill.aura"), ("Totem Protetor", "gameplay.skill.totem")):
            with self.subTest(card=name):
                scene = self.make_scene()
                scene._handle_combat_event("player_action", action=name)
                scene.update(0)
                scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(sound_id, volume=1.0, maxtime=1100)

    def test_ranged_audio_runs_only_between_launch_and_collision(self):
        for name, sound_id in (
            ("Zarabatana Venenosa", "gameplay.attack.blowgun"),
            ("Disparo de Arco", "gameplay.attack.arrow_impact"),
        ):
            with self.subTest(card=name):
                scene = self.make_scene()
                scene._handle_combat_event("attack", attacker="player", action=name)
                scene.update(767)
                scene.scene_manager.audio_manager.play_sfx.assert_not_called()
                scene.update(1)
                scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(
                    sound_id, volume=1.0, maxtime=312,
                )
                scene.update(500)
                self.assertEqual(scene.scene_manager.audio_manager.play_sfx.call_count, 1)

    def test_ranged_audio_skips_missed_collision_after_long_frame(self):
        scene = self.make_scene()
        scene._handle_combat_event("attack", attacker="player", action="Bola de Fogo")
        scene.update(1200)
        scene.scene_manager.audio_manager.play_sfx.assert_not_called()

    def test_charge_starts_running_with_animation_and_preserves_composed_impact(self):
        scene = self.make_scene()
        scene._handle_combat_event("attack", attacker="player", action="Investida")
        scene.update(0)
        scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "gameplay.attack.charge", volume=1.0, maxtime=1500,
        )
        scene.update(467)
        self.assertEqual(scene.scene_manager.audio_manager.play_sfx.call_count, 1)
        scene.update(1)
        self.assertEqual(scene.scene_manager.audio_manager.play_sfx.call_args,
                         call("gameplay.attack.charge_impact", volume=1.0, maxtime=450))
        scene.update(500)
        self.assertEqual(scene.scene_manager.audio_manager.play_sfx.call_count, 2)

    def test_self_actions_play_their_own_sound_once(self):
        for name, sound_id in (
            ("Esfera Protetora", "gameplay.skill.shield_light"),
            ("Poção de Cura", "gameplay.potion.heal"),
            ("Poção Purificadora", "gameplay.potion.cleanse"),
        ):
            with self.subTest(card=name):
                scene = self.make_scene()
                scene._handle_combat_event("player_action", action=name)
                scene.scene_manager.audio_manager.play_sfx.assert_not_called()
                scene.update(571)
                scene.scene_manager.audio_manager.play_sfx.assert_not_called()
                scene.update(1)
                scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(sound_id, volume=1.0)
                scene.update(1500)
                scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(sound_id, volume=1.0)

    def test_audio_uses_current_animation_position(self):
        scene = self.make_scene()
        scene._handle_combat_event("attack", attacker="player", action="Soco Simples")
        scene.entity_view.attack_timer = 300
        scene.entity_view.player_action_timer = 300
        scene.update(0)
        scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "gameplay.attack.punch", volume=1.0, maxtime=168,
        )


class TestPunchImpactAudio(unittest.TestCase):
    def test_arrow_plays_sound_once_at_launch_until_impact(self):
        scene = object.__new__(BattleScene)
        scene.scene_manager = MagicMock()
        scene.engine = MagicMock()
        scene.engine.state = "player_turn"
        scene.engine.enemy.name = "Slime"
        scene.entity_view = EntityView(MagicMock())
        scene.floating_texts = MagicMock()
        scene.coin_hud = MagicMock()
        scene.energy_hud = MagicMock()
        scene._ultimate_clock = 0
        scene._ultimate_events = []
        scene._boss_clock = 0
        scene._boss_events = []

        scene._handle_combat_event(
            "attack", attacker="player", action="Disparo de Arco",
        )
        scene.scene_manager.audio_manager.play_sfx.assert_not_called()

        scene.update(767)
        scene.scene_manager.audio_manager.play_sfx.assert_not_called()

        scene.update(1)
        scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "gameplay.attack.arrow_impact", volume=1.0, maxtime=312,
        )

        scene.update(500)
        scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "gameplay.attack.arrow_impact", volume=1.0, maxtime=312,
        )

    def test_blowgun_plays_sound_once_at_launch(self):
        scene = object.__new__(BattleScene)
        scene.scene_manager = MagicMock()
        scene.engine = MagicMock()
        scene.engine.state = "player_turn"
        scene.engine.enemy.name = "Slime"
        scene.entity_view = EntityView(MagicMock())
        scene.floating_texts = MagicMock()
        scene.coin_hud = MagicMock()
        scene.energy_hud = MagicMock()
        scene._ultimate_clock = 0
        scene._ultimate_events = []
        scene._boss_clock = 0
        scene._boss_events = []

        scene._handle_combat_event(
            "attack", attacker="player", action="Zarabatana Venenosa",
        )
        scene.scene_manager.audio_manager.play_sfx.assert_not_called()

        scene.update(767)
        scene.scene_manager.audio_manager.play_sfx.assert_not_called()

        scene.update(1)
        scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "gameplay.attack.blowgun", volume=1.0, maxtime=312,
        )

        scene.update(100)
        scene.update(500)
        scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "gameplay.attack.blowgun", volume=1.0, maxtime=312,
        )

    def test_bloody_dagger_preserves_composed_contact_impact(self):
        scene = object.__new__(BattleScene)
        scene.scene_manager = MagicMock()
        scene.engine = MagicMock()
        scene.engine.state = "player_turn"
        scene.engine.enemy.name = "Slime"
        scene.entity_view = EntityView(MagicMock())
        scene.floating_texts = MagicMock()
        scene.coin_hud = MagicMock()
        scene.energy_hud = MagicMock()
        scene._ultimate_clock = 0
        scene._ultimate_events = []
        scene._boss_clock = 0
        scene._boss_events = []

        scene._handle_combat_event(
            "attack", attacker="player", action="Adaga Sangrenta",
        )
        scene.scene_manager.audio_manager.play_sfx.assert_not_called()

        scene.update(215)
        scene.scene_manager.audio_manager.play_sfx.assert_not_called()

        scene.update(1)
        scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "gameplay.attack.dagger", volume=1.0, maxtime=1766,
        )

        scene.update(100)
        scene.update(500)
        scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "gameplay.attack.dagger", volume=1.0, maxtime=1766,
        )

    def test_simple_punch_sound_runs_during_motion_until_contact(self):
        scene = object.__new__(BattleScene)
        scene.scene_manager = MagicMock()
        scene.engine = MagicMock()
        scene.engine.state = "player_turn"
        scene.engine.enemy.name = "Slime"
        scene.entity_view = EntityView(MagicMock())
        scene.floating_texts = MagicMock()
        scene.coin_hud = MagicMock()
        scene.energy_hud = MagicMock()
        scene._ultimate_clock = 0
        scene._ultimate_events = []
        scene._boss_clock = 0
        scene._boss_events = []

        scene._handle_combat_event(
            "attack", attacker="player", action="Soco Simples",
        )
        scene.scene_manager.audio_manager.play_sfx.assert_not_called()

        scene.update(215)
        scene.scene_manager.audio_manager.play_sfx.assert_not_called()

        scene.update(1)
        scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "gameplay.attack.punch", volume=1.0, maxtime=252,
        )

        scene.update(100)
        scene.update(500)
        scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "gameplay.attack.punch", volume=1.0, maxtime=252,
        )


class TestTutorialGuideAudio(unittest.TestCase):
    def test_tutorial_victory_does_not_play_fanfare(self):
        scene = object.__new__(TutorialScene)
        scene.scene_manager = MagicMock()
        scene.entity_view = MagicMock()
        scene.entity_view.player_action = None

        scene._handle_combat_event("victory")

        scene.scene_manager.audio_manager.play_sfx.assert_not_called()

    def test_guide_blocks_card_hover_but_keeps_advance_click(self):
        scene = object.__new__(TutorialScene)
        scene.scene_manager = MagicMock()
        scene.window_manager = MagicMock()
        scene.window_manager.handle_window_event.return_value = False
        scene.window_manager.map_to_virtual.side_effect = lambda pos: pos
        scene.engine = MagicMock()
        scene.engine.state = "player_turn"
        scene.engine.hand = [MagicMock()]
        scene.entity_view = MagicMock()
        scene.entity_view.player_action = None
        scene.overlay = TutorialOverlay([
            TutorialStep(id="intro", title="Introdução", subtitle="Guia", lines=["Dica"]),
        ])
        scene.overlay.update(300)

        with patch.object(
            BattleScene, "_get_battle_hand_rects",
            return_value=[pygame.Rect(50, 50, 100, 100)],
        ):
            scene.handle_event(pygame.event.Event(
                pygame.MOUSEMOTION, {"pos": (100, 100)},
            ))
        scene.scene_manager.audio_manager.play_sfx.assert_not_called()
        scene.engine.play_card.assert_not_called()

        scene.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (100, 100)},
        ))
        scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "ui.click", volume=1.0,
        )
        scene.engine.play_card.assert_not_called()


class TestCardHoverTiming(unittest.TestCase):
    def setUp(self):
        self.scene = object.__new__(BattleScene)
        self.scene.scene_manager = MagicMock()
        self.scene.window_manager = MagicMock()
        self.scene.window_manager.handle_window_event.return_value = False
        self.scene.window_manager.map_to_virtual.side_effect = lambda pos: pos
        self.scene.window_manager.get_fullscreen_button_rect.return_value = pygame.Rect(0, 0, 0, 0)
        self.scene.engine = MagicMock()
        self.scene.engine.state = "player_turn"
        self.scene.engine.hand = [MagicMock(), MagicMock()]
        self.scene.entity_view = MagicMock()
        self.scene.entity_view.player_action = None
        self.scene.menu_button_rect = pygame.Rect(0, 0, 0, 0)
        self.scene.cemetery_button_rect = pygame.Rect(0, 0, 0, 0)
        self.scene.end_turn_rect = pygame.Rect(0, 0, 0, 0)
        self.rects = [pygame.Rect(50, 50, 100, 100), pygame.Rect(160, 50, 100, 100)]
        self.addCleanup(patch.stopall)
        patch.object(BattleScene, "_get_battle_hand_rects", side_effect=lambda: self.rects).start()
        patch.object(BattleScene, "_ultimate_in_hand", return_value=False).start()
        self.clock = patch("pygame.time.get_ticks", return_value=1000).start()

    def move(self, pos):
        self.scene.handle_event(pygame.event.Event(pygame.MOUSEMOTION, {"pos": pos}))

    def test_card_hover_limits_rapid_transitions(self):
        for time_ms, pos, expected_calls in (
            (1000, (100, 100), 1),
            (1040, (200, 100), 1),
            (1119, (100, 100), 1),
            (1120, (200, 100), 2),
            (1400, (200, 100), 2),
        ):
            with self.subTest(time_ms=time_ms):
                self.clock.return_value = time_ms
                self.move(pos)
                self.assertEqual(self.scene.scene_manager.audio_manager.play_sfx.call_count, expected_calls)

    def test_card_hover_ignores_hand_rearrangement_after_play(self):
        self.move((100, 100))
        self.clock.return_value = 1500
        self.scene.engine.play_card.side_effect = lambda index: self.scene.engine.hand.pop(index)
        self.scene.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (100, 100)},
        ))
        self.rects = [pygame.Rect(50, 50, 100, 100)]
        self.clock.return_value = 1700
        self.move((100, 100))
        self.assertEqual(self.scene.scene_manager.audio_manager.play_sfx.call_count, 1)
        self.move((400, 100))
        self.move((100, 100))
        self.assertEqual(self.scene.scene_manager.audio_manager.play_sfx.call_count, 2)


class TestCardGameplayAudio(unittest.TestCase):
    def test_victory_plays_sound_once(self):
        scene = object.__new__(BattleScene)
        scene.scene_manager = MagicMock()
        scene.entity_view = MagicMock()
        scene.entity_view.player_action = None
        scene.coin_hud = MagicMock()

        engine = object.__new__(CombatEngine)
        engine.state = "player_turn"
        engine.enemy = MagicMock()
        engine.enemy.boss_id = None
        engine.enemy.is_miniboss = False
        engine.on_event = scene._handle_combat_event
        engine.generate_rewards = MagicMock()

        engine._on_enemy_defeated()
        engine._on_enemy_defeated()

        self.assertEqual(engine.state, "victory")
        scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "gameplay.victory",
            volume=1.0,
        )

    def test_game_over_event_plays_sound(self):
        scene = object.__new__(BattleScene)
        scene.scene_manager = MagicMock()
        scene.entity_view = MagicMock()
        scene.entity_view.player_action = None

        scene._handle_combat_event("game_over")

        scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "gameplay.game_over",
            volume=1.0,
        )

    def test_card_hover_sound_on_entry_only(self):
        scene = object.__new__(BattleScene)
        scene.scene_manager = MagicMock()
        scene.window_manager = MagicMock()
        scene.window_manager.handle_window_event.return_value = False
        scene.window_manager.map_to_virtual.side_effect = lambda pos: pos
        scene.engine = MagicMock()
        scene.engine.state = "player_turn"
        scene.engine.hand = [MagicMock(), MagicMock()]
        scene.entity_view = MagicMock()
        scene.entity_view.player_action = None

        with (
            patch.object(
                BattleScene,
                "_get_battle_hand_rects",
                return_value=[pygame.Rect(50, 50, 100, 100), pygame.Rect(160, 50, 100, 100)],
            ),
            patch("pygame.time.get_ticks", side_effect=[1000, 1200, 1400]),
        ):
            for pos, expected_calls in (
                ((100, 100), 1),
                ((110, 100), 1),
                ((200, 100), 2),
                ((400, 100), 2),
                ((200, 100), 3),
            ):
                with self.subTest(pos=pos):
                    scene.handle_event(pygame.event.Event(pygame.MOUSEMOTION, {"pos": pos}))
                    self.assertEqual(
                        scene.scene_manager.audio_manager.play_sfx.call_count,
                        expected_calls,
                    )
                    scene.scene_manager.audio_manager.play_sfx.assert_called_with(
                        "gameplay.card_hover", volume=1.0,
                    )
        scene.engine.play_card.assert_not_called()

    def test_card_click_does_not_play_movement_sound(self):
        for success in (True, False):
            with self.subTest(success=success):
                scene = object.__new__(BattleScene)

                scene.scene_manager = MagicMock()
                scene.window_manager = MagicMock()
                scene.engine = MagicMock()
                scene.engine.state = "player_turn"
                scene.engine.hand = [MagicMock()]
                scene.engine.play_card.return_value = success

                scene.entity_view = MagicMock()
                scene.entity_view.player_action = None

                scene.menu_button_rect = pygame.Rect(0, 0, 0, 0)
                scene.cemetery_button_rect = pygame.Rect(0, 0, 0, 0)
                scene.end_turn_rect = pygame.Rect(0, 0, 0, 0)

                scene.window_manager.handle_window_event.return_value = False
                scene.window_manager.map_to_virtual.return_value = (100, 100)
                scene.window_manager.get_fullscreen_button_rect.return_value = (
                    pygame.Rect(0, 0, 0, 0)
                )

                event = pygame.event.Event(
                    pygame.MOUSEBUTTONDOWN,
                    {"button": 1, "pos": (100, 100)},
                )

                with (
                    patch.object(
                        BattleScene,
                        "_get_battle_hand_rects",
                        return_value=[pygame.Rect(50, 50, 100, 100)],
                    ),
                    patch.object(
                        BattleScene,
                        "_ultimate_in_hand",
                        return_value=False,
                    ),
                ):
                    scene.handle_event(event)

                scene.engine.play_card.assert_called_once_with(0)

                scene.scene_manager.audio_manager.play_sfx.assert_not_called()

    def test_end_turn_plays_sound(self):
        scene = object.__new__(BattleScene)

        scene.scene_manager = MagicMock()
        scene.window_manager = MagicMock()
        scene.engine = MagicMock()
        scene.engine.state = "player_turn"
        scene.engine.hand = []
        scene.entity_view = MagicMock()
        scene.entity_view.player_action = None

        scene.menu_button_rect = pygame.Rect(0, 0, 0, 0)
        scene.cemetery_button_rect = pygame.Rect(0, 0, 0, 0)
        scene.end_turn_rect = pygame.Rect(50, 50, 100, 100)

        scene.window_manager.handle_window_event.return_value = False
        scene.window_manager.map_to_virtual.return_value = (100, 100)
        scene.window_manager.get_fullscreen_button_rect.return_value = pygame.Rect(
            0, 0, 0, 0
        )

        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"button": 1, "pos": (100, 100)},
        )

        with (
            patch.object(BattleScene, "_get_battle_hand_rects", return_value=[]),
            patch.object(BattleScene, "_ultimate_in_hand", return_value=False),
        ):
            scene.handle_event(event)

        scene.engine.end_turn.assert_called_once_with()
        scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "gameplay.turn_end",
            volume=1.0,
        )

    def test_ultimate_activation_plays_sound(self):
        scene = object.__new__(BattleScene)

        scene.scene_manager = MagicMock()
        scene.window_manager = MagicMock()
        scene.engine = MagicMock()
        scene.engine.state = "player_turn"
        scene.engine.hand = []

        scene.entity_view = MagicMock()
        scene.entity_view.player_action = None

        scene.menu_button_rect = pygame.Rect(0, 0, 0, 0)
        scene.cemetery_button_rect = pygame.Rect(0, 0, 0, 0)
        scene.end_turn_rect = pygame.Rect(0, 0, 0, 0)

        scene.window_manager.handle_window_event.return_value = False
        scene.window_manager.map_to_virtual.return_value = (100, 100)
        scene.window_manager.get_fullscreen_button_rect.return_value = pygame.Rect(
            0, 0, 0, 0
        )

        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"button": 1, "pos": (100, 100)},
        )

        with (
            patch.object(
                BattleScene,
                "_get_battle_hand_rects",
                return_value=[pygame.Rect(50, 50, 100, 100)],
            ),
            patch.object(
                BattleScene,
                "_ultimate_in_hand",
                return_value=True,
            ),
        ):
            scene.handle_event(event)

        scene.engine.activate_ultimate.assert_called_once_with()
        scene.scene_manager.audio_manager.play_sfx.assert_called_once_with(
            "gameplay.ultimate_activate",
            volume=1.0,
        )
