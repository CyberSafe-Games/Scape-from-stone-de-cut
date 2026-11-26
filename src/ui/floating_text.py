import pygame
from src.config.layout import FLOAT_DURATION


class FloatingText:
    """Representa um texto flutuante com movimentação vertical e esmaecimento (fade)."""

    def __init__(self, x, y, text, color, duration=FLOAT_DURATION):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = duration
        self.max_life = duration

    def update(self, dt):
        self.life -= dt
        self.y -= 67.5 * (dt / 1000)

    def is_dead(self):
        return self.life <= 0

    def draw(self, surface, font):
        alpha = max(0, min(255, int(255 * (self.life / self.max_life))))
        if hasattr(surface,"render_text"):
            text_surface=surface.render_text(font,self.text,self.color)
            old=text_surface.get_alpha();text_surface.set_alpha(alpha)
            try:surface.blit(text_surface,text_surface.get_rect(center=(int(self.x),int(self.y))))
            finally:text_surface.set_alpha(old)
            return
        text_surface = font.render(str(self.text), True, self.color)

        alpha_surface = pygame.Surface(text_surface.get_size(), pygame.SRCALPHA)
        alpha_surface.blit(text_surface, (0, 0))
        alpha_surface.set_alpha(alpha)

        rect = alpha_surface.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(alpha_surface, rect)


class FloatingTextManager:
    """Gerencia a lista de textos flutuantes ativos."""

    def __init__(self, enabled=True):
        self.texts = []
        self.enabled = enabled

    def set_enabled(self, enabled):
        """Liga/desliga apenas a exibição; nenhum efeito de combate é alterado."""
        enabled = bool(enabled)
        if self.enabled and not enabled:
            self.clear()
        self.enabled = enabled

    def spawn(self, x, y, text, color):
        if not self.enabled:
            return
        self.texts.append(FloatingText(x, y, text, color))

    def update(self, dt):
        for item in self.texts[:]:
            item.update(dt)
            if item.is_dead():
                self.texts.remove(item)

    def draw(self, surface, font):
        for item in self.texts:
            item.draw(surface, font)

    def clear(self):
        self.texts.clear()
