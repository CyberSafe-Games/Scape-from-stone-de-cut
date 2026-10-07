from src.models.entity import Combatant
from src.models.action import Action


class Enemy(Combatant):
    """Representa um inimigo ou miniboss com atributos e ações extensíveis."""

    def __init__(
        self,
        name,
        hp,
        energy=3,
        max_energy=3,
        actions=None,
        is_miniboss=False,
    ):
        super().__init__(name, hp)
        self.energy = energy
        self.max_energy = max_energy
        self.actions = list(actions) if actions is not None else []
        self.is_miniboss = is_miniboss
        self.is_player = False
        self.intent = None
        self.intent_value = 0
        self.current_action = None

    @property
    def defense(self):
        """Bloqueio defensivo atual do inimigo (compatível com self.block)."""
        return self.block

    @defense.setter
    def defense(self, value):
        self.block = value

    def reset_energy(self):
        """Restaura a energia para o valor máximo no início do turno."""
        self.energy = self.max_energy

    def use_energy(self, amount):
        """Consome energia caso o inimigo tenha o suficiente."""
        if self.energy >= amount:
            self.energy -= amount
            return True
        return False

    def set_intent(self, intent_type, value, action=None):
        """Define a próxima ação planejada pelo inimigo."""
        self.intent = intent_type
        self.intent_value = value
        self.current_action = action

