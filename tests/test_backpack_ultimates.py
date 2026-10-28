"""Seleção persistente, equilíbrio das habilidades e navegação da mochila."""
import os
import tempfile
import unittest
from copy import deepcopy
from unittest.mock import MagicMock

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import pygame

from src.systems.save_manager import SaveManager, SaveError
from src.systems.deck_loadout import equip_ultimate
from src.systems.card_catalog import CARD_BY_NAME
from src.systems.combat_engine import CombatEngine
from src.systems.enemy_factory import create_guardiao_da_pedra
from src.models.effects.ultimate_effect import known_ultimate_ids, create_ultimate, ULTIMATE_METADATA
from src.scenes.backpack_scene import BackpackScene
from src.core.asset_manager import AssetManager


class UltimatePreparationTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.saves = SaveManager(self.folder.name)
        self.data = self.saves.create_save('slot_1')

    def test_choice_persists_and_reaches_next_battle_without_spending_charge_or_deck(self):
        before = deepcopy(self.data['progresso'])
        self.data['progresso']['carga_ultimate'] = 17
        for uid in known_ultimate_ids():
            self.assertTrue(equip_ultimate(self.saves, self.data, uid)[0])
            loaded = self.saves.load_save('slot_1')
            self.assertEqual(loaded['progresso']['ultimate_equipada'], uid)
            self.assertEqual(loaded['progresso']['carga_ultimate'], 17)
            self.assertEqual(loaded['progresso']['deck_slots'], before['deck_slots'])
            engine = CombatEngine(map_mode=True)
            engine.resume_from_save(loaded, self.saves, level=1, encounter_kind='road')
            self.assertEqual(engine.active_ultimate_id, uid)
            self.assertEqual(engine.player.ultimate_charge, 17)

    def test_invalid_choice_and_failed_write_preserve_the_previous_loadout(self):
        before = deepcopy(self.data)
        self.assertFalse(equip_ultimate(self.saves, self.data, 'inventada')[0])
        self.assertEqual(self.data, before)
        failed = MagicMock()
        failed.save.side_effect = SaveError('disco indisponível')
        self.assertFalse(equip_ultimate(failed, self.data, 'rugido_da_floresta')[0])
        self.assertEqual(self.data, before)

    def test_old_save_gains_all_three_choices_and_keeps_its_equipped_ultimate(self):
        self.data['progresso']['ultimate_equipada'] = 'forcas_ancestrais'
        self.data['progresso']['ultimates_desbloqueadas'] = ['forcas_ancestrais']
        self.saves.save(self.data)
        p = self.saves.load_save('slot_1')['progresso']
        self.assertEqual(set(p['ultimates_desbloqueadas']), set(known_ultimate_ids()))
        self.assertEqual(p['ultimate_equipada'], 'forcas_ancestrais')

    def test_mana_purifies_only_negative_effects_and_reports_actual_draws(self):
        engine = CombatEngine()
        user = engine.player
        user.energy = 0
        user.add_block(7)
        user.apply_status('aura', 3, 8)
        for effect in ('fire', 'poison', 'bleed', 'vulnerable'):
            user.apply_status(effect, 2, 2)
        user.weak_turns = 2
        engine.deck_manager.draw_pile.clear()
        engine.deck_manager.discard_pile = [engine.hand[0].copy()]
        result = create_ultimate('mana_ancestral').activate(user, engine.enemy, engine)
        self.assertEqual(result['cards_drawn'], 1)
        self.assertEqual(result['energy_restored'], 8)
        self.assertEqual(user.energy, 8)
        self.assertEqual(user.energy_max, 2)
        self.assertEqual(user.weak_turns, 0)
        self.assertEqual(set(user.statuses), {'aura'})
        self.assertEqual(user.block, 7)

    def test_rugido_breaks_shield_and_uses_strength_aura_and_vulnerability(self):
        engine = CombatEngine()
        enemy = engine.enemy
        enemy.hp = enemy.max_hp = 300
        enemy.add_block(200)
        enemy.apply_status('vulnerable', 3)
        engine.player.strength = 12
        engine.player.apply_status('aura', 3, 8)
        result = create_ultimate('rugido_da_floresta').activate(engine.player, enemy, engine)
        self.assertEqual(result['damage'], 100)  # (60+12+8) * 1.25
        self.assertEqual(enemy.block, 0)
        self.assertEqual(enemy.weak_turns, 3)

    def test_boss_weakness_lasts_three_full_rounds_and_six_actions(self):
        engine = CombatEngine()
        engine.enemy = create_guardiao_da_pedra()
        engine.enemy.hp = engine.enemy.max_hp = 999
        engine.player.hp = engine.player.max_hp = 999
        create_ultimate('rugido_da_floresta').activate(engine.player, engine.enemy, engine)
        for remaining in (3, 2, 1):
            engine.end_turn()
            for action_index in range(2):
                engine.enemy.current_action = None
                engine.enemy.intent, engine.enemy.intent_value = 'attack', 8
                hp = engine.player.hp
                engine.enemy_turn()
                self.assertEqual(hp-engine.player.hp, 6)
                self.assertEqual(engine.enemy.weak_turns, remaining)
                engine.finish_enemy_turn()
            self.assertEqual(engine.enemy.weak_turns, remaining-1)

    def test_totem_still_protects_against_the_roar(self):
        engine = CombatEngine()
        enemy = engine.enemy
        enemy.add_block(100)
        enemy.apply_status('totem', 99)
        hp = enemy.hp
        result = create_ultimate('rugido_da_floresta').activate(engine.player, enemy, engine)
        self.assertEqual(result['damage'], 0)
        self.assertEqual(result['weakness'], 0)
        self.assertEqual(enemy.hp, hp)
        self.assertEqual(enemy.block, 0)
        self.assertEqual(enemy.weak_turns, 0)
        self.assertNotIn('totem', enemy.statuses)

    def test_forcas_shield_expires_after_two_turns_while_strength_stays(self):
        engine = CombatEngine()
        user = engine.player
        create_ultimate('forcas_ancestrais').activate(user, engine.enemy, engine)
        user.begin_turn()
        self.assertEqual(user.block, 40)
        user.begin_turn()
        self.assertEqual(user.block, 0)
        self.assertEqual(user.strength, 12)


