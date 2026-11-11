"""Previsões de intenções sem consumir energia ou sortear novas ações."""
from dataclasses import dataclass
import unicodedata
from src.models.action import action_status_effects


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
    if 'grilhoes' in name: return 'chains'
    if 'travessia final' in name: return 'ferry'
    if 'foice' in name or 'passo do barqueiro' in name: return 'scythe'
    if action.action_type in ('defend', 'defense'): return 'shield'
    if action.action_type == 'heal': return 'heal'
    if action.action_type == 'buff': return 'smoke' if 'fumaca' in name else 'buff'
    statuses = action_status_effects(action)
    status = statuses[0] if statuses else None
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
    vulnerability = engine.player.statuses.get('vulnerable', {})
    expires_before_action = engine.state == 'player_turn' and vulnerability.get('turns',0) <= 1
    predicted_vulnerable = bool(vulnerability) and not expires_before_action
    predicted_totem = 'totem' in engine.player.statuses
    for i, action in enumerate(actions):
        done = i < index
        active = i == index and engine.state in ('enemy_turn', 'enemy_resolving')
        state = 'done' if done else 'active' if active else 'pending'
        special = action is getattr(enemy, 'special_action', None)
        if action.action_type == 'attack':
            base = max(0, int(round(action.damage*.75))) if enemy.weak_turns > 0 else action.damage
            value = max(0, base+bonus)
            if predicted_vulnerable:
                value = (value*125+99)//100
            text = f'Causa {value} de dano antes de Escudo e Totem.'
            if bonus: text += f' Inclui +{bonus} de bônus de dano.'
            if enemy.weak_turns: text += ' Fraqueza já considerada.'
            statuses = action_status_effects(action)
            for key,turns,potency in statuses:
                if key == 'bleed':
                    text += f' Aplica Sangramento por {turns} turnos: {potency} de dano direto no primeiro ataque do alvo por turno.'
                elif key == 'poison':
                    text += f' Aplica Veneno por {turns} turnos: {potency} de dano direto à vida no fim do turno.'
                elif key == 'vulnerable':
                    text += f' Aplica Vulnerável por {turns} turnos: recebe {potency}% a mais de dano de ataques. Reaplicar renova a duração.'
                elif key == 'fire':
                    text += f' Aplica {potency} intensidade(s) de Fogo por {turns} turnos: 3 de dano por intensidade ao fim do turno. Máximo: 3 intensidades.'
            if any(status[0] in ('bleed','poison') for status in statuses):
                text += ' Reaplicar renova a duração, sem acumular; mantém a maior intensidade ativa.'
            # Simular só ações futuras; em enemy_resolving a atual já aconteceu.
            pending = not done and not (active and engine.state == 'enemy_resolving')
            if pending:
                protected = predicted_totem
                predicted_totem = False
                if any(status[0] == 'vulnerable' for status in statuses) and not protected:
                    predicted_vulnerable = True
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
