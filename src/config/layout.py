from src.config.settings import WIDTH, HEIGHT

# ============================================================
# POSIÇÕES DOS COMBATENTES NA TELA
# ============================================================

PLAYER_X = 390
PLAYER_Y = 570

ENEMY_X = WIDTH - 390
ENEMY_Y = 570

PLAYER_GROUND_Y = PLAYER_Y + 60


# ============================================================
# DIMENSÕES E ESPAÇAMENTO DE CARTAS
# ============================================================

CARD_WIDTH = 150
CARD_HEIGHT = 258
CARD_SPACING = 18


# ============================================================
# BOTÕES DO DECK NA MOCHILA
# ============================================================

# Os dois botões ficam na mesma linha, logo abaixo do painel do deck.
BACKPACK_DECK_BUTTON_OFFSET_Y = 26
BACKPACK_DECK_BUTTON_HEIGHT = 59
BACKPACK_DECK_BUTTON_GAP = 16
BACKPACK_DECK_BUTTON_INSET_X = 8


# ============================================================
# PARÂMETROS DE ANIMAÇÃO E TIMERS (em milissegundos)
# ============================================================

FLASH_DURATION = 560
FLOAT_DURATION = 900

ATTACK_DURATION = 700
MELEE_MIN_DURATION = 1120
POSE_RECOVERY_MS = 240
PLAYER_IDLE_FRAME_MS = 210
BOSS_IDLE_FRAME_MS = 225
COMMON_IDLE_FRAME_MS = 210
VICTORY_FRAME_MS = 180
LEGACY_VICTORY_FRAME_MS = 125

APPROACH_FRAC = 0.4
STRIKE_FRAC = 0.25

APPROACH_GAP = 117

POST_ENEMY_PAUSE = 350

MINIBOSS_INTERVAL = 5
