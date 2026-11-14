"""Testes isolados da cena de cutscenes, sem alterar progressão ou saves."""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.config.cutscenes import INTRO_CUTSCENE, POST_TUTORIAL_CUTSCENE
from src.config.settings import HEIGHT, WIDTH
from src.scenes.cutscene_scene import CutsceneScene


class CutsceneSceneTests(unittest.TestCase):
    """Valida navegação, renderização e encerramento isoladamente."""

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.assets_patch = patch(
            "src.scenes.cutscene_scene.ASSETS_DIR", self.temp_dir.name
        )
        self.assets_patch.start()
        self.addCleanup(self.assets_patch.stop)
        self.manager = Mock()
        self.manager.current_scene = None
        self.window = Mock()
        self.window.handle_window_event.return_value = False
        self.assets = Mock()
        self.assets.get_font.side_effect = lambda size: pygame.font.Font(None, 32)
        self.destination = object()
        self.factory = Mock(return_value=self.destination)
        self.callback = Mock()
        self.surface = pygame.Surface((WIDTH, HEIGHT))

    def create_scene(self, entries=None):
        if entries is None:
            entries = [
                {"image": "quadro_1.png", "text": "", "position": "bottom"},
                {"image": "quadro_2.png", "text": "", "position": "bottom"},
            ]
        return CutsceneScene(
            self.manager, self.window, self.assets,
            entries, self.factory, self.callback,
        )

    @staticmethod
    def send_key(scene, key, repeat=False):
        scene.handle_event(pygame.event.Event(
            pygame.KEYDOWN, {"key": key, "repeat": repeat}
        ))

    def test_configuracao_tem_cinco_quadros_e_pos_tutorial(self):
        self.assertEqual(len(INTRO_CUTSCENE), 5)
        self.assertEqual(len(POST_TUTORIAL_CUTSCENE), 1)
        self.assertEqual(
            [item["image"] for item in INTRO_CUTSCENE],
            [f"cutscenes/intro_{index:02d}.png" for index in range(1, 6)],
        )
        self.assertEqual(
            POST_TUTORIAL_CUTSCENE[0]["image"],
            "cutscenes/pos_tutorial.png",
        )

    def test_avanco_manual_ignora_entrada_durante_transicao(self):
        scene = self.create_scene()
        self.send_key(scene, pygame.K_SPACE)
        self.assertEqual(scene.index, 0)
        scene.update(0.5)
        self.send_key(scene, pygame.K_SPACE, repeat=True)
        self.assertEqual(scene.index, 0)
        self.send_key(scene, pygame.K_SPACE)
        self.assertEqual(scene.index, 1)
        self.assertEqual(scene._phase, "crossfade")
        self.send_key(scene, pygame.K_RETURN)
        self.assertEqual(scene.index, 1)
        scene.update(0.5)
        self.assertEqual(scene._phase, "idle")
        self.assertEqual(self.callback.call_count, 0)

    def test_ultimo_quadro_encerra_so_apos_fade(self):
        scene = self.create_scene([{"image": "um.png", "text": ""}])
        scene.update(0.5)
        scene.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (20, 20)}
        ))
        self.assertEqual(scene._phase, "exit")
        self.callback.assert_not_called()
        scene.update(0.5)
        self.callback.assert_called_once_with()
        self.factory.assert_called_once_with()
        self.manager.change_scene.assert_called_once_with(self.destination)
        scene.update(0.5)
        self.callback.assert_called_once_with()

    def test_esc_pula_e_finaliza_uma_unica_vez(self):
        scene = self.create_scene()
        self.send_key(scene, pygame.K_ESCAPE)
        self.send_key(scene, pygame.K_ESCAPE)
        scene.update(1)
        self.callback.assert_called_once_with()
        self.manager.change_scene.assert_called_once_with(self.destination)

    def test_lista_vazia_finaliza_sem_exibir_quadro(self):
        scene = self.create_scene([])
        scene.update(0)
        self.callback.assert_called_once_with()
        self.manager.change_scene.assert_called_once_with(self.destination)
        scene.draw(self.surface)

    def test_imagem_ausente_nao_interrompe_renderizacao(self):
        with self.assertLogs("src.scenes.cutscene_scene", level="WARNING"):
            scene = self.create_scene([
                {"image": "inexistente.png", "text": "Texto de teste", "position": "top"}
            ])
        scene.update(0.5)
        scene.draw(self.surface)
        self.assertEqual(scene._current_layer.get_size(), (WIDTH, HEIGHT))

    def test_imagem_e_escalada_uma_vez_por_quadro(self):
        image_path = os.path.join(self.temp_dir.name, "quadro.png")
        pygame.image.save(pygame.Surface((320, 240)), image_path)
        with patch(
            "src.scenes.cutscene_scene.pygame.transform.smoothscale",
            wraps=pygame.transform.smoothscale,
        ) as scale:
            scene = self.create_scene([{"image": "quadro.png", "text": ""}])
            self.assertEqual(scale.call_count, 1)
            self.assertEqual(scale.call_args.args[1], (1440, 1080))
            scene.update(0.5)
            scene.draw(self.surface)
            scene.draw(self.surface)
            self.assertEqual(scale.call_count, 1)

    def test_quantidade_de_quadros_nao_e_fixa(self):
        entries = [
            {"image": f"quadro_{index}.png", "text": ""}
            for index in range(3)
        ]
        scene = self.create_scene(entries)
        scene.update(0.5)
        for expected_index in (1, 2):
            self.send_key(scene, pygame.K_RETURN)
            self.assertEqual(scene.index, expected_index)
            scene.update(0.5)
        self.send_key(scene, pygame.K_RETURN)
        scene.update(0.5)
        self.callback.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
