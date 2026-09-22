from src.models.entity import Combatant
from src.config.settings import HAND_SIZE_START, HAND_SIZE_MAX


class Player(Combatant):
    """Representa o herói controlado pelo jogador."""

    INITIAL_ENERGY_MAX = 2
    MAX_ENERGY_LIMIT = 8
    CEMETERY_ENERGY_COST = 1

    def __init__(self, name="Herói", hp=60, energy_max=INITIAL_ENERGY_MAX, ultimate_threshold=20):
        super().__init__(name, hp)
        self._energy_max = max(0, min(energy_max, self.MAX_ENERGY_LIMIT))
        self.energy = self._energy_max
        self.is_player = True
        self.is_miniboss = False
        self.coins = 0
        self.turn_count = 0

        # Carga da habilidade ultimate: acumula com a energia gasta em cartas.
        self.ultimate_charge = 0
        self.ultimate_threshold = ultimate_threshold

    def get_hand_size(self):
        """Calcula o tamanho da mão baseado na progressão de turnos da partida."""
        if self.turn_count <= 0:
            return HAND_SIZE_START
        return min(2 + self.turn_count, HAND_SIZE_MAX)

    @property
    def energy_max(self):
        """Retorna o valor atual da energia máxima (máximo de 8)."""
        return self._energy_max

    @energy_max.setter
    def energy_max(self, value):
        """Define a energia máxima com limite estrito de 8."""
        self._energy_max = max(0, min(int(value), self.MAX_ENERGY_LIMIT))
        if self.energy > self._energy_max:
            self.energy = self._energy_max

    def increase_max_energy(self, amount=1):
        """Aumenta progressivamente a energia máxima, respeitando o limite de 8."""
        if amount > 0 and self._energy_max < self.MAX_ENERGY_LIMIT:
            self.energy_max = self._energy_max + amount
        return self._energy_max

    def add_coins(self, amount):
        """Incrementa o saldo de moedas do jogador."""
        self.coins += amount

    def reset_energy(self):
        """Restaura a energia para o valor máximo no início do turno."""
        self.energy = self.energy_max

    def use_energy(self, amount):
        """Consome energia se houver saldo suficiente."""
        if self.energy >= amount:
            self.energy -= amount
            return True
        return False

    def can_use_cemetery(self, cost=CEMETERY_ENERGY_COST):
        """Verifica se o jogador possui energia suficiente para utilizar o Cemitério."""
        return self.energy >= cost

    def pay_cemetery_cost(self, cost=CEMETERY_ENERGY_COST):
        """Consome a energia requerida para o Cemitério caso possua saldo suficiente."""
        if self.can_use_cemetery(cost):
            return self.use_energy(cost)
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
