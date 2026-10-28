import random

from src.models.player import Player
from src.models.deck import DeckManager
from src.models.effects.ultimate_effect import create_ultimate, ULTIMATE_METADATA, DEFAULT_ULTIMATE_ID
from src.systems.card_catalog import CARD_POOL, create_starting_deck
from src.systems.enemy_factory import (
    create_enemy,
    choose_enemy_intent,
    is_miniboss_level, create_road_enemy, choose_next_action, create_point_enemy,
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
        self.encounter_kind = "point"
        self.encounter_index = None
        self.enemy_actions_remaining = 0
        self.cemetery_swap_used = False

        miniboss = is_miniboss_level(self.level)
        self.enemy = create_enemy(self.level, miniboss)
        choose_next_action(self.enemy)

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
        """Cada luta reinicia o ritmo de energia e tamanho da mão.

        Vida, moedas, baralho e carga da ultimate continuam sendo da RUN.
        """
        self.player.energy_max = Player.INITIAL_ENERGY_MAX
        self.player.turn_count = 0
        self.player.strength = 0  # Buffs permanentes duram a luta, não a RUN.
        self.player.weak_turns = 0
        self.player.reset_combat_effects()
        self.enemy.reset_combat_effects()
        self.deck_manager.start_combat()
        self.player.turn_count += 1
        self.deck_manager.draw_cards(self.player.get_hand_size())
        self.player.reset_energy()
        self.player.block = 0
        self.enemy.reset_energy()
        self.enemy.block = 0
        self.enemy_actions_remaining = 0
        self.cemetery_swap_used = False
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

        if card.card_type == 'attack':
            self._bleed_on_attack(self.player)
            if not self.player.is_alive():
                self.deck_manager.discard_card(index)
                self.state = 'game_over'
                self.on_event('game_over')
                return True

        # Aplica o efeito polimórfico da carta (Open/Closed Principle)
        card.execute(self.player, self.enemy, context=self)

        # Move a carta da mão para o descarte
        self.deck_manager.discard_card(index)

        # Verifica condição de vitória imediata
        if not self.enemy.is_alive():
            self._on_enemy_defeated()

        return True

    def can_use_cemetery(self):
        """Descarte repetível no próprio turno, ao custo de 1 energia por carta."""
        return (
            self.state == "player_turn"
            and bool(self.deck_manager.hand)
            and self.player.can_use_cemetery(self.cemetery_cost)
        )

    def use_cemetery(self, index):
        """Descarta uma carta pagando energia, sem comprar outra imediatamente."""
        if self.state != "player_turn":
            self.show_message("Cemitério só pode ser usado no seu turno!")
            return False
        if not 0 <= index < len(self.deck_manager.hand):
            self.show_message("Selecione uma carta válida para descartar!")
            return False
        if not self.player.can_use_cemetery(self.cemetery_cost):
            self.show_message("Energia insuficiente para descartar!")
            return False
        # Só debita após validar o índice e o saldo.
        if not self.player.pay_cemetery_cost(self.cemetery_cost):
            return False
        discarded = self.deck_manager.discard_card(index)
        self.show_message(f"{discarded.name} descartada (-{self.cemetery_cost} energia).", duration=1400)
        self.on_event("cemetery_discard", card=discarded)
        return True

    def can_swap_cemetery(self, index=None):
        """Permite no máximo uma troca por turno, sem custo de energia."""
        if self.state != "player_turn" or self.cemetery_swap_used:
            return False
        if index is None:
            return bool(self.deck_manager.hand) and bool(
                self.deck_manager.draw_pile or self.deck_manager.discard_pile
            )
        return self.deck_manager.has_replacement_for(index)

    def swap_cemetery(self, index):
        """Substitui uma carta da mão por uma do baralho, uma vez por turno."""
        if self.state != "player_turn":
            self.show_message("Trocas só podem ser feitas no seu turno!")
            return False
        if self.cemetery_swap_used:
            self.show_message("Você já usou sua troca neste turno!")
            return False
        if not 0 <= index < len(self.deck_manager.hand):
            self.show_message("Selecione uma carta válida para trocar!")
            return False
        if not self.deck_manager.has_replacement_for(index):
            self.show_message("Não há outra carta disponível para troca!")
            return False

        swapped = self.deck_manager.swap_card(index)
        if swapped is None:
            self.show_message("Não foi possível trocar a carta!")
            return False
        discarded, received = swapped
        self.cemetery_swap_used = True
        self.show_message(f"Trocou {discarded.name} por {received.name}.", duration=1600)
        self.on_event("cemetery_swap", old_card=discarded, new_card=received)
        return True

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

        self._tick_statuses(self.player)
        if not self.player.is_alive():
            self.state = 'game_over'
            self.on_event('game_over')
            return
        self.enemy.begin_turn()

        # A mão é persistente: só cartas jogadas/descartadas saem dela.
        self.enemy_actions_remaining = getattr(self.enemy, "actions_per_turn", 1)
        self.state = "enemy_turn"
        self.on_event("turn_ended")

    def enemy_turn(self):
        """Executa a ação calculada da inteligência artificial do inimigo."""
        if self.state != 'enemy_turn':
            return
        action = getattr(self.enemy, "current_action", None)
        if (action is not None and action.action_type == 'attack') or (action is None and self.enemy.intent == 'attack'):
            self._bleed_on_attack(self.enemy)
            if not self.enemy.is_alive():
                self._on_enemy_defeated()
                return
        attacked = False
        if action is not None:
            self.enemy.use_energy(action.energy_cost)
            if action.action_type == "heal":
                amount = min(action.defense, self.enemy.max_hp - self.enemy.hp)
                self.enemy.hp += amount
                self.trigger_enemy_action(action.visual_effect or "healer2")
                self.spawn_enemy_text(f"+{amount} vida", BLUE)
            elif hasattr(action, "execute") and callable(action.execute) and action.action_type != "attack":
                action.execute(self.enemy, self.player, context=self)
            elif action.action_type == "attack":
                damage = self._apply_weakness_modifier(action.damage)
                protected = 'totem' in self.player.statuses
                actual_damage = self.player.receive_attack(damage + self.enemy.attack_bonus)
                if getattr(action, 'status_effect', None) and not protected and self.player.is_alive():
                    self.player.apply_status(*action.status_effect)
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
                actual_damage = self.player.receive_attack(damage + self.enemy.attack_bonus)

                self.trigger_attack("enemy", action="atk")
                self.trigger_flash("player")
                self.spawn_player_text(f"-{actual_damage}", RED)
                attacked = True
            else:
                block = self.enemy.intent_value
                self.enemy.add_block(block)
                self.trigger_enemy_action("def")
                self.spawn_enemy_text(f"+{block} bloqueio", BLUE)

        if getattr(self.enemy, "special_interval", 0):
            self.enemy.action_counter += 1
        self.enemy_actions_remaining = max(0, self.enemy_actions_remaining - 1)

        if not self.player.is_alive():
            self.state = "game_over"
            self.on_event("game_over")
            return

        self.state = "enemy_resolving"

    def finish_enemy_turn(self):
        """Resolve cada ação em sequência; duas no caso de Corpo Seco."""
        if self.state != 'enemy_resolving':
            return
        if self.enemy_actions_remaining > 0:
            choose_next_action(self.enemy)
            self.state = "enemy_turn"
            return
        self._advance_status_effects()
        self._tick_statuses(self.enemy)
        if not self.enemy.is_alive():
            self._on_enemy_defeated()
            return
        self.enemy.reset_energy()
        choose_next_action(self.enemy)
        self.player.begin_turn()
        self.player.increase_max_energy(1)
        self.player.reset_energy()
        self.player.energy = min(self.player.MAX_ENERGY_LIMIT, self.player.energy + self.player.next_turn_energy)
        self.player.next_turn_energy = 0
        self.player.turn_count += 1
        self.deck_manager.refill_hand(self.player.get_hand_size())
        self.cemetery_swap_used = False
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

    def _advance_status_effects(self):
        """Fraqueza dura rodadas completas, incluindo todos os atos de chefes."""
        if getattr(self.enemy, "weak_turns", 0) > 0:
            self.enemy.weak_turns = max(0, self.enemy.weak_turns - 1)

    def _bleed_on_attack(self, combatant):
        damage = combatant.on_attack()
        if damage:
            self.spawn_damage_text(combatant, f'Sangramento -{damage}', RED)

    def _tick_statuses(self, combatant):
        for name, damage in combatant.end_turn_statuses():
            self.spawn_damage_text(combatant, f'{"Fogo" if name == "fire" else "Veneno"} -{damage}', RED)

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
        choose_next_action(self.enemy)

        if miniboss:
            self.player.hp = self.player.max_hp
            self.show_message(f"MINIBOSS: {self.enemy.name}!")
        else:
            self.player.hp = min(self.player.max_hp, self.player.hp + 8)

        self.start_combat()
        self.state = "player_turn"
        self.on_event("checkpoint", level=self.level)

    def resume_from_save(self, data, save_manager, level=None, encounter_kind="point", encounter_index=None):
        """Restaura o progresso e recomeça o combate no andar salvo.

        A partida é retomada no início do confronto, não no meio do turno.
        """
        save_manager.apply_to_game(data, self.player, self.deck_manager)
        self.player.name = "Jaum Manel"
        self.equip_ultimate(self.player.equipped_ultimate_id)
        self.level = data["progresso"]["andar"] if level is None else level
        self.encounter_kind = encounter_kind
        self.encounter_index = encounter_index
        if encounter_kind == "road":
            self.enemy = create_road_enemy(self.level)
        elif encounter_kind == "point":
            self.enemy = create_point_enemy(self.level)
        else:
            self.enemy = create_enemy(self.level, is_miniboss_level(self.level))
        choose_next_action(self.enemy)
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
