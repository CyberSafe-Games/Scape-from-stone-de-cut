"""Coordena a gravação de vitórias de fases sem depender de interface gráfica."""
from src.systems.territory_map import TERRITORIES, by_level, complete, status


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
    if save_data["progresso"].get("encontros_por_territorio", {}).get(territory.id, 0) < 3:
        raise ValueError("É preciso concluir os três encontros anteriores ao ponto de interesse.")
    from copy import deepcopy
    original = deepcopy(save_data["progresso"])
    collect_pending_coins()
    try:
        complete(save_data, territory.id)
        highest = max(save_data["progresso"]["andar"],
                      min(len(TERRITORIES), territory.level + 1))
        save_manager.update_from_game(
            save_data, engine.player, engine.deck_manager, level=highest,
        )
        save_manager.save(save_data)
    except (OSError, ValueError, TypeError):
        save_data["progresso"] = original
        raise


def record_road_victory(save_manager, save_data, engine, collect_pending_coins):
    """Registra um encontro comum, sem avançar território; máximo de 3.

    Valida estágio e evita aumentar além de três. A cena sai somente após
    confirmação da gravação do progresso e da recompensa.
    """
    if engine.state != "phase_complete" or engine.encounter_kind != "road":
        raise ValueError("Encontro ainda não concluído.")
    territory = by_level(engine.level)
    if status(save_data, territory.id) != "available":
        raise ValueError("Não é possível registrar encontro nesta área.")
    progress = save_data["progresso"]
    current = progress.setdefault("encontros_por_territorio", {}).get(territory.id, 0)
    if current >= 3:
        raise ValueError("Os três encontros já foram concluídos.")
    # O motor já possui o prêmio selecionado. Preserva o JSON em caso de falha.
    from copy import deepcopy
    snapshot = deepcopy(progress)
    collect_pending_coins()
    try:
        save_manager.update_from_game(save_data, engine.player, engine.deck_manager,
                                      level=progress["andar"])
        progress["encontros_por_territorio"][territory.id] = current + 1
        save_manager.save(save_data)
    except (OSError, ValueError, TypeError):
        save_data["progresso"] = snapshot
        raise
    return current + 1
