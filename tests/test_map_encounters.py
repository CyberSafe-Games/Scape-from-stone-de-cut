"""Seleção independente, bloqueios e repetição dos encontros do mapa."""
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pygame
from src.systems.territory_map import TERRITORIES, TERRITORY_IDS, encounter_status, encounter_positions
from src.systems.save_manager import SaveManager
from src.systems.combat_engine import CombatEngine
from src.systems.campaign_progress import record_road_victory
from src.scenes.map_scene import MapScene, MAP_AREA


class MapEncounterTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.saves = SaveManager(self.folder.name)
        self.data = self.saves.create_save('slot_1')
        self.data['progresso']['guia_mapa_visto'] = True
        self.tid = TERRITORY_IDS[0]

    def win(self, index, level=1):
        engine = CombatEngine(map_mode=True)
        engine.resume_from_save(self.data, self.saves, level=level, encounter_kind='road', encounter_index=index)
        engine.state = 'victory'
        engine.skip_reward()
        return record_road_victory(self.saves, self.data, engine, lambda: None)

    def test_new_save_opens_only_first_encounter_and_three_wins_open_main(self):
        self.assertEqual([encounter_status(self.data, self.tid, i) for i in range(3)],
                         ['available', 'locked', 'locked'])
        self.assertEqual(encounter_status(self.data, self.tid), 'locked')
        for i in range(3):
            self.assertEqual(self.win(i), i + 1)
            self.assertEqual(encounter_status(self.data, self.tid, i), 'completed')
        self.assertEqual(encounter_status(self.data, self.tid), 'available')
        self.assertEqual(encounter_status(self.data, TERRITORY_IDS[1], 0), 'locked')

    def test_replay_does_not_skip_next_encounter_or_change_checkpoint(self):
        self.win(0)
        for _ in range(3): self.assertEqual(self.win(0), 1)
        loaded = self.saves.load_save('slot_1')['progresso']
        self.assertEqual(loaded['encontros_por_territorio'][self.tid], 1)
        self.assertEqual(loaded['andar'], 1)
        self.assertEqual(loaded['territorios_concluidos'], [])
        self.assertEqual(encounter_status(self.data, self.tid, 2), 'locked')

    def test_can_replay_normal_encounters_in_completed_territory(self):
        p = self.data['progresso']
        p['territorios_concluidos'] = [self.tid]
        p['territorios_desbloqueados'].append(TERRITORY_IDS[1])
        p['encontros_por_territorio'][self.tid] = 3
        p['andar'] = 2
        for i in range(3): self.assertEqual(self.win(i), 3)
        self.assertEqual(p['andar'], 2)
        self.assertNotIn(TERRITORY_IDS[1], p['territorios_concluidos'])
        self.assertEqual(p['encontros_por_territorio'].get(TERRITORY_IDS[1], 0), 0)

    def test_locked_encounters_and_invalid_indices_cannot_grant_rewards(self):
        for index, level in ((2, 1), (0, 2), (-1, 1), (3, 1), (True, 1)):
            with self.subTest(index=index, level=level), self.assertRaises(ValueError):
                self.win(index, level)
        self.assertEqual(self.data['progresso']['encontros_por_territorio'], {})

    def test_failed_save_keeps_previous_count_and_retry_advances_once(self):
        with patch.object(self.saves, 'save', side_effect=OSError('falha')):
            with self.assertRaises(OSError): self.win(0)
        self.assertEqual(self.data['progresso']['encontros_por_territorio'], {})
        self.assertEqual(self.win(0), 1)

    def test_all_twenty_one_encounter_points_are_inside_map_and_unique(self):
        positions = [pos for t in TERRITORIES for pos in encounter_positions(t.id)]
        self.assertEqual(len(positions), 21)
        self.assertEqual(len(set(positions)), 21)
        self.assertTrue(all(MAP_AREA.collidepoint(pos) for pos in positions))

    def scene(self):
        wm = MagicMock()
        wm.handle_window_event.return_value = False
        wm.get_fullscreen_button_rect.return_value = pygame.Rect(-1000, -1000, 1, 1)
        return MapScene(MagicMock(), wm, MagicMock(), self.saves, self.data)

    def test_clicking_encounter_and_play_passes_exact_index_to_battle(self):
        self.win(0)
        scene = self.scene()
        scene.window_manager.map_to_virtual.return_value = encounter_positions(self.tid)[0]
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(0, 0)))
        self.assertEqual((scene.selected, scene.selected_encounter), (self.tid, 0))
        with patch('src.scenes.battle_scene.BattleScene') as battle:
            scene._start_selected()
            self.assertEqual(battle.call_args.kwargs['encounter_kind'], 'road')
            self.assertEqual(battle.call_args.kwargs['encounter_index'], 0)
            self.assertEqual(battle.call_args.kwargs['selected_level'], 1)

    def test_clicking_main_point_before_road_complete_does_not_start_battle(self):
        scene = self.scene()
        scene.selected_encounter = None
        with patch('src.scenes.battle_scene.BattleScene') as battle:
            scene._start_selected()
            battle.assert_not_called()
        self.assertTrue(scene.error)

    def test_keyboard_visits_all_twenty_eight_points(self):
        scene = self.scene()
        seen = set()
        for _ in range(28):
            seen.add((scene.selected, scene.selected_encounter))
            scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
        self.assertEqual(len(seen), 28)
