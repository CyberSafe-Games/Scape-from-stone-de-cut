from src.models.entity import Combatant


class Player(Combatant):
    """Representa o herói controlado pelo jogador."""

    def __init__(self, name="Herói", hp=60, energy_max=3):
        super().__init__(name, hp)
        self.energy_max = energy_max
        self.energy = energy_max
        self.is_player = True
        self.is_miniboss = False

    def reset_energy(self):
        """Restaura a energia para o valor máximo no início do turno."""
        self.energy = self.energy_max

    def use_energy(self, amount):
        """Consome energia ao jogar uma carta se houver saldo suficiente."""
        if self.energy >= amount:
            self.energy -= amount
            return True
        return False
