"""Regressões do voo e da sincronização dos ataques do Goblin Nerd."""
import unittest

from src.config.layout import ENEMY_X, PLAYER_X, APPROACH_GAP, FLASH_DURATION
from src.ui.entity_view import EntityView


class GoblinRangedAttackTests(unittest.TestCase):
    def test_ranged_attacks_stay_home_and_fly_towards_player(self):
        for action in ("atk1", "atk2"):
            with self.subTest(action=action):
                view = EntityView(None)
                view.trigger_attack("enemy", action, "Goblin Nerd")
                duration, launch, impact = view.enemy_ranged_attack
                self.assertIsNone(view.get_enemy_projectile_pose())
                positions = []
                for fraction in (launch, (launch + impact) / 2, impact - 0.001):
                    view.attack_timer = duration * fraction
                    self.assertEqual(view.get_attack_pose("enemy", ENEMY_X, PLAYER_X + APPROACH_GAP)[0], ENEMY_X)
                    positions.append(view.get_enemy_projectile_pose())
                self.assertGreater(positions[0][0], positions[1][0])
                self.assertGreater(positions[1][0], positions[2][0])
                self.assertLess(abs(positions[2][0] - PLAYER_X), 30)
                if action == "atk1":
                    self.assertLess(positions[1][1], positions[0][1] - 50)
                view.attack_timer = duration * impact
                self.assertIsNone(view.get_enemy_projectile_pose())

    def test_flash_waits_for_arrival_and_next_action_waits_for_recovery(self):
        for action in ("atk1", "atk2"):
            with self.subTest(action=action):
                view = EntityView(None)
                view.trigger_attack("enemy", action, "Goblin Nerd")
                view.trigger_flash("player")
                duration, _, impact = view.enemy_ranged_attack
                arrival = duration * impact
                view.update(arrival - 1)
                self.assertEqual(view.player_flash, 0)
                view.update(2)
                self.assertAlmostEqual(view.player_flash, FLASH_DURATION - 1)
                self.assertFalse(view.is_enemy_resolving_done())
                view.update(duration - arrival)
                self.assertTrue(view.is_enemy_resolving_done())
                self.assertIsNone(view.get_enemy_projectile_pose())

    def test_other_enemies_and_goblin_melee_still_approach(self):
        for name, action in (("Corpo Seco", "atk1"), ("Slime", "atk"), ("Goblin Nerd", "atk3")):
            with self.subTest(name=name, action=action):
                view = EntityView(None)
                view.trigger_attack("enemy", action, name)
                view.update(view.enemy_attack_duration * 0.5)
                self.assertIsNone(view.enemy_ranged_attack)
                self.assertEqual(view.get_attack_pose("enemy", ENEMY_X, PLAYER_X + APPROACH_GAP)[0], PLAYER_X + APPROACH_GAP)

    def test_next_attack_clears_ranged_state(self):
        view = EntityView(None)
        view.trigger_attack("enemy", "atk2", "Goblin Nerd")
        view.trigger_flash("player")
        view.trigger_attack("enemy", "atk3", "Goblin Nerd")
        self.assertIsNone(view.enemy_ranged_attack)
        self.assertIsNone(view.pending_player_hit_at)
