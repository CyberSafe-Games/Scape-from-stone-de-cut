from src.config.settings import WIDTH, HEIGHT

# ============================================================
# POSIÇÕES DOS COMBATENTES NA TELA
# ============================================================

PLAYER_X = 260
PLAYER_Y = 380

ENEMY_X = WIDTH - 260
ENEMY_Y = 380

PLAYER_GROUND_Y = PLAYER_Y + 40


# ============================================================
# DIMENSÕES E ESPAÇAMENTO DE CARTAS
# ============================================================

CARD_WIDTH = 108
CARD_HEIGHT = 186
CARD_SPACING = 10


# ============================================================
# PARÂMETROS DE ANIMAÇÃO E TIMERS (em milissegundos)
# ============================================================

FLASH_DURATION = 220
FLOAT_DURATION = 900

ATTACK_DURATION = 700

APPROACH_FRAC = 0.4
STRIKE_FRAC = 0.25

APPROACH_GAP = 78

POST_ENEMY_PAUSE = 350

MINIBOSS_INTERVAL = 5
