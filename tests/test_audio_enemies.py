import unittest
from unittest.mock import MagicMock

from src.models.enemy import Enemy
from src.scenes.battle_scene import BattleScene
from src.ui.entity_view import EntityView
from src.systems.enemy_factory import create_alvaro_tex, create_gordofera, create_zanzara, create_guardiao_da_pedra, create_goblin_nerd, create_corpo_seco, create_carrasco_da_vigilia


class TestCommonEnemyAudio(unittest.TestCase):
    def test_carrasco_axe_motion_and_contact_are_synchronized(self):
        for action, ultimate, movement, release, impact in (
            ("atk1", False, "gameplay.boss.carrasco.cut", 0.24, "gameplay.boss.duo.heavy_hit"),
            ("atk2", False, "gameplay.boss.carrasco.sweep", 0.24, "gameplay.boss.duo.heavy_hit"),
            ("atk3", True, "gameplay.boss.carrasco.execution", 0.40, "gameplay.boss.carrasco.execution_hit"),
        ):
            with self.subTest(action=action):
                scene = self.make_scene("Carrasco da Vigília", miniboss=True)
                scene.engine.enemy = create_carrasco_da_vigilia()
                scene._handle_combat_event("attack", attacker="enemy", action=action, ultimate=ultimate)
                scene._handle_combat_event("flash", target="player")
                view = scene.entity_view
                start = view.enemy_attack_duration * release
                contact = view.enemy_attack_duration * view.enemy_impact_fraction
                audio = scene.scene_manager.audio_manager.play_sfx
                scene.update(start - 1)
                audio.assert_not_called()
                scene.update(1)
                self.assertEqual(audio.call_args.args, (movement,))
                self.assertLessEqual(audio.call_args.kwargs["maxtime"], contact - start)
                scene.update(contact - start - 1)
                self.assertEqual(audio.call_count, 1)
                scene.update(1)
                self.assertEqual(audio.call_args.args, (impact,))
                self.assertGreater(view.player_flash, 0)
                scene.update(3000)
                self.assertEqual(audio.call_count, 2)

    def test_carrasco_vigor_has_tail_and_cancelled_execution_is_silent(self):
        scene = self.make_scene("Carrasco da Vigília", miniboss=True)
        scene.engine.enemy = create_carrasco_da_vigilia()
        scene._handle_combat_event("enemy_action", action="healer2")
        duration = scene.entity_view.enemy_action_duration
        scene.update(duration * 0.52 - 1)
        audio = scene.scene_manager.audio_manager.play_sfx
        audio.assert_not_called()
        scene.update(1)
        self.assertEqual(audio.call_args.args, ("gameplay.boss.carrasco.vigor",))
        self.assertGreaterEqual(duration * 0.52 + audio.call_args.kwargs["maxtime"], duration + 600)
        for cancel in (True, False):
            scene = self.make_scene("Carrasco da Vigília", miniboss=True)
            scene.engine.enemy = create_carrasco_da_vigilia()
            scene._handle_combat_event("attack", attacker="enemy", action="atk3", ultimate=True)
            if cancel:
                scene.entity_view.attacker = None
                scene.entity_view.enemy_action = None
            scene.update(3000)
            scene.scene_manager.audio_manager.play_sfx.assert_not_called()

    def test_corpo_seco_blades_and_flesh_contact_are_synchronized(self):
        for action, ultimate, movement, release in (
            ("atk1", False, "gameplay.boss.corpo.slash", 0.24),
            ("atk3", False, "gameplay.boss.corpo.cross", 0.24),
            ("atk4", True, "gameplay.boss.corpo.spin", 0.40),
        ):
            with self.subTest(action=action):
                scene = self.make_scene("Corpo Seco", miniboss=True)
                scene.engine.enemy = create_corpo_seco()
                scene._handle_combat_event("attack", attacker="enemy", action=action, ultimate=ultimate)
                scene._handle_combat_event("flash", target="player")
                view = scene.entity_view
                start = view.enemy_attack_duration * release
                contact = view.enemy_attack_duration * view.enemy_impact_fraction
                audio = scene.scene_manager.audio_manager.play_sfx
                scene.update(start - 1)
                audio.assert_not_called()
                scene.update(1)
                self.assertEqual(audio.call_args.args, (movement,))
                self.assertLessEqual(audio.call_args.kwargs["maxtime"], contact - start)
                scene.update(contact - start - 1)
                self.assertEqual(audio.call_count, 1)
                scene.update(1)
                self.assertEqual(audio.call_args.args, ("gameplay.boss.duo.flesh_hit",))
                self.assertGreater(view.player_flash, 0)
                scene.update(3000)
                self.assertEqual(audio.call_count, 2)

    def test_corpo_seco_guard_tail_and_cancelled_ultimate(self):
        scene = self.make_scene("Corpo Seco", miniboss=True)
        scene.engine.enemy = create_corpo_seco()
        scene._handle_combat_event("enemy_action", action="def")
        duration = scene.entity_view.enemy_action_duration
        scene.update(duration * 0.52 - 1)
        audio = scene.scene_manager.audio_manager.play_sfx
        audio.assert_not_called()
        scene.update(1)
        self.assertEqual(audio.call_args.args, ("gameplay.boss.corpo.guard",))
        self.assertGreaterEqual(duration * 0.52 + audio.call_args.kwargs["maxtime"], duration + 600)
        for cancel in (True, False):
            scene = self.make_scene("Corpo Seco", miniboss=True)
            scene.engine.enemy = create_corpo_seco()
            scene._handle_combat_event("attack", attacker="enemy", action="atk4", ultimate=True)
            if cancel:
                scene.entity_view.attacker = None
                scene.entity_view.enemy_action = None
            scene.update(3000)
            scene.scene_manager.audio_manager.play_sfx.assert_not_called()

    def test_gordofera_attacks_match_movement_and_contact(self):
        for action, ultimate, cues in (
            ("atk1", False, ((0.24, "gameplay.boss.guardian.claw"), (0.52, "gameplay.boss.guardian.claw_hit"))),
            ("atk2", False, ((0.35, "gameplay.boss.gordofera.roar"),)),
            ("atk3", False, ((0.52, "gameplay.attack.charge_impact"),)),
            ("atk4", True, ((0.25, "gameplay.boss.gordofera.jump"), (0.64, "gameplay.boss.gordofera.tremor"))),
        ):
            with self.subTest(action=action):
                scene = self.make_scene("Gordofera", miniboss=True)
                scene.engine.enemy = create_gordofera()
                scene._handle_combat_event("attack", attacker="enemy", action=action, ultimate=ultimate)
                scene._handle_combat_event("flash", target="player")
                duration = scene.entity_view.enemy_attack_duration
                elapsed = 0
                audio = scene.scene_manager.audio_manager.play_sfx
                for count, (fraction, sound_id) in enumerate(cues):
                    when = duration * fraction
                    scene.update(when - elapsed - 1)
                    self.assertEqual(audio.call_count, count)
                    scene.update(1)
                    self.assertEqual(audio.call_args.args, (sound_id,))
                    elapsed = when
                scene.update(3000)
                self.assertEqual(audio.call_count, len(cues))

    def test_gordofera_guard_and_tremor_have_tails(self):
        for ultimate in (False, True):
            scene = self.make_scene("Gordofera", miniboss=True)
            scene.engine.enemy = create_gordofera()
            if ultimate:
                scene._handle_combat_event("attack", attacker="enemy", action="atk4", ultimate=True)
                duration = scene.entity_view.enemy_attack_duration
                when = duration * 0.64
                scene.update(duration * 0.25)
                scene.update(when - duration * 0.25)
            else:
                scene._handle_combat_event("enemy_action", action="def")
                duration = scene.entity_view.enemy_action_duration
                when = duration * 0.52
                scene.update(when)
            args = scene.scene_manager.audio_manager.play_sfx.call_args
            self.assertEqual(args.args, ("gameplay.boss.gordofera.tremor" if ultimate else "gameplay.boss.gordofera.guard",))
            self.assertGreaterEqual(when + args.kwargs["maxtime"], duration + 600)

    def test_gordofera_cancelled_ultimate_does_not_play(self):
        scene = self.make_scene("Gordofera", miniboss=True)
        scene.engine.enemy = create_gordofera()
        scene._handle_combat_event("attack", attacker="enemy", action="atk4", ultimate=True)
        scene.entity_view.attacker = None
        scene.entity_view.enemy_action = None
        scene.update(1000)
        scene.scene_manager.audio_manager.play_sfx.assert_not_called()

    def test_goblin_lasers_keep_burning_after_animation(self):
        for ultimate in (False, True):
            with self.subTest(ultimate=ultimate):
                scene = self.make_scene("Goblin Nerd", miniboss=True)
                scene.engine.enemy = create_goblin_nerd()
                scene._handle_combat_event("attack", attacker="enemy", action="atk2", ultimate=ultimate)
                duration = scene.entity_view.enemy_attack_duration
                impact = duration * scene.entity_view.enemy_impact_fraction
                scene.update(impact)
                args = scene.scene_manager.audio_manager.play_sfx.call_args
                self.assertEqual(args.args, ("gameplay.boss.goblin.energy_hit",))
                self.assertGreaterEqual(impact + args.kwargs["maxtime"], duration + 900)

    def test_goblin_acid_continues_after_attack_animation(self):
        scene = self.make_scene("Goblin Nerd", miniboss=True)
        scene.engine.enemy = create_goblin_nerd()
        scene._handle_combat_event("attack", attacker="enemy", action="atk3")
        duration = scene.entity_view.enemy_attack_duration
        activation = duration * 0.43
        scene.update(duration * 0.18)
        scene.update(activation - duration * 0.18)
        audio = scene.scene_manager.audio_manager.play_sfx
        self.assertEqual(audio.call_args.args, ("gameplay.boss.goblin.toxic",))
        self.assertGreaterEqual(activation + audio.call_args.kwargs["maxtime"], duration + 900)
        scene.update(duration)
        self.assertEqual(audio.call_count, 2)

    def test_goblin_projectiles_and_ultimate_have_separate_synchronized_cues(self):
        for action, ultimate, cues in (
            ("atk1", False, ((0.30, "gameplay.boss.goblin.throw"), (0.74, "gameplay.boss.small.body_hit"))),
            ("atk2", False, ((0.30, "gameplay.boss.goblin.zap"), (0.58, "gameplay.boss.goblin.energy_hit"))),
            ("atk2", True, ((0.10, "gameplay.boss.goblin.charge"), (0.44, "gameplay.boss.goblin.beam"), (0.77, "gameplay.boss.goblin.energy_hit"))),
        ):
            with self.subTest(action=action, ultimate=ultimate):
                scene = self.make_scene("Goblin Nerd", miniboss=True)
                scene.engine.enemy = create_goblin_nerd()
                scene._handle_combat_event("attack", attacker="enemy", action=action, ultimate=ultimate)
                scene._handle_combat_event("flash", target="player")
                duration = scene.entity_view.enemy_attack_duration
                elapsed = 0
                audio = scene.scene_manager.audio_manager.play_sfx
                for count, (fraction, sound_id) in enumerate(cues):
                    when = round(duration * fraction, 6)
                    scene.update(when - elapsed - 1)
                    self.assertEqual(audio.call_count, count)
                    scene.update(1)
                    self.assertEqual(audio.call_args.args, (sound_id,))
                    elapsed = when
                self.assertGreater(scene.entity_view.player_flash, 0)
                scene.update(3000)
                self.assertEqual(audio.call_count, len(cues))

    def test_goblin_toxic_breath_and_shield_activate_once(self):
        for action, event, fraction, sound_id in (
            ("healer2", "enemy_action", 0.52, "gameplay.boss.goblin.shield"),
        ):
            scene = self.make_scene("Goblin Nerd", miniboss=True)
            scene.engine.enemy = create_goblin_nerd()
            scene._handle_combat_event(event, attacker="enemy", action=action)
            duration = scene.entity_view.enemy_attack_duration if event == "attack" else scene.entity_view.enemy_action_duration
            scene.update(duration * fraction - 1)
            audio = scene.scene_manager.audio_manager.play_sfx
            audio.assert_not_called()
            scene.update(1)
            self.assertEqual(audio.call_args.args, (sound_id,))
            if event == "enemy_action":
                self.assertGreaterEqual(duration * fraction + audio.call_args.kwargs["maxtime"], duration + 600)
            scene.update(3000)
            audio.assert_called_once()

    def test_goblin_retch_precedes_visible_acid_jet(self):
        scene = self.make_scene("Goblin Nerd", miniboss=True)
        scene.engine.enemy = create_goblin_nerd()
        scene._handle_combat_event("attack", attacker="enemy", action="atk3")
        duration = scene.entity_view.enemy_attack_duration
        audio = scene.scene_manager.audio_manager.play_sfx
        scene.update(duration * 0.18 - 1)
        audio.assert_not_called()
        scene.update(1)
        self.assertEqual(audio.call_args.args, ("gameplay.boss.goblin.retch",))
        # A voz termina por cima da saída do líquido, sem ser cortada ali.
        self.assertGreaterEqual(audio.call_args.kwargs["maxtime"], duration * (0.43 - 0.18) + 200)
        scene.update(duration * (0.43 - 0.18) - 1)
        self.assertEqual(audio.call_count, 1)
        scene.update(1)
        self.assertEqual(audio.call_args.args, ("gameplay.boss.goblin.toxic",))
        scene.update(3000)
        self.assertEqual(audio.call_count, 2)

    def test_goblin_cancelled_ultimate_and_late_frame_do_not_play(self):
        for cancel in (True, False):
            scene = self.make_scene("Goblin Nerd", miniboss=True)
            scene.engine.enemy = create_goblin_nerd()
            scene._handle_combat_event("attack", attacker="enemy", action="atk2", ultimate=True)
            if cancel:
                scene.entity_view.attacker = None
                scene.entity_view.enemy_action = None
            scene.update(3000)
            scene.scene_manager.audio_manager.play_sfx.assert_not_called()

    def test_small_phase_two_movement_and_body_contacts_are_synchronized(self):
        for action, ultimate, fraction, movement, impact in (
            ("atk2", False, 0.24, "gameplay.boss.small.club", "gameplay.boss.small.body_hit"),
            ("atk4", False, 0.38, "gameplay.boss.duo.star", "gameplay.boss.duo.flesh_hit"),
            ("atk3", True, 0.24, "gameplay.boss.small.fury", "gameplay.boss.small.fury_hit"),
        ):
            with self.subTest(action=action):
                scene = self.make_scene("Álvaro e Tex · Pequeno", miniboss=True)
                scene.engine.enemy = create_alvaro_tex(phase=2)
                scene._handle_combat_event("attack", attacker="enemy", action=action, ultimate=ultimate)
                scene._handle_combat_event("flash", target="player")
                duration = scene.entity_view.enemy_attack_duration
                launch = duration * fraction
                contact = duration * scene.entity_view.enemy_impact_fraction
                audio = scene.scene_manager.audio_manager.play_sfx
                scene.update(launch - 1)
                audio.assert_not_called()
                scene.update(1)
                self.assertEqual(audio.call_args.args, (movement,))
                scene.update(contact - launch - 1)
                self.assertEqual(audio.call_count, 1)
                scene.update(1)
                self.assertEqual(audio.call_args.args, (impact,))
                self.assertGreater(scene.entity_view.player_flash, 0)
                scene.update(3000)
                self.assertEqual(audio.call_count, 2)

    def test_small_cancelled_ultimate_or_phase_change_does_not_play(self):
        for change_phase in (False, True):
            scene = self.make_scene("Álvaro e Tex · Pequeno", miniboss=True)
            scene.engine.enemy = create_alvaro_tex(phase=2)
            scene._handle_combat_event("attack", attacker="enemy", action="atk3", ultimate=True)
            if change_phase:
                scene.engine.enemy = create_alvaro_tex(phase=1)
            else:
                scene.entity_view.attacker = None
                scene.entity_view.enemy_action = None
            scene.update(500)
            scene.scene_manager.audio_manager.play_sfx.assert_not_called()

    def test_duo_phase_one_moves_then_hits_flesh(self):
        for action, ultimate, movement, start_fraction in (
            ("atk1", False, "gameplay.boss.duo.stab", 0.24),
            ("atk2", False, "gameplay.boss.duo.star", 0.30),
            ("atk4", True, "gameplay.boss.duo.whirl", 0.24),
        ):
            with self.subTest(action=action):
                scene = self.make_scene("Álvaro e Tex", miniboss=True)
                scene.engine.enemy = create_alvaro_tex(phase=1)
                scene._handle_combat_event("attack", attacker="enemy", action=action, ultimate=ultimate)
                view = scene.entity_view
                start = view.enemy_attack_duration * start_fraction
                contact = view.enemy_attack_duration * view.enemy_impact_fraction
                audio = scene.scene_manager.audio_manager.play_sfx
                scene.update(start - 1)
                audio.assert_not_called()
                scene.update(1)
                self.assertEqual(audio.call_args.args, (movement,))
                scene.update(contact - start - 1)
                self.assertEqual(audio.call_count, 1)
                scene.update(1)
                impact = "gameplay.boss.duo.flesh_hit" if action == "atk2" else "gameplay.boss.duo.heavy_hit"
                self.assertEqual(audio.call_args.args, (impact,))
                self.assertEqual(audio.call_count, 2)
                scene.update(3000)
                self.assertEqual(audio.call_count, 2)

    def test_duo_smoke_has_tail_and_cancelled_attack_has_no_sound(self):
        scene = self.make_scene("Álvaro e Tex", miniboss=True)
        scene.engine.enemy = create_alvaro_tex(phase=1)
        scene._handle_combat_event("enemy_action", action="healer2")
        duration = scene.entity_view.enemy_action_duration
        activation = duration * 0.20
        scene.update(activation - 1)
        scene.scene_manager.audio_manager.play_sfx.assert_not_called()
        scene.update(1)
        args = scene.scene_manager.audio_manager.play_sfx.call_args
        self.assertEqual(args.args, ("gameplay.boss.duo.smoke",))
        self.assertGreaterEqual(activation + args.kwargs["maxtime"], duration + 600)
        for ultimate, action in ((False, "atk1"), (True, "atk4")):
            scene = self.make_scene("Álvaro e Tex", miniboss=True)
            scene.engine.enemy = create_alvaro_tex(phase=1)
            scene._handle_combat_event("attack", attacker="enemy", action=action, ultimate=ultimate)
            scene.entity_view.attacker = None
            scene.entity_view.enemy_action = None
            scene.update(3000)
            scene.scene_manager.audio_manager.play_sfx.assert_not_called()

    def test_guardian_claw_swings_before_contact_then_plays_flesh_cut(self):
        scene = self.make_scene("Guardião da Pedra", miniboss=True)
        scene.engine.enemy = create_guardiao_da_pedra()
        scene._handle_combat_event("attack", attacker="enemy", action="atk1")
        duration = scene.entity_view.enemy_attack_duration
        swing = duration * 0.24
        contact = duration * scene.entity_view.enemy_impact_fraction
        audio = scene.scene_manager.audio_manager.play_sfx
        scene.update(swing - 1)
        audio.assert_not_called()
        scene.update(1)
        self.assertEqual(audio.call_args.args, ("gameplay.boss.guardian.claw",))
        self.assertLessEqual(audio.call_args.kwargs["maxtime"], contact - swing)
        scene.update(contact - swing - 1)
        self.assertEqual(audio.call_count, 1)
        scene.update(1)
        self.assertEqual(audio.call_args.args, ("gameplay.boss.guardian.claw_hit",))
        self.assertEqual(audio.call_count, 2)
        scene.update(3000)
        self.assertEqual(audio.call_count, 2)

    def test_guardian_buffs_allow_audible_tail_after_animation(self):
        for action in ("def", "healer2"):
            with self.subTest(action=action):
                scene = self.make_scene("Guardião da Pedra", miniboss=True)
                scene.engine.enemy = create_guardiao_da_pedra()
                scene._handle_combat_event("enemy_action", action=action)
                duration = scene.entity_view.enemy_action_duration
                activation = duration * 0.52
                scene.update(activation)
                limit = scene.scene_manager.audio_manager.play_sfx.call_args.kwargs["maxtime"]
                self.assertGreaterEqual(activation + limit, duration + 600)
                scene.update(duration)
                scene.scene_manager.audio_manager.play_sfx.assert_called_once()

    def test_guardian_pilot_sounds_follow_action_and_ultimate_release(self):
        for action, attack, ultimate, sound_id in (
            ("def", False, False, "gameplay.boss.guardian.stone"),
            ("healer2", False, False, "gameplay.boss.guardian.heal"),
            ("atk2", True, True, "gameplay.boss.guardian.roar"),
        ):
            with self.subTest(action=action):
                scene = self.make_scene("Guardião da Pedra", miniboss=True)
                scene.engine.enemy = create_guardiao_da_pedra()
                if attack:
                    scene._handle_combat_event("attack", attacker="enemy", action=action, ultimate=ultimate)
                    view = scene.entity_view
                    fraction = view.enemy_ultimate.release if ultimate else view.enemy_impact_fraction
                    when = view.enemy_attack_duration * fraction
                else:
                    scene._handle_combat_event("enemy_action", action=action)
                    when = scene.entity_view.enemy_action_duration * 0.52
                scene.update(when - 1)
                scene.scene_manager.audio_manager.play_sfx.assert_not_called()
                scene.update(1)
                scene.scene_manager.audio_manager.play_sfx.assert_called_once()
                self.assertEqual(scene.scene_manager.audio_manager.play_sfx.call_args.args, (sound_id,))
                self.assertGreater(scene.scene_manager.audio_manager.play_sfx.call_args.kwargs["maxtime"], 0)
                scene.update(3000)
                scene.scene_manager.audio_manager.play_sfx.assert_called_once()

    def test_guardian_cancelled_or_late_ultimate_does_not_play(self):
        for cancel in (True, False):
            scene = self.make_scene("Guardião da Pedra", miniboss=True)
            scene.engine.enemy = create_guardiao_da_pedra()
            scene._handle_combat_event("attack", attacker="enemy", action="atk2", ultimate=True)
            if cancel:
                scene.entity_view.attacker = None
                scene.entity_view.enemy_action = None
            scene.update(3000)
            scene.scene_manager.audio_manager.play_sfx.assert_not_called()

    def make_scene(self, name, miniboss=False):
        scene = object.__new__(BattleScene)
        scene.scene_manager = MagicMock()
        scene.engine = MagicMock()
        scene.engine.state = "enemy_resolving"
        scene.engine.enemy = Enemy(name, 40, is_miniboss=miniboss)
        scene.entity_view = EntityView(MagicMock())
        scene.floating_texts = MagicMock()
        scene.coin_hud = MagicMock()
        scene.energy_hud = MagicMock()
        scene._ultimate_clock = 0
        scene._ultimate_events = []
        scene._boss_clock = 0
        scene._boss_events = []
        return scene

    def test_common_attacks_use_matching_sound_once_at_visual_contact(self):
        for name, action, sound_id in (
            ("Slime", "atk", "gameplay.enemy.slime"),
            ("Viniurgo", "atk1", "gameplay.attack.punch"),
            ("Viniurgo", "atk2", "gameplay.attack.punch"),
            ("Vinimuth", "atk1", "gameplay.attack.punch"),
            ("Vinimuth", "atk2", "gameplay.skill.energy"),
            ("Esqueleto Saqueador", "atk1", "gameplay.enemy.blade"),
            ("Esqueleto Saqueador", "atk2", "gameplay.attack.spear"),
            ("Golem das Ruínas", "atk1", "gameplay.attack.charge_impact"),
            ("Centauro Vigia", "atk2", "gameplay.attack.charge_impact"),
            ("Putrefato do Pântano", "atk1", "gameplay.enemy.acid"),
            ("Guerreiro da Mata", "atk1", "gameplay.attack.charge_impact"),
            ("Guerreiro da Mata", "atk2", "gameplay.attack.charge_impact"),
            ("Lagarto Couraçado", "atk1", "gameplay.attack.punch"),
            ("Morcego Sombrio", "atk1", "gameplay.attack.punch"),
            ("Morcego Sombrio", "atk2", "gameplay.skill.energy"),
            ("Lutador Mascarado", "atk1", "gameplay.attack.punch"),
            ("Lutador Mascarado", "atk2", "gameplay.attack.charge_impact"),
            ("Mago do Santuário", "atk1", "gameplay.attack.fireball"),
            ("Mago do Santuário", "atk2", "gameplay.attack.charge_impact"),
            ("Crocodilo Abissal", "atk1", "gameplay.attack.charge_impact"),
            ("Macaco Selvagem", "atk1", "gameplay.attack.punch"),
        ):
            with self.subTest(enemy=name, action=action):
                scene = self.make_scene(name)
                scene._handle_combat_event("attack", attacker="enemy", action=action)
                scene._handle_combat_event("flash", target="player")
                contact = scene.entity_view.enemy_attack_duration * scene.entity_view.enemy_impact_fraction
                scene.update(contact - 1)
                scene.scene_manager.audio_manager.play_sfx.assert_not_called()
                scene.update(1)
                scene.scene_manager.audio_manager.play_sfx.assert_called_once()
                self.assertEqual(scene.scene_manager.audio_manager.play_sfx.call_args.args, (sound_id,))
                self.assertGreater(scene.entity_view.player_flash, 0)
                scene.update(2000)
                scene.scene_manager.audio_manager.play_sfx.assert_called_once()

    def test_centaur_arrow_has_distinct_launch_and_contact(self):
        scene = self.make_scene("Centauro Vigia")
        scene._handle_combat_event("attack", attacker="enemy", action="atk1")
        scene._handle_combat_event("flash", target="player")
        duration, launch, impact = scene.entity_view.enemy_ranged_attack
        scene.update(duration * launch)
        self.assertEqual(scene.scene_manager.audio_manager.play_sfx.call_args.args, ("gameplay.attack.arrow_launch",))
        scene.update(duration * (impact - launch))
        self.assertEqual(scene.scene_manager.audio_manager.play_sfx.call_args.args, ("gameplay.attack.arrow_impact",))
        self.assertEqual(scene.scene_manager.audio_manager.play_sfx.call_count, 2)

    def test_common_defense_and_heal_sound_at_activation(self):
        for name, action, sound_id in (
            ("Slime", "def", "gameplay.skill.shield_light"),
            ("Golem das Ruínas", "def", "gameplay.skill.shield_light"),
            ("Lagarto Couraçado", "def", "gameplay.skill.shield_light"),
            ("Crocodilo Abissal", "def", "gameplay.skill.shield_light"),
            ("Putrefato do Pântano", "healer2", "gameplay.enemy.heal"),
            ("Macaco Selvagem", "healer2", "gameplay.enemy.heal"),
        ):
            with self.subTest(enemy=name, action=action):
                scene = self.make_scene(name)
                scene._handle_combat_event("enemy_action", action=action)
                activation = scene.entity_view.enemy_action_duration * 0.52
                scene.update(activation - 1)
                scene.scene_manager.audio_manager.play_sfx.assert_not_called()
                scene.update(1)
                scene.scene_manager.audio_manager.play_sfx.assert_called_once()
                self.assertEqual(scene.scene_manager.audio_manager.play_sfx.call_args.args, (sound_id,))

    def test_bosses_and_unmapped_actions_remain_without_new_sound(self):
        for name, miniboss, action in (
            ("Goblin Nerd", True, "atk1"),
            ("Corpo Seco", True, "atk1"),
            ("Zanzara", True, "atk2"),
            ("Guardião da Pedra", True, "atk1"),
            ("Carrasco da Vigília", True, "atk1"),
            ("Gordofera", True, "atk1"),
            ("Gordofera", True, "atk2"),
            ("Álvaro e Tex", True, "atk1"),
            ("Álvaro e Tex · Pequeno", True, "atk2"),
            ("Slime", True, "atk"),
            ("Inimigo desconhecido", False, "atk1"),
            ("Esqueleto Saqueador", False, "acao_desconhecida"),
        ):
            with self.subTest(enemy=name, action=action):
                scene = self.make_scene(name, miniboss)
                scene._handle_combat_event("attack", attacker="enemy", action=action)
                scene.update(3000)
                scene.scene_manager.audio_manager.play_sfx.assert_not_called()

    def test_only_basic_unarmed_boss_attacks_reuse_body_impacts(self):
        for enemy, action, sound_id in (
            (create_alvaro_tex(phase=2), "atk1", "gameplay.attack.punch"),
            (create_gordofera(), "atk3", "gameplay.attack.charge_impact"),
        ):
            with self.subTest(enemy=enemy.name):
                scene = self.make_scene(enemy.name, miniboss=True)
                scene.engine.enemy = enemy
                scene._handle_combat_event("attack", attacker="enemy", action=action)
                scene._handle_combat_event("flash", target="player")
                contact = scene.entity_view.enemy_attack_duration * scene.entity_view.enemy_impact_fraction
                scene.update(contact - 1)
                scene.scene_manager.audio_manager.play_sfx.assert_not_called()
                scene.update(1)
                scene.scene_manager.audio_manager.play_sfx.assert_called_once()
                self.assertEqual(scene.scene_manager.audio_manager.play_sfx.call_args.args, (sound_id,))
                self.assertGreater(scene.entity_view.player_flash, 0)

    def test_boss_ultimate_never_uses_basic_attack_sound(self):
        scene = self.make_scene("Zanzara", miniboss=True)
        scene.engine.enemy = create_zanzara()
        scene._handle_combat_event("attack", attacker="enemy", action="atk1", ultimate=True)
        scene.update(1000)
        scene.scene_manager.audio_manager.play_sfx.assert_not_called()

    def test_cancelled_attack_and_long_frame_do_not_play_stale_sound(self):
        for cancel in (True, False):
            with self.subTest(cancel=cancel):
                scene = self.make_scene("Lutador Mascarado")
                scene._handle_combat_event("attack", attacker="enemy", action="atk1")
                if cancel:
                    scene.entity_view.attacker = None
                    scene.entity_view.enemy_action = None
                scene.update(3000)
                scene.scene_manager.audio_manager.play_sfx.assert_not_called()
