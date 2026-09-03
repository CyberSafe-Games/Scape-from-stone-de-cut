from src.models.effects.base_effect import CardEffect
from src.config.colors import GOLD


class StrengthBuffEffect(CardEffect):
    """Concede aumento permanente de força ao usuário durante o combate."""

    def __init__(self, action_name=None):
        self.action_name = action_name

    def apply(self, card, user, target, context):
        user.strength = getattr(user, "strength", 0) + card.value
        action = self.action_name or card.name
        context.trigger_player_action(action)
        context.spawn_player_text(f"+{card.value} força", GOLD)

        return {"strength": card.value}
