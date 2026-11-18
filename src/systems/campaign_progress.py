"""Coordena a gravação de vitórias de fases sem depender de interface gráfica."""
from src.systems.territory_map import ROAD_FIGHTS, TERRITORIES, by_level, complete, status, encounter_status
from src.systems.save_manager import SaveError


def record_victory(save_manager, save_data, engine, collect_pending_coins):
    """Persiste recompensa, moedas e próximo território de forma idempotente.

    Chamar apenas quando `engine.state == 'phase_complete'`. Em caso de
    falha de I/O o chamador permanece na cena e pode chamar novamente.
    """
    if engine.state != "phase_complete":
        raise ValueError("A fase ainda não foi concluída e recompensada.")
    territory = by_level(engine.level)
    if status(save_data, territory.id) == "locked":
        raise ValueError("Esta fase ainda não está disponível.")
    if encounter_status(save_data, territory.id) == "locked":
        raise ValueError("É preciso concluir os dois encontros anteriores ao chefe.")
    from copy import deepcopy
    original = deepcopy(save_data["progresso"])
    profile_before = deepcopy(save_data.get('perfil', {}))
    collect_pending_coins()
    try:
        complete(save_data, territory.id)
        highest = max(save_data["progresso"]["andar"],
                      min(len(TERRITORIES), territory.level + 1))
        save_manager.update_from_game(
            save_data, engine.player, engine.deck_manager, level=highest,
        )
        _finish_reward(save_data, engine)
        save_manager.save(save_data)
    except (OSError, ValueError, TypeError, SaveError):
        save_data["progresso"] = original
        save_data['run'] = original
        save_data['perfil'] = profile_before
        raise


def record_road_victory(save_manager, save_data, engine, collect_pending_coins):
    """Registra um encontro comum sem avançar território.

    Valida o estágio e limita a contagem ao tamanho da rota. A cena sai após
    confirmação da gravação do progresso e da recompensa.
    """
    if engine.state != "phase_complete" or engine.encounter_kind != "road":
        raise ValueError("Encontro ainda não concluído.")
    territory = by_level(engine.level)
    if status(save_data, territory.id) == "locked":
        raise ValueError("Não é possível registrar encontro nesta área.")
    progress = save_data["progresso"]
    current = progress.setdefault("encontros_por_territorio", {}).get(territory.id, 0)
    if status(save_data, territory.id) == 'completed':
        current = ROAD_FIGHTS
    index = getattr(engine, 'encounter_index', None)
    # Sem índice mantém o fluxo sequencial dos chamadores antigos.
    if index is None:
        if current >= ROAD_FIGHTS:
            raise ValueError("Os encontros da rota já foram concluídos.")
        index = current
    if encounter_status(save_data, territory.id, index) == 'locked':
        raise ValueError('Este encontro ainda está bloqueado.')
    next_count = min(ROAD_FIGHTS, max(current, index + 1))
    # O motor já possui o prêmio selecionado. Preserva o JSON em caso de falha.
    from copy import deepcopy
    snapshot = deepcopy(progress)
    profile_before = deepcopy(save_data.get('perfil', {}))
    collect_pending_coins()
    try:
        save_manager.update_from_game(save_data, engine.player, engine.deck_manager,
                                      level=progress["andar"])
        progress["encontros_por_territorio"][territory.id] = next_count
        _finish_reward(save_data, engine)
        save_manager.save(save_data)
    except (OSError, ValueError, TypeError, SaveError):
        save_data["progresso"] = snapshot
        save_data['run'] = snapshot
        save_data['perfil'] = profile_before
        raise
    return next_count


def _finish_reward(data, engine):
    """Fecha a seleção sem duplicar material em nova tentativa de gravação."""
    p = data['progresso']
    confirm_victory(data, engine)
    key = f'{engine.level}:{engine.encounter_kind}:{engine.encounter_index}:choice'
    if key not in p.setdefault('received_rewards', []):
        reward = getattr(engine, 'material_reward', None)
        if reward:
            name, amount = reward
            if p['materials'].get(name, 0) + amount > 9:
                raise ValueError('Reserva de material completa.')
            p['materials'][name] = p['materials'].get(name, 0) + amount
        p['received_rewards'].append(key)
    p['combat_snapshot'] = None
    if engine.level == 7 and engine.encounter_kind == 'point' and not engine.is_replay:
        if p.get('estado') != 'concluida':
            data['perfil']['campanhas_concluidas'] += 1
        p['estado'] = 'concluida'


def confirm_victory(data, engine):
    """Registra fragmentos uma vez, com ou sem escolha posterior de carta."""
    from src.systems.roguelite import FRAGMENTS
    if getattr(engine, 'is_replay', False):
        return
    p = data['progresso']
    key = f'{engine.level}:{engine.encounter_kind}:{engine.encounter_index}'
    received = p.setdefault('received_rewards', [])
    if key not in received:
        received.append(key)
        if engine.enemy.is_miniboss and 'perfil' in data:
            data['perfil']['fragmentos'] += FRAGMENTS[engine.level - 1]
            data['perfil']['melhor_territorio'] = max(engine.level, data['perfil']['melhor_territorio'])
