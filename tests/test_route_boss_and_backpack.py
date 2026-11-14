"""Regressões da campanha, Corpo Seco e deck 3x fixo."""
import tempfile
import unittest
from unittest.mock import patch

from src.models.player import Player
from src.systems.normal_enemy_catalog import biome_enemy_names
from src.systems.save_manager import SaveManager, SaveCorruptedError
from src.systems.combat_engine import CombatEngine
from src.systems.enemy_factory import create_corpo_seco, create_road_enemy
from src.systems.campaign_progress import record_road_victory, record_victory
from src.systems.territory_map import TERRITORY_IDS, encounter_status, status
from src.systems.deck_loadout import (
    COPIES_PER_CARD,
    DECK_SLOT_LIMIT,
    add_card_to_slots,
    commit_deck,
    deck_is_ready_for_exit,
    remove_card_from_slots,
)
from src.systems.shop_system import purchase_card


class RouteBossDeckTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.saves = SaveManager(self.folder.name)
        self.data = self.saves.create_save('slot_1')

    def tearDown(self):
        self.folder.cleanup()

    def _add(self, name):
        progress = self.data['progresso']
        ok, message, slots = add_card_to_slots(
            progress['deck_slots'], progress['cartas_colecao'], name
        )
        if ok:
            saved, save_message = commit_deck(self.saves, self.data, slots)
            if not saved:
                return False, save_message
        return ok, message

    def _remove(self, slot_index):
        progress = self.data['progresso']
        ok, message, slots = remove_card_from_slots(
            progress['deck_slots'], slot_index
        )
        if ok and deck_is_ready_for_exit(slots):
            saved, save_message = commit_deck(self.saves, self.data, slots)
            if not saved:
                return False, save_message
        return ok, message

    def _road_victory(self, level=1):
        engine = CombatEngine(map_mode=True)
        engine.resume_from_save(self.data, self.saves, level=level, encounter_kind='road')
        self.assertIn(engine.enemy.name, biome_enemy_names(level))
        engine.state = 'victory'
        engine.skip_reward()
        self.assertEqual(engine.state, 'phase_complete')
        record_road_victory(self.saves, self.data, engine, lambda: None)

    def test_new_save_starts_with_zero_road_encounters(self):
        self.assertEqual(self.data['progresso']['encontros_por_territorio'], {})
        self.assertEqual(status(self.data, TERRITORY_IDS[0]), 'available')

    def test_two_road_encounters_then_point_fight_unlock(self):
        for i in range(2):
            self._road_victory()
            self.assertEqual(self.saves.load_save('slot_1')['progresso']['encontros_por_territorio'][TERRITORY_IDS[0]], i+1)
            self.assertEqual(status(self.data, TERRITORY_IDS[1]), 'locked')
        engine = CombatEngine(map_mode=True)
        engine.resume_from_save(self.data, self.saves, level=1)
        engine.state = 'victory'
        engine.skip_reward()
        record_victory(self.saves, self.data, engine, lambda: None)
        self.assertEqual(status(self.data, TERRITORY_IDS[0]), 'completed')
        self.assertEqual(status(self.data, TERRITORY_IDS[1]), 'available')
        self.assertEqual(self.data['progresso']['encontros_por_territorio'].get(TERRITORY_IDS[1], 0), 0)

    def test_point_cannot_unlock_before_road(self):
        engine = CombatEngine(map_mode=True)
        engine.state = 'victory'
        engine.skip_reward()
        with self.assertRaises(ValueError):
            record_victory(self.saves, self.data, engine, lambda: None)

    def test_road_cannot_be_counted_three_times(self):
        for _ in range(3):
            self._road_victory()
        progress = self.saves.load_save('slot_1')['progresso']
        self.assertEqual(progress['encontros_por_territorio'][TERRITORY_IDS[0]], 2)

    def test_legacy_save_preserves_open_point_battles(self):
        old = self.saves.create_save('slot_2')
        old['progresso'].pop('encontros_por_territorio', None)
        self.saves.save(old)
        self.assertEqual(self.saves.load_save('slot_2')['progresso']['encontros_por_territorio'][TERRITORY_IDS[0]], 2)

    def test_old_three_win_counter_is_migrated_without_relocking_the_boss(self):
        from pathlib import Path
        import json
        slot = Path(self.folder.name) / 'slot_1.json'
        old = json.loads(slot.read_text(encoding='utf-8'))
        old['progresso']['encontros_por_territorio'][TERRITORY_IDS[0]] = 3
        slot.write_text(json.dumps(old), encoding='utf-8')
        loaded = self.saves.load_save('slot_1')
        self.assertEqual(loaded['progresso']['encontros_por_territorio'][TERRITORY_IDS[0]], 2)
        self.assertEqual(encounter_status(loaded, TERRITORY_IDS[0]), 'available')

    def test_fortress_boss_and_other_road_enemies(self):
        self.assertEqual(create_corpo_seco(5).name, 'Corpo Seco')
        self.assertIn(create_road_enemy(5).name, biome_enemy_names(5))
        self.data['progresso']['andar'] = 5
        e = CombatEngine(map_mode=True)
        e.resume_from_save(self.data, self.saves, level=5, encounter_kind='point')
        self.assertEqual(e.enemy.name, 'Corpo Seco')
        self.assertEqual(e.enemy.actions_per_turn, 2)
        e.resume_from_save(self.data, self.saves, level=5, encounter_kind='road')
        self.assertIn(e.enemy.name, biome_enemy_names(5))

    def test_boss_gets_two_actions_and_spins_every_eight_actions(self):
        e = CombatEngine(map_mode=True)
        e.resume_from_save(self.data, self.saves, level=5, encounter_kind='point')
        e.player.hp = 999
        e.player.max_hp = 999
        action_names = []
        for i in range(16):
            if e.state == 'player_turn':
                e.end_turn()
            action_names.append(e.enemy.current_action.name)
            e.enemy_turn()
            self.assertEqual(e.enemy.action_counter, i+1)
            if i % 2 == 0:
                self.assertEqual(e.enemy_actions_remaining, 1)
            else:
                self.assertEqual(e.enemy_actions_remaining, 0)
            e.finish_enemy_turn()
        self.assertEqual(action_names[7], 'Ataque Giratório')
        self.assertEqual(action_names[15], 'Ataque Giratório')
        self.assertEqual(e.player.turn_count, 9)
        self.assertTrue(all(name != 'Ataque Giratório' for i, name in enumerate(action_names) if (i+1) % 8 != 0))

    def test_normal_enemy_one_action(self):
        e = CombatEngine(map_mode=True)
        e.resume_from_save(self.data, self.saves, level=1, encounter_kind='road')
        e.end_turn()
        e.enemy_turn()
        self.assertEqual(e.enemy_actions_remaining, 0)
        e.finish_enemy_turn()
        self.assertEqual(e.state, 'player_turn')

    def test_initial_deck_three_copies_per_starter(self):
        p = self.data['progresso']
        self.assertEqual(p['deck_slots'][:6], ['Soco Simples'] * 3 + ['Esfera Protetora'] * 3)
        self.assertEqual(p['deck_slots'][6:], [None] * (DECK_SLOT_LIMIT - 6))
        self.assertEqual(p['cartas'].count('Soco Simples'), 3)
        self.assertEqual(p['cartas'].count('Esfera Protetora'), 3)
        self.assertEqual(len(p['deck_slots']), DECK_SLOT_LIMIT)

    def test_purchase_collect_then_add_three_copies(self):
        self.data['progresso']['moedas'] = 1000
        self.assertTrue(purchase_card(self.saves, self.data, 'Investida').success)
        self.assertNotIn('Investida', self.data['progresso']['cartas'])
        for _ in range(COPIES_PER_CARD):
            self.assertTrue(self._add('Investida')[0])
        saved = self.saves.load_save('slot_1')['progresso']
        self.assertEqual(saved['cartas'].count('Investida'), COPIES_PER_CARD)
        # A quarta cópia é recusada.
        self.assertFalse(self._add('Investida')[0])
        # Carta que o jogador não possui não entra.
        self.assertFalse(self._add('Fúria')[0])
        index = self.data['progresso']['deck_slots'].index('Investida')
        self.assertTrue(self._remove(index)[0])
        self.assertEqual(self.data['progresso']['cartas'].count('Investida'), COPIES_PER_CARD - 1)

    def test_deck_removal_can_empty_the_draft_without_persisting_it(self):
        progress = self.data['progresso']
        official_before = list(progress['deck_slots'])
        slots = list(progress['deck_slots'])
        while any(name for name in slots):
            index = next(i for i, name in enumerate(slots) if name)
            ok, message, slots = remove_card_from_slots(slots, index)
            self.assertTrue(ok)
            if deck_is_ready_for_exit(slots):
                self.assertTrue(commit_deck(self.saves, self.data, slots)[0])
        self.assertEqual([name for name in slots if name], [])
        # O rascunho vazio não substitui o último deck válido.
        self.assertEqual(
            self.data['progresso']['deck_slots'], official_before
        )
        self.assertTrue(deck_is_ready_for_exit(self.data['progresso']['deck_slots']))
        # Adicionar depois de zerar o rascunho volta a funcionar normalmente.
        ok, message, slots = add_card_to_slots(
            slots, progress['cartas_colecao'], 'Soco Simples'
        )
        self.assertTrue(ok)
        self.assertFalse(commit_deck(self.saves, self.data, slots)[0])
        self.assertEqual(
            self.data['progresso']['cartas'],
            ['Soco Simples'] * 3 + ['Esfera Protetora'] * 3,
        )

    def test_bad_encounter_counter_rejected(self):
        for value in (4, -1, True, '3'):
            self.data['progresso']['encontros_por_territorio'] = {TERRITORY_IDS[0]: value}
            with self.assertRaises(SaveCorruptedError):
                self.saves.save(self.data)


if __name__ == '__main__':
    unittest.main()
