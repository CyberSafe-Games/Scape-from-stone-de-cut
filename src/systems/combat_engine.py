import random

from src.models.player import Player
from src.models.deck import DeckManager
from src.models.effects.ultimate_effect import create_ultimate, ULTIMATE_METADATA, DEFAULT_ULTIMATE_ID
from src.systems.card_catalog import CARD_POOL, create_starting_deck
from src.systems.enemy_factory import (
    create_enemy,
    choose_enemy_intent,
    is_miniboss_level,
)
from src.config.colors import RED, BLUE, GOLD
from src.config.layout import PLAYER_X, PLAYER_Y, ENEMY_X, ENEMY_Y


class CombatEngine:
    """Motor central de lógica de combate e regras de jogo (Puro Python).

    Desacoplado de qualquer biblioteca de renderização gráfica (SRP / DIP).
    """

    def __init__(self, on_event_callback=None, map_mode=False):
        self.on_event = on_event_callback or (lambda event, **kwargs: None)
        self.map_mode = map_mode

        self.player = Player("Jaum Manel", 60, energy_max=Player.INITIAL_ENERGY_MAX)
        self.deck_manager = DeckManager(create_starting_deck())
        self.ultimate = create_ultimate(self.player.equipped_ultimate_id)
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

    @property
    def cemetery_cost(self):
        return Player.CEMETERY_ENERGY_COST

    @property
    def ultimate_charge(self):
        return self.player.ultimate_charge

    @property
    def ultimate_threshold(self):
        return self.player.ultimate_threshold

    @property
    def ultimate_ready(self):
        return self.player.is_ultimate_ready()

    @property
    def active_ultimate_id(self):
        return self.player.equipped_ultimate_id

    @property
    def active_ultimate_name(self):
        return getattr(self.ultimate, "name", "Ultimate")

    @property
    def active_ultimate_description(self):
        return getattr(self.ultimate, "description", "")

    @property
    def active_ultimate_color(self):
        return getattr(self.ultimate, "accent_color", GOLD)

    @property
    def unlocked_ultimates(self):
        return list(getattr(self.player, "unlocked_ultimates", [DEFAULT_ULTIMATE_ID]))

    def equip_ultimate(self, ultimate_id):
        if self.player.equip_ultimate(ultimate_id):
            self.ultimate = create_ultimate(ultimate_id)
            meta = ULTIMATE_METADATA.get(ultimate_id, {})
            self.player.ultimate_threshold = meta.get("charge_requirement", 20)
            self.player.ultimate_charge = min(self.player.ultimate_charge, self.player.ultimate_threshold)
            return True
        return False


    # ========================================================
    # FLUXO DO COMBATE
    # ========================================================

    def start_combat(self):
        """Prepara os combatentes e cartas para um novo confronto."""
        self.deck_manager.start_combat()
        self.player.turn_count += 1
        self.deck_manager.draw_cards(self.player.get_hand_size())
        self.player.reset_energy()
        self.player.block = 0
        self.enemy.reset_energy()
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

        # Acumula carga da ultimate proporcionalmente à energia gasta
        self.player.add_ultimate_charge(card.cost)

        # Aplica o efeito polimórfico da carta (Open/Closed Principle)
        card.execute(self.player, self.enemy, context=self)

        # Move a carta da mão para o descarte
        self.deck_manager.discard_card(index)

        # Verifica condição de vitória imediata
        if not self.enemy.is_alive():
            self._on_enemy_defeated()

        return True

    def can_use_cemetery(self):
        """Verifica se o Cemitério pode ser utilizado pelo jogador."""
        return (
            self.state == "player_turn"
            and self.player.can_use_cemetery(self.cemetery_cost)
            and len(self.deck_manager.hand) > 0
        )

    def use_cemetery(self, index):
        """Descarta uma carta da mão pelo Cemitério consumindo 1 de energia."""
        if self.state != "player_turn":
            self.show_message("Cemitério só pode ser usado no seu turno!")
            return False

        if not self.player.can_use_cemetery(self.cemetery_cost):
            self.show_message("Energia insuficiente para usar o Cemitério!")
            return False

        if index < 0 or index >= len(self.deck_manager.hand):
            self.show_message("Nenhuma carta selecionada para descarte!")
            return False

        # Consome o custo de 1 energia
        if not self.player.pay_cemetery_cost(self.cemetery_cost):
            self.show_message("Energia insuficiente para usar o Cemitério!")
            return False

        # Remove a carta da mão e transfere para a pilha de descarte
        discarded_card = self.deck_manager.discard_card(index)
        if discarded_card:
            self.spawn_player_text("-1 Energia", (80, 200, 255))
            self.spawn_player_text(f"Cemitério: {discarded_card.name}", (185, 145, 230))
            self.show_message(f"Carta '{discarded_card.name}' descartada no Cemitério!", duration=1600)
            self.on_event("cemetery_discard", card=discarded_card)
            return True

        return False

    def activate_ultimate(self):
        """Ativa a habilidade ultimate do jogador, se a carga estiver completa."""
        if self.state != "player_turn":
            return False

        if not self.player.consume_ultimate():
            self.show_message("Ultimate ainda não está pronta!")
            return False

        self.ultimate.activate(self.player, self.enemy, context=self)

        # Verifica condição de vitória imediata
        if not self.enemy.is_alive():
            self._on_enemy_defeated()

        return True

    def _on_enemy_defeated(self):
        """Concede recompensa de moedas e avança para a tela de vitória."""
        if self.enemy.is_miniboss:
            coin_amount = random.randint(50, 70)
        else:
            coin_amount = random.randint(30, 50)
        self.on_event(
            "coin_drop",
            amount=coin_amount,
            x=ENEMY_X,
            y=ENEMY_Y,
        )
        self.state = "victory"
        self.generate_rewards()

    def end_turn(self):
        """Encerra a vez do jogador e passa o turno para o inimigo."""
        if self.state != "player_turn":
            return

        self.deck_manager.discard_hand()
        self.state = "enemy_turn"
        self.on_event("turn_ended")

    def enemy_turn(self):
        """Executa a ação calculada da inteligência artificial do inimigo."""
        action = getattr(self.enemy, "current_action", None)
        attacked = False
        if action is not None:
            self.enemy.use_energy(action.energy_cost)
            if hasattr(action, "execute") and callable(action.execute) and action.action_type != "attack":
                action.execute(self.enemy, self.player, context=self)
            elif action.action_type == "attack":
                damage = self._apply_weakness_modifier(action.damage)
                actual_damage = self.player.take_damage(damage)
                self.trigger_attack("enemy", action=action.visual_effect or "atk")
                self.trigger_flash("player")
                self.spawn_player_text(f"-{actual_damage}", RED)
                attacked = True
            else:
                block = action.defense
                self.enemy.add_block(block)
                self.trigger_enemy_action("def")
                self.spawn_enemy_text(f"+{block} bloqueio", BLUE)
        else:
            if self.enemy.intent == "attack":
                damage = self._apply_weakness_modifier(self.enemy.intent_value)
                actual_damage = self.player.take_damage(damage)

                self.trigger_attack("enemy", action="atk")
                self.trigger_flash("player")
                self.spawn_player_text(f"-{actual_damage}", RED)
                attacked = True
            else:
                block = self.enemy.intent_value
                self.enemy.add_block(block)
                self.trigger_enemy_action("def")
                self.spawn_enemy_text(f"+{block} bloqueio", BLUE)

        self._advance_status_effects(attacked=attacked)

        if not self.player.is_alive():
            self.state = "game_over"
            self.on_event("game_over")
            return

        self.state = "enemy_resolving"

    def finish_enemy_turn(self):
        """Finaliza a resolução da rodada e inicia o novo turno do jogador."""
        self.enemy.reset_energy()
        choose_enemy_intent(self.enemy)
        self.player.block = 0
        self.player.increase_max_energy(1)
        self.player.reset_energy()
        self.player.turn_count += 1
        self.deck_manager.draw_cards(self.player.get_hand_size())
        self.state = "player_turn"

    def _apply_weakness_modifier(self, damage):
        """Reduz o dano do inimigo quando ele está sob Fraqueza."""
        if getattr(self.enemy, "weak_turns", 0) > 0:
            weakened = max(0, int(round(damage * 0.75)))
            reduction = max(0, damage - weakened)
            if reduction > 0:
                self.spawn_enemy_text(f"Fraqueza -{reduction}", (125, 205, 120))
            return weakened
        return damage

    def _advance_status_effects(self, attacked=False):
        """Consome durações de efeitos temporários ao final da ação do inimigo."""
        if getattr(self.enemy, "weak_turns", 0) > 0:
            self.enemy.weak_turns = max(0, self.enemy.weak_turns - 1)

    # ========================================================
    # PROGRESSÃO E RECOMPENSAS
    # ========================================================

    def generate_rewards(self):
        """Gera 3 cartas aleatórias do catálogo para escolha."""
        self.reward_cards = [
            random.choice(CARD_POOL).copy() for _ in range(3)
        ]

    def choose_reward(self, index):
        """Seleciona recompensa; no modo mapa, retorna ao mapa após a fase."""
        if self.state != "victory":
            return
        if 0 <= index < len(self.reward_cards):
            self.deck_manager.add_to_deck(self.reward_cards[index])
            if self.map_mode:
                self.finish_map_phase()
            else:
                self.next_level()

    def skip_reward(self):
        """Pula recompensa; no modo mapa, retorna ao mapa após a fase."""
        if self.state != "victory":
            return
        if self.map_mode:
            self.finish_map_phase()
        else:
            self.next_level()

    def finish_map_phase(self):
        """Fecha a fase uma única vez, depois da recompensa.

        A cena responsável pelo mapa valida, grava e confirma o desbloqueio.
        Não cria automaticamente a batalha do próximo andar.
        """
        if not self.map_mode or self.state != "victory":
            return
        if self.enemy.is_miniboss:
            self.player.hp = self.player.max_hp
        else:
            self.player.hp = min(self.player.max_hp, self.player.hp + 8)
        self.player.reset_energy()
        self.state = "phase_complete"
        self.on_event("phase_complete", level=self.level)

    def next_level(self):
        """Avança de andar com balanceamento e cura."""
        self.level += 1
        miniboss = is_miniboss_level(self.level)
        self.enemy = create_enemy(self.level, miniboss)
        choose_enemy_intent(self.enemy)

        if miniboss:
            self.player.hp = self.player.max_hp
            self.show_message(f"MINIBOSS: {self.enemy.name}!")
        else:
            self.player.hp = min(self.player.max_hp, self.player.hp + 8)

        self.start_combat()
        self.state = "player_turn"
        self.on_event("checkpoint", level=self.level)

    def resume_from_save(self, data, save_manager, level=None):
        """Restaura o progresso e recomeça o combate no andar salvo.

        A partida é retomada no início do confronto, não no meio do turno.
        """
        save_manager.apply_to_game(data, self.player, self.deck_manager)
        self.player.name = "Jaum Manel"
        self.equip_ultimate(self.player.equipped_ultimate_id)
        self.level = data["progresso"]["andar"] if level is None else level
        self.enemy = create_enemy(self.level, is_miniboss_level(self.level))
        choose_enemy_intent(self.enemy)
        self.start_combat()

    # ========================================================
    # NOTIFICAÇÕES VISUAIS E CONTEXTO DE EFEITOS
    # ========================================================

    def trigger_attack(self, attacker, action=None):
        self.on_event("attack", attacker=attacker, action=action)

    def trigger_flash(self, target):
        self.on_event("flash", target=target)

    def trigger_player_action(self, action):
        self.on_event("player_action", action=action)

    def trigger_enemy_action(self, action):
        self.on_event("enemy_action", action=action)

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
