from __future__ import annotations

from abc import ABC, abstractmethod

from src.config.colors import RED, GOLD, BLUE, WHITE, GREEN

DEFAULT_ULTIMATE_ID = "mana_ancestral"


class UltimateAbility(ABC):
    """Interface base para habilidades ultimate do herói."""

    ultimate_id = "base"
    name = "Ultimate"
    action_name = "Ultimate"
    description = ""
    accent_color = GOLD
    charge_requirement = 20

    @abstractmethod
    def activate(self, user, target, context):
        """Executa a lógica da ultimate."""


class ManaAncestralUltimate(UltimateAbility):
    """Ultimate padrão: restaura a energia e compra cartas."""

    ultimate_id = DEFAULT_ULTIMATE_ID
    name = "Mana Ancestral"
    action_name = "Mana Ancestral"
    description = "Restaura a energia ao máximo e compra 3 cartas"
    accent_color = (110, 190, 255)

    def __init__(self, draw_count=3):
        self.draw_count = draw_count

    def activate(self, user, target, context):
        previous_energy = user.energy
        user.energy = user.energy_max
        context.deck_manager.draw_cards(self.draw_count)
        context.trigger_player_action(self.action_name)
        restored = max(0, user.energy_max - previous_energy)
        if restored:
            context.spawn_player_text(f"+{restored} energia", self.accent_color)
        context.spawn_player_text(f"+{self.draw_count} cartas", WHITE)
        context.show_message("Mana Ancestral ativada!", duration=1800)
        return {"energy_restored": restored, "cards_drawn": self.draw_count}


class ForcasAncestraisUltimate(UltimateAbility):
    """Concede poder ofensivo e defesa permanente no combate atual."""

    ultimate_id = "forcas_ancestrais"
    name = "Forças Ancestrais"
    action_name = "Forças Ancestrais"
    description = "Ganha 4 de força e 15 de bloqueio"
    accent_color = GOLD

    def __init__(self, strength_gain=4, block_gain=15):
        self.strength_gain = strength_gain
        self.block_gain = block_gain

    def activate(self, user, target, context):
        user.strength = getattr(user, "strength", 0) + self.strength_gain
        user.add_block(self.block_gain)
        context.trigger_player_action(self.action_name)
        context.spawn_player_text(f"+{self.strength_gain} força", RED)
        context.spawn_player_text(f"+{self.block_gain} bloqueio", BLUE)
        context.show_message("Forças Ancestrais ativadas!", duration=1800)
        return {"strength": self.strength_gain, "block": self.block_gain}


class RugidoDaFlorestaUltimate(UltimateAbility):
    """Causa dano em área e aplica fraqueza.

    Nesta versão há apenas um inimigo por combate, mas a lógica já é preparada
    para atingir múltiplos alvos quando o sistema for expandido.
    """

    ultimate_id = "rugido_da_floresta"
    name = "Rugido da Floresta"
    action_name = "Rugido da Floresta"
    description = "Causa dano em todos os inimigos e aplica Fraqueza (2)"
    accent_color = GREEN

    def __init__(self, damage=12, weak_turns=2):
        self.damage = damage
        self.weak_turns = weak_turns

    def _targets(self, target, context):
        enemies = getattr(context, "enemies", None)
        if isinstance(enemies, list) and enemies:
            return [enemy for enemy in enemies if getattr(enemy, "hp", 0) > 0]
        return [target] if target is not None else []

    def activate(self, user, target, context):
        targets = self._targets(target, context)
        total_damage = 0
        hits = 0
        context.trigger_player_action(self.action_name)
        for enemy in targets:
            damage = self.damage + getattr(user, "strength", 0)
            actual = enemy.take_damage(damage)
            enemy.weak_turns = getattr(enemy, "weak_turns", 0) + self.weak_turns
            total_damage += actual
            hits += 1
        if targets:
            context.trigger_flash("enemy")
        if total_damage:
            text = f"-{total_damage}" if hits == 1 else f"-{total_damage} área"
            context.spawn_damage_text(targets[0], text, RED)
        if targets:
            context.spawn_enemy_text(f"Fraqueza {self.weak_turns}", self.accent_color)
        context.show_message("Rugido da Floresta ecoa pelo campo!", duration=1800)
        return {"damage": total_damage, "weakness": self.weak_turns, "targets": hits}


ULTIMATE_REGISTRY = {
    ManaAncestralUltimate.ultimate_id: ManaAncestralUltimate,
    ForcasAncestraisUltimate.ultimate_id: ForcasAncestraisUltimate,
    RugidoDaFlorestaUltimate.ultimate_id: RugidoDaFlorestaUltimate,
}

ULTIMATE_METADATA = {
    ultimate_id: {
        "name": cls.name,
        "description": cls.description,
        "accent_color": cls.accent_color,
        "charge_requirement": cls.charge_requirement,
    }
    for ultimate_id, cls in ULTIMATE_REGISTRY.items()
}


def create_ultimate(ultimate_id: str | None):
    """Cria uma instância da ultimate solicitada, com fallback seguro."""
    cls = ULTIMATE_REGISTRY.get(ultimate_id or DEFAULT_ULTIMATE_ID, ManaAncestralUltimate)
    return cls()


def known_ultimate_ids():
    return list(ULTIMATE_REGISTRY.keys())
