from src.models.effects.base_effect import CardEffect
from src.config.colors import RED, BLUE, GOLD


class TacticalCardEffect(CardEffect):
    """Efeitos das cartas comuns, sem alterar as habilidades ultimate."""
    def __init__(self, spec):
        self.spec = spec

    def apply(self, card, user, target, context):
        rule, animation = self.spec[5:7]
        result = {}
        blocked = card.card_type == 'attack' and 'totem' in target.statuses
        if card.card_type == 'attack':
            result['damage'] = target.receive_attack(card.value + user.attack_bonus, hits=3 if rule == 'darts' else 1)
            context.spawn_damage_text(target, f"-{result['damage']}", RED)
        if rule in ('shield', 'mask'):
            user.add_block(card.value)
            context.spawn_player_text(f'+{card.value} Escudo', BLUE)
        if rule in ('heal', 'mask'):
            healed = min(card.value, user.max_hp - user.hp)
            user.hp += healed
            result['heal'] = healed
            context.spawn_player_text(f'+{healed} vida', (102, 210, 137))
        if rule == 'aura': user.apply_status('aura', 3, card.value)
        elif rule == 'vulnerable': target.apply_status('vulnerable', 3, 25)
        elif rule == 'cleanse': user.cleanse()
        elif rule == 'totem': user.apply_status('totem', 0, 1)
        elif rule == 'darts' and not blocked: target.apply_status('poison', 3, 5)
        elif rule == 'break': target.block = 0
        elif rule == 'dispel': target.cleanse(all_effects=True)
        elif rule == 'bleed' and not blocked: target.apply_status('bleed', 2, 4)
        elif rule == 'fire' and not blocked: target.apply_status('fire', 3, 1)
        elif rule == 'poison': target.apply_status('poison', 4, 5)
        elif rule == 'energy':
            user.next_turn_energy = min(8, user.next_turn_energy + card.value)
            context.spawn_player_text(f'+{card.value} energia no próximo turno', GOLD)
        if animation in ('melee', 'ranged'):
            context.trigger_attack('player', card.name)
            context.trigger_flash('enemy')
        else: context.trigger_player_action(card.name)
        return result
