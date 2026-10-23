import os
import unittest

# Configura driver dummy do SDL para execução de testes em ambiente headless/CLI
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

pygame.init()
pygame.font.init()

from src.models.player import Player
from src.models.deck import DeckManager
from src.systems.combat_engine import CombatEngine
from src.systems.card_catalog import create_starting_deck
from src.scenes.cemetery_modal import CemeteryModal
from src.scenes.battle_scene import BattleScene
from src.core.window import WindowManager
from src.core.asset_manager import AssetManager
from src.core.scene_manager import SceneManager
from src.config.settings import WIDTH, HEIGHT, TITLE


class TestPlayerCemeteryRules(unittest.TestCase):
    """Regras de descarte livre sem custo e troca por turno."""

    def test_cemetery_costs_one_energy_each(self):
        self.assertEqual(Player.CEMETERY_ENERGY_COST, 1)
        player = Player("Jaum Manel", 60, energy_max=2)
        self.assertTrue(player.pay_cemetery_cost())
        self.assertEqual(player.energy, 1)
        self.assertTrue(player.pay_cemetery_cost())
        self.assertEqual(player.energy, 0)
        self.assertFalse(player.can_use_cemetery())
        self.assertFalse(player.pay_cemetery_cost())


class TestCombatEngineCemeteryIntegration(unittest.TestCase):
    def test_discard_repeats_only_while_energy_remains(self):
        events = []
        engine = CombatEngine(on_event_callback=lambda event, **kw: events.append((event, kw)))
        start = len(engine.hand)
        self.assertTrue(engine.use_cemetery(0))
        self.assertTrue(engine.use_cemetery(0))
        self.assertFalse(engine.use_cemetery(0))
        self.assertEqual(engine.energy, 0)
        self.assertEqual(len(engine.hand), start - 2)
        self.assertEqual(len(engine.discard_pile), 2)
        self.assertEqual(len([ev for ev, _ in events if ev == 'cemetery_discard']), 2)

    def test_swap_once_per_turn(self):
        engine = CombatEngine()
        initial_energy = engine.energy
        initial_hand = len(engine.hand)
        self.assertTrue(engine.swap_cemetery(0))
        self.assertFalse(engine.swap_cemetery(0))
        self.assertEqual(engine.energy, initial_energy)
        self.assertEqual(len(engine.hand), initial_hand)
        self.assertEqual(len(engine.discard_pile), 1)

    def test_cemetery_blocked_outside_player_turn(self):
        engine = CombatEngine()
        engine.state = 'enemy_turn'
        self.assertFalse(engine.use_cemetery(0))
        self.assertFalse(engine.swap_cemetery(0))

    def test_cemetery_invalid_card_index(self):
        engine = CombatEngine()
        self.assertFalse(engine.use_cemetery(-1))
        self.assertFalse(engine.use_cemetery(999))
        self.assertFalse(engine.swap_cemetery(-1))


class TestCemeteryModalUI(unittest.TestCase):
    """Testes de interface, renderização e seleção do modal do Cemitério."""

    def setUp(self):
        self.wm = WindowManager(WIDTH, HEIGHT, TITLE)
        self.am = AssetManager()
        self.sm = SceneManager()
        self.engine = CombatEngine()
        self.modal = CemeteryModal(self.sm, self.wm, self.am, self.engine)

    def test_modal_draw(self):
        """Modal deve renderizar sem exceções."""
        surface = pygame.Surface((WIDTH, HEIGHT))
        self.modal.update(16)
        self.modal.draw(surface)

    def test_modal_card_selection_and_discard_flow(self):
        """Simula seleção de carta e clique no botão de descarte dentro do modal."""
        self.sm.push_modal(self.modal)
        self.assertTrue(self.sm.has_modal)

        initial_hand_len = len(self.engine.hand)
        card_rects = self.modal._get_card_rects(initial_hand_len)
        self.assertGreater(len(card_rects), 0)

        # 1. Simula clique na primeira carta para selecionar
        first_card_center = card_rects[0].center
        click_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            pos=first_card_center,
            button=1,
        )
        self.modal.handle_event(click_event)
        self.assertEqual(self.modal.selected_index, 0)

        # 2. Simula clique no botão de descarte
        discard_btn_center = self.modal.discard_button_rect.center
        discard_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            pos=discard_btn_center,
            button=1,
        )
        self.modal.handle_event(discard_event)

        # Modal continua aberto para permitir descartes ilimitados.
        self.assertEqual(len(self.engine.hand), initial_hand_len - 1)
        self.assertEqual(len(self.engine.discard_pile), 1)
        self.assertTrue(self.sm.has_modal)
        self.assertIsNone(self.modal.selected_index)

    def test_modal_swap_once_and_stays_open(self):
        self.sm.push_modal(self.modal)
        first = self.modal._get_card_rects(len(self.engine.hand))[0]
        self.modal.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                                   pos=first.center, button=1))
        start = len(self.engine.hand)
        self.modal.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                                   pos=self.modal.swap_button_rect.center, button=1))
        self.assertTrue(self.engine.cemetery_swap_used)
        self.assertEqual(len(self.engine.hand), start)
        self.assertTrue(self.sm.has_modal)
        self.assertIsNone(self.modal.selected_index)

    def test_modal_close_via_esc(self):
        """Pressionar ESC dentro do modal deve fechar o modal."""
        self.sm.push_modal(self.modal)
        self.assertTrue(self.sm.has_modal)

        esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        self.modal.handle_event(esc_event)
        self.assertFalse(self.sm.has_modal)

    def test_modal_close_via_button(self):
        """Clicar no botão Fechar deve fechar o modal."""
        self.sm.push_modal(self.modal)
        self.assertTrue(self.sm.has_modal)

        close_btn_center = self.modal.close_button_rect.center
        click_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            pos=close_btn_center,
            button=1,
        )
        self.modal.handle_event(click_event)
        self.assertFalse(self.sm.has_modal)


class TestBattleSceneCemeteryIntegration(unittest.TestCase):
    """Testes integrados do botão e acesso ao Cemitério na BattleScene."""

    def test_battle_scene_cemetery_button_opens_modal(self):
        """Clicar no botão Cemitério na BattleScene deve abrir o CemeteryModal."""
        wm = WindowManager(WIDTH, HEIGHT, TITLE)
        am = AssetManager()
        sm = SceneManager()
        scene = BattleScene(sm, wm, am)

        sm.change_scene(scene)
        self.assertFalse(sm.has_modal)

        # Simula clique no botão do Cemitério
        click_cemetery = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            pos=scene.cemetery_button_rect.center,
            button=1,
        )
        sm.handle_event(click_cemetery)

        self.assertTrue(sm.has_modal)
        self.assertIsInstance(sm.modal_stack[-1], CemeteryModal)

    def test_battle_scene_c_key_opens_modal(self):
        """Pressionar a tecla C durante o turno do jogador deve abrir o CemeteryModal."""
        wm = WindowManager(WIDTH, HEIGHT, TITLE)
        am = AssetManager()
        sm = SceneManager()
        scene = BattleScene(sm, wm, am)

        sm.change_scene(scene)
        self.assertFalse(sm.has_modal)

        key_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c)
        sm.handle_event(key_event)

        self.assertTrue(sm.has_modal)
        self.assertIsInstance(sm.modal_stack[-1], CemeteryModal)


if __name__ == "__main__":
    unittest.main()
