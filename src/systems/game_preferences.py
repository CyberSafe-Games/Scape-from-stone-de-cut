"""Preferências globais do jogo, independentes dos saves da campanha.

Este módulo é puro Python (sem pygame): valida, aplica e persiste áudio, vídeo e
opções de jogo em um único arquivo JSON.
"""

import json
import math
import os
from pathlib import Path
import tempfile

from src.config.preferences import (
    AUDIO_PREFERENCE_KEYS,
    DEFAULT_PREFERENCES,
    ENEMY_COMBO_WINDUP_MS,
    ENEMY_SPEED_MULTIPLIERS,
    ENEMY_SPEED_NORMAL,
    ENEMY_WINDUP_MS,
    PREFERENCE_KEYS_BY_TAB,
    VOLUME_MAX,
    VOLUME_MIN,
    WINDOW_SIZE_LARGE,
    WINDOW_SIZE_LEGACY,
)
from src.config.settings import PREFERENCES_PATH

BOOLEAN_KEYS = ("fullscreen", "show_fps", "damage_numbers")
ENUM_KEYS = {
    "window_size": (WINDOW_SIZE_LEGACY, WINDOW_SIZE_LARGE),
    "enemy_speed": tuple(ENEMY_SPEED_MULTIPLIERS),
}


def _sanitize(key, value, default):
    """Aceita apenas valores válidos; ausente, corrompido ou fora da faixa volta ao padrão."""
    if key in AUDIO_PREFERENCE_KEYS:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return default
        if not math.isfinite(value):
            return default
        value = float(value)
        return value if VOLUME_MIN <= value <= VOLUME_MAX else default

    if key in BOOLEAN_KEYS:
        return value if isinstance(value, bool) else default

    if key in ENUM_KEYS:
        return value if value in ENUM_KEYS[key] else default

    return default


def enemy_windup_ms(speed, combo_followup=False):
    """Pausa visual antes da ação do inimigo, sem alterar regras de combate."""
    base = ENEMY_COMBO_WINDUP_MS if combo_followup else ENEMY_WINDUP_MS
    multiplier = ENEMY_SPEED_MULTIPLIERS.get(speed, 1.0)
    return int(round(base * multiplier))


class GamePreferences:
    """Fonte única das preferências globais do computador."""

    def __init__(self, path=None):
        self.path = Path(path) if path is not None else Path(PREFERENCES_PATH)
        self.values = dict(DEFAULT_PREFERENCES)
        self.load()

    def load(self):
        """Lê o arquivo e devolve os valores validados, completando chaves ausentes."""
        self.values = dict(DEFAULT_PREFERENCES)
        try:
            data = json.loads(self.path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError, UnicodeError):
            return dict(self.values)

        if isinstance(data, dict):
            for key, default in DEFAULT_PREFERENCES.items():
                self.values[key] = _sanitize(key, data.get(key, default), default)
        return dict(self.values)

    def set(self, key, value):
        """Valida e atualiza uma preferência em memória."""
        if key not in DEFAULT_PREFERENCES:
            raise KeyError(key)
        self.values[key] = _sanitize(key, value, DEFAULT_PREFERENCES[key])
        return self.values[key]

    def get(self, key):
        return self.values.get(key, DEFAULT_PREFERENCES.get(key))

    def restore_tab(self, tab):
        """Restaura apenas as chaves da aba informada."""
        for key in PREFERENCE_KEYS_BY_TAB.get(tab, ()):
            self.values[key] = DEFAULT_PREFERENCES[key]

    def sync_audio(self, audio):
        for key in AUDIO_PREFERENCE_KEYS:
            self.set(key, getattr(audio, key))

    def sync_video(self, window_manager):
        self.set("fullscreen", bool(getattr(window_manager, "is_fullscreen", False)))
        self.set(
            "window_size",
            WINDOW_SIZE_LARGE
            if getattr(window_manager, "is_large_window", False)
            else WINDOW_SIZE_LEGACY,
        )

    def apply_audio(self, audio):
        for key in AUDIO_PREFERENCE_KEYS:
            getattr(audio, "set_" + key)(self.values[key])

    def apply_video(self, window_manager):
        apply_display_preferences = getattr(
            window_manager, "apply_display_preferences", None
        )
        if apply_display_preferences is None:
            return
        apply_display_preferences(
            fullscreen=self.values["fullscreen"],
            large_window=self.values["window_size"] == WINDOW_SIZE_LARGE,
        )

    def apply(self, audio):
        """Compatibilidade com o carregamento de áudio do ponto de entrada."""
        self.load()
        self.apply_audio(audio)

    def save(self, audio=None, window_manager=None):
        """Persiste todas as preferências de forma atômica."""
        if audio is not None:
            self.sync_audio(audio)
        if window_manager is not None:
            self.sync_video(window_manager)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=".audio-",
                suffix=".tmp",
                delete=False,
            ) as file:
                temporary = Path(file.name)
                json.dump(
                    {
                        key: _sanitize(key, self.values.get(key), default)
                        for key, default in DEFAULT_PREFERENCES.items()
                    },
                    file,
                    ensure_ascii=False,
                    indent=2,
                )
            os.replace(temporary, self.path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def default_enemy_speed():
    return ENEMY_SPEED_NORMAL
