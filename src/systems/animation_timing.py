"""Constantes e funções puras para transições de animação do Corpo Seco.

A duração do ataque define também por quanto tempo a IA espera antes de
iniciar o segundo ato, mantendo os frames sincronizados com o combate.
"""

BOSS_ANIMATIONS_MS = {
    "atk1": 810,
    "atk3": 940,
    "atk4": 1290,   # ataque giratório: animação mais elaborada
    "def": 870,
    "healer2": 1000,
}


def animation_duration(group, default=700):
    return BOSS_ANIMATIONS_MS.get(group, default)


def frame_index(group, elapsed_ms, duration_ms, frame_count):
    """Seleciona frame de modo determinístico, independentemente do FPS.

    O giro repete sua passagem central para transmitir rotação contínua.
    """
    if frame_count <= 0:
        return 0
    if frame_count == 1:
        return 0
    duration_ms = max(1, duration_ms)
    progress = max(0.0, min(0.999999, elapsed_ms / duration_ms))
    if group == "atk4" and frame_count >= 3:
        sequence = list(range(frame_count)) + list(range(1, frame_count))
        return sequence[min(len(sequence) - 1, int(progress * len(sequence)))]
    return min(frame_count - 1, int(progress * frame_count))


def dash_distance(group, is_corpo_seco):
    """Evita que o miniboss atravesse a arena inteira em poucos frames."""
    if not is_corpo_seco:
        return None
    return 120 if group == "atk4" else 225
