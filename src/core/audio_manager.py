"""Gerenciamento centralizado de áudio do jogo.

Os demais módulos devem solicitar sons por identificadores (ex.: "ui.confirm"),
sem carregar arquivos ou manipular diretamente o mixer do Pygame.
"""

import logging
import sys
from pathlib import Path

import pygame

from src.config.audio_mix import DAMAGE_SOUND_IDS, INTERFACE_SOUND_IDS
from src.config.settings import ASSETS_DIR

logger = logging.getLogger(__name__)

WEB_MIXER = dict(frequency=44100, size=-16, channels=2, buffer=4096)
WEB_SFX_CHANNELS = 4
WEB_SFX_GAIN = 0.16
WEB_MUSIC_GAIN = 0.25


def prepare_web_audio():
    """Configura antes de inicializar subsistemas; não abre áudio sem gesto."""
    if sys.platform == "emscripten":
        pygame.mixer.pre_init(**WEB_MIXER)



class AudioManager:
    """Centraliza efeitos sonoros, música e volumes da aplicação.

    A classe tolera falhas de inicialização do dispositivo de áudio e arquivos
    ausentes para que o jogo continue funcionando sem som.
    """

    def __init__(self, assets_dir=None, master_volume=1.0, sfx_volume=1.0, music_volume=0.7, combat_volume=1.0, damage_volume=1.0, defer_initialization=False):
        self._web_audio = sys.platform == "emscripten"
        self.assets_dir = Path(assets_dir) if assets_dir else Path(ASSETS_DIR) / "audio"
        self._sound_paths = {}
        self._sounds = {}
        self._sound_volumes = {}
        self._sfx_call_volumes = {}
        self._failed_sounds = set()
        self._mixer_available = False
        self._music_path = None

        self.master_volume = self._clamp_volume(master_volume)
        self.sfx_volume = self._clamp_volume(sfx_volume)
        self.music_volume = self._clamp_volume(music_volume)
        self.combat_volume = self._clamp_volume(combat_volume)
        self.damage_volume = self._clamp_volume(damage_volume)

        self._audio_locked = bool(defer_initialization)
        self._deferred_music = None
        if not self._audio_locked:
            self._initialize_mixer()

    def unlock_after_interaction(self):
        """Desbloqueia áudio após gesto; desktop continua inicializando normalmente."""
        if not self._audio_locked:
            return self.available
        self._audio_locked = False
        self._initialize_mixer()
        if self._deferred_music is not None:
            path, loops, start, fade = self._deferred_music
            self._deferred_music = None
            self.play_music(path, loops=loops, start=start, fade_ms=fade)
        return self.available

    def set_suspended(self, suspended):
        """Pausa canais e trilha sem perder posição, somente quando há transição."""
        suspended = bool(suspended)
        if suspended == getattr(self, "_suspended", False):
            return
        self._suspended = suspended
        if not self.available:
            return
        if suspended:
            pygame.mixer.pause()
            pygame.mixer.music.pause()
        else:
            pygame.mixer.unpause()
            pygame.mixer.music.unpause()

    @staticmethod
    def _clamp_volume(value):
        """Limita o volume ao intervalo aceito pelo Pygame: 0.0 a 1.0."""
        return max(0.0, min(1.0, float(value)))

    def _initialize_mixer(self):
        """Inicializa o mixer se necessário, sem interromper o jogo em caso de erro."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(**WEB_MIXER) if self._web_audio else pygame.mixer.init()
            if self._web_audio:
                pygame.mixer.set_num_channels(WEB_SFX_CHANNELS)
            self._mixer_available = pygame.mixer.get_init() is not None
        except (pygame.error, AttributeError) as exc:
            self._mixer_available = False
            logger.warning("Áudio indisponível; o jogo continuará sem som: %s", exc)

    @property
    def available(self):
        """Indica se o mixer está inicializado e pronto para reprodução."""
        return not self._audio_locked and self._mixer_available and pygame.mixer.get_init() is not None

    def register_sound(self, sound_id, relative_path):
        """Registra o caminho de um efeito sem carregá-lo imediatamente.

        Args:
            sound_id: identificador estável usado pelo código (ex.: "player.hurt").
            relative_path: caminho relativo à pasta assets/audio ou caminho absoluto.
        """
        path = Path(relative_path)
        if not path.is_absolute():
            path = self.assets_dir / path
        self._sound_paths[str(sound_id)] = path
        self._sounds.pop(str(sound_id), None)
        self._failed_sounds.discard(str(sound_id))

    def register_sounds(self, sounds):
        """Registra vários efeitos a partir de um dicionário {id: caminho}."""
        for sound_id, path in sounds.items():
            self.register_sound(sound_id, path)

    def _get_sound(self, sound_id):
        if not self.available or sound_id not in self._sound_paths:
            return None
        if sound_id in self._sounds:
            return self._sounds[sound_id]
        if sound_id in self._failed_sounds:
            return None

        path = self._sound_paths[sound_id]
        try:
            sound = pygame.mixer.Sound(str(path))
            self._sounds[sound_id] = sound
            return sound
        except (pygame.error, OSError) as exc:
            self._failed_sounds.add(sound_id)
            logger.warning("Não foi possível carregar o som '%s' (%s): %s", sound_id, path, exc)
            return None

    def play_sfx(self, sound_id, volume=1.0, maxtime=None):
        """Reproduz um efeito sonoro registrado; não falha se ele estiver ausente."""
        sound = self._get_sound(sound_id)
        if sound is None:
            return None
        self._sfx_call_volumes[sound_id] = volume
        effective_volume = self._effective_sfx_volume(sound_id, volume)
        sound.set_volume(effective_volume)
        try:
            if maxtime is not None:
                if maxtime <= 0:
                    return None
                return sound.play(maxtime=max(1, int(maxtime)))
            return sound.play()
        except pygame.error as exc:
            logger.warning("Não foi possível reproduzir o som '%s': %s", sound_id, exc)
            return None

    def _effective_sfx_volume(self, sound_id, call_volume):
        category_volume = (self.damage_volume if sound_id in DAMAGE_SOUND_IDS
                           else self.combat_volume if sound_id.startswith('gameplay.')
                           and sound_id not in INTERFACE_SOUND_IDS else 1.0)
        gain = WEB_SFX_GAIN if self._web_audio else 1.0
        return gain * self._clamp_volume(self.master_volume * self.sfx_volume * call_volume
                                  * self._sound_volumes.get(sound_id, 1.0) * category_volume)

    def _effective_music_volume(self):
        gain = WEB_MUSIC_GAIN if self._web_audio else 1.0
        return gain * self._clamp_volume(self.master_volume * self.music_volume)

    def _apply_sfx_volumes(self):
        for sound_id, sound in self._sounds.items():
            sound.set_volume(self._effective_sfx_volume(sound_id, self._sfx_call_volumes.get(sound_id, 1.0)))

    def set_combat_volume(self, volume):
        self.combat_volume = self._clamp_volume(volume)
        self._apply_sfx_volumes()

    def set_damage_volume(self, volume):
        self.damage_volume = self._clamp_volume(volume)
        self._apply_sfx_volumes()

    def play_music(self, relative_path, loops=-1, start=0.0, fade_ms=0):
        """Inicia música de fundo. Por padrão, a música repete continuamente."""
        if self._audio_locked:
            self._deferred_music = (relative_path, loops, start, fade_ms)
            return False

        if not self.available:
            return False
        path = Path(relative_path)
        if not path.is_absolute():
            path = self.assets_dir / path
        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(self._effective_music_volume())
            if fade_ms > 0:
                pygame.mixer.music.play(loops=loops, start=start, fade_ms=int(fade_ms))
            else:
                pygame.mixer.music.play(loops=loops, start=start)
            self._music_path = path
            return True
        except (pygame.error, OSError) as exc:
            logger.warning("Não foi possível iniciar a música '%s': %s", path, exc)
            return False

    def stop_music(self, fade_ms=0):
        """Para a música imediatamente ou após uma transição gradual."""
        if not self.available:
            return
        if fade_ms > 0:
            pygame.mixer.music.fadeout(int(fade_ms))
        else:
            pygame.mixer.music.stop()
        self._music_path = None

    def set_master_volume(self, volume):
        self.master_volume = self._clamp_volume(volume)
        self._apply_music_volume()
        self._apply_sfx_volumes()

    def set_sfx_volume(self, volume):
        self.sfx_volume = self._clamp_volume(volume)
        self._apply_sfx_volumes()

    def set_sound_volume(self, sound_id, volume):
        """Ajusta o ganho de um efeito nas próximas reproduções (0.0 a 1.0)."""
        self._sound_volumes[str(sound_id)] = self._clamp_volume(volume)
        self._apply_sfx_volumes()

    def set_music_volume(self, volume):
        self.music_volume = self._clamp_volume(volume)
        self._apply_music_volume()

    def _apply_music_volume(self):
        if self.available:
            pygame.mixer.music.set_volume(self._effective_music_volume())

    def stop_all_sfx(self):
        """Interrompe os efeitos que estão tocando, sem parar a música."""
        if self.available:
            pygame.mixer.stop()

    def shutdown(self):
        """Libera a reprodução de áudio antes de encerrar o Pygame."""
        if self.available:
            pygame.mixer.music.stop()
            pygame.mixer.stop()
        self._music_path = None
