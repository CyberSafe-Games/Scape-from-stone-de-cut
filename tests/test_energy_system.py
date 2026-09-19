import os
import unittest

# Configura driver dummy do SDL para execução de testes em ambiente headless/CLI
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

pygame.init()
pygame.font.init()

from src.models.player import Player
from src.systems.combat_engine import CombatEngine
from src.ui.energy_hud import EnergyHUD


class TestPlayerEnergySystem(unittest.TestCase):
    """Testes unitários focados nas regras de energia da entidade Player."""

    def test_initial_energy_is_two(self):
        """O jogador deve iniciar com energia máxima 2 e energia atual 2."""
        player = Player("Herói", 60)
        self.assertEqual(player.energy_max, 2)
        self.assertEqual(player.energy, 2)
        self.assertEqual(Player.INITIAL_ENERGY_MAX, 2)
        self.assertEqual(Player.MAX_ENERGY_LIMIT, 8)

    def test_increase_max_energy_progression(self):
        """A energia máxima deve evoluir progressivamente quando solicitado."""
        player = Player("Herói", 60)
        self.assertEqual(player.energy_max, 2)

        player.increase_max_energy(1)
        self.assertEqual(player.energy_max, 3)

        player.increase_max_energy(2)
        self.assertEqual(player.energy_max, 5)

    def test_max_energy_limit_strictly_eight(self):
        """A energia máxima não pode ultrapassar o limite de 8 sob nenhuma circunstância."""
        player = Player("Herói", 60)
        # Tenta aumentar 10 vezes além do limite
        for _ in range(15):
            player.increase_max_energy(1)
        self.assertEqual(player.energy_max, 8)

        # Tentativa de atribuição direta acima de 8 via setter
        player.energy_max = 99
        self.assertEqual(player.energy_max, 8)

        # Tentativa de inicialização direta acima de 8
        over_player = Player("Herói", 60, energy_max=25)
        self.assertEqual(over_player.energy_max, 8)

    def test_reset_energy_restores_to_current_max(self):
        """reset_energy deve restaurar a energia atual para o valor máximo atual."""
        player = Player("Herói", 60)
        player.use_energy(2)
        self.assertEqual(player.energy, 0)

        player.reset_energy()
        self.assertEqual(player.energy, 2)

        player.increase_max_energy(3)  # Agora max é 5
        player.reset_energy()
        self.assertEqual(player.energy, 5)

    def test_use_energy_validation(self):
        """use_energy só deve consumir energia se o jogador tiver saldo suficiente."""
        player = Player("Herói", 60)  # 2 de energia
        self.assertTrue(player.use_energy(1))
        self.assertEqual(player.energy, 1)

        self.assertFalse(player.use_energy(2))  # saldo insuficiente
        self.assertEqual(player.energy, 1)

        self.assertTrue(player.use_energy(1))
        self.assertEqual(player.energy, 0)

        self.assertFalse(player.use_energy(1))
        self.assertEqual(player.energy, 0)


