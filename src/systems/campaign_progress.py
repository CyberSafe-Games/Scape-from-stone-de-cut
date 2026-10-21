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
    complete(save_data, territory.id)
    collect_pending_coins()
    highest = max(save_data["progresso"]["andar"],
                  min(len(TERRITORIES), territory.level + 1))
    save_manager.update_from_game(
        save_data, engine.player, engine.deck_manager, level=highest,
    )
    save_manager.save(save_data)
