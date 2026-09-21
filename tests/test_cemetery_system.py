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
    """Testes unitários focados nas regras de energia e Cemitério no modelo Player."""

    def test_cemetery_energy_cost_constant(self):
        """O custo de energia do Cemitério deve ser definido como 1."""
        self.assertEqual(Player.CEMETERY_ENERGY_COST, 1)

    def test_can_use_cemetery_verification(self):
        """can_use_cemetery deve retornar True apenas se o jogador tiver pelo menos 1 de energia."""
        player = Player("Herói", 60, energy_max=2)
        self.assertTrue(player.can_use_cemetery())

        player.use_energy(1)  # sobra 1
        self.assertTrue(player.can_use_cemetery())

        player.use_energy(1)  # sobra 0
        self.assertFalse(player.can_use_cemetery())

    def test_pay_cemetery_cost(self):
        """pay_cemetery_cost deve consumir exatamente 1 de energia se houver saldo."""
        player = Player("Herói", 60, energy_max=2)
        self.assertEqual(player.energy, 2)

        paid = player.pay_cemetery_cost()
        self.assertTrue(paid)
        self.assertEqual(player.energy, 1)

        paid = player.pay_cemetery_cost()
        self.assertTrue(paid)
        self.assertEqual(player.energy, 0)

        # Tentativa com saldo zero deve falhar
        paid = player.pay_cemetery_cost()
        self.assertFalse(paid)
        self.assertEqual(player.energy, 0)


class TestCombatEngineCemeteryIntegration(unittest.TestCase):
    """Testes da lógica de descarte e movimentação de cartas do Cemitério no CombatEngine."""

    def test_cemetery_discards_card_and_consumes_one_energy(self):
        """use_cemetery deve consumir 1 energia, remover carta da mão e mover para o descarte."""
        events = []
        engine = CombatEngine(on_event_callback=lambda evt, **kw: events.append((evt, kw)))

        self.assertEqual(engine.energy, 2)
        initial_hand_count = len(engine.hand)
        initial_discard_count = len(engine.discard_pile)
        self.assertGreater(initial_hand_count, 0)

        target_card = engine.hand[0]

        # Executa descarte no Cemitério
        success = engine.use_cemetery(0)
        self.assertTrue(success)

        # Energia deve ter sido reduzida em 1
        self.assertEqual(engine.energy, 1)

        # Mão deve ter diminuído em 1 e descarte aumentado em 1
        self.assertEqual(len(engine.hand), initial_hand_count - 1)
        self.assertEqual(len(engine.discard_pile), initial_discard_count + 1)
        self.assertEqual(engine.discard_pile[-1].name, target_card.name)

        # Evento visual cemetery_discard deve ter sido disparado
        discard_events = [e for e in events if e[0] == "cemetery_discard"]
        self.assertEqual(len(discard_events), 1)
        self.assertEqual(discard_events[0][1]["card"].name, target_card.name)

    def test_cemetery_blocked_when_insufficient_energy(self):
        """use_cemetery deve ser bloqueado quando o jogador não tiver energia suficiente."""
        engine = CombatEngine()
        # Consome toda a energia
        engine.player.use_energy(engine.energy)
        self.assertEqual(engine.energy, 0)

        initial_hand_count = len(engine.hand)
        initial_discard_count = len(engine.discard_pile)

        success = engine.use_cemetery(0)
        self.assertFalse(success)
        self.assertIn("Energia insuficiente", engine.message)

        # Nenhuma carta deve ser movida
        self.assertEqual(len(engine.hand), initial_hand_count)
        self.assertEqual(len(engine.discard_pile), initial_discard_count)

    def test_cemetery_blocked_outside_player_turn(self):
        """Cemitério só pode ser acionado durante o turno do jogador."""
        engine = CombatEngine()
        engine.state = "enemy_turn"

        success = engine.use_cemetery(0)
        self.assertFalse(success)
        self.assertIn("turno", engine.message.lower())

    def test_cemetery_invalid_card_index(self):
        """use_cemetery deve retornar False se o índice da carta for inválido."""
        engine = CombatEngine()
        self.assertFalse(engine.use_cemetery(-1))
        self.assertFalse(engine.use_cemetery(999))


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

        # O modal deve ter processado o descarte e fechado (pop_modal)
        self.assertEqual(len(self.engine.hand), initial_hand_len - 1)
        self.assertEqual(len(self.engine.discard_pile), 1)
        self.assertFalse(self.sm.has_modal)

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
