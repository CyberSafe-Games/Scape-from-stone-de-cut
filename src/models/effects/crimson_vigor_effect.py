from src.models.effects.base_effect import CardEffect


class CrimsonVigorEffect(CardEffect):
    """Recuperação e bônus temporário do Carrasco; reaplicar renova, não soma."""
    def apply(self, action, user, target, context):
        recovered = min(action.defense, user.max_hp - user.hp)
        user.hp += recovered
        user.apply_status('aura', 2, 4)
        context.trigger_enemy_action(action.visual_effect or 'healer2')
        context.spawn_enemy_text(f'+{recovered} vida · +4 dano (2 turnos)', (244, 83, 98))
        return {'heal': recovered, 'attack_bonus': 4, 'turns': 2}
