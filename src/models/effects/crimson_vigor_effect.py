from src.models.effects.base_effect import CardEffect


class CrimsonVigorEffect(CardEffect):
    """Recuperação e bônus temporário do Carrasco; reaplicar renova, não soma."""
    attack_bonus = 3
    duration = 2
    def apply(self, action, user, target, context):
        recovered = min(action.defense, user.max_hp - user.hp)
        user.hp += recovered
        user.apply_status('aura', 2, 3)
        context.trigger_enemy_action(action.visual_effect or 'healer2')
        context.spawn_enemy_text(f'+{recovered} vida · +3 dano (2 turnos)', (244, 83, 98))
        return {'heal': recovered, 'attack_bonus': 3, 'turns': 2}
