"""Cenários da campanha e compatibilidade com os saves existentes (sem Pygame)."""
import json
import os
import tempfile
import unittest

from src.systems.combat_engine import CombatEngine
from src.systems.campaign_progress import record_victory
from src.systems.save_manager import SaveManager, SaveCorruptedError
from src.systems.territory_map import (
    TERRITORIES, TERRITORY_IDS, by_id, by_level, status, complete,
    completed_count,
)


class TestTerritoryMap(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.saves = SaveManager(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def test_seven_distinct_territories_and_levels(self):
        self.assertEqual(len(TERRITORIES), 7)
        self.assertEqual(len(set(TERRITORY_IDS)), 7)
        self.assertEqual([t.level for t in TERRITORIES], list(range(1, 8)))
        for t in TERRITORIES:
            self.assertIs(by_id(t.id), t)
            self.assertIs(by_level(t.level), t)

    def test_new_save_only_first_is_open(self):
        data = self.saves.create_save('slot_1')
        self.assertEqual([status(data, tid) for tid in TERRITORY_IDS],
                         ['available'] + ['locked'] * 6)
        self.assertEqual(data['progresso']['territorios_concluidos'], [])
        self.assertFalse(data['progresso']['guia_mapa_visto'])

    def test_locked_stage_cannot_be_completed(self):
        data = self.saves.create_save('slot_1')
        with self.assertRaises(ValueError):
            complete(data, TERRITORY_IDS[3])
        self.assertEqual(completed_count(data), 0)
        self.assertEqual(len(data['progresso']['territorios_desbloqueados']), 1)

    def test_progresses_one_stage_at_a_time_and_replays(self):
        data = self.saves.create_save('slot_1')
        for idx, tid in enumerate(TERRITORY_IDS):
            self.assertEqual(status(data, tid), 'available')
            unlocked_next = complete(data, tid)
            self.assertEqual(status(data, tid), 'completed')
            self.assertEqual(completed_count(data), idx + 1)
            self.assertEqual(unlocked_next.id if unlocked_next else None,
                             TERRITORY_IDS[idx + 1] if idx < 6 else None)
            # Revisitar/concluir outra vez não pode duplicar registros.
            complete(data, tid)
            self.assertEqual(data['progresso']['territorios_concluidos'].count(tid), 1)
        self.assertEqual(completed_count(data), 7)
        self.assertEqual(len(data['progresso']['territorios_desbloqueados']), 7)
        self.saves.save(data)
        restored = self.saves.load_save('slot_1')
        self.assertEqual(completed_count(restored), 7)

    def test_slots_are_independent_across_map_progress(self):
        a = self.saves.create_save('slot_1')
        self.saves.create_save('slot_2')
        complete(a, TERRITORY_IDS[0])
        a['progresso']['moedas'] = 99
        self.saves.save(a)
        self.assertEqual(completed_count(self.saves.load_save('slot_2')), 0)
        self.assertEqual(status(self.saves.load_save('slot_2'), TERRITORY_IDS[1]), 'locked')
        self.assertEqual(self.saves.load_save('slot_2')['progresso']['moedas'], 0)
        self.assertEqual(status(self.saves.load_save('slot_1'), TERRITORY_IDS[1]), 'available')

    def test_legacy_save_migration_infers_previous_wins(self):
        path = os.path.join(self.directory.name, 'slot_1.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                'versao': 2, 'nome': 'Jornada antiga',
                'progresso': {'andar': 4, 'moedas': 56,
                             'territorios_desbloqueados': ['stone_the_cut'],
                             'cartas': ['Golpe']},
            }, f)
        loaded = self.saves.load_save('slot_1')
        self.assertEqual(loaded['progresso']['moedas'], 56)
        self.assertEqual(completed_count(loaded), 3)
        self.assertEqual(status(loaded, TERRITORY_IDS[3]), 'available')
        self.assertEqual(status(loaded, TERRITORY_IDS[4]), 'locked')
        self.saves.save(loaded)
        self.assertEqual(completed_count(self.saves.load_save('slot_1')), 3)

    def test_legacy_checkpoint_without_unlocked_field_recovers_map(self):
        path = os.path.join(self.directory.name, 'slot_1.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'versao': 2, 'nome': 'Antigo',
                       'progresso': {'andar': 5, 'moedas': 12}}, f)
        data = self.saves.load_save('slot_1')
        self.assertEqual(completed_count(data), 4)
        self.assertEqual(status(data, TERRITORY_IDS[4]), 'available')
        self.assertEqual(status(data, TERRITORY_IDS[5]), 'locked')

    def test_corrupt_completed_list_is_rejected(self):
        data = self.saves.create_save('slot_1')
        data['progresso']['territorios_concluidos'] = [1]
        with self.assertRaises(SaveCorruptedError):
            self.saves.save(data)

    def test_map_mode_reward_triggers_phase_complete_not_next_level(self):
        events = []
        engine = CombatEngine(map_mode=True, on_event_callback=lambda event, **kw: events.append((event, kw)))
        engine.player.hp = 22
        engine.level = 1
        engine.state = 'victory'
        engine.generate_rewards()
        deck_len = len(engine.deck_manager.deck)
        engine.choose_reward(0)
        self.assertEqual(engine.level, 1)
        self.assertEqual(engine.state, 'phase_complete')
        self.assertEqual(engine.player.hp, 30)
        self.assertEqual(len(engine.deck_manager.deck), deck_len + 1)
        self.assertEqual(events[-1], ('phase_complete', {'level': 1}))
        engine.choose_reward(0)
        self.assertEqual(len(engine.deck_manager.deck), deck_len + 1)

    def test_skip_reward_and_legacy_flow(self):
        map_events = []
        engine = CombatEngine(map_mode=True, on_event_callback=lambda e, **kw: map_events.append(e))
        engine.state = 'victory'
        before = len(engine.deck_manager.deck)
        engine.skip_reward()
        self.assertEqual(len(engine.deck_manager.deck), before)
        self.assertEqual(engine.level, 1)
        self.assertEqual(map_events, ['phase_complete'])
        legacy = CombatEngine()
        legacy.state = 'victory'
        legacy.skip_reward()
        self.assertEqual(legacy.level, 2)

    def test_record_victory_collects_coins_and_persists_all_rewards(self):
        data = self.saves.create_save('slot_1')
        engine = CombatEngine(map_mode=True)
        engine.state = 'victory'
        engine.generate_rewards()
        engine.choose_reward(0)
        credited = []

        def finish_animation():
            if not credited:
                engine.player.add_coins(47)
                credited.append(True)

        record_victory(self.saves, data, engine, finish_animation)
        loaded = self.saves.load_save('slot_1')
        self.assertEqual(status(loaded, TERRITORY_IDS[0]), 'completed')
        self.assertEqual(status(loaded, TERRITORY_IDS[1]), 'available')
        self.assertEqual(loaded['progresso']['andar'], 2)
        self.assertEqual(loaded['progresso']['moedas'], 47)
        self.assertEqual(len(loaded['progresso']['cartas']), 8)
        # Um retry de gravação não deve voltar a recompensar a mesma fase.
        record_victory(self.saves, data, engine, finish_animation)
        self.assertEqual(self.saves.load_save('slot_1')['progresso']['moedas'], 47)
        self.assertEqual(completed_count(data), 1)

    def test_cannot_record_victory_before_reward(self):
        data = self.saves.create_save('slot_1')
        engine = CombatEngine(map_mode=True)
        engine.state = 'victory'
        with self.assertRaises(ValueError):
            record_victory(self.saves, data, engine, lambda: None)
        self.assertEqual(completed_count(data), 0)

    def test_last_territory_completion_has_no_phantom_eighth_stage(self):
        data = self.saves.create_save('slot_1')
        for tid in TERRITORY_IDS[:6]:
            complete(data, tid)
        data['progresso']['andar'] = 7
        engine = CombatEngine(map_mode=True)
        engine.resume_from_save(data, self.saves, level=7)
        engine.state = 'victory'
        engine.skip_reward()
        record_victory(self.saves, data, engine, lambda: None)
        progress = self.saves.load_save('slot_1')['progresso']
        self.assertEqual(progress['andar'], 7)
        self.assertEqual(len(progress['territorios_desbloqueados']), 7)
        self.assertEqual(len(progress['territorios_concluidos']), 7)

    def test_replay_completed_stage_retains_highest_available_stage(self):
        data = self.saves.create_save('slot_1')
        for tid in TERRITORY_IDS[:4]:
            complete(data, tid)
        data['progresso']['andar'] = 5
        self.saves.save(data)
        engine = CombatEngine(map_mode=True)
        engine.resume_from_save(data, self.saves, level=2)
        engine.state = 'victory'
        engine.skip_reward()
        record_victory(self.saves, data, engine, lambda: None)
        restored = self.saves.load_save('slot_1')
        self.assertEqual(restored['progresso']['andar'], 5)
        self.assertEqual(completed_count(restored), 4)
        self.assertEqual(status(restored, TERRITORY_IDS[4]), 'available')
        self.assertEqual(status(restored, TERRITORY_IDS[5]), 'locked')

    def test_selected_stage_does_not_overwrite_campaign_checkpoint(self):
        data = self.saves.create_save('slot_1')
        for tid in TERRITORY_IDS[:4]:
            complete(data, tid)
        data['progresso']['andar'] = 5
        self.saves.save(data)
        engine = CombatEngine(map_mode=True)
        engine.resume_from_save(self.saves.load_save('slot_1'), self.saves, level=2)
        self.assertEqual(engine.level, 2)
        self.assertEqual(data['progresso']['andar'], 5)
        # A cena grava sempre o maior entre o andar jogado e o checkpoint.
        self.saves.update_from_game(data, engine.player, engine.deck_manager,
                                    level=max(data['progresso']['andar'], engine.level))
        self.saves.save(data)
        self.assertEqual(self.saves.load_save('slot_1')['progresso']['andar'], 5)


if __name__ == '__main__':
    unittest.main()
