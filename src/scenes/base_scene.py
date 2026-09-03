from abc import ABC, abstractmethod


class BaseScene(ABC):
    """Classe base abstrata para todas as cenas do jogo (Open/Closed Principle)."""

    def __init__(self, scene_manager, window_manager, asset_manager):
        self.scene_manager = scene_manager
        self.window_manager = window_manager
        self.asset_manager = asset_manager

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
