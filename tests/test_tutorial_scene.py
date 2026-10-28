"""Testes unitários e de integração da fase de Tutorial guiado."""
import os
import tempfile
import unittest
from unittest.mock import MagicMock

import pygame

# Inicialização headless do pygame para execução dos testes
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((1280, 720))

from src.config.settings import WIDTH, HEIGHT
from src.core.asset_manager import AssetManager
from src.core.window import WindowManager
from src.models.action import Action
from src.models.deck import DeckManager
from src.models.enemy import Enemy
from src.models.player import Player
from src.scenes.map_scene import MapScene
from src.scenes.save_selection_scene import SaveSelectionScene
from src.scenes.tutorial_scene import TutorialScene
from src.systems.combat_engine import CombatEngine
from src.systems.save_manager import SaveManager
from src.ui.tutorial_overlay import TutorialOverlay, TutorialStep, draw_tutorial_arrow, draw_tutorial_spotlight


class TestTutorialOverlay(unittest.TestCase):
    """Testa a lógica de passos, navegação e conteúdos do guia do tutorial."""

    def setUp(self):
        self.completed = False

        def on_done():
            self.completed = True

        dummy_steps = [
            TutorialStep(id="s1", title="Passo 1", subtitle="Sub 1", lines=["Linha 1"], bubble_pos=(300, 100)),
            TutorialStep(id="s2", title="Passo 2", subtitle="Sub 2", lines=["Linha 2"], bubble_pos=(500, 200)),
            TutorialStep(id="s3", title="Passo 3", subtitle="Sub 3", lines=["Linha 3"], bubble_pos=(200, 400)),
        ]
        self.overlay = TutorialOverlay(dummy_steps, on_complete=on_done)

    def test_initial_state(self):
        self.assertTrue(self.overlay.is_active)
        self.assertEqual(self.overlay.step_index, 0)
        self.assertEqual(self.overlay.current_step.id, "s1")

    def test_advance_and_fluid_transition(self):
        # Inicia com fade-in
        self.assertEqual(self.overlay.anim_state, "in")
        self.overlay.update(250)  # Conclui o fade-in
        self.assertEqual(self.overlay.anim_state, "active")
        self.assertEqual(self.overlay.current_alpha, 255)

        # Clicar para avançar aciona transição de saída (out)
        self.overlay.advance()
        self.assertEqual(self.overlay.anim_state, "out")

        # Conclui o tempo de transição (130ms)
        self.overlay.update(130)
        self.assertEqual(self.overlay.step_index, 1)
        self.assertEqual(self.overlay.current_step.id, "s2")
        self.assertEqual(self.overlay.anim_state, "in")

    def test_skip_finishes_overlay(self):
        self.overlay.skip()
        self.assertEqual(self.overlay.anim_state, "closing")
        self.overlay.update(150)
        self.assertFalse(self.overlay.is_active)
        self.assertTrue(self.completed)

    def test_screen_click_advances(self):
        # Clique em qualquer ponto da tela avança
        click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(600, 300))
        handled = self.overlay.handle_event(click_event, (600, 300))
        self.assertTrue(handled)
        self.assertEqual(self.overlay.anim_state, "out")

    def test_draw_helpers_do_not_crash(self):
        surface = pygame.Surface((WIDTH, HEIGHT))
        draw_tutorial_arrow(surface, (100, 100), (200, 200), pulse=1.0, alpha=255)
        draw_tutorial_spotlight(surface, pygame.Rect(50, 50, 120, 80), pulse=0.5, alpha=255)


