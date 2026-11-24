"""Geometria simétrica da faixa superior na superfície virtual."""
from src.config.settings import WIDTH

PLAYER_PANEL = (33, 30, 680, 138)
ENEMY_PANEL = (WIDTH - 33 - 680, 30, 680, 138)
MENU_BUTTON = (WIDTH // 2 - 90, 80, 180, 56)
ARENA_TITLE = (WIDTH // 2 - 225, 27, 450, 42)

# Abertura útil da arte hud_health.png, em pixels da referência original.
# Deve passar pela mesma escala em faixas usada na moldura das águias.
HEALTH_FRAME_REFERENCE = (733, 188)
HEALTH_WINDOW_POLYGON = (
    (146,53), (586,53), (599,65), (605,79), (605,94), (594,109),
    (585,116), (145,116), (134,108), (127,94), (127,78), (135,64),
)
