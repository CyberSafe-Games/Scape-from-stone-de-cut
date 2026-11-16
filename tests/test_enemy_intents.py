"""A sequência anunciada é estável, completa e corresponde às ações executadas."""
import os
import unittest
from unittest.mock import patch
from types import SimpleNamespace
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
from src.systems.enemy_factory import create_alvaro_tex, create_point_enemy, create_road_enemy, choose_next_action
from src.systems.combat_engine import CombatEngine
from src.systems.enemy_intents import preview_intents
from src.core.asset_manager import AssetManager
from src.ui.enemy_intent_view import EnemyIntentView
from src.models.action import Action, action_status_effects
from src.models.enemy import Enemy


class IntentPlanningTests(unittest.TestCase):
    def engine(self, level=7):
        engine = CombatEngine()
        engine.enemy = create_point_enemy(level)
        engine.player.hp = engine.player.max_hp = 2000
        choose_next_action(engine.enemy)
        return engine

    def test_every_boss_announces_two_actions_and_common_enemy_one(self):
        for level in range(1, 8):
            e = self.engine(level)
            self.assertEqual(len(preview_intents(e)), 2, level)
            self.assertLessEqual(sum(a.energy_cost for a in e.enemy.action_plan), e.enemy.energy)
            e.enemy = create_road_enemy(level)
            choose_next_action(e.enemy)
            self.assertEqual(len(preview_intents(e)), 1, level)

    def test_goblin_shock_stacks_for_one_player_turn(self):
        e = self.engine(3)
        shot = e.enemy.actions[1]
        ultimate = e.enemy.special_action
        e.enemy.action_plan = [shot, ultimate]
        e.enemy.set_intent('attack', shot.damage, shot)
        self.assertIn('Choque ×1', preview_intents(e)[0].description)
        self.assertIn('Choque ×2', preview_intents(e)[1].description)
        e.end_turn()
        e.enemy_turn()
        self.assertEqual(e.player.statuses['shock'], {'turns': 1, 'potency': 1})
        e.finish_enemy_turn()
        e.enemy_turn()
        self.assertEqual(e.player.statuses['shock']['potency'], 3)
        e.finish_enemy_turn()
        self.assertEqual(e.player.energy, max(0, e.player.energy_max - 3))
        self.assertNotIn('shock', e.player.statuses)
        e._begin_player_turn()
        self.assertEqual(e.player.energy, e.player.energy_max)
        self.assertFalse(e.enemy.apply_status('shock', 1, 1))
        self.assertEqual(e.enemy.add_stacks('shock', 1), 0)

    def test_corpse_guard_and_executioner_attack_effects_match_intents(self):
        e = self.engine(5)
        guard = e.enemy.actions[2]
        e.enemy.hp -= 25
        e.enemy.set_intent(guard.action_type, guard.value, guard)
        self.assertIn('20 de vida', preview_intents(e)[0].description)
        e.end_turn()
        e.enemy_turn()
        self.assertEqual(e.enemy.block, 10)
        self.assertEqual(e.enemy.hp, e.enemy.max_hp - 5)
        self.assertEqual(e.enemy.actions[0].status_effect, ('bleed', 2, 2))
        self.assertEqual(e.enemy.actions[1].status_effect, ('bleed', 2, 2))

        e = self.engine(6)
        strike = e.enemy.actions[0]
        followup = e.enemy.special_action
        e.enemy.action_plan = [strike, followup]
        e.enemy.set_intent('attack', strike.damage, strike)
        predicted = preview_intents(e)
        self.assertEqual(predicted[0].value, strike.damage)
        self.assertEqual(predicted[1].value, followup.damage + 4)
        e.end_turn()
        e.enemy_turn()
        self.assertEqual(e.enemy.attack_bonus, 4)
        e.finish_enemy_turn()
        e.enemy_turn()
        self.assertEqual(e.enemy.statuses['aura'], {'turns': 2, 'potency': 4})

    def test_planned_second_action_executes_without_a_new_random_draw(self):
        for level in range(1, 8):
            e = self.engine(level)
            plan = list(e.enemy.action_plan)
            e.end_turn()
            e.enemy_turn()
            with patch('src.systems.enemy_factory.random.choices', side_effect=AssertionError('Segunda ação sorteada novamente')):
                e.finish_enemy_turn()
            self.assertIs(e.enemy.current_action, plan[1])
            self.assertEqual(e.enemy.action_plan_index, 1)
            self.assertEqual([i.state for i in preview_intents(e)], ['done', 'active'])
            e.enemy_turn()
            e.finish_enemy_turn()
            self.assertEqual(e.state, 'player_turn')
            self.assertEqual(len(e.enemy.action_plan), 2)
            self.assertEqual(e.enemy.action_plan_index, 0)

    def test_ultimate_is_visible_as_second_action_before_the_turn(self):
        for level in range(1, 8):
            e = self.engine(level)
            e.enemy.action_counter = 6
            choose_next_action(e.enemy)
            intents = preview_intents(e)
            self.assertFalse(intents[0].special)
            self.assertTrue(intents[1].special)
            self.assertIs(intents[1].action, e.enemy.special_action)
            e.end_turn(); e.enemy_turn(); e.finish_enemy_turn()
            self.assertIs(e.enemy.current_action, e.enemy.special_action)

    def test_special_reserves_energy_in_advance(self):
        enemy = Enemy('Teste', 100, energy=2, max_energy=2, actions=[Action('Caro', damage=8, energy_cost=2)])
        enemy.actions_per_turn = 2
        enemy.action_counter, enemy.special_interval = 6, 8
        enemy.special_action = Action('Especial', damage=20, energy_cost=1)
        choose_next_action(enemy)
        self.assertEqual(enemy.action_plan[0].name, 'Aguardar')
        self.assertIs(enemy.action_plan[1], enemy.special_action)

    def test_generic_enemy_executes_the_new_announced_action_instead_of_a_stale_one(self):
        e = self.engine()
        e.enemy = Enemy('Genérico', 100)
        e.enemy.set_intent('attack', 0, Action('Antiga', damage=0))
        with patch('src.systems.enemy_factory.random.random', return_value=.1), patch('src.systems.enemy_factory.random.randint', return_value=10):
            choose_next_action(e.enemy)
        forecast = preview_intents(e)[0].value
        self.assertEqual(forecast, 10)
        hp = e.player.hp
        e.end_turn(); e.enemy_turn()
        self.assertEqual(hp-e.player.hp, forecast)

    def test_vulnerability_expiring_at_end_of_player_turn_is_not_counted(self):
        e = self.engine()
        attack = e.enemy.actions[0]
        e.enemy.set_intent('attack', attack.damage, attack)
        e.player.apply_status('vulnerable', 1)
        forecast = preview_intents(e)[0].value
        self.assertEqual(forecast, attack.damage)
        hp = e.player.hp
        e.end_turn(); e.enemy_turn()
        self.assertEqual(hp-e.player.hp, forecast)

    def test_preview_includes_strength_weakness_vulnerability_and_prior_buff(self):
        e = self.engine(6)  # Carrasco mantém buff; Zanzara agora é necromante.
        buff = next(a for a in e.enemy.actions if a.action_type == 'buff')
        attack = e.enemy.actions[0]
        e.enemy.action_plan = [buff, attack]
        e.enemy.set_intent(buff.action_type, buff.value, buff)
        e.enemy.strength = 2
        e.enemy.weak_turns = 1
        e.player.apply_status('vulnerable', 2)
        intents = preview_intents(e)
        expected = ( (int(round(attack.damage*.75))+2+4)*125+99)//100
        self.assertEqual(intents[1].value, expected)
        self.assertIn('Não causa dano', intents[0].description)
        self.assertEqual(e.enemy.hp, e.enemy.max_hp)
        self.assertEqual(e.enemy.statuses, {})
        self.assertEqual(e.enemy.energy, 4)
        hp = e.player.hp
        e.end_turn(); e.enemy_turn(); e.finish_enemy_turn(); e.enemy_turn()
        self.assertEqual(hp-e.player.hp, intents[1].value)


class IntentInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init(); pygame.display.set_mode((1, 1))
        cls.assets = AssetManager()

    def test_boss_cards_load_with_a_separate_ultimate_illustration(self):
        bosses = [create_point_enemy(level) for level in (2, 3, 4, 5, 6, 7)]
        bosses.append(create_alvaro_tex(phase=2))
        images = []
        for boss in bosses:
            for action in (*boss.actions, boss.special_action):
                image = self.assets.get_intent_art(
                    boss.name, action.visual_effect, special=action is boss.special_action,
                )
                if action.name == 'Guarda Ferrenha':
                    self.assertIsNone(image)
                else:
                    self.assertIsInstance(image, pygame.Surface, action.name)
                    images.append(pygame.image.tobytes(image, 'RGB'))
        self.assertEqual(len(set(images)), 29)
        self.assertIsNone(self.assets.get_intent_art(bosses[0].name, None))

    def test_zanzara_actions_match_the_four_printed_cards(self):
        boss = create_point_enemy(7)
        scythe_status = (('bleed', 2, 2), ('poison', 2, 1))
        self.assertEqual(
            [(action.damage, action_status_effects(action)) for action in (*boss.actions, boss.special_action)],
            [(20, scythe_status), (24, scythe_status), (20, (('vulnerable', 2, 25),)),
             (45, (('poison', 2, 2),))],
        )

    def test_tall_intent_art_is_centered_and_counters_do_not_cover_it(self):
        engine = CombatEngine()
        engine.enemy = create_point_enemy(7)
        choose_next_action(engine.enemy)
        view = EnemyIntentView(self.assets)
        surface = pygame.Surface((1920, 1080))
        illustration = pygame.Surface((50, 100))
        color = (250, 1, 237)
        illustration.fill(color)
        with patch.object(self.assets, 'get_intent_art', return_value=illustration):
            view.draw(surface, engine, (-1, -1))
        for slot, _ in view.entries:
            area = pygame.Rect(slot.x+5, slot.y+5, slot.width-10, 78)
            fitted = pygame.Rect(0, 0, 39, 78)
            fitted.center = area.center
            rendered = surface.subsurface(fitted)
            expected = pygame.transform.smoothscale(illustration, fitted.size)
            self.assertEqual(pygame.image.tobytes(rendered, 'RGB'), pygame.image.tobytes(expected, 'RGB'))

    def test_every_icon_has_hover_description_inside_the_window_without_randomness(self):
        for level in range(1, 8):
            e = CombatEngine()
            e.enemy = create_point_enemy(level)
            e.enemy.action_counter = 6
            choose_next_action(e.enemy)
            view = EnemyIntentView(self.assets)
            surface = pygame.Surface((1920, 1080))
            plan = list(e.enemy.action_plan)
            with patch('src.systems.enemy_factory.random.choices', side_effect=AssertionError('Hover alterou a intenção')):
                view.draw(surface, e, (-1, -1))
                self.assertEqual(len(view.entries), 2)
                for rect, intent in view.entries:
                    self.assertTrue(surface.get_rect().contains(rect))
                    self.assertGreater(view.icon(intent.family).get_bounding_rect().width, 15)
                    view.draw_tooltip(surface, rect.center)
                    self.assertIsNotNone(view.tooltip_rect)
                    self.assertTrue(surface.get_rect().contains(view.tooltip_rect))
                    self.assertTrue(intent.description)
                view.draw_tooltip(surface, (-1, -1))
                self.assertIsNone(view.tooltip_rect)
            self.assertEqual(e.enemy.action_plan, plan)

    def test_boss_phase_switch_replaces_both_icons(self):
        from src.systems.enemy_factory import create_alvaro_tex
        e = CombatEngine()
        e.enemy = create_alvaro_tex()
        choose_next_action(e.enemy)
        old = list(e.enemy.action_plan)
        e.enemy.hp = 0
        e._on_enemy_defeated()
        e.finish_boss_transition()
        self.assertEqual(len(preview_intents(e)), 2)
        self.assertTrue(all(action not in old for action in e.enemy.action_plan))
