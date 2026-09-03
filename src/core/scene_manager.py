class SceneManager:
    """Gerencia a máquina de estados de cenas do jogo e sobreposição de modais."""

    def __init__(self):
        self.current_scene = None
        self.modal_stack = []

    def change_scene(self, scene):
        """Muda a cena ativa e limpa eventuais modais sobrepostos."""
        self.modal_stack.clear()
        self.current_scene = scene

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
        if self.modal_stack:
            self.modal_stack[-1].handle_event(event)
        elif self.current_scene:
            self.current_scene.handle_event(event)

    def update(self, dt):
        """Atualiza a lógica da cena ativa ou do modal."""
        if self.modal_stack:
            self.modal_stack[-1].update(dt)
        elif self.current_scene:
            self.current_scene.update(dt)

    def draw(self, surface):
        """Desenha a cena atual e, se houver, os modais por cima."""
        if self.current_scene:
            self.current_scene.draw(surface)

        for modal in self.modal_stack:
            modal.draw(surface)