class BackpackInteractionTests(unittest.TestCase):
    def setUp(self):
        self.window = MagicMock()
        self.window.handle_window_event.return_value = False
        self.data = SaveManager()._new_data('Teste', 'preview')
        self.data['progresso']['cartas_colecao'] = list(CARD_BY_NAME)
        self.saves = MagicMock()
        self.scene = BackpackScene(MagicMock(), self.window, MagicMock(), self.saves, self.data)

    def click(self, rect):
        self.window.map_to_virtual.return_value = rect.center
        self.scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center))

    def test_ultimate_tab_equips_each_choice_without_changing_deck(self):
        slots = list(self.data['progresso']['deck_slots'])
        self.click(self.scene.ultimate_tab_rect)
        self.assertEqual(self.scene.tab, 'ultimates')
        for uid in reversed(known_ultimate_ids()):
            self.click(self.scene.ultimate_buttons[uid])
            self.assertEqual(self.data['progresso']['ultimate_equipada'], uid)
        self.assertEqual(self.data['progresso']['deck_slots'], slots)
        self.click(self.scene.deck_tab_rect)
        self.assertEqual(self.scene.tab, 'deck')

    def test_preview_then_equip_and_owned_filter(self):
        self.click(self.scene.slots[2])
        self.click(self.scene.cards['Investida'])
        self.assertEqual(self.scene.selected_card, 'Investida')
        self.assertIsNone(self.data['progresso']['deck_slots'][2])
        self.click(self.scene.equip_rect)
        self.assertEqual(self.data['progresso']['deck_slots'][2], 'Investida')
        self.data['progresso']['cartas_colecao'] = ['Soco Simples', 'Esfera Protetora', 'Investida']
        self.click(self.scene.filter_rect)
        self.assertEqual(set(self.scene.cards), set(self.data['progresso']['cartas_colecao']))
        self.assertEqual(self.scene.page_count, 1)

    def test_both_tabs_keep_buttons_inside_the_screen(self):
        screen = pygame.Rect(0, 0, 1280, 720)
        for rect in [*self.scene.slots, *self.scene.cards.values(), *self.scene.ultimate_buttons.values(),
                     self.scene.equip_rect, self.scene.clear_rect, self.scene.back_rect]:
            self.assertTrue(screen.contains(rect))


class UltimateCardArtTests(unittest.TestCase):
    def test_new_art_and_both_backpack_tabs_render(self):
        initialized = pygame.get_init()
        pygame.init()
        pygame.display.set_mode((1, 1))
        if not initialized: self.addCleanup(pygame.quit)
        assets = AssetManager()
        for uid, meta in ULTIMATE_METADATA.items():
            image = assets.get_ultimate_image(uid)
            self.assertEqual(image.get_size(), (300, 440))
            self.assertGreater(image.get_bounding_rect().width, 290)
            self.assertEqual(meta['charge_requirement'], 20)
        window = MagicMock()
        window.get_virtual_mouse_pos.return_value = (-1, -1)
        scene = BackpackScene(MagicMock(), window, assets, MagicMock(), SaveManager()._new_data('T', 'p'))
        canvas = pygame.Surface((1280, 720))
        for tab in ('deck', 'ultimates'):
            scene.tab = tab
            scene.draw(canvas)
