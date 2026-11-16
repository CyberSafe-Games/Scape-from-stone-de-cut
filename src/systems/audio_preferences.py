"""Compatibilidade: as preferências de áudio agora vivem em GamePreferences.

O arquivo settings/audio.json é o mesmo de antes; as novas chaves são
acrescentadas a ele, sem criar um segundo arquivo de configuração.
"""

from src.config.preferences import (
    AUDIO_PREFERENCE_KEYS,
    DEFAULT_PREFERENCES,
    VOLUME_STEP,
)
from src.systems.game_preferences import GamePreferences

DEFAULT_VOLUMES = {
    key: DEFAULT_PREFERENCES[key] for key in AUDIO_PREFERENCE_KEYS
}

class AudioPreferences(GamePreferences):
    """Visão apenas de áudio da mesma configuração global (compatibilidade)."""

    def load(self):
        values = super().load()
        return {key: values[key] for key in AUDIO_PREFERENCE_KEYS}

    def apply(self, audio):
        self.load()
        self.apply_audio(audio)


# Nome antigo mantido para os módulos e testes que ainda o importam.

__all__ = [
    "AudioPreferences",
    "DEFAULT_PREFERENCES",
    "DEFAULT_VOLUMES",
    "GamePreferences",
    "VOLUME_STEP",
]
