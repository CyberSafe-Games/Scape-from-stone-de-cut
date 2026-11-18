STACK_STATUS_DAMAGE = {'poison': 5, 'bleed': 3}
STACK_STATUS_LIMIT = 5
STACK_STATUS_TURNS = 2
STACK_APPLICATION_LIMIT = 2
BLEED_TRIGGER_LIMIT = 2


class Combatant:
    """Estado de combate; durações avançam por turno do dono, nunca por ação."""
    NEGATIVE_STATUSES = frozenset((
        'fire', 'poison', 'bleed', 'burn', 'vulnerable', 'weak', 'stun',
        'no_heal', 'no_block', 'poison_on_damage',
        'burn_on_action', 'shock',
    ))

    def __init__(self, name, hp):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self._block_layers = []
        self.strength = 0
        self._strength_buffs = []
        self.weak_turns = 0
        self.statuses = {}
        self.next_turn_energy = 0
        self.bleed_triggers_this_turn = 0
        self.attack_lock_turns = 0
        self.attack_lock_pending = 0
        self.last_totem_trigger = None

    @property
    def poison_stacks(self):
        return self.statuses.get('poison', {}).get('potency', 0)

    @property
    def poison_turns(self):
        return self.statuses.get('poison', {}).get('turns', 0)

    @property
    def bleed_stacks(self):
        return self.statuses.get('bleed', {}).get('potency', 0)

    @property
    def bleed_turns(self):
        return self.statuses.get('bleed', {}).get('turns', 0)

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
        return (
            self.strength
            + self.temporary_strength
            + self.statuses.get('aura', {}).get('potency', 0)
        )

    @property
    def temporary_strength(self):
        return sum(layer['potency'] for layer in self._strength_buffs)

    def apply_strength(self, amount, turns):
        if amount <= 0 or turns <= 0:
            return
        self._strength_buffs.append({'potency': amount, 'turns': turns})
        self._refresh_strength_status()

    def _refresh_strength_status(self):
        if self._strength_buffs:
            self.statuses['strength'] = {
                'turns': max(layer['turns'] for layer in self._strength_buffs),
                'potency': self.temporary_strength,
            }
        else:
            self.statuses.pop('strength', None)

    def take_damage(self, damage, bypass_block=False):
        damage = max(0, int(damage))
        if not bypass_block:
            for layer in self._block_layers:
                absorbed = min(layer[0], damage)
                layer[0] -= absorbed
                damage -= absorbed
            self._block_layers = [layer for layer in self._block_layers if layer[0] > 0]
        actual = min(self.hp, damage)
        if getattr(self, 'invulnerable', False):
            return 0
        self.hp = max(0, self.hp - damage)
        if actual and 'poison_on_damage' in self.statuses:
            self.add_stacks('poison', self.statuses['poison_on_damage']['potency'])
        return actual

    def receive_attack(self, damage, hits=1):
        self.last_totem_trigger = None
        # O Totem protege o ataque completo, inclusive uma rajada de dardos.
        if 'totem' in self.statuses:
            self.last_totem_trigger = self.statuses['totem'].get('trigger')
            del self.statuses['totem']
            return 0
        if 'vulnerable' in self.statuses:
            damage = (max(0, damage) * 125 + 99) // 100
        total = 0
        for i in range(max(1, hits)):
            total += self.take_damage(int(damage) // max(1, hits) + (i < int(damage) % max(1, hits)))
        return total

    def add_block(self, amount):
        if amount > 0 and 'no_block' not in self.statuses:
            self._block_layers.append([amount, 2])

    def remove_block(self, amount):
        """Remove Escudo sem dano nem renovação das durações existentes."""
        remaining = max(0, int(amount))
        removed = 0
        for layer in self._block_layers:
            consumed = min(layer[0], remaining)
            layer[0] -= consumed
            remaining -= consumed
            removed += consumed
        self._block_layers = [layer for layer in self._block_layers if layer[0] > 0]
        return removed

    def begin_turn(self):
        self.bleed_triggers_this_turn = 0
        for layer in self._block_layers:
            layer[1] -= 1
        self._block_layers = [layer for layer in self._block_layers if layer[1] > 0]

    def apply_status(self, name, turns, potency=1):
        if name in STACK_STATUS_DAMAGE:
            return self.add_stacks(name, potency) > 0
        if name == 'shock' and not getattr(self, 'is_player', False):
            return False
        if name in self.NEGATIVE_STATUSES and 'debuff_immunity' in self.statuses:
            return False
        previous = self.statuses.get(name, {})
        if name == 'fire':
            potency = min(3, previous.get('potency', 0) + potency)
        self.statuses[name] = {'turns': max(turns, previous.get('turns', 0)), 'potency': potency}
        if name == 'weak':
            self.weak_turns = max(self.weak_turns, turns)
        return True

    def add_stacks(self, name, amount, turns=3, additional_cap=None):
        """Acrescenta acúmulos aos debuffs que usam intensidade acumulável."""
        if name == 'shock' and not getattr(self, 'is_player', False):
            return 0
        if amount <= 0 or name in self.NEGATIVE_STATUSES and 'debuff_immunity' in self.statuses:
            return 0
        previous = self.statuses.get(name, {})
        current = previous.get('potency', 0)
        added = min(amount, additional_cap) if additional_cap is not None else amount
        if name in STACK_STATUS_DAMAGE:
            if added <= 0:
                return 0
            added = min(added, STACK_APPLICATION_LIMIT, STACK_STATUS_LIMIT - current)
            self.statuses[name] = {'turns': STACK_STATUS_TURNS, 'potency': current + added}
            return added
        self.statuses[name] = {
            'turns': max(turns, previous.get('turns', 0)),
            'potency': current + added,
        }
        return added

    def cleanse(self, all_effects=False):
        self.statuses = {k: v for k, v in self.statuses.items()
                         if not all_effects and k not in self.NEGATIVE_STATUSES}
        self.weak_turns = 0
        if all_effects:
            self.block = 0
            self.strength = 0
            self._strength_buffs.clear()
            self.next_turn_energy = 0
            self.attack_lock_turns = 0
            self.attack_lock_pending = 0

    def remove_positive_effects(self):
        """Dissipa benefícios sem apagar os debuffs aplicados pelo adversário."""
        self.statuses = {key: value for key, value in self.statuses.items()
                         if key in self.NEGATIVE_STATUSES}
        self.block = 0
        self.strength = 0
        self._strength_buffs.clear()
        self.next_turn_energy = 0

    def on_attack(self):
        if self.bleed_stacks and self.bleed_triggers_this_turn < BLEED_TRIGGER_LIMIT:
            self.bleed_triggers_this_turn += 1
            return self.take_damage(STACK_STATUS_DAMAGE['bleed'] * self.bleed_stacks, bypass_block=True)
        return 0

    def end_turn_statuses(self):
        ticks = []
        for name in tuple(self.statuses):
            if name == 'strength':
                continue
            state = self.statuses[name]
            if name == 'fire':
                ticks.append((name, self.take_damage(3 * state['potency'])))
            elif name == 'poison':
                ticks.append((name, self.take_damage(STACK_STATUS_DAMAGE['poison'] * state['potency'], bypass_block=True)))
            elif name == 'burn':
                ticks.append((name, self.take_damage(state['potency'], bypass_block=True)))
            if name != 'totem':
                current = self.statuses[name]
                current['turns'] -= 1
                if current['turns'] <= 0:
                    del self.statuses[name]
        if self.weak_turns > 0:
            self.weak_turns -= 1
            if self.weak_turns <= 0:
                self.statuses.pop('weak', None)
        if self.attack_lock_turns > 0:
            self.attack_lock_turns -= 1
        for layer in self._strength_buffs:
            layer['turns'] -= 1
        self._strength_buffs = [layer for layer in self._strength_buffs if layer['turns'] > 0]
        self._refresh_strength_status()
        return ticks

    def reset_combat_effects(self):
        self.block = 0
        self.strength = 0
        self._strength_buffs.clear()
        self._refresh_strength_status()
        self.weak_turns = 0
        self.statuses.clear()
        self.next_turn_energy = 0
        self.bleed_triggers_this_turn = 0
        self.attack_lock_turns = 0
        self.attack_lock_pending = 0
        self.last_totem_trigger = None

    def clear_damage_stacks(self):
        for name in STACK_STATUS_DAMAGE:
            self.statuses.pop(name, None)
        self.bleed_triggers_this_turn = 0

    def is_alive(self):
        return self.hp > 0


Entity = Combatant
