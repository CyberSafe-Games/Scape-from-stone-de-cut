"""Verifica o destino do tutorial sem carregar o restante do jogo."""

import ast
from pathlib import Path
import unittest
from unittest.mock import Mock


class SaveError(Exception):
    """Erro simulado de gravação."""


class FakeMapScene:
    """Cena de mapa simulada."""

    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs


class FakeCutsceneScene:
    """Cena de cutscene simulada."""

    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs

    def finish(self):
        self.kwargs['on_finish']()
        return self.kwargs['next_scene_factory']()


class TestPostTutorial(unittest.TestCase):
    """Testa a conclusão, persistência e prevenção de duplicidade."""

    @classmethod
    def setUpClass(cls):
        source = Path('src/scenes/tutorial_scene.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        tutorial = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                        and node.name == 'TutorialScene')
        method = next(node for node in tutorial.body if isinstance(node, ast.FunctionDef)
                      and node.name == '_complete_tutorial')
        # Extrai apenas o método, mantendo a implementação real sob teste.
        wrapper = ast.ClassDef(name='IsolatedTutorial', bases=[], keywords=[],
                               body=[method], decorator_list=[])
        module = ast.fix_missing_locations(ast.Module(body=[wrapper], type_ignores=[]))
        cls.globals = {'MapScene': FakeMapScene, 'SaveError': SaveError}
        exec(compile(module, '<tutorial>', 'exec'), cls.globals)
        cls.tutorial_class = cls.globals['IsolatedTutorial']

    def make_scene(self, seen=False, with_save=True):
        scene = self.tutorial_class()
        scene.engine = Mock()
        scene.engine.state = 'victory'
        scene.engine.player.coins = 0
        scene.engine.player.hp = 20
        scene.engine.player.max_hp = 20
        scene.engine.player.add_coins.side_effect = lambda amount: setattr(
            scene.engine.player, 'coins', scene.engine.player.coins + amount)
        scene.engine.deck_manager = Mock()
        scene._tutorial_completion_committed = False
        scene.scene_manager = Mock()
        scene.window_manager = Mock()
        scene.asset_manager = Mock()
        scene.play_ui_sound = Mock()
        scene.save_manager = Mock() if with_save else None
        scene.save_data = ({'progresso': {'tutorial_concluido': False,
                                         'pos_tutorial_visto': seen}}
                           if with_save else None)
        return scene

    def test_victory_cutscene_then_map(self):
        scene = self.make_scene()
        # As importações de produção só ocorrem no ramo da cutscene.
        import sys
        from types import ModuleType
        from unittest.mock import patch
        config = ModuleType('src.config.cutscenes')
        config.POST_TUTORIAL_CUTSCENE = [{'image': 'cutscenes/pos_tutorial.png',
                                         'text': '', 'position': 'bottom'}]
        scenes = ModuleType('src.scenes.cutscene_scene')
        scenes.CutsceneScene = FakeCutsceneScene
        with patch.dict(sys.modules, {'src.config.cutscenes': config,
                                      'src.scenes.cutscene_scene': scenes}):
            scene._complete_tutorial()
        destination = scene.scene_manager.change_scene.call_args.args[0]
        self.assertIsInstance(destination, FakeCutsceneScene)
        self.assertEqual(scene.engine.player.coins, 30)
        self.assertTrue(scene.save_data['progresso']['tutorial_concluido'])
        self.assertFalse(scene.save_data['progresso']['pos_tutorial_visto'])
        self.assertEqual(scene.save_manager.save.call_count, 1)
        self.assertIsInstance(destination.finish(), FakeMapScene)
        self.assertTrue(scene.save_data['progresso']['pos_tutorial_visto'])
        self.assertEqual(scene.save_manager.save.call_count, 2)

    def test_already_seen_goes_directly_to_map(self):
        scene = self.make_scene(seen=True)
        scene._complete_tutorial()
        destination = scene.scene_manager.change_scene.call_args.args[0]
        self.assertIsInstance(destination, FakeMapScene)
        self.assertEqual(scene.save_manager.save.call_count, 1)

    def test_repeat_does_not_add_coins_or_change_scene_again(self):
        scene = self.make_scene(seen=True)
        scene._complete_tutorial()
        scene._complete_tutorial()
        self.assertEqual(scene.engine.player.coins, 30)
        self.assertEqual(scene.save_manager.save.call_count, 1)
        self.assertEqual(scene.scene_manager.change_scene.call_count, 1)

    def test_debug_without_save_goes_directly_to_map(self):
        scene = self.make_scene(with_save=False)
        scene._complete_tutorial()
        self.assertIsInstance(scene.scene_manager.change_scene.call_args.args[0], FakeMapScene)

    def test_failed_tutorial_save_stays_on_victory(self):
        scene = self.make_scene()
        scene.save_manager.save.side_effect = SaveError('sem espaço')
        scene._complete_tutorial()
        scene.scene_manager.change_scene.assert_not_called()
        self.assertFalse(scene._tutorial_completion_committed)
        self.assertEqual(scene.engine.player.coins, 0)
        self.assertFalse(scene.save_data['progresso']['tutorial_concluido'])


if __name__ == '__main__':
    unittest.main()
