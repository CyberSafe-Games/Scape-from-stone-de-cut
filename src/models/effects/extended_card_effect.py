import random

from src.config.colors import BLUE, RED
from src.models.effects.base_effect import CardEffect


class ExtendedCardEffect(CardEffect):
    """Regras das cartas novas que ainda não possuem arte própria."""

    DAMAGE_STATUSES = ('poison', 'bleed', 'burn', 'fire', 'weak', 'vulnerable')

    def __init__(self, spec):
        self.spec = spec
        self.params = spec[8]

    def apply(self, card, user, target, context):
        rule = self.spec[5]
        value = card.value
        result = {}
        blocked = card.card_type == 'attack' and 'totem' in target.statuses

        def attack(amount, hits=1):
            if blocked:
                target.receive_attack(amount, hits=hits)
                context._resolve_totem_trigger(target, user)
                result['damage'] = 0
                return 0
            each_hit = max(0, int(amount + user.attack_bonus))
            damage = target.receive_attack(each_hit * max(1, hits), hits=max(1, hits))
            context._resolve_totem_trigger(target, user)
            result['damage'] = damage
            context.spawn_damage_text(target, f'-{damage}', RED)
            self._apply_attack_statuses(user, target)
            return damage

        def consume_attack_totem():
            if blocked and 'totem' in target.statuses:
                target.receive_attack(0)
                context._resolve_totem_trigger(target, user)

        def add_status(name, stacks, turns=3, additional_cap=None):
            if blocked:
                return
            if card.card_type == 'attack':
                multiplier = user.statuses.get(f'double_{name}', {}).get('potency', 1)
                stacks *= multiplier
            target.add_stacks(name, stacks, turns, additional_cap=additional_cap)

        def apply_statuses(statuses, turns=3):
            if blocked:
                return
            for name, stacks in statuses.items():
                add_status(name, stacks, turns)

        if rule == 'damage':
            attack(value)
        elif rule == 'draw':
            context.deck_manager.draw_cards(value)
        elif rule == 'discard_draw':
            if context.deck_manager.hand:
                context.deck_manager.discard_card(random.randrange(len(context.deck_manager.hand)))
            context.deck_manager.draw_cards(value)
        elif rule == 'hurt_energy':
            self._hurt(user, self.params['damage'], context)
            user.energy = min(user.MAX_ENERGY_LIMIT, user.energy + value)
        elif rule == 'block':
            self._block(user, value, context)
        elif rule == 'block_damage':
            attack(user.block)
        elif rule == 'damage_block':
            attack(value)
            self._block(user, self.params['block'], context)
        elif rule == 'cleanse_immunity':
            user.cleanse()
            user.apply_status('debuff_immunity', value)
        elif rule == 'next_energy':
            user.next_turn_energy = min(user.MAX_ENERGY_LIMIT, user.next_turn_energy + value)
        elif rule == 'hurt_restore_energy':
            self._hurt(user, self.params['damage'], context)
            user.energy = min(user.MAX_ENERGY_LIMIT, user.energy + value)
        elif rule == 'heal_attack_lock':
            self._heal(user, value, context)
            user.attack_lock_pending = max(user.attack_lock_pending, 1)
        elif rule == 'damage_status':
            attack(value)
            add_status(self.params['status'], self.params['stacks'])
        elif rule == 'block_status':
            self._block(user, value, context)
            apply_statuses({self.params['status']: self.params['stacks']})
        elif rule == 'poison_on_damage':
            consume_attack_totem()
            if not blocked:
                target.apply_status('poison_on_damage', 1, value)
        elif rule == 'status':
            consume_attack_totem()
            if not blocked:
                if self.params['status'] in ('poison', 'bleed', 'burn'):
                    add_status(self.params['status'], value)
                else:
                    target.apply_status(self.params['status'], value, 1)
        elif rule == 'conditional_damage':
            stacks = target.statuses.get(self.params['condition'], {}).get('potency', 0)
            attack(self.params['alternate'] if stacks >= self.params['threshold'] else value)
        elif rule == 'double_poison':
            consume_attack_totem()
            if not blocked:
                target.apply_status('poison_multiplier', 1, 2)
        elif rule == 'purge_status':
            consume_attack_totem()
            if not blocked:
                state = target.statuses.pop(self.params['status'], None)
                if state:
                    damage = state['potency'] * self.params['damage_per_stack']
                    result['damage'] = target.take_damage(damage, bypass_block=True)
                    context.spawn_damage_text(target, f"-{result['damage']}", RED)
        elif rule == 'conditional_status':
            consume_attack_totem()
            if not blocked:
                amount = value + (
                    self.params['bonus']
                    if self.params['condition'] in target.statuses
                    else 0
                )
                add_status(self.params['status'], amount)
        elif rule == 'multi_status':
            consume_attack_totem()
            apply_statuses(self.params['statuses'])
        elif rule == 'double_status':
            if card.card_type == 'power':
                user.apply_status(f"double_{self.params['status']}", 1, 2)
            elif not blocked and self.params['status'] == 'burn':
                current = target.statuses.get('burn', {}).get('potency', 0)
                target.add_stacks('burn', current, additional_cap=self.params['cap'])
            elif not blocked:
                consume_attack_totem()
                current = target.statuses.get(self.params['status'], {}).get('potency', 0)
                target.add_stacks(self.params['status'], current)
        elif rule == 'draw_no_heal':
            context.deck_manager.draw_cards(value)
            target.apply_status('no_heal', 1)
        elif rule == 'attack_status':
            consume_attack_totem()
            if not blocked:
                user.apply_status('attack_burn', 1, value)
        elif rule == 'draw_per_status':
            amount = min(self.params['cap'], target.statuses.get(self.params['status'], {}).get('potency', 0) // self.params['divisor'])
            context.deck_manager.draw_cards(amount)
        elif rule == 'damage_per_status':
            attack(target.statuses.get(self.params['status'], {}).get('potency', 0) * self.params['multiplier'])
        elif rule == 'block_reactive_status':
            self._block(user, value, context)
            target.apply_status('burn_on_action', 1, self.params['stacks'])
        elif rule == 'status_hurt':
            add_status(self.params['status'], value)
            self._hurt(user, self.params['damage'], context)
        elif rule == 'no_block_status':
            target.apply_status('no_block', 1)
            add_status(self.params['status'], self.params['stacks'])
        elif rule == 'conditional_weak':
            attack(value)
            if any(name in target.statuses for name in ('poison', 'bleed', 'burn')):
                target.apply_status('weak', 1)
        elif rule == 'block_stun':
            self._block(user, value, context)
            self._stun(target, self.params['chance'], blocked)
        elif rule == 'block_per_debuff':
            amount = value * self._debuff_types(target)
            self._block(user, amount, context)
        elif rule == 'weak_or_damage':
            if 'weak' in target.statuses or target.weak_turns:
                attack(value)
            else:
                consume_attack_totem()
                if not blocked:
                    target.apply_status('weak', 1)
        elif rule == 'strength_hurt':
            user.apply_strength(value, self.params['turns'])
            self._hurt(user, self.params['damage'], context)
        elif rule == 'strength':
            user.apply_strength(value, self.params['turns'])
        elif rule == 'damage_strength':
            attack(value)
            user.apply_strength(self.params['strength'], self.params['turns'])
        elif rule == 'block_strength':
            self._block(user, value, context)
            user.apply_strength(self.params['strength'], self.params['turns'])
        elif rule == 'multi_damage_strength':
            attack(value, self.params['hits'])
            user.apply_strength(self.params['strength'], self.params['turns'])
        elif rule == 'double_strength':
            current = user.strength + user.temporary_strength
            user.apply_strength(current, 1)
        elif rule == 'multi_damage':
            attack(value, self.params['hits'])
        elif rule == 'permanent_strength':
            user.strength = min(5, user.strength + value)
        elif rule == 'strength_no_block':
            user.apply_strength(value, self.params['turns'])
            user.apply_status('no_block', self.params['turns'])
        elif rule == 'draw_strength':
            context.deck_manager.draw_cards(value)
            user.apply_strength(1, self.params['turns'])
        elif rule == 'damage_stun':
            attack(value)
            self._stun(target, self.params['chance'], blocked)
        elif rule == 'damage_stun_per_debuff':
            attack(value)
            chance = min(50, 10 * self._debuff_types(target))
            self._stun(target, chance, blocked)
        elif rule == 'damage_stun_draw':
            attack(value)
            stunned = not blocked and random.randint(1, 100) <= self.params['chance']
            if stunned:
                target.apply_status('stun', 1)
            elif not blocked:
                context.deck_manager.draw_cards(1)
        elif rule == 'totem':
            user.apply_status('totem', 0, 1)
        elif rule == 'totem_block':
            user.apply_status('totem', 0, 1)
            user.statuses['totem']['trigger'] = None
            self._block(user, self.params['block'], context)
        elif rule == 'totem_poison':
            user.apply_status('totem', 0, 1)
            user.statuses['totem']['trigger'] = 'poison'
        elif rule == 'totem_heal':
            user.apply_status('totem', 0, 1)
            user.statuses['totem']['trigger'] = 'heal'
        elif rule == 'damage_multi_status':
            attack(value)
            apply_statuses(self.params['statuses'])
        elif rule == 'damage_per_debuff':
            attack(value * self._debuff_types(target))
        elif rule == 'add_existing_debuffs':
            consume_attack_totem()
            if not blocked:
                for name in ('poison', 'bleed', 'burn'):
                    if name in target.statuses:
                        target.add_stacks(name, value, additional_cap=10)
        elif rule == 'trigger_debuffs':
            consume_attack_totem()
            if not blocked:
                damage = 0
                for name, status in target.statuses.items():
                    if name == 'poison':
                        damage += status['potency']
                    elif name == 'bleed':
                        damage += status['potency']
                    elif name == 'burn':
                        damage += status['potency']
                    elif name == 'fire':
                        damage += 3 * status['potency']
                result['damage'] = target.take_damage(damage, bypass_block=True)
                context.spawn_damage_text(target, f'-{result["damage"]}', RED)
        elif rule == 'draw_per_debuff':
            context.deck_manager.draw_cards(self._debuff_types(target))
        elif rule == 'damage_status_strength':
            attack(value)
            add_status(self.params['status'], self.params['stacks'])
            user.apply_strength(self.params['strength'], self.params['turns'])
        elif rule == 'damage_stun_status':
            attack(value)
            self._stun(target, self.params['chance'], blocked)
            add_status(self.params['status'], self.params['stacks'])
        elif rule == 'double_all_debuffs_lock':
            consume_attack_totem()
            if not blocked:
                for name in ('poison', 'bleed', 'burn'):
                    current = target.statuses.get(name, {}).get('potency', 0)
                    if current:
                        target.add_stacks(name, current, additional_cap=value)
            user.attack_lock_turns = max(user.attack_lock_turns, 1)

        if card.card_type == 'attack':
            context.trigger_attack('player', card.name)
            context.trigger_flash('enemy')
        else:
            context.trigger_player_action(card.name)
        return result

    def _apply_attack_statuses(self, user, target):
        stacks = user.statuses.get('attack_burn', {}).get('potency', 0)
        if stacks:
            target.add_stacks('burn', stacks)

    @staticmethod
    def _block(user, amount, context):
        before = user.block
        user.add_block(amount)
        gained = user.block - before
        context.spawn_player_text(f'+{gained} Escudo', BLUE)

    @staticmethod
    def _hurt(user, amount, context):
        damage = user.take_damage(amount, bypass_block=True)
        context.spawn_player_text(f'-{damage} vida', RED)

    @staticmethod
    def _heal(user, amount, context):
        if 'no_heal' in user.statuses:
            return
        healed = min(amount, user.max_hp - user.hp)
        user.hp += healed
        context.spawn_player_text(f'+{healed} vida', (102, 210, 137))

    @staticmethod
    def _stun(target, chance, blocked):
        if not blocked and chance > 0 and random.randint(1, 100) <= chance:
            target.apply_status('stun', 1)

    def _debuff_types(self, target):
        return sum(name in target.statuses for name in target.NEGATIVE_STATUSES)
