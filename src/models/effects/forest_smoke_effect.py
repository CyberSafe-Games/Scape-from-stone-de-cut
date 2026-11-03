"""Fumaça restauradora da dupla da Mata Sombria."""
from src.models.effects.base_effect import CardEffect


class ForestSmokeEffect(CardEffect):
    """Cura limitada à vida máxima e força temporária sem acúmulo por reaplicação."""

    def apply(self, action, user, target, context):
        recovered = min(action.defense, max(0, user.max_hp - user.hp))
        user.hp += recovered
        user.apply_status('aura', 2, 3)
        context.trigger_enemy_action(action.visual_effect or 'healer2')
        context.spawn_enemy_text(f'+{recovered} vida · +3 dano (2 turnos)', (157, 207, 93))
        return {'heal': recovered, 'attack_bonus': 3, 'turns': 2}
