"""Regressões: mão persistente e duas ações do Cemitério."""
import unittest
from collections import Counter

from src.models.deck import DeckManager
from src.systems.card_catalog import create_starting_deck
from src.systems.combat_engine import CombatEngine


class PersistentHandTests(unittest.TestCase):
    @staticmethod
    def next_player_turn(game):
        game.end_turn()
        game.player.hp = 999
        game.player.max_hp = 999
        while game.state in ('enemy_turn', 'enemy_resolving'):
            if game.state == 'enemy_turn':
                game.enemy_turn()
            else:
                game.finish_enemy_turn()
        assert game.state == 'player_turn'

    def test_unused_cards_remain_in_same_order_and_only_missing_cards_are_drawn(self):
        engine = CombatEngine()
        first_card = engine.hand[0]
        remaining = list(engine.hand)
        self.next_player_turn(engine)
        self.assertEqual(len(engine.hand), 4)
        self.assertTrue(all(a is b for a, b in zip(engine.hand[:3], remaining)))
        self.assertIs(engine.hand[0], first_card)
        self.assertEqual(len(engine.discard_pile), 0)

    def test_only_replenishes_up_to_current_turn_target(self):
        game = CombatEngine()
        self.assertTrue(game.use_cemetery(0))
        self.assertEqual(len(game.hand), 2)
        self.next_player_turn(game)
        self.assertEqual(len(game.hand), 4)
        self.next_player_turn(game)
        self.assertEqual(len(game.hand), 5)
        self.next_player_turn(game)
        self.assertEqual(len(game.hand), 5)

    def test_extra_cards_are_not_removed_when_hand_exceeds_target(self):
        game = CombatEngine()
        game.deck_manager.draw_cards(3)
        self.assertEqual(len(game.hand), 6)
        previous = list(game.hand)
        self.next_player_turn(game)
        self.assertEqual(len(game.hand), 6)
        self.assertTrue(all(a is b for a, b in zip(game.hand, previous)))

    def test_cemetery_discard_does_not_automatically_replace(self):
        game = CombatEngine()
        game.use_cemetery(0)
        self.assertEqual(len(game.hand), 2)
        self.assertEqual(len(game.discard_pile), 1)

    def test_combat_restart_still_creates_fresh_hand(self):
        game = CombatEngine()
        game.use_cemetery(0)
        game.start_combat()
        self.assertEqual(game.player.turn_count, 1)
        self.assertEqual(len(game.hand), 3)
        self.assertFalse(game.cemetery_swap_used)


class CemeteryTradeTests(unittest.TestCase):
    def test_discard_costs_one_per_card_until_energy_exhausted(self):
        game = CombatEngine()
        self.assertEqual(game.cemetery_cost, 1)
        self.assertTrue(game.use_cemetery(0))
        self.assertEqual(game.energy, 1)
        self.assertTrue(game.use_cemetery(0))
        self.assertEqual(game.energy, 0)
        before = len(game.hand)
        self.assertFalse(game.use_cemetery(0))
        self.assertEqual(len(game.hand), before)
        self.assertFalse(game.can_use_cemetery())
        self.assertEqual(len(game.discard_pile), 2)

    def test_swap_one_per_turn_preserves_hand_size_and_energy(self):
        game = CombatEngine()
        before_hand = len(game.hand)
        before_energy = game.energy
        counts = Counter(card.name for card in game.hand + game.draw_pile + game.discard_pile)
        self.assertTrue(game.swap_cemetery(1))
        self.assertEqual(len(game.hand), before_hand)
        self.assertEqual(game.energy, before_energy)
        self.assertEqual(len(game.discard_pile), 1)
        self.assertTrue(game.cemetery_swap_used)
        self.assertFalse(game.swap_cemetery(0))
        after_counts = Counter(card.name for card in game.hand + game.draw_pile + game.discard_pile)
        self.assertEqual(counts, after_counts)

    def test_swap_does_not_consume_charge_or_energy(self):
        game = CombatEngine()
        game.player.energy = 0
        game.player.ultimate_charge = 4
        self.assertTrue(game.swap_cemetery(0))
        self.assertEqual(game.energy, 0)
        self.assertEqual(game.ultimate_charge, 4)

    def test_swap_resets_at_start_of_next_player_turn(self):
        game = CombatEngine()
        game.swap_cemetery(0)
        self.next_turn(game)
        self.assertFalse(game.cemetery_swap_used)
        self.assertTrue(game.swap_cemetery(0))

    @staticmethod
    def next_turn(game):
        game.player.hp = 999
        game.player.max_hp = 999
        game.end_turn()
        while game.state in ('enemy_turn','enemy_resolving'):
            if game.state == 'enemy_turn': game.enemy_turn()
            else: game.finish_enemy_turn()

    def test_swap_not_reset_between_boss_two_actions(self):
        game = CombatEngine()
        game.resume_from_save({"progresso": {"andar": 5}},
                              _FakeSaveManager(), level=5, encounter_kind='point')
        game.player.hp = 999
        game.player.max_hp = 999
        game.swap_cemetery(0)
        game.end_turn()
        self.assertEqual(game.enemy_actions_remaining, 2)
        game.enemy_turn()
        game.finish_enemy_turn()
        self.assertEqual(game.state, 'enemy_turn')
        self.assertTrue(game.cemetery_swap_used)
        game.enemy_turn()
        game.finish_enemy_turn()
        self.assertEqual(game.state, 'player_turn')
        self.assertFalse(game.cemetery_swap_used)

    def test_swap_requires_valid_index_and_replacement(self):
        game = CombatEngine()
        self.assertFalse(game.swap_cemetery(-1))
        self.assertFalse(game.swap_cemetery(99))
        self.assertFalse(game.cemetery_swap_used)
        solo = DeckManager(create_starting_deck()[:1])
        solo.start_combat()
        solo.draw_cards(1)
        self.assertFalse(solo.has_replacement_for(0))
        self.assertIsNone(solo.swap_card(0))
        self.assertEqual(len(solo.hand), 1)

    def test_swap_reshuffles_old_discard_without_redrawing_discarded_selection(self):
        deck = DeckManager(create_starting_deck())
        deck.start_combat()
        deck.draw_cards(4)
        old = deck.hand[0]
        old_discard = deck.discard_card(1)
        deck.draw_pile.clear()
        replaced = deck.swap_card(0)
        self.assertIsNotNone(replaced)
        self.assertIs(replaced[0], old)
        self.assertIs(replaced[1], old_discard)
        self.assertIs(deck.discard_pile[-1], old)

    def test_swap_disabled_when_not_player_turn(self):
        game = CombatEngine()
        game.end_turn()
        self.assertFalse(game.use_cemetery(0))
        self.assertFalse(game.swap_cemetery(0))


class _FakeSaveManager:
    def apply_to_game(self, data, player, deck):
        pass


if __name__ == '__main__':
    unittest.main()
