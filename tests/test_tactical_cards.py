"""Regras das 20 cartas e durações por turno completo, incluindo chefes."""
from pathlib import Path
import unittest
from unittest.mock import patch

from src.models.entity import Combatant
from src.models.action import Action
from src.models.enemy import Enemy
from src.systems.combat_engine import CombatEngine
from src.systems.card_catalog import AVAILABLE_CARD_NAMES, CARD_POOL, CARD_BY_NAME
from src.systems.card_definitions import ADDITIONAL_CARD_SPECS, CARD_SPECS, LEGACY_CARD_NAMES
from src.systems.deck_loadout import normalize_collection_and_slots
from src.systems.shop_system import CARD_OFFERS
from src.ui.entity_view import EntityView
from src.ui.card_fx import projectile_pose


class TacticalCardTests(unittest.TestCase):
    def engine(self):
        engine = CombatEngine()
        harmless = Action('Ataque', damage=0)
        engine.enemy = Enemy('Alvo', 500, actions=[harmless])
        engine.enemy.set_intent('attack', 0, harmless)
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
        expected_cards = len(CARD_SPECS) + len(ADDITIONAL_CARD_SPECS)
        self.assertEqual(len(CARD_POOL), expected_cards)
        self.assertEqual(set(CARD_OFFERS), {spec[1] for spec in CARD_SPECS})
        engine = self.engine()
        self.assertEqual({c.name for c in engine.deck}, {'Soco Simples', 'Esfera Protetora'})
        engine.generate_rewards()
        self.assertTrue(all(c.name in AVAILABLE_CARD_NAMES for c in engine.reward_cards))
        self.assertFalse(set(LEGACY_CARD_NAMES) & set(CARD_BY_NAME))

    def test_every_card_consumes_its_cost_and_has_a_valid_effect(self):
        for card in CARD_POOL:
            with self.subTest(card=card.name):
                engine = self.engine()
                engine.player.hp = 20
                self.play(engine, card.name)
                expected_energy = 8 - card.cost
                if card.name == 'Sem Dor, Sem Ganho':
                    expected_energy += 1
                elif card.name == 'Pacto Doloroso':
                    expected_energy += 2
                self.assertEqual(engine.energy, min(8, expected_energy))
                self.assertEqual(len(engine.discard_pile), 1)
                self.assertLessEqual(engine.player.hp, engine.player.max_hp)

    def test_attacks_match_printed_damage_and_darts_total_ten(self):
        for name, damage in (('Soco Simples', 6), ('Investida', 18), ('Disparo de Arco', 20),
                             ('Zarabatana Venenosa', 10), ('Machados Gêmeos', 40),
                             ('Lança Perfurante', 30), ('Adaga Sangrenta', 8), ('Bola de Fogo', 12)):
            engine = self.engine()
            self.play(engine, name)
            self.assertEqual(engine.enemy.hp, 500 - damage, name)

    def test_fire_stacks_and_burns_shield_while_poison_bypasses_it(self):
        target = Combatant('Alvo', 100)
        target.add_block(30)
        for _ in range(5): target.apply_status('fire', 3, 1)
        self.assertEqual(target.statuses['fire']['potency'], 3)
        target.add_stacks('poison', 1)
        target.end_turn_statuses()
        self.assertEqual(target.block, 21)
        self.assertEqual(target.hp, 95)
        target.add_stacks('poison', 2)
        target.add_stacks('poison', 2)
        self.assertEqual((target.poison_stacks, target.poison_turns), (5, 2))
        self.assertIn(('poison', 25), target.end_turn_statuses())
        self.assertEqual(target.add_stacks('poison', 1), 0)
        self.assertEqual(target.poison_turns, 2)
        self.assertIn(('poison', 25), target.end_turn_statuses())
        self.assertIn(('poison', 25), target.end_turn_statuses())
        self.assertEqual((target.poison_stacks, target.poison_turns), (0, 0))

    def test_fire_and_burn_share_one_audio_event_per_tick(self):
        for statuses in (("fire",), ("burn",), ("fire", "burn")):
            with self.subTest(statuses=statuses):
                events = []
                engine = CombatEngine(lambda event, **details: events.append((event, details)))
                engine.player.add_block(10)
                for status in statuses:
                    engine.player.apply_status(status, 2, 1)
                engine.end_turn()
                cues = [data for event, data in events if event == "status_trigger"]
                self.assertEqual(cues, [{"status": "burn", "target": "player"}])

    def test_poison_ticks_once_after_all_boss_actions_and_kill_rewards_once(self):
        events = []
        engine = self.engine()
        engine.on_event = lambda name, **kw: events.append(name)
        engine.enemy.actions_per_turn = 2
        engine.enemy.hp = 7
        engine.enemy.add_stacks('poison', 1)
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

    def test_bleeding_uses_all_stacks_once_per_turn_for_a_boss(self):
        engine = self.engine()
        boss = engine.enemy
        attack = Action('Ataque', damage=1)
        boss.actions = [attack]
        boss.actions_per_turn = 3
        boss.set_intent('attack', 1, attack)
        boss.add_block(20)
        boss.add_stacks('bleed', 2)
        boss.add_stacks('bleed', 1)
        self.full_round(engine)
        self.assertEqual(boss.hp, 491)
        self.assertEqual(boss.block, 20)
        self.assertEqual((boss.bleed_stacks, boss.bleed_turns), (3, 1))
        self.full_round(engine)
        self.assertEqual(boss.hp, 482)
        self.assertEqual((boss.bleed_stacks, boss.bleed_turns), (0, 0))

    def test_player_bleed_skips_defense_and_triggers_on_shield_damage(self):
        engine = self.engine()
        player, enemy = engine.player, engine.enemy
        player.add_stacks('bleed', 2)
        enemy.block = 6
        self.play(engine, 'Esfera Protetora')
        self.assertEqual(player.bleed_triggers_this_turn, 0)
        self.play(engine, 'Soco Simples')
        self.assertEqual(player.bleed_triggers_this_turn, 1)
        self.assertEqual(player.hp, player.max_hp - 6)
        for _ in range(3):
            self.play(engine, 'Soco Simples')
        self.assertEqual(enemy.hp, 482)
        self.assertEqual(player.hp, player.max_hp - 6)
        self.assertEqual(player.bleed_triggers_this_turn, 1)
        self.full_round(engine)
        self.assertEqual(player.bleed_triggers_this_turn, 0)

    def test_adaga_bleed_triggers_when_enemy_only_hits_player_shield(self):
        engine = self.engine()
        player, enemy = engine.player, engine.enemy
        self.play(engine, 'Adaga Sangrenta')
        player.add_block(20)
        hit = Action('Ataque', damage=7)
        enemy.set_intent('attack', hit.damage, hit)
        engine.end_turn()
        engine.enemy_turn()
        self.assertEqual(player.hp, player.max_hp)
        self.assertEqual(player.block, 13)
        self.assertEqual(enemy.bleed_triggers_this_turn, 1)
        self.assertEqual(enemy.hp, 500 - 8 - 6)

    def test_totem_blocks_the_hit_but_the_attacker_still_bleeds(self):
        engine = self.engine()
        player, enemy = engine.player, engine.enemy
        enemy.add_stacks('bleed', 2)
        player.add_block(20)
        player.apply_status('totem', 0, 1)
        hit = Action('Ataque', damage=7)
        enemy.set_intent('attack', hit.damage, hit)
        engine.end_turn()
        engine.enemy_turn()
        self.assertEqual(player.hp, player.max_hp)
        self.assertEqual(player.block, 20)
        self.assertEqual(enemy.bleed_triggers_this_turn, 1)
        self.assertEqual(enemy.hp, 494)

    def test_dagger_does_not_apply_or_refresh_bleed_without_hp_damage(self):
        engine = self.engine()
        enemy = engine.enemy
        enemy.block = 9
        self.play(engine, 'Adaga Sangrenta')
        self.assertEqual(enemy.bleed_stacks, 0)
        enemy.add_stacks('bleed', 1)
        enemy.statuses['bleed']['turns'] = 1
        enemy.block = 8
        self.play(engine, 'Adaga Sangrenta')
        self.assertEqual((enemy.block, enemy.hp), (0, 500))
        self.assertEqual((enemy.bleed_stacks, enemy.bleed_turns), (1, 1))
        enemy.block = 7
        self.play(engine, 'Adaga Sangrenta')
        self.assertEqual((enemy.block, enemy.hp), (0, 499))
        self.assertEqual((enemy.bleed_stacks, enemy.bleed_turns), (3, 2))

    def test_enemy_attack_statuses_require_hp_damage(self):
        for block in (8, 7, 6, 0):
            with self.subTest(block=block):
                engine = self.engine()
                hit = Action('Ataque', damage=7, status_effects=(
                    ('poison', 2, 1), ('bleed', 2, 1), ('fire', 3, 1), ('shock', 1, 1),
                ))
                engine.player.block = block
                engine.enemy.set_intent('attack', hit.damage, hit)
                engine.end_turn()
                engine.enemy_turn()
                for status in ('poison', 'bleed', 'fire', 'shock'):
                    self.assertEqual(status in engine.player.statuses, block < hit.damage)

    def test_lethal_bleed_happens_after_player_action_and_clears_battle_stacks(self):
        engine = self.engine()
        engine.player.hp = 3
        engine.player.add_stacks('bleed', 1)
        engine.enemy.add_stacks('poison', 2)
        self.play(engine, 'Soco Simples')
        self.assertEqual(engine.enemy.hp, 494)
        self.assertEqual(engine.state, 'game_over')
        self.assertEqual(engine.player.bleed_stacks, 0)
        self.assertEqual(engine.player.bleed_triggers_this_turn, 0)
        self.assertEqual(engine.enemy.poison_stacks, 0)

    def test_only_damaging_ultimate_triggers_bleed(self):
        engine = self.engine()
        player = engine.player
        player.add_stacks('bleed', 1)
        for ultimate in ('forcas_ancestrais', 'rugido_da_floresta'):
            engine.equip_ultimate(ultimate)
            player.ultimate_charge = player.ultimate_threshold
            player.energy = 5
            self.assertTrue(engine.activate_ultimate())
            if ultimate == 'forcas_ancestrais':
                self.assertEqual(player.hp, player.max_hp)
                self.assertEqual(player.bleed_triggers_this_turn, 0)
        self.assertEqual(player.hp, player.max_hp - 3)
        self.assertEqual(player.bleed_triggers_this_turn, 1)

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
        target.add_stacks('poison', 1)
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

    def test_cleanse_preserves_buffs_and_dispel_preserves_debuffs(self):
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
        for name in ('bleed', 'fire', 'vulnerable', 'weak'):
            engine.enemy.apply_status(name, 2, 1)
        engine.enemy.apply_strength(6, 2)
        engine.enemy.next_turn_energy = 2
        engine.enemy.attack_lock_turns = 2
        negative_before = {key: dict(value) for key, value in engine.enemy.statuses.items()
                           if key in Combatant.NEGATIVE_STATUSES}
        self.play(engine, 'Amuleto Dissipador')
        self.assertEqual(engine.enemy.statuses, negative_before)
        self.assertEqual(engine.enemy.weak_turns, 2)
        self.assertEqual(engine.enemy.attack_lock_turns, 2)
        self.assertEqual(engine.enemy.next_turn_energy, 0)
        self.assertEqual(engine.enemy.temporary_strength, 0)
        self.assertEqual(engine.enemy.block, 0)
        self.assertEqual(engine.enemy.strength, 0)

    def test_aura_fragility_and_delayed_energy(self):
        engine = self.engine()
        self.play(engine, 'Aura Rubra')
        self.play(engine, 'Poção Fragilizante')
        self.play(engine, 'Soco Simples')
        self.assertEqual(engine.enemy.hp, 485)  # ceil((6+6)*1.25)
        for _ in range(3): self.full_round(engine)
        self.assertEqual(engine.player.attack_bonus, 0)
        self.assertNotIn('vulnerable', engine.enemy.statuses)
        engine.player.energy_max = 3
        engine.player.energy = 3
        engine.deck_manager.hand = [CARD_BY_NAME['Surto de Energia'].copy()]
        self.assertTrue(engine.play_card(0))
        self.assertEqual(engine.energy, 2)
        self.full_round(engine)
        self.assertEqual(engine.energy_max, 4)
        self.assertEqual(engine.energy, 6)
        self.full_round(engine)
        self.assertEqual(engine.energy, 5)

    def test_surge_forecast_handles_partial_gain_and_existing_bonus(self):
        from src.models.effects.tactical_card_effect import next_turn_energy_gain
        for maximum, pending, amount, expected in (
                (3, 0, 2, 2), (5, 0, 3, 2), (5, 2, 2, 0),
                (6, 0, 2, 1), (7, 0, 2, 0), (8, 0, 3, 0)):
            with self.subTest(maximum=maximum, pending=pending):
                engine = self.engine()
                engine.player.energy_max = maximum
                engine.player.next_turn_energy = pending
                self.assertEqual(next_turn_energy_gain(engine.player, amount), expected)
                before = min(8, maximum + 1 + pending)
                engine.player.next_turn_energy += amount
                self.full_round(engine)
                self.assertEqual(engine.energy - before, expected)

    def test_updated_mask_and_charge_at_both_levels(self):
        from src.systems.roguelite import instance_card
        for level, heal, damage in ((1, 14, 18), (2, 18, 24)):
            engine = self.engine()
            engine.player.hp = 20
            engine.deck_manager.hand = [instance_card({'id': 'mask', 'name': 'Máscara Ancestral', 'level': level})]
            self.assertTrue(engine.play_card(0))
            self.assertEqual(engine.player.hp, 20 + heal)
            self.assertEqual(engine.player.block, 22 if level == 1 else 28)
            self.assertEqual(engine.energy, 4)
            engine.player.energy = 8
            engine.deck_manager.hand = [instance_card({'id': 'charge', 'name': 'Investida', 'level': level})]
            self.assertTrue(engine.play_card(0))
            self.assertEqual(engine.enemy.hp, 500 - damage)
            self.assertEqual(engine.energy, 6)

    def test_charge_removes_quarter_of_remaining_shield_after_damage(self):
        from src.systems.roguelite import instance_card
        for level, expected in ((1, 17), (2, 12)):
            engine = self.engine()
            engine.enemy.add_block(40)
            engine.deck_manager.hand = [instance_card({'id': 'charge', 'name': 'Investida', 'level': level})]
            self.assertTrue(engine.play_card(0))
            self.assertEqual(engine.enemy.hp, 500)
            self.assertEqual(engine.enemy.block, expected)
            self.assertEqual(engine.energy, 6)

    def test_charge_does_not_pierce_or_break_through_totem(self):
        for initial, expected_hp, expected_block, totem in (
                (0, 482, 0, False), (10, 492, 0, False),
                (21, 500, 3, False), (40, 500, 40, True)):
            engine = self.engine()
            engine.enemy.add_block(initial)
            if totem:
                engine.enemy.apply_status('totem', 0)
            self.play(engine, 'Investida')
            self.assertEqual(engine.enemy.hp, expected_hp)
            self.assertEqual(engine.enemy.block, expected_block)

    def test_charge_preserves_remaining_shield_layer_durations(self):
        engine = self.engine()
        engine.enemy.add_block(30)
        engine.enemy.begin_turn()
        engine.enemy.add_block(20)
        self.play(engine, 'Investida')
        self.assertEqual(engine.enemy._block_layers, [[4, 1], [20, 2]])
        engine.enemy.begin_turn()
        self.assertEqual(engine.enemy.block, 20)

    def test_poison_death_on_player_end_prevents_enemy_acting(self):
        engine = self.engine()
        engine.player.hp = 3
        engine.player.apply_status('poison', 2, 5)
        engine.end_turn()
        self.assertEqual(engine.state, 'game_over')
        engine.enemy_turn()
        self.assertEqual(engine.state, 'game_over')

    def test_new_fight_clears_temporary_effects_and_ultimate_charge(self):
        engine = self.engine()
        engine.player.ultimate_charge = 13
        engine.player.apply_status('fire', 3)
        engine.player.next_turn_energy = 2
        engine.player.add_block(10)
        engine.start_combat()
        self.assertEqual(engine.player.ultimate_charge, 0)
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
