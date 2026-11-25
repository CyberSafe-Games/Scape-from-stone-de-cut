from pygame import event
import pygame
import asyncio
from src.core.music_director import MusicDirector


class SceneManager:
    """Gerencia a máquina de estados de cenas do jogo e sobreposição de modais."""

    def __init__(self, audio_manager=None, audio_preferences=None, platform_service=None, home_factory=None):
        from src.platforms import get_platform
        self.platform = platform_service or get_platform()
        self.home_factory = home_factory
        self.exit_requested = False
        self.pending_task = None
        self.pending_ms = 0
        self.storage_error = ""
        self._command_complete = None
        self._command_failed = None
        self.current_scene = None
        self.modal_stack = []
        # Serviço opcional compartilhado pelas cenas, sem acoplá-las ao mixer.
        self.audio_manager = audio_manager
        self.audio_preferences = audio_preferences
        self.music_director = MusicDirector(audio_manager) if audio_manager is not None else None

    @property
    def saving(self):
        return self.pending_task is not None

    def submit(self, work, complete, failed=None):
        if self.saving:
            return False
        self.storage_error = ""
        self.pending_ms = 0
        self._command_complete, self._command_failed = complete, failed
        self.pending_task = asyncio.create_task(work())
        return True

    def poll_pending(self):
        if not self.saving or not self.pending_task.done():
            return
        task, complete, failed = self.pending_task, self._command_complete, self._command_failed
        self.pending_task = None
        try:
            result = task.result()
        except Exception as error:
            self.storage_error = str(error)
            if failed:
                failed(error)
        else:
            complete(result)

    def request_exit(self):
        """Um único comando: desktop encerra; web retorna ao início quando disponível."""
        if self.platform.exit_action() == "home" and self.home_factory is not None:
            self.change_scene(self.home_factory())
        else:
            self.exit_requested = True

    def change_scene(self, scene):
        """Muda a cena ativa e limpa eventuais modais sobrepostos."""
        self.modal_stack.clear()
        self.current_scene = scene
        if self.music_director is not None:
            self.music_director.set_context(getattr(scene, "music_context", None))

    def push_modal(self, modal):
        """Empilha um modal (ex: confirmação de saída) sobre a cena atual."""
        self.modal_stack.append(modal)

    def pop_modal(self):
        """Remove o modal do topo da pilha."""
        if self.modal_stack:
            return self.modal_stack.pop()
        return None

    @property
    def has_modal(self):
        return len(self.modal_stack) > 0

    def handle_event(self, event):
        """Delega o evento para o modal ativo ou para a cena atual."""
        import pygame

        if self.saving:
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            if self.audio_manager is not None:
                self.audio_manager.play_sfx("ui.click", volume=1.0)

        if self.modal_stack:
            self.modal_stack[-1].handle_event(event)
        elif self.current_scene:
            self.current_scene.handle_event(event)

    def update(self, dt):
        """Atualiza a lógica da cena ativa ou do modal."""
        if self.saving:
            self.pending_ms += max(0,dt)
            return
        if self.modal_stack:
            self.modal_stack[-1].update(dt)
        elif self.current_scene:
            self.current_scene.update(dt)

        if self.music_director is not None:
            self.music_director.set_context(getattr(self.current_scene, "music_context", None))
            self.music_director.update(dt)

    def draw(self, surface):
        """Desenha a cena atual e, se houver, os modais por cima."""
        if self.current_scene:
            if hasattr(surface,"begin_owner"):surface.begin_owner(self.current_scene)
            self.current_scene.draw(surface)

        for modal in self.modal_stack:
            if hasattr(surface,"begin_owner"):surface.begin_owner(modal)
            modal.draw(surface)
        if (self.saving and self.pending_ms > 100) or self.storage_error:
            font = pygame.font.Font(None, 30)
            message = "GRAVANDO... AGUARDE A CONFIRMAÇÃO" if self.saving else self.storage_error
            text = font.render(message[:140],True,(245,218,150))
            rect = text.get_rect(center=(surface.get_width()//2, surface.get_height()-45)).inflate(30,20)
            pygame.draw.rect(surface,(12,20,17),rect,border_radius=8)
            surface.blit(text,text.get_rect(center=rect.center))
