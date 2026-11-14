"""Preferências de áudio locais e independentes do progresso da campanha."""
import json
import math
import os
from pathlib import Path
import tempfile
from src.config.music import MUSIC_VOLUME

DEFAULT_VOLUMES = dict(master_volume=1.0, music_volume=MUSIC_VOLUME,
                       combat_volume=1.0, damage_volume=1.0)


class AudioPreferences:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else Path(__file__).resolve().parents[2]/'settings/audio.json'

    @staticmethod
    def _value(value, default):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            return default
        return max(0.0, min(1.0, float(value)))

    def load(self):
        values = DEFAULT_VOLUMES.copy()
        try:
            data = json.loads(self.path.read_text(encoding='utf-8-sig'))
            if isinstance(data, dict):
                values.update({key:self._value(data.get(key),default) for key,default in values.items()})
        except (OSError, ValueError, UnicodeError):
            pass
        return values

    def apply(self, audio):
        for key,value in self.load().items():
            getattr(audio, 'set_'+key)(value)

    def save(self, audio):
        values = {key:self._value(getattr(audio,key),default) for key,default in DEFAULT_VOLUMES.items()}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.path.parent,
                                             prefix='.audio-', suffix='.tmp', delete=False) as file:
                temporary = Path(file.name)
                json.dump(values, file, ensure_ascii=False, indent=2)
            os.replace(temporary, self.path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
