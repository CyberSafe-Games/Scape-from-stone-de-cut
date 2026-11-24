"""Contrato das cartas Ultimate, energia real e efeitos completos de combate."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

from src.models.effects.ultimate_effect import ULTIMATE_METADATA
from src.systems.combat_engine import CombatEngine
from src.ui.ultimate_card_art import build_ultimate_card

ROOT = Path(__file__).resolve().parents[1]


class UltimateCardTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()
        cls.manifest = json.loads((ROOT / 'assets/ultimates/art_manifest.json').read_text(encoding='utf-8'))

    def test_all_three_match_lv2_geometry_and_have_transparent_exterior(self):
        regular = pygame.image.load(str(ROOT / 'assets/cards/lv2/esfera_protetora.png'))
        regular_manifest = json.loads((ROOT / 'assets/cards/art_manifest.json').read_text(encoding='utf-8'))
        standard = regular_manifest['cards']['esfera_protetora:2']
        for uid, meta in ULTIMATE_METADATA.items():
            with self.subTest(ultimate=uid):
                layout = self.manifest['cards'][uid]
                art = pygame.image.load(str(ROOT / 'assets/ultimates' / layout['file']))
                self.assertEqual(art.get_size(), regular.get_size())
                self.assertEqual(layout['cost_center'], standard['cost_center'])
                self.assertLessEqual(abs(layout['cost_radius'] - standard['cost_radius']), 1)
                for point in [(0, 0), (art.get_width()-1, 0), (0, art.get_height()-1)]:
                    self.assertEqual(art.get_at(point).a, 0)
                self.assertEqual(layout['description'], meta['description'])
                self.assertEqual(meta['energy_cost'], 2)

    def test_dynamic_cost_replaces_only_diamond_and_footer_without_moving_border(self):
        import numpy as np
        for uid, meta in ULTIMATE_METADATA.items():
            with self.subTest(ultimate=uid):
                layout = self.manifest['cards'][uid]
                art = pygame.image.load(str(ROOT / 'assets/ultimates' / layout['file']))
                default = build_ultimate_card(art, meta, SimpleNamespace(), layout)
                changed = build_ultimate_card(art, dict(meta, energy_cost=7), SimpleNamespace(), layout)
                repeat = build_ultimate_card(changed, dict(meta, energy_cost=7), SimpleNamespace(), layout)
                self.assertEqual(pygame.image.tobytes(changed, 'RGBA'), pygame.image.tobytes(repeat, 'RGBA'))
                allowed = pygame.Surface(art.get_size())
                pygame.draw.polygon(allowed, 'white', layout['cost_polygon'])
                pygame.draw.rect(allowed, 'white', layout['footer_rect'])
                diff = np.any(pygame.surfarray.array3d(default) != pygame.surfarray.array3d(changed), axis=2)
                mask = pygame.surfarray.array3d(allowed)[:, :, 0] > 0
                self.assertTrue(np.any(diff))
                self.assertFalse(np.any(diff & ~mask))
                footer = pygame.Rect(layout['footer_rect'])
                self.assertNotEqual(pygame.image.tobytes(default.subsurface(footer), 'RGBA'),
                                    pygame.image.tobytes(changed.subsurface(footer), 'RGBA'))


class UltimateCompleteEffectsTests(unittest.TestCase):
    def ready(self, uid):
        engine = CombatEngine()
        engine.equip_ultimate(uid)
        engine.player.energy = 2
        engine.player.ultimate_charge = 20
        return engine

    def test_mana_cleans_all_negative_states_and_keeps_benefits(self):
        engine = self.ready('mana_ancestral')
        user = engine.player
        user.add_block(11)
        for effect in user.NEGATIVE_STATUSES:
            user.apply_status(effect, 2, 2)
        user.attack_lock_pending = user.attack_lock_turns = 2
        user.strength = 7
        user.apply_status('aura', 3, 6)
        self.assertTrue(engine.activate_ultimate())
        self.assertEqual(user.energy, 8)
        self.assertFalse(user.NEGATIVE_STATUSES.intersection(user.statuses))
        self.assertEqual((user.poison_stacks, user.poison_turns, user.bleed_stacks,
                          user.bleed_turns, user.weak_turns, user.attack_lock_turns,
                          user.attack_lock_pending), (0, 0, 0, 0, 0, 0, 0))
        self.assertEqual((user.strength, user.block), (7, 11))
        self.assertIn('aura', user.statuses)

    def test_forcas_strength_outlasts_two_turn_shield(self):
        engine = self.ready('forcas_ancestrais')
        self.assertTrue(engine.activate_ultimate())
        self.assertEqual((engine.energy, engine.player.strength, engine.player.block_turns), (0, 12, 2))
        engine.player.begin_turn()
        self.assertEqual(engine.player.block, 40)
        engine.player.begin_turn()
        self.assertEqual((engine.player.block, engine.player.strength), (0, 12))
        engine.player.reset_combat_effects()
        self.assertEqual(engine.player.strength, 0)

    def test_rugido_destroys_shield_before_damage_and_registers_weakness(self):
        engine = self.ready('rugido_da_floresta')
        engine.enemy.hp = engine.enemy.max_hp = 200
        engine.enemy.add_block(150)
        self.assertTrue(engine.activate_ultimate())
        self.assertEqual((engine.enemy.block, engine.enemy.hp, engine.energy), (0, 140, 0))
        self.assertEqual(engine.enemy.statuses['weak']['turns'], 3)
        self.assertEqual(engine.enemy.weak_turns, 3)

    def test_each_ultimate_consumes_two_energy_once_and_cannot_repeat_without_charge(self):
        from copy import deepcopy
        for uid in ULTIMATE_METADATA:
            with self.subTest(ultimate=uid):
                engine = self.ready(uid)
                engine.enemy.hp = engine.enemy.max_hp = 500
                self.assertTrue(engine.activate_ultimate())
                self.assertEqual(engine.energy, 8 if uid == 'mana_ancestral' else 0)
                self.assertEqual(engine.player.ultimate_charge, 0)
                # Energia suficiente não substitui a recarga necessária.
                engine.player.energy = 8
                before = (engine.enemy.hp, engine.player.strength, engine.player.block,
                          deepcopy(engine.player.statuses), deepcopy(engine.enemy.statuses))
                self.assertFalse(engine.activate_ultimate())
                after = (engine.enemy.hp, engine.player.strength, engine.player.block,
                         engine.player.statuses, engine.enemy.statuses)
                self.assertEqual(after, before)


if __name__ == '__main__':
    unittest.main()
