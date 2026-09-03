from src.models.effects.base_effect import CardEffect
from src.config.colors import RED


class DamageEffect(CardEffect):
    """Aplica dano direto ao alvo considerando a força do usuário."""

    def __init__(self, action_name=None):
        self.action_name = action_name

    def apply(self, card, user, target, context):
        damage = card.value + getattr(user, "strength", 0)
        actual_damage = target.take_damage(damage)

        action = self.action_name or card.name
        context.trigger_attack("player", action)
        context.trigger_flash("enemy")
        context.spawn_damage_text(target, f"-{actual_damage}", RED)

        return {"damage": actual_damage}


class MultiHitDamageEffect(CardEffect):
    """Aplica múltiplos golpes consecutivos (ex: Golpe Duplo)."""

    def __init__(self, hits=2, action_name="Golpe Duplo"):
        self.hits = hits
        self.action_name = action_name

    def apply(self, card, user, target, context):
        total_damage = 0
        damage_per_hit = card.value + getattr(user, "strength", 0)

        for _ in range(self.hits):
            total_damage += target.take_damage(damage_per_hit)

        action = self.action_name or card.name
        context.trigger_attack("player", action)
        context.trigger_flash("enemy")
        context.spawn_damage_text(target, f"-{total_damage}", RED)

        return {"damage": total_damage, "hits": self.hits}
