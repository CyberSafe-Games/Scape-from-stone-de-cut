import unittest
from unittest.mock import patch

import pygame
from src.models.action import Action
from src.models.enemy import Enemy
from src.systems.card_catalog import CARD_BY_NAME, CARD_POOL
from src.systems.card_definitions import ADDITIONAL_CARD_SPECS
from src.systems.combat_engine import CombatEngine
from src.ui.card_view import CardView


class ExtendedCardTests(unittest.TestCase):
    def engine(self):
        engine = CombatEngine()
        harmless = Action('Ataque', damage=0)
        engine.enemy = Enemy('Alvo', 500, actions=[harmless])
        engine.enemy.set_intent('attack', 0, harmless)
        engine.player.energy_max = 8
        engine.player.energy = 8
        return engine

    def play(self, engine, name, energy=8):
        engine.deck_manager.hand = [CARD_BY_NAME[name].copy()]
        engine.player.energy = energy
        self.assertTrue(engine.play_card(0))

    def test_txt_cards_are_registered_without_replacing_existing_soco(self):
        self.assertEqual(len(ADDITIONAL_CARD_SPECS), 75)
        self.assertEqual(len(CARD_POOL), 95)
        self.assertEqual(CARD_BY_NAME['Soco Simples'].cost, 1)
        self.assertEqual(CARD_BY_NAME['Soco MUITO Simples'].cost, 0)
        self.assertEqual(CARD_BY_NAME['Soco MUITO Simples'].value, 3)

    def test_artless_card_fallback_displays_cost_name_and_effect(self):
        pygame.font.init()
        font = pygame.font.Font(None, 20)
        rendered = []

        class Assets:
            small_font = font

            def get_card_image(self, name):
                return None

        class RecordingFont:
            def size(self, text):
                return font.size(text)

            def get_linesize(self):
                return font.get_linesize()

            def render(self, text, antialias, color):
                rendered.append(str(text))
                return font.render(text, antialias, color)

        assets = Assets()
        assets.small_font = RecordingFont()
        card = CARD_BY_NAME['Proteção']
        surface = pygame.Surface((150, 258), pygame.SRCALPHA)
        CardView.draw_card(surface, surface.get_rect(), card, assets)
        self.assertIn('2 E', rendered)
        self.assertTrue(any('Receba' in line for line in rendered))
        self.assertTrue(any('escudo' in line.lower() for line in rendered))

    def test_poison_stacks_tick_and_purge_deals_damage_per_stack(self):
        engine = self.engine()
        self.play(engine, 'Peçonha Concentrada')
        self.assertEqual(engine.enemy.statuses['poison']['potency'], 7)
        engine.enemy.end_turn_statuses()
        self.assertEqual(engine.enemy.hp, 493)

        engine = self.engine()
        engine.enemy.add_stacks('poison', 4)
        self.play(engine, 'Purga da Jararaca')
        self.assertEqual(engine.enemy.hp, 492)
        self.assertNotIn('poison', engine.enemy.statuses)

    def test_multihit_bonus_and_temporary_strength(self):
        engine = self.engine()
        self.play(engine, 'Combo do Javali')
        self.assertEqual(engine.enemy.hp, 494)
        self.assertEqual(engine.player.attack_bonus, 2)
        self.play(engine, 'Três Golpes da Onça')
        self.assertEqual(engine.enemy.hp, 476)

    def test_temporary_strength_layers_expire_independently(self):
        engine = self.engine()
        engine.player.apply_strength(2, 2)
        self.play(engine, 'Fúria Multiplicada')
        self.assertEqual(engine.player.attack_bonus, 4)
        engine._tick_statuses(engine.player)
        self.assertEqual(engine.player.attack_bonus, 2)
        engine._tick_statuses(engine.player)
        self.assertEqual(engine.player.attack_bonus, 0)

    def test_immunity_and_attack_lock(self):
        engine = self.engine()
        self.play(engine, 'Banho de Ervas')
        engine.player.add_stacks('poison', 3)
        self.assertNotIn('poison', engine.player.statuses)
        self.assertIn('debuff_immunity', engine.player.statuses)

        self.play(engine, 'Bênção da Mãe-Terra')
        engine.end_turn()
        engine.enemy_turn()
        engine.finish_enemy_turn()
        engine.deck_manager.hand = [CARD_BY_NAME['Marretada'].copy()]
        engine.player.energy = 8
        self.assertFalse(engine.play_card(0))
        self.assertEqual(engine.energy, 8)

    def test_burn_doubling_and_final_attack_lock(self):
        engine = self.engine()
        engine.enemy.add_stacks('burn', 6)
        self.play(engine, 'Sopro de Boitatá')
        self.assertEqual(engine.enemy.statuses['burn']['potency'], 12)

        engine = self.engine()
        for name, amount in (('poison', 6), ('bleed', 3), ('burn', 4)):
            engine.enemy.add_stacks(name, amount)
        self.play(engine, 'Juízo Final da Floresta')
        self.assertEqual(engine.enemy.statuses['poison']['potency'], 12)
        self.assertEqual(engine.enemy.statuses['bleed']['potency'], 6)
        self.assertEqual(engine.enemy.statuses['burn']['potency'], 8)
        engine.deck_manager.hand = [CARD_BY_NAME['Marretada'].copy()]
        engine.player.energy = 8
        self.assertFalse(engine.play_card(0))

    def test_stun_skips_enemy_turn_and_totem_triggers(self):
        engine = self.engine()
        with patch('src.models.effects.extended_card_effect.random.randint', return_value=1):
            self.play(engine, 'Pancada de Tacape')
        self.assertIn('stun', engine.enemy.statuses)
        before = engine.player.hp
        engine.end_turn()
        engine.enemy_turn()
        self.assertEqual(engine.player.hp, before)

        engine = self.engine()
        self.play(engine, 'Totem da Serpente')
        engine.enemy.current_action = Action('Mordida', damage=5)
        engine.enemy.set_intent('attack', 5, engine.enemy.current_action)
        engine.end_turn()
        engine.enemy_turn()
        self.assertEqual(engine.enemy.statuses['poison']['potency'], 5)

        engine = self.engine()
        engine.player.hp -= 10
        self.play(engine, 'Totem da Cura')
        engine.enemy.current_action = Action('Mordida', damage=5)
        engine.enemy.set_intent('attack', 5, engine.enemy.current_action)
        engine.end_turn()
        engine.enemy_turn()
        self.assertEqual(engine.player.hp, engine.player.max_hp - 2)

    def test_draw_and_energy_restore_effects(self):
        engine = self.engine()
        engine.deck_manager.draw_pile = [
            CARD_BY_NAME['Soco Simples'].copy(),
            CARD_BY_NAME['Esfera Protetora'].copy(),
        ]
        self.play(engine, 'Bisbilhotar')
        self.assertEqual(len(engine.hand), 2)

        engine = self.engine()
        self.play(engine, 'Pacto Doloroso', energy=5)
        self.assertEqual(engine.energy, 5)
        self.assertEqual(engine.player.hp, 56)

    def test_no_heal_blocks_enemy_healing(self):
        engine = self.engine()
        self.play(engine, 'Ferida que Não Fecha')
        engine.enemy.hp = 300
        heal = Action('Cura', action_type='heal', defense=20)
        engine.enemy.current_action = heal
        engine.enemy.set_intent('heal', 0, heal)
        engine.end_turn()
        engine.enemy_turn()
        self.assertEqual(engine.enemy.hp, 300)


if __name__ == '__main__':
    unittest.main()
