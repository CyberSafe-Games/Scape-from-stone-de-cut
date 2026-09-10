from abc import ABC, abstractmethod

from src.config.colors import RED, GOLD


class UltimateAbility(ABC):
    """Interface abstrata para habilidades ultimate.

    Análoga a CardEffect, mas não depende de uma Card — é ativada
    diretamente pelo motor de combate quando a carga máxima é atingida
    (Open/Closed Principle: novos heróis podem ter sua própria ultimate
    sem alterar o CombatEngine).
    """

    @abstractmethod
    def activate(self, user, target, context):
        """Executa a lógica da ultimate.

        :param user: Quem ativou a ultimate (Player).
        :param target: Alvo da ação (Enemy).
        :param context: Referência ao CombatEngine (para eventos/animações).
        :return: Dicionário com o resultado da ativação.
        """
        pass


class StoneBreakUltimate(UltimateAbility):
    """Ultimate padrão: dano pesado ao inimigo + bloqueio para o jogador."""

    def __init__(self, damage=20, block=10, action_name="Ultimate"):
        self.damage = damage
        self.block = block
        self.action_name = action_name

    def activate(self, user, target, context):
        total_damage = self.damage + getattr(user, "strength", 0)
        actual_damage = target.take_damage(total_damage)
        user.add_block(self.block)

        context.trigger_attack("player", self.action_name)
        context.trigger_flash("enemy")
        context.spawn_damage_text(target, f"-{actual_damage}", RED)
        context.spawn_player_text(f"+{self.block} bloqueio", GOLD)

        return {"damage": actual_damage, "block": self.block}
