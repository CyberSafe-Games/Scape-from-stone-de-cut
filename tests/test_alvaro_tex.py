"""Duas fases, recompensa única, recursos contínuos e oito poses reais por ataque."""
import os
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

from src.systems.combat_engine import CombatEngine
from src.systems.enemy_factory import create_alvaro_tex, create_point_enemy, create_road_enemy, choose_next_action
from src.systems.alvaro_tex_animations import NAMES, ATTACK_MS, TRANSITION_MS
from src.ui.entity_view import EntityView


class AlvaroTexCombatTests(TestCase):
    def setUp(self):
        self.events = []
        self.engine = CombatEngine(lambda event, **kw: self.events.append((event, kw)), map_mode=True)
        self.engine.level = 2
        self.engine.enemy = create_point_enemy(2)
        choose_next_action(self.engine.enemy)
        self.events.clear()

    def test_biome_and_phases(self):
        self.assertEqual(self.engine.enemy.name, 'Álvaro e Tex')
        self.assertTrue(self.engine.enemy.is_miniboss)
        for _ in range(15):
            self.assertNotEqual(getattr(create_road_enemy(2), 'boss_id', None), 'alvaro_tex')
        with self.assertRaises(ValueError):
            create_alvaro_tex(phase=3)

    def test_first_defeat_preserves_player_and_only_second_rewards(self):
        e = self.engine
        e.player.hp = 31
        e.player.energy = 1
        e.player.add_block(12)
        e.player.strength = 8
        e.player.ultimate_charge = 7
        e.cemetery_swap_used = True
        hand = list(e.hand)
        piles = (list(e.draw_pile), list(e.discard_pile))
        e.enemy.apply_status('poison', 3, 5)
        e.enemy.hp = 0
        e._on_enemy_defeated()
        self.assertEqual(e.state, 'boss_transition')
        self.assertFalse(e.reward_cards)
        self.assertNotIn('coin_drop', [x[0] for x in self.events])
        self.assertFalse(e.play_card(0))
        e.end_turn()
        self.assertEqual(e.state, 'boss_transition')
        self.assertTrue(e.finish_boss_transition())
        self.assertFalse(e.finish_boss_transition())
        self.assertEqual(e.enemy.phase, 2)
        self.assertFalse(e.enemy.statuses)
        self.assertEqual((e.player.hp, e.player.energy, e.player.block, e.player.strength, e.player.ultimate_charge), (31,1,12,8,7))
        self.assertEqual(e.hand, hand)
        self.assertEqual((e.draw_pile, e.discard_pile), piles)
        self.assertTrue(e.cemetery_swap_used)
        e.enemy.hp = 0
        e._on_enemy_defeated()
        e._on_enemy_defeated()
        self.assertEqual(e.state, 'victory')
        self.assertEqual(len(e.reward_cards), 3)
        self.assertEqual([x[0] for x in self.events].count('coin_drop'), 1)

    def test_poison_and_fire_end_of_enemy_round_transition(self):
        for status in ('poison', 'fire'):
            with self.subTest(status=status):
                self.setUp()
                e = self.engine
                e.enemy.hp = 1
                e.enemy.apply_status(status, 2, 3)
                e.enemy_actions_remaining = 0
                e.state = 'enemy_resolving'
                turn = e.player.turn_count
                e.finish_enemy_turn()
                self.assertEqual(e.state, 'boss_transition')
                e.finish_boss_transition()
                self.assertEqual(e.state, 'player_turn')
                self.assertEqual(e.player.turn_count, turn+1)
                self.assertEqual(e.player.energy, e.player.energy_max)

    def test_bleed_killing_first_phase_cancels_remaining_attacks(self):
        e = self.engine
        e.enemy.hp = 1
        e.enemy.apply_status('bleed', 2, 5)
        e.enemy.set_intent('attack', 9, e.enemy.actions[0])
        hp = e.player.hp
        e.end_turn()
        e.enemy_turn()
        self.assertEqual(e.state, 'boss_transition')
        self.assertEqual(e.enemy_actions_remaining, 0)
        self.assertEqual(e.player.hp, hp)

    def test_lethal_player_ultimate_does_not_skip_second_phase(self):
        e = self.engine
        e.equip_ultimate('rugido_da_floresta')
        e.player.ultimate_charge = e.player.ultimate_threshold
        e.enemy.hp = 1
        self.assertTrue(e.activate_ultimate())
        self.assertEqual(e.state, 'boss_transition')
        e.finish_boss_transition()
        self.assertEqual(e.enemy.hp, e.enemy.max_hp)
        self.assertEqual(e.player.ultimate_charge, 0)

    def test_lethal_card_discards_and_consumes_energy_before_transition(self):
        from src.systems.card_catalog import CARD_BY_NAME
        e = self.engine
        card = CARD_BY_NAME['Soco Simples'].copy()
        e.deck_manager.hand[:] = [card]
        energy = e.player.energy
        e.enemy.hp = 1
        self.assertTrue(e.play_card(0))
        self.assertEqual(e.state, 'boss_transition')
        e.finish_boss_transition()
        self.assertEqual(e.player.energy, energy-card.cost)
        self.assertIn(card, e.discard_pile)
        self.assertFalse(e.hand)

    def test_resume_starts_both_phases_again_without_touching_save_format(self):
        e = self.engine
        e.resume_from_save({'progresso': {'andar': 2}},
                           SimpleNamespace(apply_to_game=lambda *_: None), level=2)
        self.assertEqual(e.enemy.phase, 1)
        self.assertEqual(e.enemy.hp, 76)

    def test_eight_action_specials_in_both_phases(self):
        for phase in (1, 2):
            boss = create_alvaro_tex(phase=phase)
            for counter in range(16):
                boss.action_counter = counter
                choose_next_action(boss)
                self.assertEqual(boss.current_action is boss.special_action, counter in (7,15))

    def test_smoke_heals_and_buffs_without_hurting_or_poisoning_player(self):
        e = self.engine
        boss = e.enemy
        smoke = next(a for a in boss.actions if a.visual_effect == 'healer2')
        self.assertEqual(smoke.action_type, 'buff')
        self.assertEqual(smoke.damage, 0)
        self.assertIsNone(smoke.status_effect)
        boss.hp = boss.max_hp-6
        boss.apply_status('bleed',2,5)
        player_hp = e.player.hp
        boss.set_intent('buff',smoke.value,smoke)
        e.end_turn()
        self.events.clear()
        e.enemy_turn()
        self.assertEqual(boss.hp,boss.max_hp)
        self.assertEqual(boss.attack_bonus,3)
        self.assertEqual(e.player.hp,player_hp)
        self.assertFalse(e.player.statuses)
        names = [x[0] for x in self.events]
        self.assertIn('enemy_action',names)
        self.assertNotIn('attack',names)
        self.assertNotIn('flash',names)
        self.assertFalse(boss._bled_this_turn)

    def test_smoke_refreshes_bonus_and_lasts_full_rounds_not_actions(self):
        e = self.engine
        boss = e.enemy
        smoke = next(a for a in boss.actions if a.visual_effect == 'healer2')
        smoke.execute(boss,e.player,e)
        smoke.execute(boss,e.player,e)
        self.assertEqual(boss.attack_bonus,3)
        boss.set_intent('buff',smoke.value,smoke)
        e.end_turn()
        e.enemy_turn()
        e.finish_enemy_turn()
        self.assertEqual(boss.statuses['aura']['turns'],2)
        boss.set_intent('attack',boss.actions[0].value,boss.actions[0])
        e.enemy_turn()
        e.finish_enemy_turn()
        self.assertEqual(boss.statuses['aura']['turns'],1)
        self.assertEqual(boss.attack_bonus,3)
        self.assertEqual(boss.hp,boss.max_hp)


