import pygame

from src.scenes.base_scene import BaseScene
from src.scenes.confirmation_modal import ConfirmationModal
from src.scenes.cemetery_modal import CemeteryModal
from src.systems.combat_engine import CombatEngine
from src.ui.card_view import CardView
from src.ui.entity_view import EntityView
from src.ui.floating_text import FloatingTextManager
from src.ui.coin_hud import CoinHUD
from src.ui.energy_hud import EnergyHUD
from src.ui.helpers import draw_text, draw_health_bar
from src.config.settings import WIDTH, HEIGHT
from src.config.colors import (
    BG,
    BLACK,
    WHITE,
    RED,
    GREEN,
    BLUE,
    GOLD,
    GRAY,
    BUTTON_BG,
    BUTTON_HOVER,
)
from src.config.layout import (
    PLAYER_X,
    ENEMY_X,
    POST_ENEMY_PAUSE,
)


class BattleScene(BaseScene):
    """Cena principal de batalha onde o combate por turnos acontece."""

    def __init__(self, scene_manager, window_manager, asset_manager):
        super().__init__(scene_manager, window_manager, asset_manager)

        self.floating_texts = FloatingTextManager()
        self.entity_view = EntityView(asset_manager)

        # Inicializa o motor puro de combate com callbacks para efeitos visuais
        self.engine = CombatEngine(on_event_callback=self._handle_combat_event)

        # Sistema de moedas (instanciado apos o engine para ter acesso ao player)
        self.coin_hud = CoinHUD(self.engine.player)
        self.energy_hud = EnergyHUD(self.engine.player)

        self.enemy_turn_timer = 0
        self.menu_button_rect = pygame.Rect(WIDTH - 120, 20, 100, 40)
        self.end_turn_rect = pygame.Rect(WIDTH - 160, HEIGHT - 200, 130, 50)
        self.cemetery_button_rect = pygame.Rect(WIDTH - 160, HEIGHT - 140, 130, 44)
        self.skip_reward_rect = pygame.Rect(WIDTH // 2 - 60, HEIGHT - 100, 120, 40)
        self.ultimate_button_rect = pygame.Rect(20, HEIGHT - 170, 150, 46)

    def _handle_combat_event(self, event_name, **kwargs):
        """Reage a eventos emitidos pelo motor de combate."""
        if event_name == "attack":
            self.entity_view.trigger_attack(kwargs.get("attacker"), kwargs.get("action"))
        elif event_name == "flash":
            self.entity_view.trigger_flash(kwargs.get("target"))
        elif event_name == "player_action":
            self.entity_view.trigger_player_action(kwargs.get("action"))
        elif event_name == "floating_text":
            self.floating_texts.spawn(
                kwargs["x"], kwargs["y"], kwargs["text"], kwargs["color"]
            )
        elif event_name == "coin_drop":
            self.coin_hud.spawn_coins(
                kwargs["amount"], kwargs["x"], kwargs["y"]
            )
        elif event_name == "cemetery_discard":
            card = kwargs.get("card")
            card_name = card.name if card else "Carta"
            self.floating_texts.spawn(
                PLAYER_X,
                HEIGHT - 220,
                f"{card_name} Descartada",
                (200, 160, 255),
            )

    def update(self, dt):
        self.engine.update_message(dt)
        self.entity_view.update(dt)
        self.floating_texts.update(dt)
        self.coin_hud.update(dt)
        self.energy_hud.update(dt)

        # ----------------------------------------------------
        # Turno do Inimigo
        # ----------------------------------------------------
        if self.engine.state == "enemy_turn":
            self.enemy_turn_timer += dt
            if self.enemy_turn_timer >= 800:
                self.engine.enemy_turn()
                self.entity_view.post_enemy_pause = POST_ENEMY_PAUSE
                self.enemy_turn_timer = 0
        else:
            self.enemy_turn_timer = 0

        # ----------------------------------------------------
        # Finalização da rodada do Inimigo
        # ----------------------------------------------------
        if self.engine.state == "enemy_resolving":
            if self.entity_view.is_enemy_resolving_done():
                self.engine.finish_enemy_turn()

    def draw(self, surface):
        # 1. Fundo do cenário
        if self.asset_manager.background is not None:
            surface.blit(self.asset_manager.background, (0, 0))
        else:
            surface.fill(BG)

        # 2. Inimigo: HUD e Informações
        enemy = self.engine.enemy
        if enemy.is_miniboss:
            draw_text(
                surface, "MINIBOSS", self.asset_manager.small_font, GOLD, ENEMY_X, 38, center=True
            )

        draw_text(
            surface,
            enemy.name,
            self.asset_manager.big_font,
            GOLD if enemy.is_miniboss else WHITE,
            ENEMY_X,
            70,
            center=True,
        )
        draw_health_bar(surface, WIDTH - 320, 100, 240, 24, enemy.hp, enemy.max_hp, RED)
        draw_text(
            surface, f"{enemy.hp}/{enemy.max_hp}", self.asset_manager.font, WHITE, ENEMY_X, 112, center=True
        )

        if enemy.block > 0:
            draw_text(
                surface, f"Bloqueio: {enemy.block}", self.asset_manager.font, BLUE, ENEMY_X, 140, center=True
            )

        if enemy.intent:
            if enemy.intent == "attack":
                intent_text = f"Intenção: Atacar ({enemy.intent_value})"
                enemy_color = (200, 90, 90)
            else:
                intent_text = f"Intenção: Defender ({enemy.intent_value})"
                enemy_color = (90, 130, 200)

            draw_text(surface, intent_text, self.asset_manager.font, GOLD, ENEMY_X, 168, center=True)
        else:
            enemy_color = WHITE

        # 3. Inimigo: Animação e Sprite
        self.entity_view.draw_enemy(surface, enemy_color)

        # 4. Jogador: HUD e Informações
        player = self.engine.player
        draw_text(surface, player.name, self.asset_manager.big_font, WHITE, PLAYER_X, 70, center=True)
        draw_health_bar(surface, 80, 100, 240, 24, player.hp, player.max_hp, GREEN)
        draw_text(
            surface, f"{player.hp}/{player.max_hp}", self.asset_manager.font, WHITE, PLAYER_X, 112, center=True
        )

        if player.block > 0:
            draw_text(
                surface, f"Bloqueio: {player.block}", self.asset_manager.font, BLUE, PLAYER_X, 140, center=True
            )
        if player.strength > 0:
            draw_text(
                surface, f"Força: {player.strength}", self.asset_manager.font, RED, PLAYER_X, 165, center=True
            )

        # 5. Jogador: Animação e Sprite
        self.entity_view.draw_player(surface, self.engine.state)

        # 6. HUD de Energia (atual e máxima, com slots de progressão até 8)
        self.energy_hud.draw(
            surface, self.asset_manager.font, self.asset_manager.small_font
        )

        # 6.1 Barra de Carga da Ultimate
        self._draw_ultimate_bar(surface)

        # 7. Informações de Baralho e Andar
        draw_text(
            surface,
            f"Compra: {len(self.engine.draw_pile)}",
            self.asset_manager.small_font,
            GRAY,
            WIDTH - 130,
            HEIGHT - 40,
        )
        draw_text(
            surface,
            f"Descarte: {len(self.engine.discard_pile)}",
            self.asset_manager.small_font,
            GRAY,
            WIDTH - 130,
            HEIGHT - 20,
        )
        draw_text(
            surface,
            f"Andar: {self.engine.level}",
            self.asset_manager.small_font,
            GRAY,
            20,
            20,
        )

        # 8. Botão de Menu e Tela Cheia
        self._draw_menu_button(surface)
        self.window_manager.draw_fullscreen_button(self.asset_manager.small_font)

        # 9. Cartas na Mão
        if self.engine.state in ("player_turn", "enemy_turn", "enemy_resolving"):
            mouse_pos = self.window_manager.get_virtual_mouse_pos()
            hand_rects = CardView.get_hand_rects(len(self.engine.hand))

            for rect, card in zip(hand_rects, self.engine.hand):
                hovered = rect.collidepoint(mouse_pos) and (self.engine.state == "player_turn")
                CardView.draw_card(surface, rect, card, self.asset_manager, hovered)

        # 10. Botão de Fim de Turno
        if self.engine.state == "player_turn":
            btn_color = (100, 60, 60)
            btn_label = "Fim de turno"
        else:
            btn_color = (60, 60, 60)
            btn_label = "Turno inimigo..."

        pygame.draw.rect(surface, btn_color, self.end_turn_rect, border_radius=8)
        draw_text(
            surface,
            btn_label,
            self.asset_manager.font,
            WHITE,
            self.end_turn_rect.centerx,
            self.end_turn_rect.centery,
            center=True,
        )

        # 10.1 Botão do Cemitério
        self._draw_cemetery_button(surface)

        # 11. Textos Flutuantes
        self.floating_texts.draw(surface, self.asset_manager.font)

        # 12. HUD de Moedas (por cima de tudo, exceto overlays de game over/vitoria)
        self.coin_hud.draw(surface, self.asset_manager.font, self.asset_manager.coin_icon)

        # 12. Mensagem de Alerta (Ex: "Energia insuficiente!")
        if self.engine.message:
            draw_text(
                surface,
                self.engine.message,
                self.asset_manager.font,
                RED,
                WIDTH // 2,
                HEIGHT - 240,
                center=True,
            )

        # 13. Tela de Derrota (Game Over)
        if self.engine.state == "game_over":
            self._draw_game_over(surface)

        # 14. Tela de Vitória e Escolha de Recompensa
        if self.engine.state == "victory":
            self._draw_victory(surface)

    def _draw_cemetery_button(self, surface):
        """Desenha o botão de acesso ao Cemitério durante a partida."""
        mouse_pos = self.window_manager.get_virtual_mouse_pos()
        hovered = self.cemetery_button_rect.collidepoint(mouse_pos)
        is_player_turn = self.engine.state == "player_turn"
        has_energy = self.engine.player.can_use_cemetery()

        if is_player_turn:
            if has_energy:
                btn_color = (95, 55, 125) if hovered else (70, 40, 95)
                border_color = (190, 130, 240) if hovered else (150, 95, 200)
                text_color = WHITE
            else:
                btn_color = (48, 40, 60)
                border_color = (90, 80, 110)
                text_color = (160, 150, 170)
        else:
            btn_color = (40, 36, 48)
            border_color = (60, 55, 70)
            text_color = GRAY

        pygame.draw.rect(surface, btn_color, self.cemetery_button_rect, border_radius=8)
        pygame.draw.rect(surface, border_color, self.cemetery_button_rect, 2, border_radius=8)
        draw_text(
            surface,
            "Cemitério (1 E.)",
            self.asset_manager.small_font,
            text_color,
            self.cemetery_button_rect.centerx,
            self.cemetery_button_rect.centery,
            center=True,
        )

    def _draw_ultimate_bar(self, surface):
        ready = self.engine.ultimate_ready
        bar_x, bar_y, bar_w, bar_h = 20, HEIGHT - 210, 150, 18

        draw_health_bar(
            surface,
            bar_x,
            bar_y,
            bar_w,
            bar_h,
            self.engine.ultimate_charge,
            self.engine.ultimate_threshold,
            GOLD,
        )
        draw_text(
            surface,
            f"ULTIMATE {self.engine.ultimate_charge}/{self.engine.ultimate_threshold}",
            self.asset_manager.small_font,
            WHITE,
            bar_x + bar_w // 2,
            bar_y - 12,
            center=True,
        )

        can_click = ready and self.engine.state == "player_turn"
        hovered = self.ultimate_button_rect.collidepoint(
            self.window_manager.get_virtual_mouse_pos()
        )

        if ready:
            btn_color = BUTTON_HOVER if hovered and can_click else GOLD
            btn_label = "ULTIMATE!"
            text_color = BLACK
        else:
            btn_color = (60, 60, 60)
            btn_label = "Ultimate"
            text_color = GRAY

        pygame.draw.rect(surface, btn_color, self.ultimate_button_rect, border_radius=8)
        pygame.draw.rect(surface, GOLD, self.ultimate_button_rect, 2, border_radius=8)
        draw_text(
            surface,
            btn_label,
            self.asset_manager.font,
            text_color,
            self.ultimate_button_rect.centerx,
            self.ultimate_button_rect.centery,
            center=True,
        )

    def _draw_menu_button(self, surface):
        hovered = self.menu_button_rect.collidepoint(
            self.window_manager.get_virtual_mouse_pos()
        )
        color = BUTTON_HOVER if hovered else BUTTON_BG
        pygame.draw.rect(surface, color, self.menu_button_rect, border_radius=8)
        pygame.draw.rect(surface, GOLD, self.menu_button_rect, 2, border_radius=8)
        draw_text(
            surface,
            "MENU",
            self.asset_manager.small_font,
            WHITE,
            self.menu_button_rect.centerx,
            self.menu_button_rect.centery,
            center=True,
        )

    def _draw_game_over(self, surface):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(210)
        overlay.fill(BLACK)
        surface.blit(overlay, (0, 0))

        draw_text(
            surface, "VOCÊ MORREU", self.asset_manager.big_font, RED, WIDTH // 2, HEIGHT // 2 - 20, center=True
        )
        draw_text(
            surface,
            f"Você chegou até o andar {self.engine.level}",
            self.asset_manager.font,
            WHITE,
            WIDTH // 2,
            HEIGHT // 2 + 20,
            center=True,
        )
        draw_text(
            surface,
            "Pressione R para reiniciar",
            self.asset_manager.font,
            WHITE,
            WIDTH // 2,
            HEIGHT // 2 + 60,
            center=True,
        )

    def _draw_victory(self, surface):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(220)
        overlay.fill((10, 10, 20))
        surface.blit(overlay, (0, 0))

        draw_text(
            surface,
            "VITÓRIA! Escolha uma carta:",
            self.asset_manager.big_font,
            GOLD,
            WIDTH // 2,
            120,
            center=True,
        )

        mouse_pos = self.window_manager.get_virtual_mouse_pos()
        reward_rects = CardView.get_reward_rects(len(self.engine.reward_cards))

        for rect, card in zip(reward_rects, self.engine.reward_cards):
            hovered = rect.collidepoint(mouse_pos)
            CardView.draw_card(surface, rect, card, self.asset_manager, hovered)

        pygame.draw.rect(surface, (80, 80, 80), self.skip_reward_rect, border_radius=8)
        draw_text(
            surface,
            "Pular",
            self.asset_manager.font,
            WHITE,
            self.skip_reward_rect.centerx,
            self.skip_reward_rect.centery,
            center=True,
        )

    def handle_event(self, event):
        # Trata atalho de tela cheia ou redimensionamento
        if self.window_manager.handle_window_event(event):
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            virt_pos = self.window_manager.map_to_virtual(event.pos)

            # Botão de Tela Cheia
            if self.window_manager.get_fullscreen_button_rect().collidepoint(virt_pos):
                self.window_manager.toggle_fullscreen()
                return

            # Botão de Menu In-game
            if self.menu_button_rect.collidepoint(virt_pos):
                self._open_menu_confirmation()
                return

            # Turno do Jogador: Jogar Carta, Ativar Ultimate, Acessar Cemitério ou Encerrar Turno
            if self.engine.state == "player_turn" and self.entity_view.player_action is None:
                # Botão do Cemitério
                if self.cemetery_button_rect.collidepoint(virt_pos):
                    self._open_cemetery_modal()
                    return

                if self.ultimate_button_rect.collidepoint(virt_pos):
                    if self.engine.ultimate_ready:
                        self.engine.activate_ultimate()
                    return

                hand_rects = CardView.get_hand_rects(len(self.engine.hand))
                for index, rect in enumerate(hand_rects):
                    if rect.collidepoint(virt_pos):
                        self.engine.play_card(index)
                        return

                if self.end_turn_rect.collidepoint(virt_pos):
                    self.engine.end_turn()
                    return

            # Recompensa de Vitória: Escolher Carta ou Pular
            elif self.engine.state == "victory":
                reward_rects = CardView.get_reward_rects(len(self.engine.reward_cards))
                for index, rect in enumerate(reward_rects):
                    if rect.collidepoint(virt_pos):
                        self.engine.choose_reward(index)
                        return

                if self.skip_reward_rect.collidepoint(virt_pos):
                    self.engine.skip_reward()
                    return

        elif event.type == pygame.KEYDOWN:
            # Reiniciar partida em Game Over
            if event.key == pygame.K_r and self.engine.state == "game_over":
                self.engine = CombatEngine(on_event_callback=self._handle_combat_event)
                self.coin_hud = CoinHUD(self.engine.player)
                self.energy_hud = EnergyHUD(self.engine.player)
                self.floating_texts.clear()
                self.enemy_turn_timer = 0

            # Tecla C para atalho rápido do Cemitério durante o turno do jogador
            elif event.key == pygame.K_c and self.engine.state == "player_turn":
                self._open_cemetery_modal()

            # ESC para abrir menu de confirmação
            elif event.key == pygame.K_ESCAPE and self.engine.state in (
                "player_turn",
                "game_over",
                "victory",
            ):
                self._open_menu_confirmation()

    def _open_cemetery_modal(self):
        """Abre a interface interativa do Cemitério como modal."""
        modal = CemeteryModal(
            self.scene_manager,
            self.window_manager,
            self.asset_manager,
            self.engine,
        )
        self.scene_manager.push_modal(modal)

    def _open_menu_confirmation(self):
        modal = ConfirmationModal(
            self.scene_manager,
            self.window_manager,
            self.asset_manager,
            on_confirm=self._return_to_main_menu,
        )
        self.scene_manager.push_modal(modal)

    def _return_to_main_menu(self):
        from src.scenes.menu_scene import MenuScene
        self.scene_manager.change_scene(
            MenuScene(self.scene_manager, self.window_manager, self.asset_manager)
        )
