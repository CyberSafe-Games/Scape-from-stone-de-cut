from src.models.effects.base_effect import CardEffect


class GoldenAmuletEffect(CardEffect):
    """Zanzara recupera vida e renova uma força temporária, sem causar dano."""

    def apply(self, action, user, target, context):
        recovered = max(0, min(action.defense, user.max_hp-user.hp))
        user.hp += recovered
        user.apply_status('aura', 2, 4)
        context.trigger_enemy_action(action.visual_effect or 'healer2')
        context.spawn_enemy_text(f'+{recovered} vida · +4 dano (2 turnos)', (246, 199, 83))
        return {'heal': recovered, 'attack_bonus': 4, 'turns': 2}