class TestCombatEngineEnergyIntegration(unittest.TestCase):
    """Testes de integração entre o fluxo de combate e o sistema de energia."""

    def test_combat_engine_initial_energy(self):
        """CombatEngine deve iniciar a partida com o jogador em 2/2 de energia."""
        engine = CombatEngine()
        self.assertEqual(engine.energy_max, 2)
        self.assertEqual(engine.energy, 2)

    def test_playing_cards_spends_energy_and_blocks_insufficient(self):
        """Jogar cartas consome energia e bloqueia quando não há energia suficiente."""
        engine = CombatEngine()
        # Mão com cartas iniciais (todas com custo >= 1)
        self.assertGreater(len(engine.hand), 0)
        first_card = engine.hand[0]
        cost = first_card.cost

        # Joga a primeira carta
        played = engine.play_card(0)
        self.assertTrue(played)
        self.assertEqual(engine.energy, 2 - cost)

    def test_turn_by_turn_progression_up_to_eight(self):
        """A cada novo turno do jogador, a energia máxima deve aumentar em 1 até 8."""
        engine = CombatEngine()

        # Turno 1: Começa com 2
        self.assertEqual(engine.energy_max, 2)
        self.assertEqual(engine.energy, 2)

        expected_max_values = [3, 4, 5, 6, 7, 8, 8, 8]
        for turn_idx, expected_max in enumerate(expected_max_values, start=2):
            # Jogador encerra o turno
            engine.end_turn()
            self.assertEqual(engine.state, "enemy_turn")

            # Inimigo finaliza a ação e chama finish_enemy_turn
            engine.finish_enemy_turn()
            self.assertEqual(engine.state, "player_turn")

            self.assertEqual(
                engine.energy_max,
                expected_max,
                f"Falha no turno {turn_idx}: esperado {expected_max}, obtido {engine.energy_max}",
            )
            self.assertEqual(
                engine.energy,
                expected_max,
                f"Energia atual no turno {turn_idx} deveria ser restaurada para {expected_max}",
            )

    def test_different_match_moments(self):
        """Valida o sistema em diferentes momentos da partida (início, meio, fim de andar e restart)."""
        engine = CombatEngine()

        # 1. Momento Inicial: 2 de energia máxima
        self.assertEqual(engine.energy_max, 2)

        # 2. Momento Médio (3 turnos passados): energia máxima deve ser 5
        for _ in range(3):
            engine.end_turn()
            engine.finish_enemy_turn()
        self.assertEqual(engine.energy_max, 5)
        self.assertEqual(engine.energy, 5)

        # 3. Transição para próximo nível/andar: mantém a energia máxima adquirida
        engine.next_level()
        self.assertEqual(engine.level, 2)
        self.assertEqual(engine.energy_max, 5)
        self.assertEqual(engine.energy, 5)

        # 4. Momento Avançado: continua progredindo até atingir o limite de 8
        for _ in range(5):
            engine.end_turn()
            engine.finish_enemy_turn()
        self.assertEqual(engine.energy_max, 8)
        self.assertEqual(engine.energy, 8)

        # Mais turnos não ultrapassam 8
        for _ in range(3):
            engine.end_turn()
            engine.finish_enemy_turn()
        self.assertEqual(engine.energy_max, 8)

        # 5. Reinício de partida (Game Over): nova partida reinicia em 2
        engine_restarted = CombatEngine()
        self.assertEqual(engine_restarted.energy_max, 2)
        self.assertEqual(engine_restarted.energy, 2)


class TestEnergyHUD(unittest.TestCase):
    """Testes de renderização visual e componentes da interface EnergyHUD."""

    def setUp(self):
        self.surface = pygame.Surface((1280, 720))
        self.font = pygame.font.SysFont(None, 24)
        self.small_font = pygame.font.SysFont(None, 16)

    def test_hud_draw_at_different_stages(self):
        """O HUD deve renderizar com sucesso nas fases inicial (2), intermediária (5) e máxima (8)."""
        player = Player("Herói", 60)
        hud = EnergyHUD(player)

        # 1. Estágio Inicial (2/2)
        hud.update(16)
        hud.draw(self.surface, self.font, self.small_font)

        # 2. Estágio com energia gasta (1/2)
        player.use_energy(1)
        hud.draw(self.surface, self.font, self.small_font)

        # 3. Estágio Intermediário (4/5)
        player.energy_max = 5
        player.reset_energy()
        player.use_energy(1)
        hud.draw(self.surface, self.font, self.small_font)

        # 4. Estágio Máximo (8/8)
        player.energy_max = 8
        player.reset_energy()
        hud.draw(self.surface, self.font, self.small_font)

        # 5. Estágio Máximo com energia esgotada (0/8)
        player.use_energy(8)
        hud.draw(self.surface, self.font, self.small_font)


class TestBattleSceneEnergyIntegration(unittest.TestCase):
    """Testes integrados na cena de batalha completa."""

    def test_battle_scene_draw_and_restart(self):
        """BattleScene deve inicializar, desenhar e reiniciar o EnergyHUD sem erros."""
        from src.config.settings import WIDTH, HEIGHT, TITLE
        from src.core.window import WindowManager
        from src.core.asset_manager import AssetManager
        from src.core.scene_manager import SceneManager
        from src.scenes.battle_scene import BattleScene

        wm = WindowManager(WIDTH, HEIGHT, TITLE)
        am = AssetManager()
        sm = SceneManager()
        scene = BattleScene(sm, wm, am)

        # Verifica estado inicial no HUD e engine
        self.assertEqual(scene.engine.energy, 2)
        self.assertEqual(scene.engine.energy_max, 2)
        self.assertEqual(scene.energy_hud.player.energy_max, 2)

        # Atualiza e desenha
        scene.update(16)
        scene.draw(wm.virtual_screen)

        # Simula game over e reinício com tecla R
        scene.engine.state = "game_over"
        event_r = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)
        scene.handle_event(event_r)

        self.assertEqual(scene.engine.energy, 2)
        self.assertEqual(scene.engine.energy_max, 2)
        self.assertEqual(scene.energy_hud.player.energy_max, 2)


if __name__ == "__main__":
    unittest.main()

