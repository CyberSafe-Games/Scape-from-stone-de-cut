"""Snapshots JSON do estado lógico; não serializa objetos executáveis."""
from copy import deepcopy
import random

from src.models.action import Action
from src.models.enemy import Enemy
from src.models.effects.crimson_vigor_effect import CrimsonVigorEffect
from src.models.effects.forest_smoke_effect import ForestSmokeEffect
from src.systems.roguelite import instance_card


def validate(data):
    """Recusa snapshots incompletos sem tentar restaurar um turno parcial."""
    from src.systems.card_catalog import AVAILABLE_CARD_NAMES
    if (not isinstance(data, dict) or type(data.get('level')) is not int
            or not 1 <= data['level'] <= 7 or data.get('kind') not in ('road', 'point')
            or data.get('state') not in ('player_turn', 'enemy_turn', 'enemy_resolving',
                                       'victory', 'boss_transition', 'phase_complete')):
        raise ValueError('Snapshot de combate inválido.')
    for key in ('player', 'enemy'):
        entity = data.get(key)
        if not isinstance(entity, dict):
            raise ValueError('Entidade ausente no snapshot.')
        for field in ('hp', 'max_hp', 'energy'):
            if type(entity.get(field)) is not int or entity[field] < 0:
                raise ValueError('Atributo inválido no snapshot.')
        if entity['hp'] > entity['max_hp'] or not isinstance(entity.get('statuses'), dict):
            raise ValueError('Vida ou efeitos inválidos no snapshot.')
    if not isinstance(data.get('piles'), dict):
        raise ValueError('Pilhas ausentes no snapshot.')
    for key in ('deck', 'hand', 'draw_pile', 'discard_pile'):
        pile = data['piles'].get(key)
        if not isinstance(pile, list) or any(not isinstance(c, dict) or
                c.get('name') not in AVAILABLE_CARD_NAMES or c.get('level') not in (1, 2) for c in pile):
            raise ValueError('Carta inválida no snapshot.')
    for key in ('actions', 'action_plan'):
        for action in data['enemy'][key]:
            _restore_action(action)
    _restore_action(data['enemy']['current_action'])
    _restore_action(data['enemy']['special_action'])
    def tuples(value):
        return tuple(tuples(v) for v in value) if isinstance(value, (list, tuple)) else value
    try:
        random.Random().setstate(tuples(data['random']))
    except (ValueError, TypeError, KeyError) as exc:
        raise ValueError('Estado aleatório inválido no snapshot.') from exc


def _action(action):
    if action is None:
        return None
    data = deepcopy(vars(action))
    data['effect'] = type(action.effect).__name__ if action.effect else None
    return data


def _restore_action(data):
    if data is None:
        return None
    data = deepcopy(data)
    effects = {'CrimsonVigorEffect': CrimsonVigorEffect, 'ForestSmokeEffect': ForestSmokeEffect}
    effect = data.pop('effect')
    if effect is not None and effect not in effects:
        raise ValueError('Efeito de ação desconhecido no snapshot.')
    data['effect'] = effects[effect]() if effect else None
    return Action(**data)


def capture(engine, include_random=True):
    enemy = {k: deepcopy(v) for k, v in vars(engine.enemy).items()
             if k not in ('actions', 'special_action', 'current_action', 'action_plan')}
    for key in ('actions', 'action_plan'):
        enemy[key] = [_action(a) for a in getattr(engine.enemy, key, [])]
    enemy['current_action'] = _action(engine.enemy.current_action)
    enemy['special_action'] = _action(getattr(engine.enemy, 'special_action', None))
    result = {'level': engine.level, 'kind': engine.encounter_kind, 'index': engine.encounter_index,
              'state': engine.state, 'player': deepcopy(vars(engine.player)), 'enemy': enemy,
              'remaining': engine.enemy_actions_remaining, 'swap': engine.cemetery_swap_used,
              'phase_ended': getattr(engine, '_phase_ended_enemy_turn', False),
              'reward_cards': [c.name for c in engine.reward_cards],
              'material_reward': getattr(engine, 'material_reward', None),
              'reward_selection': getattr(engine, 'reward_selection', None)}
    result['piles'] = {key: [{'id': c.copy_id, 'name': c.name, 'level': c.level} for c in
                            getattr(engine.deck_manager, key)]
                       for key in ('deck', 'hand', 'draw_pile', 'discard_pile')}
    if include_random:
        result['random'] = random.getstate()
    return result


def restore(engine, snapshot):
    from src.systems.card_catalog import CARD_BY_NAME
    data = deepcopy(snapshot)
    engine.player.__dict__.update(data['player'])
    enemy_data = data['enemy']
    engine.enemy = Enemy(enemy_data['name'], enemy_data['max_hp'])
    for key in ('actions', 'action_plan'):
        enemy_data[key] = [_restore_action(a) for a in enemy_data[key]]
    special = enemy_data['special_action'] = _restore_action(enemy_data['special_action'])
    current = _restore_action(enemy_data['current_action'])
    # O motor identifica a Ultimate por identidade de objeto.
    if special and current and current.name == special.name:
        current = special
    enemy_data['current_action'] = current
    if special:
        enemy_data['action_plan'] = [special if a.name == special.name else a
                                    for a in enemy_data['action_plan']]
    engine.enemy.__dict__.update(enemy_data)
    for key, cards in data['piles'].items():
        setattr(engine.deck_manager, key, [instance_card(c) for c in cards])
    engine.state = data['state']
    engine.enemy_actions_remaining = data['remaining']
    engine.cemetery_swap_used = data['swap']
    engine._phase_ended_enemy_turn = data['phase_ended']
    engine.reward_cards = [CARD_BY_NAME[n].copy() for n in data['reward_cards']]
    engine.material_reward = data.get('material_reward')
    engine.reward_selection = data.get('reward_selection')
    def tuples(value):
        return tuple(tuples(v) for v in value) if isinstance(value, (list, tuple)) else value
    random.setstate(tuples(data['random']))
