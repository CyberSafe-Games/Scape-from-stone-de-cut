"""Laboratório separado, imunidade real e ausência de vazamento para saves normais."""
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pygame
from src.models.player import Player
from src.models.deck import DeckManager
from src.systems.save_manager import SaveManager, TEST_SAVE_ID, is_test_save, SaveError
from src.systems.card_catalog import CARD_POOL
from src.systems.territory_map import TERRITORY_IDS, encounter_status
from src.systems.combat_engine import CombatEngine
from src.models.effects.ultimate_effect import known_ultimate_ids
from src.scenes.save_selection_scene import SaveSelectionScene


class TestLaboratorySave(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.saves = SaveManager(self.folder.name)

    def test_creates_extra_save_without_overwriting_any_normal_slot(self):
        original = []
        for i in range(1, 4):
            self.saves.create_save(f'slot_{i}')
            with open(self.saves._path(f'slot_{i}'), 'rb') as stream: original.append(stream.read())
        data = self.saves.load_or_create_test_save()
        self.assertEqual(data['id'], TEST_SAVE_ID)
        self.assertTrue(is_test_save(data))
        for i in range(1, 4):
            with open(self.saves._path(f'slot_{i}'), 'rb') as stream:
                self.assertEqual(stream.read(), original[i - 1])

    def test_unlocks_every_encounter_card_and_ultimate(self):
        data = self.saves.load_or_create_test_save()
        p = data['progresso']
        self.assertEqual(p['territorios_concluidos'], list(TERRITORY_IDS))
        self.assertEqual(set(p['cartas_colecao']), {c.name for c in CARD_POOL})
        self.assertEqual(set(p['ultimates_desbloqueadas']), set(known_ultimate_ids()))
        for tid in TERRITORY_IDS:
            for index in (0, 1, 2, None):
                self.assertEqual(encounter_status(data, tid, index), 'completed')

    def test_invulnerability_includes_all_damage_and_preserves_shield_consumption(self):
        engine = CombatEngine(map_mode=True)
        data = self.saves.load_or_create_test_save()
        engine.resume_from_save(data, self.saves, level=6, encounter_kind='point')
        player = engine.player
        self.assertTrue(player.invulnerable)
        player.add_block(10)
        self.assertEqual(player.receive_attack(1000, hits=3), 0)
        self.assertEqual(player.block, 0)
        for name, amount in (('fire', 3), ('poison', 5), ('bleed', 4)):
            player.apply_status(name, 3, amount)
        player.on_attack()
        engine.end_turn()
        for _ in range(2):
            engine.enemy_turn()
            engine.finish_enemy_turn()
        self.assertEqual(player.hp, player.max_hp)
        self.assertEqual(engine.state, 'player_turn')

    def test_normal_save_and_same_display_name_do_not_enable_invulnerability(self):
        normal = self.saves.create_save('slot_1', display_name='Laboratório de Testes')
        player = Player()
        self.saves.apply_to_game(self.saves.load_or_create_test_save(), player, DeckManager())
        self.assertTrue(player.invulnerable)
        self.saves.apply_to_game(normal, player, DeckManager())
        self.assertFalse(player.invulnerable)
        self.assertEqual(player.receive_attack(7), 7)
        self.assertEqual(player.hp, 53)

    def test_equipped_deck_and_ultimate_are_preserved_when_reopening_laboratory(self):
        data = self.saves.load_or_create_test_save()
        data['progresso']['deck_slots'][0] = 'Poção Venenosa'
        data['progresso']['ultimate_equipada'] = 'rugido_da_floresta'
        data['progresso']['moedas'] = 1234
        self.saves.save(data)
        loaded = self.saves.load_or_create_test_save()
        self.assertEqual(loaded['progresso']['deck_slots'][0], 'Poção Venenosa')
        self.assertEqual(loaded['progresso']['ultimate_equipada'], 'rugido_da_floresta')
        self.assertEqual(loaded['progresso']['moedas'], 1234)
        self.assertEqual(len(loaded['progresso']['cartas_colecao']), 20)

    def test_never_overwrites_non_test_file_with_reserved_name(self):
        self.saves.create_save(TEST_SAVE_ID)
        with self.assertRaises(SaveError): self.saves.load_or_create_test_save()
        self.assertFalse(is_test_save(self.saves.load_save(TEST_SAVE_ID)))

    def test_ui_keyboard_opens_lab_directly_on_map(self):
        wm = MagicMock()
        wm.handle_window_event.return_value = False
        manager = MagicMock()
        scene = SaveSelectionScene(manager, wm, MagicMock(), self.saves)
        with patch('src.scenes.map_scene.MapScene') as map_scene:
            scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_t))
            data = map_scene.call_args.kwargs['save_data']
            self.assertTrue(is_test_save(data))
            manager.change_scene.assert_called_once_with(map_scene.return_value)