class AlvaroTexVisualTests(TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1,1))
        cls.groups = {}
        root = Path(__file__).resolve().parents[1]/'assets/bosses/alvaro_tex'
        for phase, name in enumerate(NAMES,1):
            for group in ('idle','dano','atk1','atk2','atk3','atk4','transition'):
                cls.groups[name,group] = [pygame.image.load(str(p)).convert_alpha()
                    for p in sorted((root/f'phase{phase}').glob(f'{group}_*.png'))]
        cls.groups[NAMES[0],'healer2'] = cls.groups[NAMES[0],'atk3']
        cls.assets = SimpleNamespace(get_enemy_sprite_group=lambda n,g: cls.groups.get((n,g),[]))

    def test_all_attack_poses_used_and_no_quadrilateral_background(self):
        for name in NAMES:
            for group in ('atk1','atk2','atk3','atk4'):
                frames = self.groups[name,group]
                self.assertEqual(len(frames),8)
                self.assertEqual(len({pygame.image.tobytes(f,'RGBA') for f in frames}),8)
                view = EntityView(self.assets)
                view.trigger_attack('enemy',group,enemy_name=name)
                for i in range(8):
                    view.attack_timer = (i+.5)*ATTACK_MS[name][group]/8
                    self.assertIs(view.get_enemy_frame(SimpleNamespace(name=name)),frames[i])
                for f in frames:
                    self.assertEqual(f.get_at((0,0)).a,0)
                    self.assertLess(f.get_bounding_rect().width, f.get_width())

    def test_transition_waits_for_finishing_animation(self):
        from src.scenes.battle_scene import BattleScene
        window = SimpleNamespace(get_virtual_mouse_pos=lambda:(-1,-1))
        scene = BattleScene(None,window,self.assets)
        scene.engine.enemy = create_point_enemy(2)
        scene.engine.level = 2
        scene.entity_view.trigger_player_action('Rugido da Floresta')
        scene.engine.enemy.hp = 0
        scene.engine._on_enemy_defeated()
        scene.update(500)
        self.assertIsNone(scene.entity_view.phase_transition_timer)
        scene.update(2500)
        self.assertEqual(scene.entity_view.phase_transition_timer,0)
        scene.update(TRANSITION_MS-1)
        self.assertEqual(scene.engine.enemy.phase,1)
        scene.update(1)
        self.assertEqual(scene.engine.enemy.phase,2)
        self.assertIsNone(scene.entity_view.phase_transition_timer)

    def test_smoke_uses_eight_frames_at_home_without_projectile(self):
        view = EntityView(self.assets)
        view.trigger_enemy_action('healer2',enemy_name=NAMES[0])
        self.assertIsNone(view.attacker)
        self.assertIsNone(view.get_enemy_projectile_pose())
        self.assertEqual(view.enemy_action_duration,1800)
        for i in range(8):
            view.enemy_action_timer = (i+.5)*1800/8
            self.assertIs(view.get_enemy_frame(SimpleNamespace(name=NAMES[0])), self.groups[NAMES[0],'healer2'][i])
        canvas = pygame.Surface((1920,1080),pygame.SRCALPHA)
        view.enemy_action_timer = 900
        view.draw_enemy_projectile(canvas)
        self.assertGreater(canvas.get_bounding_rect().left,1200)
        self.assertFalse(view.is_enemy_resolving_done())
        view.update(1800)
        self.assertTrue(view.is_enemy_resolving_done())
