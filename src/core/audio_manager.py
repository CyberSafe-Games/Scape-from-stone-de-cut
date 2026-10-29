"""Gerenciamento centralizado de áudio do jogo.

Os demais módulos devem solicitar sons por identificadores (ex.: "ui.confirm"),
sem carregar arquivos ou manipular diretamente o mixer do Pygame.
"""

from pathlib import Path
import logging

import pygame

logger = logging.getLogger(__name__)


class AudioManager:
    """Centraliza efeitos sonoros, música e volumes da aplicação.

    A classe tolera falhas de inicialização do dispositivo de áudio e arquivos
    ausentes para que o jogo continue funcionando sem som.
    """

    def __init__(self, assets_dir=None, master_volume=1.0, sfx_volume=1.0, music_volume=0.7):
        project_root = Path(__file__).resolve().parents[2]
        self.assets_dir = Path(assets_dir) if assets_dir else project_root / "assets" / "audio"
        self._sound_paths = {}
        self._sounds = {}
        self._failed_sounds = set()
        self._mixer_available = False
        self._music_path = None

        self.master_volume = self._clamp_volume(master_volume)
        self.sfx_volume = self._clamp_volume(sfx_volume)
        self.music_volume = self._clamp_volume(music_volume)

        self._initialize_mixer()

    @staticmethod
    def _clamp_volume(value):
        """Limita o volume ao intervalo aceito pelo Pygame: 0.0 a 1.0."""
        return max(0.0, min(1.0, float(value)))

    def _initialize_mixer(self):
        """Inicializa o mixer se necessário, sem interromper o jogo em caso de erro."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self._mixer_available = pygame.mixer.get_init() is not None
        except (pygame.error, AttributeError) as exc:
            self._mixer_available = False
            logger.warning("Áudio indisponível; o jogo continuará sem som: %s", exc)

    @property
    def available(self):
        """Indica se o mixer está inicializado e pronto para reprodução."""
        return self._mixer_available and pygame.mixer.get_init() is not None

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

    def play_sfx(self, sound_id, volume=1.0):
        """Reproduz um efeito sonoro registrado; não falha se ele estiver ausente."""
        sound = self._get_sound(sound_id)
        if sound is None:
            return None
        effective_volume = self._clamp_volume(self.master_volume * self.sfx_volume * volume)
        sound.set_volume(effective_volume)
        try:
            return sound.play()
        except pygame.error as exc:
            logger.warning("Não foi possível reproduzir o som '%s': %s", sound_id, exc)
            return None

    def play_music(self, relative_path, loops=-1, start=0.0):
        """Inicia música de fundo. Por padrão, a música repete continuamente."""
        if not self.available:
            return False
        path = Path(relative_path)
        if not path.is_absolute():
            path = self.assets_dir / path
        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(self._clamp_volume(self.master_volume * self.music_volume))
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

    def set_sfx_volume(self, volume):
        self.sfx_volume = self._clamp_volume(volume)

    def set_music_volume(self, volume):
        self.music_volume = self._clamp_volume(volume)
        self._apply_music_volume()

    def _apply_music_volume(self):
        if self.available:
            pygame.mixer.music.set_volume(self._clamp_volume(self.master_volume * self.music_volume))

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
