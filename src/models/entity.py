class Combatant:
    """Estado de combate; durações avançam por turno do dono, nunca por ação."""
    NEGATIVE_STATUSES = frozenset(('fire', 'poison', 'bleed', 'vulnerable'))

    def __init__(self, name, hp):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self._block_layers = []
        self.strength = 0
        self.weak_turns = 0
        self.statuses = {}
        self.next_turn_energy = 0
        self._bled_this_turn = False

    @property
    def block(self):
        return sum(layer[0] for layer in self._block_layers)

    @block.setter
    def block(self, amount):
        self._block_layers = [[max(0, amount), 2]] if amount > 0 else []

    @property
    def block_turns(self):
        return max((layer[1] for layer in self._block_layers), default=0)

    @property
    def attack_bonus(self):
        return self.strength + self.statuses.get('aura', {}).get('potency', 0)

    def take_damage(self, damage, bypass_block=False):
        damage = max(0, int(damage))
        if not bypass_block:
            for layer in self._block_layers:
                absorbed = min(layer[0], damage)
                layer[0] -= absorbed
                damage -= absorbed
            self._block_layers = [layer for layer in self._block_layers if layer[0] > 0]
        actual = min(self.hp, damage)
        self.hp = max(0, self.hp - damage)
        return actual

    def receive_attack(self, damage, hits=1):
        # O Totem protege o ataque completo, inclusive uma rajada de dardos.
        if 'totem' in self.statuses:
            del self.statuses['totem']
            return 0
        if 'vulnerable' in self.statuses:
            damage = (max(0, damage) * 125 + 99) // 100
        total = 0
        for i in range(max(1, hits)):
            total += self.take_damage(int(damage) // max(1, hits) + (i < int(damage) % max(1, hits)))
        return total

    def add_block(self, amount):
        if amount > 0:
            self._block_layers.append([amount, 2])

    def begin_turn(self):
        self._bled_this_turn = False
        for layer in self._block_layers:
            layer[1] -= 1
        self._block_layers = [layer for layer in self._block_layers if layer[1] > 0]

    def apply_status(self, name, turns, potency=1):
        previous = self.statuses.get(name, {})
        if name == 'fire':
            potency = min(3, previous.get('potency', 0) + potency)
        self.statuses[name] = {'turns': max(turns, previous.get('turns', 0)), 'potency': potency}

    def cleanse(self, all_effects=False):
        self.statuses = {k: v for k, v in self.statuses.items()
                         if not all_effects and k not in self.NEGATIVE_STATUSES}
        self.weak_turns = 0
        if all_effects:
            self.block = 0
            self.strength = 0
            self.next_turn_energy = 0

    def on_attack(self):
        if 'bleed' in self.statuses and not self._bled_this_turn:
            self._bled_this_turn = True
            return self.take_damage(self.statuses['bleed']['potency'], bypass_block=True)
        return 0

    def end_turn_statuses(self):
        ticks = []
        for name, state in list(self.statuses.items()):
            if name == 'fire':
                ticks.append((name, self.take_damage(3 * state['potency'])))
            elif name == 'poison':
                ticks.append((name, self.take_damage(state['potency'], bypass_block=True)))
            if name != 'totem':
                state['turns'] -= 1
                if state['turns'] <= 0:
                    del self.statuses[name]
        return ticks

    def reset_combat_effects(self):
        self.block = 0
        self.strength = 0
        self.weak_turns = 0
        self.statuses.clear()
        self.next_turn_energy = 0
        self._bled_this_turn = False

    def is_alive(self):
        return self.hp > 0


Entity = Combatant
