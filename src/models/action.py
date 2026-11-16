def action_status_effects(action):
    """Normaliza ações antigas de um efeito e ações com múltiplos debuffs."""
    single = getattr(action,'status_effect',None)
    effects = [tuple(single)] if single else []
    effects.extend(tuple(effect) for effect in (getattr(action,'status_effects',()) or ()))
    return tuple(dict.fromkeys(effects))


class Action:
    """Representa uma ação ou habilidade de um combatente/inimigo.
    
    Projetada para ser extensível, com suporte a custos de energia, pesos probabilísticos,
    ganchos para efeitos visuais futuros e efeitos polimórficos de combate.
    """

    def __init__(
        self,
        name: str,
        action_type: str = "attack",
        damage: int = 0,
        defense: int = 0,
        energy_cost: int = 0,
        weight: float = 1.0,
        visual_effect: str | None = None,
        effect=None,
        status_effect=None,
        status_effects=None,
        self_heal=0,
        self_attack_buff=None,
    ):
        self.name = name
        self.action_type = action_type  # "attack", "defend", etc.
        self.damage = damage
        self.defense = defense
        self.energy_cost = energy_cost
        self.weight = weight
        self.visual_effect = visual_effect
        self.effect = effect
        self.status_effect = status_effect
        self.status_effects = tuple(status_effects or ())
        self.self_heal = self_heal
        self.self_attack_buff = self_attack_buff

    @property
    def value(self) -> int:
        """Retorna o valor principal associado ao tipo de ação."""
        return self.damage if self.action_type == "attack" else self.defense

    def execute(self, user, target, context):
        """Executa o efeito da ação no alvo ou usuário."""
        if self.effect is not None:
            return self.effect.apply(self, user, target, context)

        if self.action_type == "attack":
            actual_damage = target.take_damage(self.damage)
            context.trigger_attack("enemy", action=self.visual_effect)
            context.trigger_flash("player")
            from src.config.colors import RED
            context.spawn_player_text(f"-{actual_damage}", RED)
            return actual_damage
        elif self.action_type in ("defend", "defense"):
            from src.config.colors import BLUE
            user.add_block(self.defense)
            if self.self_heal and 'no_heal' not in user.statuses:
                recovered = min(self.self_heal, user.max_hp - user.hp)
                user.hp += recovered
                if recovered:
                    context.spawn_enemy_text(f"+{recovered} vida", BLUE)
            context.trigger_enemy_action(self.visual_effect or 'def')
            context.spawn_enemy_text(f"+{self.defense} bloqueio", BLUE)
            return self.defense
        return 0
