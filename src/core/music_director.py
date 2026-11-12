"""Troca músicas sem bloquear o jogo nem interromper os efeitos sonoros."""
from src.config.music import MUSIC_TRACKS, FADE_OUT_MS, FADE_IN_MS


class MusicDirector:
    def __init__(self, audio):
        self.audio = audio
        self._desired = None
        self._playing = None
        self._fading = False
        self._remaining = 0

    def set_context(self, context):
        target = MUSIC_TRACKS.get(context) if isinstance(context, str) else None
        if target == self._desired:
            return
        self._desired = target
        if self._fading:
            return  # A última escolha será usada ao terminar a saída atual.
        if self._playing is not None:
            self.audio.stop_music(fade_ms=FADE_OUT_MS)
            self._remaining = FADE_OUT_MS
            self._fading = True
        else:
            self._start_desired()

    def _start_desired(self):
        if self._desired is not None:
            if self.audio.play_music(self._desired, loops=-1, fade_ms=FADE_IN_MS):
                self._playing = self._desired

    def update(self, dt):
        if not self._fading:
            return
        self._remaining = max(0, self._remaining - max(0, dt))
        if self._remaining == 0:
            self._fading = False
            self._playing = None
            self._start_desired()
