class Combatant:
    """Classe base para qualquer entidade envolvida em combate (Jogador ou Inimigo).

    Segue o princípio de substituição de Liskov (LSP).
    """

    def __init__(self, name, hp):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.block = 0
        self.strength = 0

    def take_damage(self, damage):
        """Aplica dano considerando o valor atual de bloqueio."""
        damage = max(0, damage)
        absorbed = min(self.block, damage)
        self.block -= absorbed
        remaining_damage = damage - absorbed
        self.hp = max(0, self.hp - remaining_damage)
        return remaining_damage

    def add_block(self, amount):
        """Acrescenta bloqueio defensivo."""
        self.block += max(0, amount)

    def is_alive(self):
        """Retorna True se ainda possuir pontos de vida."""
        return self.hp > 0


# Alias para compatibilidade
Entity = Combatant
