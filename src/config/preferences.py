"""Chaves, padrões, limites e abas das preferências globais do jogo."""

from src.config.music import MUSIC_VOLUME

# ============================================================
# CHAVES E VALORES PADRÃO
# ============================================================
# Os padrões preservam exatamente o comportamento anterior ao menu de opções.

AUDIO_PREFERENCE_KEYS = (
    "master_volume",
    "music_volume",
    "combat_volume",
    "damage_volume",
)

VIDEO_PREFERENCE_KEYS = (
    "fullscreen",
    "window_size",
    "show_fps",
)

GAME_PREFERENCE_KEYS = (
    "enemy_speed",
    "damage_numbers",
)

PREFERENCE_KEYS = AUDIO_PREFERENCE_KEYS + VIDEO_PREFERENCE_KEYS + GAME_PREFERENCE_KEYS

DEFAULT_PREFERENCES = {
    "master_volume": 1.0,
    "music_volume": MUSIC_VOLUME,
    "combat_volume": 1.0,
    "damage_volume": 1.0,
    "fullscreen": False,
    "window_size": "legacy",
    "show_fps": False,
    "enemy_speed": "normal",
    "damage_numbers": True,
}

VOLUME_MIN = 0.0
VOLUME_MAX = 1.0
VOLUME_STEP = 0.05

# ============================================================
# OPÇÕES DE VÍDEO E JOGO
# ============================================================

WINDOW_SIZE_LEGACY = "legacy"
WINDOW_SIZE_LARGE = "large"
WINDOW_SIZE_OPTIONS = (
    (WINDOW_SIZE_LEGACY, "1280 × 720"),
    (WINDOW_SIZE_LARGE, "JANELA GRANDE"),
)

ENEMY_SPEED_NORMAL = "normal"
ENEMY_SPEED_FAST = "fast"
ENEMY_SPEED_OPTIONS = (
    (ENEMY_SPEED_NORMAL, "NORMAL"),
    (ENEMY_SPEED_FAST, "RÁPIDA"),
)
# Apenas o ritmo visual das pausas do inimigo; nunca regras de combate.
ENEMY_SPEED_MULTIPLIERS = {
    ENEMY_SPEED_NORMAL: 1.0,
    ENEMY_SPEED_FAST: 0.5,
}
ENEMY_WINDUP_MS = 800
ENEMY_COMBO_WINDUP_MS = 270

# ============================================================
# ABAS DO MENU DE OPÇÕES
# ============================================================

TAB_AUDIO = "audio"
TAB_VIDEO = "video"
TAB_GAME = "game"
TAB_CONTROLS = "controls"

OPTIONS_TABS = (
    (TAB_AUDIO, "ÁUDIO"),
    (TAB_VIDEO, "VÍDEO"),
    (TAB_GAME, "JOGO"),
    (TAB_CONTROLS, "CONTROLES"),
)

PREFERENCE_KEYS_BY_TAB = {
    TAB_AUDIO: AUDIO_PREFERENCE_KEYS,
    TAB_VIDEO: VIDEO_PREFERENCE_KEYS,
    TAB_GAME: GAME_PREFERENCE_KEYS,
    TAB_CONTROLS: (),
}
