"""Deck por espaços individuais: um espaço por cópia, até 3 por carta."""
import json
import os
import tempfile
import unittest
from collections import Counter

from src.models.deck import DeckManager
from src.systems.card_catalog import AVAILABLE_CARD_NAMES
from src.systems.deck_loadout import (
    COPIES_PER_CARD,
    DECK_SLOT_LIMIT,
    INITIAL_SLOTS,
    add_card_to_slots,
    commit_deck,
    deck_cards,
    deck_is_ready_for_exit,
    normalize_collection_and_slots,
    remove_card_from_slots,
)
from src.systems.save_manager import SAVE_VERSION, SaveManager


class DeckSlotsTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.saves = SaveManager(self.folder.name)
        self.data = self.saves.create_save('slot_1')

    def _give_collection(self, *names):
        for name in names:
            if name not in self.data['progresso']['cartas_colecao']:
                self.data['progresso']['cartas_colecao'].append(name)

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

    def test_add_occupies_next_free_slot(self):
        self._give_collection('Investida')
        before = self.data['progresso']['deck_slots']
        self.assertTrue(self._add('Investida')[0])
        self.assertEqual(self.data['progresso']['deck_slots'][6], 'Investida')
        # Os espaços iniciais não são reorganizados.
        self.assertEqual(self.data['progresso']['deck_slots'][:6], before[:6])
        self.assertTrue(self._add('Investida')[0])
        self.assertEqual(self.data['progresso']['deck_slots'][7], 'Investida')
        self.assertEqual(self.data['progresso']['cartas'].count('Investida'), 2)

    def test_fourth_copy_is_rejected(self):
        self._give_collection('Investida')
        for _ in range(COPIES_PER_CARD):
            self.assertTrue(self._add('Investida')[0])
        ok, message = self._add('Investida')
        self.assertFalse(ok)
        self.assertEqual(self.data['progresso']['cartas'].count('Investida'), COPIES_PER_CARD)
        self.assertEqual(self.data['progresso']['deck_slots'].count('Investida'), COPIES_PER_CARD)

    def test_deck_never_exceeds_slot_limit(self):
        # Coleção completa: enche o deck até o limite e garante que mais nada entra.
        for name in AVAILABLE_CARD_NAMES:
            self._give_collection(name)
        for name in AVAILABLE_CARD_NAMES:
            for _ in range(COPIES_PER_CARD):
                self._add(name)
        progress = self.data['progresso']
        self.assertEqual(
            sum(n is not None for n in progress['deck_slots']), DECK_SLOT_LIMIT
        )
        self.assertEqual(len(progress['deck_slots']), DECK_SLOT_LIMIT)
        for name in AVAILABLE_CARD_NAMES:
            ok, message = self._add(name)
            if progress['deck_slots'].count(name) < COPIES_PER_CARD:
                # Ainda sobrava cota desta carta antes do deck encher? Não pode:
                # ao encher, o limite global foi atingido primeiro.
                self.assertFalse(ok)
            else:
                self.assertFalse(ok)

    def test_remove_frees_only_that_slot(self):
        self._give_collection('Investida')
        self._add('Investida')
        slots_before = list(self.data['progresso']['deck_slots'])
        target = slots_before.index('Investida')
        self.assertTrue(self._remove(target)[0])
        slots_after = self.data['progresso']['deck_slots']
        for i, (before, after) in enumerate(zip(slots_before, slots_after)):
            if i == target:
                self.assertIsNone(after)
            else:
                self.assertEqual(before, after)

    def test_remove_last_card_leaves_draft_empty_without_touching_official(self):
        progress = self.data['progresso']
        official = list(progress['deck_slots'])
        self.assertTrue(deck_is_ready_for_exit(official))
        ok, message, slots = remove_card_from_slots(
            ['Soco Simples'] + [None] * (DECK_SLOT_LIMIT - 1), 0
        )
        self.assertTrue(ok)
        self.assertEqual(message, 'Soco Simples removida do deck.')
        self.assertEqual(deck_cards(slots), [])
        self.assertFalse(commit_deck(self.saves, self.data, slots)[0])
        # O rascunho inválido não sobrescreve o deck oficial.
        self.assertEqual(self.data['progresso']['cartas'], deck_cards(official))
        self.assertEqual(self.data['progresso']['deck_slots'], official)

    def test_initial_deck_fills_slots_per_rule(self):
        progress = self.data['progresso']
        self.assertEqual(len(progress['deck_slots']), DECK_SLOT_LIMIT)
        self.assertEqual(progress['deck_slots'], list(INITIAL_SLOTS))
        self.assertEqual(Counter(deck_cards(progress['deck_slots'])),
                         {'Soco Simples': 3, 'Esfera Protetora': 3})
        self.assertEqual(progress['cartas'],
                         ['Soco Simples'] * 3 + ['Esfera Protetora'] * 3)

    def test_normalize_uses_initial_deck_when_deck_is_missing(self):
        progress = {'cartas_colecao': ['Soco Simples', 'Esfera Protetora', 'Investida']}
        normalize_collection_and_slots(progress)
        self.assertEqual(
            Counter(deck_cards(progress['deck_slots'])),
            {'Soco Simples': 3, 'Esfera Protetora': 3},
        )
        self.assertEqual(len(progress['deck_slots']), DECK_SLOT_LIMIT)
        self.assertEqual(progress['cartas_colecao'],
                         ['Soco Simples', 'Esfera Protetora', 'Investida'])

    def test_deck_manager_builds_stacks_with_exact_copies(self):
        self._give_collection('Investida')
        for _ in range(2):
            self._add('Investida')
        player_deck = DeckManager()
        self.saves.apply_to_game(self.saves.load_save('slot_1'), self._player(), player_deck)
        self.assertEqual(
            Counter(card.name for card in player_deck.deck),
            {'Soco Simples': 3, 'Esfera Protetora': 3, 'Investida': 2},
        )
        player_deck.start_combat()
        self.assertEqual(player_deck.hand, [])
        player_deck.draw_cards(DECK_SLOT_LIMIT + 5)
        self.assertEqual(
            Counter(card.name for card in player_deck.hand),
            Counter(deck_cards(self.data['progresso']['deck_slots'])),
        )
        self.assertEqual(player_deck.draw_pile, [])

    def test_save_and_load_round_trip_keeps_deck(self):
        self._give_collection('Investida', 'Bola de Fogo')
        self._add('Investida')
        self._add('Bola de Fogo')
        self._add('Bola de Fogo')
        slots = list(self.data['progresso']['deck_slots'])
        loaded = self.saves.load_save('slot_1')
        self.assertEqual(loaded['progresso']['deck_slots'], slots)
        self.assertEqual(loaded['versao'], SAVE_VERSION)
        self.assertEqual(loaded['progresso']['cartas'], deck_cards(slots))

    def test_legacy_v8_save_migrates_to_individual_slots(self):
        path = os.path.join(self.folder.name, 'velho.json')
        legacy = {
            'versao': 8,
            'id': 'velho',
            'nome': 'Velho',
            'criado_em': '2026-11-01T00:00:00',
            'atualizado_em': '2026-11-01T00:00:00',
            'progresso': {
                'moedas': 5,
                'curas_compradas_run': 0,
                'cartas_colecao': ['Soco Simples', 'Esfera Protetora', 'Investida'],
                'deck_slots': ['Soco Simples', 'Esfera Protetora', 'Investida', None, None, None],
                'cartas': ['Soco Simples'] * 3 + ['Esfera Protetora'] * 3 + ['Investida'] * 3,
            },
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(legacy, f, ensure_ascii=False)
        loaded = self.saves.load_save('velho')
        progress = loaded['progresso']
        self.assertEqual(loaded['versao'], SAVE_VERSION)
        self.assertEqual(len(progress['deck_slots']), DECK_SLOT_LIMIT)
        self.assertEqual(progress['deck_slots'][:9],
                         ['Soco Simples'] * 3 + ['Esfera Protetora'] * 3 + ['Investida'] * 3)
        self.assertEqual(progress['deck_slots'][9:], [None] * (DECK_SLOT_LIMIT - 9))
        self.assertEqual(progress['cartas'].count('Investida'), COPIES_PER_CARD)

    def test_legacy_save_without_deck_slots_uses_collection(self):
        progress = {'cartas_colecao': ['Soco Simples', 'Esfera Protetora'],
                    'cartas': ['Soco Simples', 'Esfera Protetora']}
        normalize_collection_and_slots(progress)
        self.assertEqual(deck_cards(progress['deck_slots']).count('Soco Simples'), COPIES_PER_CARD)
        self.assertEqual(deck_cards(progress['deck_slots']).count('Esfera Protetora'), COPIES_PER_CARD)

    def test_add_from_unknown_or_unowned_card_does_not_change_deck(self):
        before = list(self.data['progresso']['deck_slots'])
        self.assertFalse(self._add('Carta Que Não Existe')[0])
        self.assertFalse(self._add('Investida')[0])
        self.assertEqual(self.data['progresso']['deck_slots'], before)

    def _player(self):
        from src.models.player import Player
        return Player('Jaum Manel', 60)


if __name__ == '__main__':
    unittest.main()
