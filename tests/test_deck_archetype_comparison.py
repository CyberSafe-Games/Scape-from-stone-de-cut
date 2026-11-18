"""Restrições dos experimentos de dano, híbrido e defesa estrita."""
import unittest
import tempfile

from devtools.compare_deck_archetypes import (
    DECKS, slots_for, controlled_engine, fight, has_damage_route, buy_heals,
)
from devtools.simulate_roguelite_balance import play_turn
from src.systems.card_catalog import CARD_BY_NAME
from src.systems.combat_engine import CombatEngine
from src.systems.save_manager import SaveManager


class DeckArchetypeComparisonTests(unittest.TestCase):
    def test_equal_size_valid_decks_without_healing(self):
        for archetype, counts in DECKS.items():
            self.assertEqual(sum(counts.values()), 9)
            self.assertTrue(all(count <= 3 for count in counts.values()))
            self.assertEqual(len(slots_for(archetype)), 18)
            rules = {CARD_BY_NAME[name].effect.spec[5] for name in counts}
            self.assertFalse(rules.intersection(('heal', 'mask')))
        self.assertTrue(all(CARD_BY_NAME[n].card_type == 'attack' for n in DECKS['somente_dano']))
        self.assertTrue(all(CARD_BY_NAME[n].card_type == 'attack' for n in DECKS['dano_efeitos']))
        self.assertTrue(all(CARD_BY_NAME[n].effect.spec[5] in ('shield', 'totem') for n in DECKS['somente_defesa']))

    def test_pure_defense_has_no_damage_route_without_offensive_ultimate(self):
        engine = controlled_engine('somente_defesa', 1, None, 0)
        self.assertFalse(has_damage_route(engine, 'nenhuma'))
        self.assertFalse(has_damage_route(engine, 'mana_ancestral'))
        self.assertTrue(has_damage_route(engine, 'rugido_da_floresta'))
        before = engine.enemy.hp
        self.assertEqual(fight(engine, 'nenhuma', 'conservadora'), 'sem_via_de_dano')
        self.assertEqual(engine.enemy.hp, before)

    def test_actual_starter_is_not_reported_as_pure_damage_or_defense(self):
        owned = ['Soco Simples', 'Esfera Protetora']
        for archetype in ('somente_dano', 'somente_defesa'):
            self.assertEqual(slots_for(archetype, owned)[:6],
                             ['Soco Simples'] * 3 + ['Esfera Protetora'] * 3)

    def test_disabling_ultimate_preserves_its_charge(self):
        engine = CombatEngine()
        engine.player.ultimate_charge = engine.player.ultimate_threshold
        engine.player.energy = 0
        engine.deck_manager.hand = []
        engine.enemy.hp = engine.enemy.max_hp = 999
        engine.player.hp = engine.player.max_hp = 999
        play_turn(engine, allow_ultimate=False)
        self.assertEqual(engine.player.ultimate_charge, engine.player.ultimate_threshold)

    def test_shop_healing_spends_real_gold_and_keeps_cards_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            manager = SaveManager(folder)
            data = manager.create_save('comparison')
            p = data['progresso']
            p.update(vida=20, moedas=30)
            deck_before = list(p['deck_slots'])
            self.assertEqual(buy_heals(manager, data), [{'vida': 20, 'ouro': 30}])
            self.assertEqual((p['vida'], p['moedas']), (40, 0))
            self.assertEqual(p['deck_slots'], deck_before)

    def test_upgraded_control_has_only_three_lv2_and_keeps_cleanse_without_healing(self):
        for archetype in DECKS:
            engine = controlled_engine(archetype, 1, None, 0, upgrades=True)
            self.assertEqual(sum(c.level == 2 for c in engine.deck), 3)
            self.assertTrue(all(c.name not in ('Poção de Cura', 'Máscara Ancestral') for c in engine.deck))
            self.assertTrue(all(c.level == 1 for c in engine.deck if c.name == 'Poção Purificadora'))
