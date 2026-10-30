"""Cena de tutorial guiado de combate para Scape From Stone de Cut.

Integra o cenário de tutorial, inimigo didático, balões flutuantes próximos
aos elementos ensinados, setas animadas e caixas de texto com narrativa e instruções,
proporcionando uma experiência jogável completa e explicativa com avanço por clique.
"""
import pygame

from src.config.colors import (
    BG,
    BLACK,
    WHITE,
    GOLD,
    GRAY,
    GREEN,
    RED,
    BLUE,
)
from src.config.settings import WIDTH, HEIGHT
from src.models.action import Action
from src.models.enemy import Enemy
from src.scenes.battle_scene import BattleScene
from src.scenes.map_scene import MapScene
from src.systems.save_manager import SaveError
from src.ui.helpers import draw_text, draw_panel, draw_vignette
from src.ui import dark_fantasy_theme as theme
from src.ui.tutorial_overlay import TutorialOverlay, TutorialStep


class TutorialScene(BattleScene):
    """Fase interativa de tutorial que ensina as regras e elementos de combate."""

    def __init__(self, scene_manager, window_manager, asset_manager, save_manager=None, save_data=None):
        super().__init__(
            scene_manager,
            window_manager,
            asset_manager,
            save_manager=save_manager,
            save_data=save_data,
            map_mode=False,
            selected_level=1,
        )

        # Configura o inimigo didático específico do tutorial
        self._setup_tutorial_enemy()

        # Garante mão balanceada para a aula prática
        self._setup_tutorial_hand()

        # Evita persistir dano ou consumo do treinamento antes da conclusão.
        self._tutorial_completion_committed = False

        # Botão para reabrir o guia durante a batalha
        self.help_button_rect = pygame.Rect(WIDTH // 2 - 70, 16, 140, 30)

        # Botão de conclusão do tutorial na tela de vitória
        self.finish_tutorial_button_rect = pygame.Rect(WIDTH // 2 - 160, HEIGHT // 2 + 130, 320, 52)

        # Inicializa o overlay com todos os passos, balões flutuantes e setas
        self.overlay = TutorialOverlay(self._create_tutorial_steps())

    def _handle_combat_event(self, event_name, **kwargs):
        # O treinamento concede uma recompensa fixa na conclusão, em vez do
        # sorteio de moedas do combate comum (que impediria repetir com segurança).
        if event_name == "coin_drop":
            return
        super()._handle_combat_event(event_name, **kwargs)

    def _setup_tutorial_enemy(self):
        """Cria um Slime balanceado com ações previsíveis para o aprendizado."""
        tutorial_actions = [
            Action(
                name="Investida Leve",
                action_type="attack",
                damage=5,
                energy_cost=1,
                weight=0.6,
                visual_effect="atk",
            ),
            Action(
                name="Escudo de Gosma",
                action_type="defend",
                defense=5,
                energy_cost=1,
                weight=0.4,
                visual_effect="def",
            ),
        ]
        self.engine.enemy = Enemy(
            name="Slime",
            hp=20,
            energy=2,
            max_energy=2,
            actions=tutorial_actions,
            is_miniboss=False,
        )
        # O inimigo inicia anunciando ataque para demonstrar a intenção e incentivar a defesa
        self.engine.enemy.set_intent("attack", 5, action=tutorial_actions[0])

    def _setup_tutorial_hand(self):
        """Assegura cartas fundamentais na mão inicial (Golpe, Defesa)."""
        hand_names = [c.name for c in self.engine.hand]
        if "Esfera Protetora" not in hand_names or "Soco Simples" not in hand_names:
            from src.systems.card_catalog import CARD_POOL
            catalog = {c.name: c for c in CARD_POOL}
            if len(self.engine.hand) >= 2:
                self.engine.hand[0] = catalog["Soco Simples"].copy()
                self.engine.hand[1] = catalog["Esfera Protetora"].copy()

    def _create_tutorial_steps(self) -> list[TutorialStep]:
        """Constrói os balões flutuantes posicionados perto de cada elemento ensinado."""
        steps = []

        # 1. Introdução Narrativa (Centro-alto da tela)
        steps.append(
            TutorialStep(
                id="intro",
                title="O DESPERTAR NA PEDRA DO CORTE",
                subtitle="Introdução Narrativa",
                lines=[
                    "Você desperta na clareira sombria de Pedra do Corte.",
                    "Uma criatura mística espreita entre as árvores antigas.",
                    "Antes de avançar pela floresta, domine as runas de combate!",
                    "Aprenda seus recursos, cartas e táticas de sobrevivência.",
                ],
                target_rect_fn=None,
                bubble_pos=((WIDTH - 480) // 2, 210),
                bubble_size=(480, 196),
                arrow_origin_fn=None,
                arrow_target_fn=None,
            )
        )

        # 2. Barra de Vida (HP) - Balão ao lado direito do painel de HP do jogador
        steps.append(
            TutorialStep(
                id="hp",
                title="BARRA DE VIDA (HP)",
                subtitle="Vitalidade e Sobrevivência",
                lines=[
                    "No topo esquerdo está sua barra de VIDA (HP).",
                    "No topo direito está a VIDA DO INIMIGO.",
                    "Reduza a vida do Slime a zero para vencer a batalha!",
                    "Se seu HP acabar, você pode reiniciar o treinamento.",
                ],
                target_rect_fn=lambda: pygame.Rect(22, 20, 390, 92),
                bubble_pos=(432, 20),
                bubble_size=(470, 190),
                arrow_origin_fn=lambda: (432, 66),
                arrow_target_fn=lambda: (412, 66),
            )
        )

        # 3. Barra de Energia - Balão ao lado direito das gemas de energia
        steps.append(
            TutorialStep(
                id="energy",
                title="BARRA DE ENERGIA",
                subtitle="O Combustível das Ações",
                lines=[
                    "A ENERGIA é necessária para jogar cartas!",
                    "Cada gema dourada representa 1 ponto de energia.",
                    "Toda carta possui seu custo gravado no canto superior.",
                    "Sua energia é totalmente restaurada a cada novo turno.",
                ],
                target_rect_fn=lambda: pygame.Rect(36, 156, 170, 26),
                bubble_pos=(222, 132),
                bubble_size=(470, 190),
                arrow_origin_fn=lambda: (222, 169),
                arrow_target_fn=lambda: (206, 169),
            )
        )

        # 4. Cartas Disponíveis (Mão) - Balão flutuando logo acima da mão de cartas
        steps.append(
            TutorialStep(
                id="cards",
                title="CARTAS DISPONÍVEIS",
                subtitle="Seu Arsenal em Mão",
                lines=[
                    "Estas são as cartas disponíveis para você jogar.",
                    "• Ataques (ex: Soco Simples) drenam o HP do adversário.",
                    "• Defesas protegem seu corpo contra ataques iminentes.",
                    "Cartas não usadas permanecem na mão no próximo turno.",
                ],
                target_rect_fn=lambda: pygame.Rect(250, HEIGHT - 180, WIDTH - 500, 160),
                bubble_pos=((WIDTH - 470) // 2, HEIGHT - 395),
                bubble_size=(470, 196),
                arrow_origin_fn=lambda: (WIDTH // 2, HEIGHT - 199),
                arrow_target_fn=lambda: (WIDTH // 2, HEIGHT - 175),
            )
        )

        # 5. Status de Bloqueio e Força - Balão à direita dos chips de status
        steps.append(
            TutorialStep(
                id="stats",
                title="BLOQUEIO E FORÇA",
                subtitle="Mitigação e Amplificação",
                lines=[
                    "Abaixo da vida ficam seus STATUS especiais:",
                    "• ESCUDO absorve dano e dura 2 turnos completos.",
                    "• FORÇA aumenta o dano; Aura Rubra dura 3 turnos.",
                    "• Fogo acumula; Veneno ignora Escudo.",
                    "Sangramento pune o primeiro ataque de cada turno.",
                ],
                target_rect_fn=lambda: pygame.Rect(120, 94, 276, 48),
                bubble_pos=(416, 78),
                bubble_size=(480, 192),
                arrow_origin_fn=lambda: (416, 106),
                arrow_target_fn=lambda: (396, 106),
            )
        )

        # 6. Intenção do Inimigo - Balão à esquerda da caixa de intenção
        steps.append(
            TutorialStep(
                id="intent",
                title="INTENÇÃO DO INIMIGO",
                subtitle="Previsão Tática",
                lines=[
                    "Esta caixa revela com antecedência o plano do monstro:",
                    "• Ícone de Espada: ele atacará e exibirá o dano (ex: 5).",
                    "• Ícone de Escudo: ele erguerá bloqueio.",
                    "Antecipe seus passos: use Esfera Protetora se ele for atacar!",
                ],
                target_rect_fn=lambda: pygame.Rect(900, 156, 270, 28),
                bubble_pos=(418, 126),
                bubble_size=(470, 190),
                arrow_origin_fn=lambda: (888, 170),
                arrow_target_fn=lambda: (900, 170),
            )
        )

        # 7. Barra de Ultimate - Balão flutuando logo acima da barra inferior
        steps.append(
            TutorialStep(
                id="ultimate",
                title="BARRA DE ULTIMATE",
                subtitle="Poder Rúnico Supremo",
                lines=[
                    "Ao gastar energia jogando cartas, a Ultimate se carrega.",
                    "Quando a barra atingir 100%, sua habilidade suprema desperta!",
                    "Uma carta dourada lendária aparecerá na sua mão sem custo.",
                      "Depois do treino, escolha sua habilidade na aba Ultimates da mochila.",
                    "Liberte o poder supremo quando estiver pronto.",
                ],
                target_rect_fn=lambda: pygame.Rect(WIDTH // 2 - 170, HEIGHT - 32, 340, 26),
                  bubble_pos=((WIDTH - 470) // 2, HEIGHT - 298),
                  bubble_size=(470, 240),
                arrow_origin_fn=lambda: (WIDTH // 2, HEIGHT - 58),
                arrow_target_fn=lambda: (WIDTH // 2, HEIGHT - 34),
            )
        )

        # 8. O Cemitério - Balão flutuando perto do cemitério no canto inferior esquerdo
        steps.append(
            TutorialStep(
                id="cemetery",
                title="O CEMITÉRIO",
                subtitle="Descarte e Reciclagem",
                lines=[
                    "O CEMITÉRIO permite reciclar runas da sua mão.",
                    "O descarte custa 1 de energia por carta; sem limite fixo.",
                    "Trocar uma carta por outra é grátis, 1 vez por turno.",
                    "Aperte C ou clique no livro do Cemitério!",
                ],
                target_rect_fn=lambda: pygame.Rect(28, HEIGHT - 154, 92, 124),
                bubble_pos=(134, HEIGHT - 245),
                bubble_size=(470, 192),
                arrow_origin_fn=lambda: (134, HEIGHT - 100),
                arrow_target_fn=lambda: (120, HEIGHT - 92),
            )
        )

        # 9. Conclusão da Explicação e Início da Batalha (Perto do botão Fim de Turno)
        steps.append(
            TutorialStep(
                id="fight",
                title="TREINAMENTO PRÁTICO",
                subtitle="A Batalha Começa Agora",
                lines=[
                    "Tudo pronto! Agora vença o Slime de treino:",
                    "1. Jogue 'Esfera Protetora' para bloquear os 5 de dano previstos.",
                    "2. Jogue 'Soco Simples' para causar dano ao inimigo.",
                    "3. Encerre sua vez clicando no botão FIM DO TURNO.",
                    "Clique em qualquer lugar da tela para lutar!",
                ],
                target_rect_fn=lambda: self.end_turn_rect,
                bubble_pos=(WIDTH - 604, HEIGHT - 250),
                bubble_size=(474, 198),
                arrow_origin_fn=lambda: (WIDTH - 130, HEIGHT - 82),
                arrow_target_fn=lambda: (WIDTH - 120, HEIGHT - 82),
            )
        )

        return steps

    def _draw_background(self, surface):
        """Renderiza o cenário com a textura exclusiva do tutorial."""
        bg = self.asset_manager.background_tutorial
        if bg is not None:
            surface.blit(bg, (0, 0))
        else:
            surface.fill(BG)

        # Sombra suave e vinheta dark fantasy
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((4, 10, 10, 115))
        surface.blit(shade, (0, 0))
        draw_vignette(surface, WIDTH, HEIGHT, alpha=80)

        # Sombras sob os pés dos combatentes
        ground = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        from src.config.layout import PLAYER_X, ENEMY_X
        pygame.draw.ellipse(ground, (0, 0, 0, 80), pygame.Rect(PLAYER_X - 92, 422, 180, 36))
        pygame.draw.ellipse(ground, (0, 0, 0, 80), pygame.Rect(ENEMY_X - 86, 422, 170, 34))
        surface.blit(ground, (0, 0))

    def update(self, dt):
        self.overlay.update(dt)

        if self.overlay.is_active:
            # Durante a explicação, mantém as animações idle vivas mas congela a IA do inimigo
            self.entity_view.update(dt)
            self.floating_texts.update(dt)
            return

        super().update(dt)

    def draw(self, surface):
        # Renderiza a batalha base (cenário, entidades, HUD e cartas)
        super().draw(surface)

        cursor = self.window_manager.get_virtual_mouse_pos()

        # Se o guia explicativo estiver ativo, desenha os balões flutuantes animados e setas
        if self.overlay.is_active:
            self.overlay.draw(surface, self.asset_manager, cursor)
        else:
            # Durante o combate prático, exibe botão discreto para rever o tutorial
            hover = self.help_button_rect.collidepoint(cursor)
            theme.button(
                surface,
                self.help_button_rect,
                "? REVER GUIA",
                self.asset_manager.small_font,
                hover=hover,
                prominent=False,
            )

            # Barra superior discreta com dicas essenciais de combate
            tip_rect = pygame.Rect(WIDTH // 2 - 310, 52, 620, 24)
            draw_panel(surface, tip_rect, fill=(10, 16, 16, 210), border=(90, 78, 54), radius=10, shadow=False)
            draw_text(
                surface,
                "ENERGIA para jogar cartas  ·  BLOQUEIO reduz dano  ·  FORÇA amplia ataques",
                self.asset_manager.small_font,
                (225, 215, 175),
                tip_rect.centerx,
                tip_rect.centery,
                center=True,
            )

            # Avisos do combate ficam acima do botão e da faixa de dicas para não serem cortados
            self._draw_top_message(surface)

        # Sobrescreve a tela de vitória quando o tutorial for concluído
        if self.engine.state == "victory" and self.entity_view.player_action is None and self.entity_view.attacker is None:
            self._draw_tutorial_victory(surface, cursor)

    def _draw_tutorial_victory(self, surface, cursor):
        """Tela triunfante de conclusão da fase de tutorial após a derrota do inimigo."""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((4, 8, 8, 230))
        surface.blit(overlay, (0, 0))

        card_rect = pygame.Rect(WIDTH // 2 - 300, HEIGHT // 2 - 210, 600, 420)
        theme.panel(surface, card_rect, highlighted=True, fill=(12, 18, 18, 250))

        theme.eyebrow(
            surface,
            "JORNADA INICIADA  ·  TREINAMENTO RÚNICO CONCLUÍDO",
            self.asset_manager.small_font,
            card_rect.centerx,
            card_rect.y + 28,
            center=True,
        )
        draw_text(
            surface,
            "TUTORIAL CONCLUÍDO!",
            self.asset_manager.title_font,
            GOLD,
            card_rect.centerx,
            card_rect.y + 60,
            center=True,
        )
        theme.divider(surface, card_rect.x + 40, card_rect.right - 40, card_rect.y + 125)

        lines = [
            "Você derrotou o Slime e assimilou os pilares do combate por cartas!",
            "• A Energia permite ditar o ritmo de suas jogadas.",
            "• O Bloqueio preserva sua vida frente às ameaças.",
            "• A Força eleva seus golpes a novos patamares.",
            "• Cemitério: descarte por 1 energia; troca grátis por turno.",
            "",
            "A névoa da floresta se dissipa diante de sua coragem.",
            "Recompensa: +30 Moedas de Ouro pelo treinamento!",
        ]

        text_y = card_rect.y + 145
        for line in lines:
            color = GOLD if "Recompensa" in line else (205, 210, 205) if line.startswith("•") else WHITE
            font = self.asset_manager.font if line else self.asset_manager.small_font
            draw_text(surface, line, font, color, card_rect.centerx, text_y, center=True)
            text_y += 24

        # Botão para avançar para o mapa
        hover = self.finish_tutorial_button_rect.collidepoint(cursor)
        theme.button(
            surface,
            self.finish_tutorial_button_rect,
            "INICIAR EXPEDIÇÃO NO MAPA →",
            self.asset_manager.menu_font,
            hover=hover,
            prominent=True,
        )

        draw_text(
            surface,
            "Pressione ENTER, ESPAÇO ou CLIQUE para avançar",
            self.asset_manager.small_font,
            GRAY,
            card_rect.centerx,
            card_rect.bottom + 18,
            center=True,
        )

    def handle_event(self, event):
        virt_pos = self.window_manager.map_to_virtual(
            event.pos if hasattr(event, "pos") else (0, 0)
        )

        # Se a vitória ocorreu, trata o clique ou atalho para avançar ao mapa
        if self.engine.state == "victory":
            if self.window_manager.handle_window_event(event):
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Qualquer clique na tela ou no botão avança
                self._complete_tutorial()
                return
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._complete_tutorial()
                return
            return

        # Se o overlay de explicação estiver ativo, consome seus cliques e avança
        if self.overlay.is_active:
            if self.window_manager.handle_window_event(event):
                return
            if self.overlay.handle_event(event, virt_pos):
                return

        # Clique no botão de rever guia
        if not self.overlay.is_active and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.help_button_rect.collidepoint(virt_pos):
                self.overlay.reset()
                return

        # Tecla de atalho 'H' ou 'F1' para reabrir o guia
        if not self.overlay.is_active and event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_h, pygame.K_F1):
                self.overlay.reset()
                return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_r and self.engine.state == "game_over":
            self.scene_manager.change_scene(TutorialScene(
                self.scene_manager, self.window_manager, self.asset_manager,
                save_manager=self.save_manager, save_data=self.save_data,
            ))
            return

        # Executa os eventos normais da batalha
        super().handle_event(event)

    def _complete_tutorial(self):
        """Marca a conclusão somente após a vitória e um save bem-sucedido.

        Salva apenas uma vez: repetir clique / tecla não concede moedas duplicadas.
        """
        if self.engine.state != "victory" or self._tutorial_completion_committed:
            return
        if self.save_data is None or self.save_manager is None:
            # O tutorial também pode ser aberto sem save para depuração.
            self._tutorial_completion_committed = True
        else:
            try:
                if not self.save_data["progresso"].get("tutorial_concluido", False):
                    self.engine.player.add_coins(30)
                    self.save_data["progresso"]["tutorial_concluido"] = True
                    self.save_manager.update_from_game(
                        self.save_data, self.engine.player,
                        self.engine.deck_manager, level=1,
                    )
                    self.save_manager.save(self.save_data)
                self._tutorial_completion_committed = True
            except (OSError, ValueError, SaveError) as exc:
                # Restaura o estado lógico; o jogador pode tentar salvar de novo.
                self.engine.player.coins = max(0, self.engine.player.coins - 30)
                self.save_data["progresso"]["tutorial_concluido"] = False
                self.engine.show_message(f"Falha ao gravar tutorial: {exc}", duration=5000)
                return

        self.scene_manager.change_scene(MapScene(
            self.scene_manager, self.window_manager, self.asset_manager,
            save_manager=self.save_manager, save_data=self.save_data,
        ))

    def _save_progress(self):
        """Nunca registra um checkpoint parcial de treinamento."""
        return True

    def save_on_exit(self):
        """O treinamento incompleto volta a abrir ao selecionar o save."""
        return True

    def _return_to_main_menu(self):
        """ESC/MENU antes da vitória não libera o mapa."""
        from src.scenes.menu_scene import MenuScene
        self.scene_manager.change_scene(MenuScene(
            self.scene_manager, self.window_manager, self.asset_manager,
        ))
