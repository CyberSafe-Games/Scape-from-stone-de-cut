"""Previsões de intenções sem consumir energia ou sortear novas ações."""
from dataclasses import dataclass
import unicodedata


@dataclass(frozen=True)
class IntentPreview:
    action: object
    order: int
    total: int
    state: str
    special: bool
    family: str
    value: int
    description: str


def icon_family(action):
    name = ''.join(c for c in unicodedata.normalize('NFD', action.name.lower()) if not unicodedata.combining(c))
    if action.action_type in ('defend', 'defense'): return 'shield'
    if action.action_type == 'heal': return 'heal'
    if action.action_type == 'buff': return 'smoke' if 'fumaca' in name else 'buff'
    status = getattr(action, 'status_effect', None)
    if status:
        return {'fire': 'fire', 'poison': 'poison', 'bleed': 'claw'}.get(status[0], 'strike')
    for words, family in ((('moeda',), 'coins'), (('chave',), 'tool'),
                          (('descarga', 'runa'), 'bolt'), (('onda', 'rugido', 'mare'), 'wave'),
                          (('abalo', 'rocha', 'terra'), 'earth'), (('flecha', 'shuriken', 'estrela'), 'arrow'),
                          (('giratorio', 'vendaval'), 'spin'), (('laminas cruzadas',), 'blades'),
                          (('machado', 'carrasco', 'execucao'), 'axe'),
                          (('corte', 'estocada'), 'blade'),
                          (('corte', 'lamina', 'giratorio', 'garras', 'varredura'), 'claw')):
        if any(word in name for word in words): return family
    return 'strike'


def preview_intents(engine):
    enemy = engine.enemy
    actions = list(getattr(enemy, 'action_plan', ()))
    if not actions and enemy.current_action:
        actions = [enemy.current_action]
    index = getattr(enemy, 'action_plan_index', 0)
    bonus = enemy.attack_bonus
    result = []
    for i, action in enumerate(actions):
        done = i < index
        active = i == index and engine.state in ('enemy_turn', 'enemy_resolving')
        state = 'done' if done else 'active' if active else 'pending'
        special = action is getattr(enemy, 'special_action', None)
        if action.action_type == 'attack':
            base = max(0, int(round(action.damage*.75))) if enemy.weak_turns > 0 else action.damage
            value = max(0, base+bonus)
            vulnerability = engine.player.statuses.get('vulnerable', {})
            expires_before_action = engine.state == 'player_turn' and vulnerability.get('turns', 0) <= 1
            if vulnerability and not expires_before_action:
                value = (value*125+99)//100
            text = f'Causa {value} de dano antes de Escudo e Totem.'
            if bonus: text += f' Inclui +{bonus} de bônus de dano.'
            if enemy.weak_turns: text += ' Fraqueza já considerada.'
            status = getattr(action, 'status_effect', None)
            if status:
                key, turns, potency = status
                if key == 'bleed':
                    text += f' Aplica Sangramento por {turns} turnos: {potency} de dano direto no primeiro ataque do alvo por turno.'
                elif key == 'poison':
                    text += f' Aplica Veneno por {turns} turnos: {potency} de dano direto à vida no fim do turno.'
                elif key == 'fire':
                    text += f' Aplica {potency} intensidade(s) de Fogo por {turns} turnos: 3 de dano por intensidade ao fim do turno. Máximo: 3 intensidades.'
        elif action.action_type in ('defend', 'defense'):
            value = action.defense
            text = f'Recebe {value} de Escudo por 2 turnos completos. Esta ação não causa dano.'
        elif action.action_type == 'heal':
            value = action.defense
            text = f'Recupera até {value} de vida, sem ultrapassar a vida máxima. Não causa dano.'
        else:
            value = action.defense
            effect = getattr(action, 'effect', None)
            extra = getattr(effect, 'attack_bonus', 0)
            duration = getattr(effect, 'duration', 2)
            text = f'Recupera até {value} de vida'
            text += f' e recebe +{extra} de dano por {duration} turnos completos.' if extra else '.'
            text += ' Reaplicar renova a duração, sem acumular o bônus. Não causa dano.'
            if not done and extra:
                bonus = enemy.strength+extra
        if special: text += ' Ultimate do chefe.'
        result.append(IntentPreview(action, i+1, len(actions), state, special, icon_family(action), value, text))
    return result
