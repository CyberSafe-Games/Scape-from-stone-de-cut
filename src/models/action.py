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
    ):
        self.name = name
        self.action_type = action_type  # "attack", "defend", etc.
        self.damage = damage
        self.defense = defense
        self.energy_cost = energy_cost
        self.weight = weight
        self.visual_effect = visual_effect
        self.effect = effect

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
            user.add_block(self.defense)
            from src.config.colors import BLUE
            context.spawn_enemy_text(f"+{self.defense} bloqueio", BLUE)
            return self.defense
        return 0
