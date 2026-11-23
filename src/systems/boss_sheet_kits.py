"""Kits de oito quadros importados do pacote BossesNovasSprites.

Os IDs legados permanecem estáveis para áudio, combate e saves.
"""
SHEET_KITS = {
    'guardião da pedra': ('guardiao_da_pedra', {'atk2': 'ultimate'}),
    'corpo seco': ('corpo_seco', {'atk4': 'ultimate', 'def': 'healer2'}),
    'carrasco da vigília': ('carrasco_da_vigilia', {'atk3': 'ultimate'}),
}

SHEET_GRID = (4, 2)
SHEET_CELL_SIZE = (448, 320)
SHEET_FRAME_COUNT = 8


def sheet_pose(progress, contact=.52):
    """Oito poses em ordem; preparação/impacto acompanham a duração da ação."""
    from src.systems.animation_inbetweens import action_pose
    return max(0, min(7, action_pose(max(0, min(1, progress)), 8, contact)))