class TestTutorialSceneIntegration(unittest.TestCase):
    """Testa a integração da cena de tutorial com o motor de combate e persistência."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.save_manager = SaveManager(saves_dir=self._tmp.name)
        self.save_data = self.save_manager.create_save("slot_1", display_name="Jornada 01")

        self.scene_manager = MagicMock()
        self.window_manager = WindowManager()
        self.asset_manager = AssetManager()

        self.tutorial_scene = TutorialScene(
            self.scene_manager,
            self.window_manager,
            self.asset_manager,
            save_manager=self.save_manager,
            save_data=self.save_data,
        )

    def tearDown(self):
        self._tmp.cleanup()

    def test_floating_bubbles_positioned_near_targets(self):
        """Garante que os balões não estão todos no centro e ficam próximos aos elementos."""
        bubble_positions = [step.bubble_pos for step in self.tutorial_scene.overlay.steps]
        # Pelo menos 4 posições diferentes
        unique_positions = set(bubble_positions)
        self.assertGreaterEqual(len(unique_positions), 5)

        # Passo do HP deve ter balão próximo ao topo esquerdo
        hp_step = next(s for s in self.tutorial_scene.overlay.steps if s.id == "hp")
        self.assertLess(hp_step.bubble_pos[1], 100)

        # Passo do Cemitério deve ter balão na metade inferior esquerda
        cem_step = next(s for s in self.tutorial_scene.overlay.steps if s.id == "cemetery")
        self.assertGreater(cem_step.bubble_pos[1], 400)
        self.assertLess(cem_step.bubble_pos[0], 250)

    def test_tutorial_required_elements_covered_in_steps(self):
        """Verifica se todos os tópicos exigidos pelo usuário estão presentes nos passos."""
        step_ids = [step.id for step in self.tutorial_scene.overlay.steps]
        required_topics = ["intro", "hp", "energy", "cards", "stats", "intent", "ultimate", "cemetery", "fight"]
        for topic in required_topics:
            self.assertIn(topic, step_ids)

        all_text = " ".join(
            " ".join(step.lines) for step in self.tutorial_scene.overlay.steps
        ).lower()

        self.assertIn("energia", all_text)
        self.assertIn("jogar cartas", all_text)
        self.assertIn("escudo absorve dano", all_text)
        self.assertIn("força aumenta o dano", all_text)
        self.assertIn("cemitério", all_text)
        self.assertIn("descarte", all_text)

    def test_tutorial_enemy_setup(self):
        """O inimigo de tutorial é o Slime com ações didáticas de ataque e defesa."""
        enemy = self.tutorial_scene.engine.enemy
        self.assertEqual(enemy.name, "Slime")
        self.assertEqual(enemy.hp, 20)
        action_types = [a.action_type for a in enemy.actions]
        self.assertIn("attack", action_types)
        self.assertIn("defend", action_types)
        self.assertEqual(enemy.intent, "attack")

    def test_tutorial_hand_setup(self):
        """A mão inicial do jogador possui cartas fundamentais de ataque e defesa."""
        hand_names = [c.name for c in self.tutorial_scene.engine.hand]
        self.assertIn("Soco Simples", hand_names)
        self.assertIn("Esfera Protetora", hand_names)

    def test_overlay_navigation_via_screen_click(self):
        """Qualquer clique na tela faz o tutorial avançar."""
        self.assertEqual(self.tutorial_scene.overlay.step_index, 0)
        click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(500, 400))
        self.tutorial_scene.handle_event(click_event)
        self.assertEqual(self.tutorial_scene.overlay.anim_state, "out")

        # Avança o tempo de transição
        self.tutorial_scene.overlay.update(130)
        self.assertEqual(self.tutorial_scene.overlay.step_index, 1)

    def test_tutorial_cannot_complete_before_victory(self):
        self.tutorial_scene._complete_tutorial()
        self.assertFalse(self.save_manager.load_save("slot_1")["progresso"]["tutorial_concluido"])
        self.scene_manager.change_scene.assert_not_called()

    def test_tutorial_completion_is_once_only(self):
        self.tutorial_scene.engine.enemy.take_damage(999)
        self.tutorial_scene.engine._on_enemy_defeated()
        self.tutorial_scene._complete_tutorial()
        self.tutorial_scene._complete_tutorial()
        self.assertTrue(self.save_manager.load_save("slot_1")["progresso"]["tutorial_concluido"])
        self.assertEqual(self.save_manager.load_save("slot_1")["progresso"]["moedas"], 30)
        self.assertEqual(self.scene_manager.change_scene.call_count, 1)

    def test_victory_and_completion_flow(self):
        """Derrotar o inimigo conclui a fase, atualiza save e transiciona para o mapa."""
        # Fecha overlay para liberar o combate direto
        self.tutorial_scene.overlay.finish()
        self.tutorial_scene.overlay.update(200)
        self.assertFalse(self.tutorial_scene.overlay.is_active)

        # Causa dano letal ao Slime
        self.tutorial_scene.engine.enemy.take_damage(999)
        self.tutorial_scene.engine._on_enemy_defeated()

        self.assertEqual(self.tutorial_scene.engine.state, "victory")

        # Dispara a conclusão do tutorial
        self.tutorial_scene._complete_tutorial()

        # Verifica se o save foi marcado com tutorial_concluido = True
        loaded = self.save_manager.load_save("slot_1")
        self.assertTrue(loaded["progresso"]["tutorial_concluido"])
        self.assertGreaterEqual(loaded["progresso"]["moedas"], 30)

        # Verifica se transicionou para MapScene
        self.scene_manager.change_scene.assert_called()
        new_scene = self.scene_manager.change_scene.call_args[0][0]
        self.assertIsInstance(new_scene, MapScene)


class TestSaveSelectionRouting(unittest.TestCase):
    """Testa se a tela de seleção de jornada direciona novos saves ao TutorialScene."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.save_manager = SaveManager(saves_dir=self._tmp.name)
        self.scene_manager = MagicMock()
        self.window_manager = WindowManager()
        self.asset_manager = AssetManager()

    def tearDown(self):
        self._tmp.cleanup()

    def test_empty_slot_routes_to_tutorial(self):
        selection_scene = SaveSelectionScene(
            self.scene_manager,
            self.window_manager,
            self.asset_manager,
            save_manager=self.save_manager,
        )
        # Seleciona o primeiro slot (vazio)
        selection_scene._select(0)

        self.scene_manager.change_scene.assert_called()
        target_scene = self.scene_manager.change_scene.call_args[0][0]
        self.assertIsInstance(target_scene, TutorialScene)

    def test_existing_save_without_tutorial_flag_does_not_restart_training(self):
        data = self.save_manager.create_save("slot_1")
        del data["progresso"]["tutorial_concluido"]
        self.save_manager.save(data)
        self.assertTrue(self.save_manager.load_save("slot_1")["progresso"]["tutorial_concluido"])
        scene = SaveSelectionScene(self.scene_manager, self.window_manager,
                                   self.asset_manager, save_manager=self.save_manager)
        scene._select(0)
        target = self.scene_manager.change_scene.call_args[0][0]
        self.assertIsInstance(target, MapScene)

    def test_unfinished_tutorial_routes_back_to_training(self):
        data = self.save_manager.create_save("slot_1")
        self.assertFalse(data["progresso"]["tutorial_concluido"])
        scene = SaveSelectionScene(self.scene_manager, self.window_manager,
                                   self.asset_manager, save_manager=self.save_manager)
        scene._select(0)
        target = self.scene_manager.change_scene.call_args[0][0]
        self.assertIsInstance(target, TutorialScene)

    def test_completed_save_routes_to_map(self):
        data = self.save_manager.create_save("slot_1", display_name="Gabriel")
        data["progresso"]["tutorial_concluido"] = True
        self.save_manager.save(data)

        selection_scene = SaveSelectionScene(
            self.scene_manager,
            self.window_manager,
            self.asset_manager,
            save_manager=self.save_manager,
        )
        selection_scene._select(0)

        self.scene_manager.change_scene.assert_called()
        target_scene = self.scene_manager.change_scene.call_args[0][0]
        self.assertIsInstance(target_scene, MapScene)


if __name__ == "__main__":
    unittest.main()
