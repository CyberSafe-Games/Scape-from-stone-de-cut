
from abc import ABC, abstractmethod


class BaseScene(ABC):
    """Classe base abstrata para todas as cenas do jogo (Open/Closed Principle)."""

    def __init__(self, scene_manager, window_manager, asset_manager):
        self.scene_manager = scene_manager
        self.window_manager = window_manager
        self.asset_manager = asset_manager

    def play_ui_sound(self, sound_id, volume=1.0):
        """Reproduz um efeito de interface se o áudio estiver disponível."""
        audio_manager = getattr(self.scene_manager, "audio_manager", None)

        if audio_manager is not None:
            return audio_manager.play_sfx(sound_id, volume=volume)

        return None

    @abstractmethod
    def handle_event(self, event):
        """Processa eventos de entrada (mouse, teclado)."""
        pass

    @abstractmethod
    def update(self, dt):
        """Atualiza a lógica e o estado da cena."""
        pass

    @abstractmethod
    def draw(self, surface):
        """Renderiza os elementos da cena na superfície informada."""
        pass
