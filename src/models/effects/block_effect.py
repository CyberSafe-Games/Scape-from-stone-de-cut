from src.models.effects.base_effect import CardEffect
from src.config.colors import BLUE


class BlockEffect(CardEffect):
    """Concede pontos de bloqueio ao usuário."""

    def __init__(self, action_name=None):
        self.action_name = action_name

    def apply(self, card, user, target, context):
        user.add_block(card.value)
        action = self.action_name or card.name
        context.trigger_player_action(action)
        context.spawn_player_text(f"+{card.value} bloqueio", BLUE)

        return {"block": card.value}
