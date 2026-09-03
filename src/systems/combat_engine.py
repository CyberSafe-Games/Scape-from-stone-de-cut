import random

from src.models.player import Player
from src.models.deck import DeckManager
from src.systems.card_catalog import CARD_POOL, create_starting_deck
from src.systems.enemy_factory import (
    create_enemy,
    choose_enemy_intent,
    is_miniboss_level,
)
from src.config.colors import RED, BLUE
from src.config.layout import PLAYER_X, PLAYER_Y, ENEMY_X, ENEMY_Y


class CombatEngine:
    """Motor central de lógica de combate e regras de jogo (Puro Python).

    Desacoplado de qualquer biblioteca de renderização gráfica (SRP / DIP).
    """

    def __init__(self, on_event_callback=None):
        self.on_event = on_event_callback or (lambda event, **kwargs: None)

        self.player = Player("Herói", 60, energy_max=3)
        self.deck_manager = DeckManager(create_starting_deck())
        self.level = 1

        miniboss = is_miniboss_level(self.level)
        self.enemy = create_enemy(self.level, miniboss)
        choose_enemy_intent(self.enemy)

        if self.enemy.is_miniboss:
            self.player.hp = self.player.max_hp

        self.state = "player_turn"
        self.message = ""
        self.message_timer = 0
        self.reward_cards = []

        self.start_combat()

    # ========================================================
    # PROPRIEDADES DE CONVENIÊNCIA
    # ========================================================

    @property
    def hand(self):
        return self.deck_manager.hand

    @property
    def draw_pile(self):
        return self.deck_manager.draw_pile

    @property
    def discard_pile(self):
        return self.deck_manager.discard_pile

    @property
    def deck(self):
        return self.deck_manager.deck

    @property
    def energy(self):
        return self.player.energy

    @property
    def energy_max(self):
        return self.player.energy_max

    # ========================================================
    # FLUXO DO COMBATE
    # ========================================================

    def start_combat(self):
        """Prepara os combatentes e cartas para um novo confronto."""
        self.deck_manager.start_combat()
        self.deck_manager.draw_cards(5)
        self.player.reset_energy()
        self.player.block = 0
        self.enemy.block = 0
        self.state = "player_turn"

    def play_card(self, index):
        """Executa a carta da mão especificada pelo índice."""
        if self.state != "player_turn":
            return False

        if index < 0 or index >= len(self.deck_manager.hand):
            return False

        card = self.deck_manager.hand[index]

        if not self.player.use_energy(card.cost):
            self.show_message("Energia insuficiente!")
            return False

        # Aplica o efeito polimórfico da carta (Open/Closed Principle)
        card.execute(self.player, self.enemy, context=self)

        # Move a carta da mão para o descarte
        self.deck_manager.discard_card(index)

        # Verifica condição de vitória imediata
        if not self.enemy.is_alive():
            self.state = "victory"
            self.generate_rewards()

        return True

    def end_turn(self):
        """Encerra a vez do jogador e passa o turno para o inimigo."""
        if self.state != "player_turn":
            return

        self.deck_manager.discard_hand()
        self.state = "enemy_turn"
        self.on_event("turn_ended")

    def enemy_turn(self):
        """Executa a ação calculada da inteligência artificial do inimigo."""
        if self.enemy.intent == "attack":
            damage = self.enemy.intent_value
            actual_damage = self.player.take_damage(damage)

            self.trigger_attack("enemy")
            self.trigger_flash("player")
            self.spawn_player_text(f"-{actual_damage}", RED)
        else:
            block = self.enemy.intent_value
            self.enemy.add_block(block)
            self.spawn_enemy_text(f"+{block} bloqueio", BLUE)

        if not self.player.is_alive():
            self.state = "game_over"
            self.on_event("game_over")
            return

        self.state = "enemy_resolving"

    def finish_enemy_turn(self):
        """Finaliza a resolução da rodada e inicia o novo turno do jogador."""
        choose_enemy_intent(self.enemy)
        self.player.block = 0
        self.player.reset_energy()
        self.deck_manager.draw_cards(5)
        self.state = "player_turn"

    # ========================================================
    # PROGRESSÃO E RECOMPENSAS
    # ========================================================

    def generate_rewards(self):
        """Gera 3 cartas aleatórias do catálogo para escolha."""
        self.reward_cards = [
            random.choice(CARD_POOL).copy() for _ in range(3)
        ]

    def choose_reward(self, index):
        """Seleciona uma carta de recompensa e avança para o próximo andar."""
        if 0 <= index < len(self.reward_cards):
            self.deck_manager.add_to_deck(self.reward_cards[index])
            self.next_level()

    def skip_reward(self):
        """Pula a escolha da carta de recompensa e avança de andar."""
        self.next_level()

    def next_level(self):
        """Avança de andar com balanceamento e cura."""
        self.level += 1
        miniboss = is_miniboss_level(self.level)
        self.enemy = create_enemy(self.level, miniboss)
        choose_enemy_intent(self.enemy)

        if miniboss:
            self.player.hp = self.player.max_hp
            self.show_message(f"⚠ MINIBOSS: {self.enemy.name}!")
        else:
            self.player.hp = min(self.player.max_hp, self.player.hp + 8)

        self.start_combat()
        self.state = "player_turn"

    # ========================================================
    # NOTIFICAÇÕES VISUAIS E CONTEXTO DE EFEITOS
    # ========================================================

    def trigger_attack(self, attacker, action=None):
        self.on_event("attack", attacker=attacker, action=action)

    def trigger_flash(self, target):
        self.on_event("flash", target=target)

    def trigger_player_action(self, action):
        self.on_event("player_action", action=action)

    def spawn_damage_text(self, target, text, color):
        x = PLAYER_X if target.is_player else ENEMY_X
        y = (PLAYER_Y if target.is_player else ENEMY_Y) - 60
        self.on_event("floating_text", x=x, y=y, text=text, color=color)

    def spawn_player_text(self, text, color):
        self.on_event("floating_text", x=PLAYER_X, y=PLAYER_Y - 60, text=text, color=color)

    def spawn_enemy_text(self, text, color):
        self.on_event("floating_text", x=ENEMY_X, y=ENEMY_Y - 60, text=text, color=color)

    def show_message(self, text, duration=1500):
        self.message = text
        self.message_timer = duration

    def update_message(self, dt):
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = ""
