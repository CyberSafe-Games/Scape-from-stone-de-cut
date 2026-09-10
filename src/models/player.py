from src.models.entity import Combatant


class Player(Combatant):
    """Representa o herói controlado pelo jogador."""

    def __init__(self, name="Herói", hp=60, energy_max=3, ultimate_threshold=20):
        super().__init__(name, hp)
        self.energy_max = energy_max
        self.energy = energy_max
        self.is_player = True
        self.is_miniboss = False
        self.coins = 0

        # Carga da habilidade ultimate: acumula com a energia gasta em cartas.
        self.ultimate_charge = 0
        self.ultimate_threshold = ultimate_threshold

    def add_coins(self, amount):
        """Incrementa o saldo de moedas do jogador."""
        self.coins += amount

    def reset_energy(self):
        """Restaura a energia para o valor máximo no início do turno."""
        self.energy = self.energy_max

    def use_energy(self, amount):
        """Consome energia ao jogar uma carta se houver saldo suficiente."""
        if self.energy >= amount:
            self.energy -= amount
            return True
        return False

    def add_ultimate_charge(self, amount):
        """Acumula carga da ultimate proporcionalmente à energia gasta."""
        self.ultimate_charge = min(
            self.ultimate_threshold, self.ultimate_charge + max(0, amount)
        )

    def is_ultimate_ready(self):
        """Retorna True se a carga atingiu o limite necessário para ativar a ultimate."""
        return self.ultimate_charge >= self.ultimate_threshold

    def consume_ultimate(self):
        """Zera a carga ao ativar a ultimate, caso ela esteja pronta."""
        if self.is_ultimate_ready():
            self.ultimate_charge = 0
            return True
        return False
