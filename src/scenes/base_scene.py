
from abc import ABC, abstractmethod


class BaseScene(ABC):
    """Classe base abstrata para todas as cenas do jogo (Open/Closed Principle)."""

    @property
    def music_context(self):
        return 'menu'

    def __init__(self, scene_manager, window_manager, asset_manager):
        self.scene_manager = scene_manager
        self.window_manager = window_manager
        self.asset_manager = asset_manager

    def persist_command(self, command, complete):
        from src.storage.manager import persist_command
        return persist_command(self, command, complete)

    def management_back(self):
        callback = getattr(self.scene_manager, "management_home", None)
        if getattr(getattr(self, "save_manager", None), "async_commands", False) is True and callable(callback):
            callback(self.save_manager, self.save_data)
            return True
        return False

    def play_ui_sound(self, sound_id, volume=1.0, maxtime=None):
        """Reproduz um efeito de interface se o áudio estiver disponível."""
        audio_manager = getattr(self.scene_manager, "audio_manager", None)

        if audio_manager is not None:
            if maxtime is not None:
                return audio_manager.play_sfx(sound_id, volume=volume, maxtime=maxtime)
            return audio_manager.play_sfx(sound_id, volume=volume)

        return None

    def open_options_modal(self):
        """Abre o menu de Opções por cima da cena, congelando a atual."""
        from src.scenes.options_scene import OptionsScene

        self.play_ui_sound("ui.click")
        self.scene_manager.push_modal(
            OptionsScene(
                self.scene_manager,
                self.window_manager,
                self.asset_manager,
                modal=True,
            )
        )

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
