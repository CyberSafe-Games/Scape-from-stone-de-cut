"""Regras das 20 cartas e durações por turno completo, incluindo chefes."""
from pathlib import Path
import unittest
from unittest.mock import patch

from src.models.entity import Combatant
from src.models.action import Action
from src.models.enemy import Enemy
from src.systems.combat_engine import CombatEngine
from src.systems.card_catalog import CARD_POOL, CARD_BY_NAME
from src.systems.card_definitions import CARD_SPECS, LEGACY_CARD_NAMES
from src.systems.deck_loadout import normalize_collection_and_slots
from src.systems.shop_system import CARD_OFFERS
from src.ui.entity_view import EntityView
from src.ui.card_fx import projectile_pose


class TacticalCardTests(unittest.TestCase):
    def engine(self):
        engine = CombatEngine()
        engine.enemy = Enemy('Alvo', 500)
        engine.enemy.set_intent('attack', 0, Action('Ataque', damage=0))
        engine.player.energy_max = 8
        engine.player.energy = 8
        return engine

    def play(self, engine, name):
        engine.deck_manager.hand = [CARD_BY_NAME[name].copy()]
        engine.player.energy = 8
        self.assertTrue(engine.play_card(0))

    def full_round(self, engine):
        engine.end_turn()
        while engine.state in ('enemy_turn', 'enemy_resolving'):
            if engine.state == 'enemy_turn': engine.enemy_turn()
            else: engine.finish_enemy_turn()

    def test_only_new_catalog_in_rewards_shop_and_starter(self):
        self.assertEqual(len(CARD_POOL), 20)
        self.assertEqual(len(CARD_OFFERS), 20)
        engine = self.engine()
        self.assertEqual({c.name for c in engine.deck}, {'Soco Simples', 'Esfera Protetora'})
        engine.generate_rewards()
        self.assertTrue(all(c.name in CARD_BY_NAME for c in engine.reward_cards))
        self.assertFalse(set(LEGACY_CARD_NAMES) & set(CARD_BY_NAME))

    def test_every_card_consumes_its_cost_and_has_a_valid_effect(self):
        for card in CARD_POOL:
            with self.subTest(card=card.name):
                engine = self.engine()
                engine.player.hp = 20
                self.play(engine, card.name)
                self.assertEqual(engine.energy, 8 - card.cost)
                self.assertEqual(len(engine.discard_pile), 1)
                self.assertLessEqual(engine.player.hp, engine.player.max_hp)

    def test_attacks_match_printed_damage_and_darts_total_ten(self):
        for name, damage in (('Soco Simples', 6), ('Investida', 10), ('Disparo de Arco', 20),
                             ('Zarabatana Venenosa', 10), ('Machados Gêmeos', 40),
                             ('Lança Perfurante', 30), ('Adaga Sangrenta', 5), ('Bola de Fogo', 10)):
            engine = self.engine()
            self.play(engine, name)
            self.assertEqual(engine.enemy.hp, 500 - damage, name)

    def test_fire_stacks_and_burns_shield_while_poison_bypasses_it(self):
        target = Combatant('Alvo', 100)
        target.add_block(30)
        for _ in range(5): target.apply_status('fire', 3, 1)
        self.assertEqual(target.statuses['fire']['potency'], 3)
        target.apply_status('poison', 4, 5)
        target.end_turn_statuses()
        self.assertEqual(target.block, 21)
        self.assertEqual(target.hp, 95)
        target.apply_status('poison', 3, 5)
        self.assertEqual(target.statuses['poison'], {'turns': 3, 'potency': 5})

    def test_poison_ticks_once_after_all_boss_actions_and_kill_rewards_once(self):
        events = []
        engine = self.engine()
        engine.on_event = lambda name, **kw: events.append(name)
        engine.enemy.actions_per_turn = 2
        engine.enemy.hp = 7
        engine.enemy.apply_status('poison', 2, 5)
        engine.end_turn()
        engine.enemy_turn()
        engine.finish_enemy_turn()
        self.assertEqual(engine.enemy.hp, 7)
        engine.enemy_turn()
        engine.finish_enemy_turn()
        self.assertEqual(engine.enemy.hp, 2)
        self.assertEqual(engine.enemy.statuses['poison']['turns'], 1)
        self.full_round(engine)
        self.assertEqual(engine.state, 'victory')
        self.assertEqual(events.count('coin_drop'), 1)
        engine.finish_enemy_turn()
        self.assertEqual(events.count('coin_drop'), 1)

    def test_bleeding_first_attack_only_each_owner_turn(self):
        engine = self.engine()
        engine.enemy.actions_per_turn = 2
        engine.enemy.apply_status('bleed', 2, 4)
        self.full_round(engine)
        self.assertEqual(engine.enemy.hp, 496)
        self.full_round(engine)
        self.assertEqual(engine.enemy.hp, 492)
        self.assertNotIn('bleed', engine.enemy.statuses)

    def test_shield_survives_two_full_rounds_not_two_boss_actions(self):
        engine = self.engine()
        engine.enemy.actions_per_turn = 2
        engine.player.add_block(30)
        self.full_round(engine)
        self.assertEqual(engine.player.block, 30)
        self.assertEqual(engine.player.block_turns, 1)
        self.full_round(engine)
        self.assertEqual(engine.player.block, 0)

    def test_shield_layers_expire_independently_and_oldest_absorbs_first(self):
        target = Combatant('Alvo', 100)
        target.add_block(10)
        target.begin_turn()
        target.add_block(30)
        target.take_damage(7)
        target.begin_turn()
        self.assertEqual(target.block, 30)
        target.begin_turn()
        self.assertEqual(target.block, 0)

    def test_enemy_shield_protects_two_player_turns(self):
        engine = self.engine()
        engine.enemy.add_block(20)
        # O escudo foi ganho durante a vez inimiga, depois de begin_turn.
        engine.state = 'enemy_resolving'
        engine.finish_enemy_turn()
        self.play(engine, 'Soco Simples')
        self.assertEqual(engine.enemy.block, 14)
        self.full_round(engine)
        self.play(engine, 'Soco Simples')
        self.assertEqual(engine.enemy.block, 8)
        self.full_round(engine)
        self.assertEqual(engine.enemy.block, 0)

    def test_totem_blocks_whole_multi_hit_attack_but_not_poison(self):
        target = Combatant('Alvo', 100)
        target.apply_status('totem', 0)
        target.apply_status('poison', 2, 5)
        target.end_turn_statuses()
        self.assertEqual(target.hp, 95)
        self.assertIn('totem', target.statuses)
        self.assertEqual(target.receive_attack(30, hits=3), 0)
        self.assertNotIn('totem', target.statuses)
        self.assertEqual(target.receive_attack(10), 10)

    def test_totem_prevents_on_hit_negatives_from_blocked_attacks(self):
        for name in ('Bola de Fogo', 'Adaga Sangrenta', 'Zarabatana Venenosa'):
            engine = self.engine()
            engine.enemy.apply_status('totem', 0)
            self.play(engine, name)
            self.assertEqual(engine.enemy.hp, 500)
            self.assertFalse(engine.enemy.statuses)

    def test_cleanse_preserves_positive_effects_and_dispel_removes_everything(self):
        engine = self.engine()
        engine.player.add_block(10)
        engine.player.apply_status('aura', 3, 8)
        for name in Combatant.NEGATIVE_STATUSES: engine.player.apply_status(name, 2, 1)
        engine.player.weak_turns = 2
        self.play(engine, 'Poção Purificadora')
        self.assertEqual(set(engine.player.statuses), {'aura'})
        self.assertEqual(engine.player.block, 10)
        self.assertEqual(engine.player.weak_turns, 0)
        engine.enemy.add_block(10)
        engine.enemy.strength = 4
        engine.enemy.apply_status('poison', 2, 5)
        engine.enemy.apply_status('totem', 0)
        self.play(engine, 'Amuleto Dissipador')
        self.assertFalse(engine.enemy.statuses)
        self.assertEqual(engine.enemy.block, 0)
        self.assertEqual(engine.enemy.strength, 0)

    def test_aura_fragility_and_delayed_energy(self):
        engine = self.engine()
        self.play(engine, 'Aura Rubra')
        self.play(engine, 'Poção Fragilizante')
        self.play(engine, 'Soco Simples')
        self.assertEqual(engine.enemy.hp, 482)  # ceil((6+8)*1.25)
        for _ in range(3): self.full_round(engine)
        self.assertEqual(engine.player.attack_bonus, 0)
        self.assertNotIn('vulnerable', engine.enemy.statuses)
        engine.player.energy_max = 3
        engine.player.energy = 3
        engine.deck_manager.hand = [CARD_BY_NAME['Surto de Energia'].copy()]
        self.assertTrue(engine.play_card(0))
        self.assertEqual(engine.energy, 1)
        self.full_round(engine)
        self.assertEqual(engine.energy_max, 4)
        self.assertEqual(engine.energy, 6)
        self.full_round(engine)
        self.assertEqual(engine.energy, 5)

    def test_poison_death_on_player_end_prevents_enemy_acting(self):
        engine = self.engine()
        engine.player.hp = 3
        engine.player.apply_status('poison', 2, 5)
        engine.end_turn()
        self.assertEqual(engine.state, 'game_over')
        engine.enemy_turn()
        self.assertEqual(engine.state, 'game_over')

    def test_new_fight_clears_temporary_effects_but_preserves_ultimate(self):
        engine = self.engine()
        engine.player.ultimate_charge = 13
        engine.player.apply_status('fire', 3)
        engine.player.next_turn_energy = 2
        engine.player.add_block(10)
        engine.start_combat()
        self.assertEqual(engine.player.ultimate_charge, 13)
        self.assertFalse(engine.player.statuses)
        self.assertEqual(engine.player.next_turn_energy, 0)
        self.assertEqual(engine.player.block, 0)

    def test_legacy_collection_and_slots_migrate_without_changing_ultimates(self):
        progress = {'cartas_colecao': list(LEGACY_CARD_NAMES), 'deck_slots': list(LEGACY_CARD_NAMES) + [None],
                    'cartas': ['Golpe', 'Defesa'], 'ultimate_equipada': 'rugido_da_floresta'}
        normalize_collection_and_slots(progress)
        self.assertEqual(progress['cartas_colecao'], list(LEGACY_CARD_NAMES.values()))
        self.assertEqual(progress['deck_slots'][0], 'Soco Simples')
        self.assertEqual(progress['ultimate_equipada'], 'rugido_da_floresta')

    def test_all_art_and_animation_frames_exist_with_alpha(self):
        from PIL import Image
        root = Path(__file__).resolve().parents[1] / 'assets'
        for spec in CARD_SPECS:
            self.assertTrue((root / 'cards' / (spec[0] + '.png')).is_file())
            for i in range(1, 5):
                with Image.open(root / 'card_effects' / f'{spec[0]}_{i}.png') as frame:
                    self.assertEqual(frame.size, (260, 200))
                    self.assertEqual(frame.mode, 'RGBA')
                    self.assertEqual(frame.getpixel((0, 0))[3], 0)

    def test_ranged_projectiles_travel_right_and_only_flash_on_arrival(self):
        for spec in CARD_SPECS:
            if spec[6] != 'ranged': continue
            with self.subTest(card=spec[1]):
                view = EntityView(None)
                view.trigger_attack('player', spec[1])
                view.trigger_flash('enemy')
                self.assertIsNone(projectile_pose(view))
                view.update(view.player_attack_duration * 0.7)
                first = projectile_pose(view)
                self.assertEqual(view.get_attack_pose('player', 260, 942)[0], 260)
                view.update(view.player_attack_duration * 0.1)
                self.assertGreater(projectile_pose(view)[0], first[0])
                self.assertEqual(view.enemy_flash, 0)
                view.update(view.player_attack_duration * 0.11)
                self.assertIsNone(projectile_pose(view))
                self.assertGreater(view.enemy_flash, 0)
