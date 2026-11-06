import pygame
from src.config.settings import WIDTH, HEIGHT, TITLE, LEGACY_WINDOW_SIZE
from src.config.colors import BLACK, BUTTON_BG, BUTTON_HOVER, GOLD, WHITE
from src.ui import dark_fantasy_theme as theme


class WindowManager:
    """Gerencia a janela real do Pygame, alternância de tela cheia,

    resolução virtual (1920x1080) e mapeamento de coordenadas do mouse.
    """

    def __init__(self, width=WIDTH, height=HEIGHT, title=TITLE, window_size=None):
        self.width = width
        self.height = height
        self.title = title

        self.is_fullscreen = False
        # Tamanho da janela real; por padrão igual à resolução de renderização.
        self.windowed_size = tuple(window_size) if window_size else (width, height)

        self.display_surface = pygame.display.set_mode(
            self.windowed_size, pygame.RESIZABLE
        )
        pygame.display.set_caption(self.title)

        # Superfície interna de tamanho fixo usada por todo o desenho
        self.screen = pygame.Surface((self.width, self.height))

    @property
    def virtual_screen(self):
        """Retorna a superfície virtual onde o jogo é desenhado."""
        return self.screen

    def get_scale_and_offset(self):
        """Calcula a escala e o deslocamento (letterbox) da superfície

        virtual dentro da janela real atual.
        """
        dw, dh = self.display_surface.get_size()
        scale = min(dw / self.width, dh / self.height)
        scale = max(scale, 0.0001)

        new_w = self.width * scale
        new_h = self.height * scale

        offset_x = (dw - new_w) / 2
        offset_y = (dh - new_h) / 2

        return scale, offset_x, offset_y

    def map_to_virtual(self, pos):
        """Converte uma posição de mouse na janela real para a posição

        correspondente na superfície virtual fixa (WIDTH x HEIGHT).
        """
        scale, offset_x, offset_y = self.get_scale_and_offset()
        vx = (pos[0] - offset_x) / scale
        vy = (pos[1] - offset_y) / scale
        return vx, vy

    def get_virtual_mouse_pos(self):
        """Como pygame.mouse.get_pos(), mas já convertido para as

        coordenadas da superfície virtual do jogo.
        """
        return self.map_to_virtual(pygame.mouse.get_pos())

    def present(self):
        """Escala a superfície virtual para a janela real com letterboxing e exibe."""
        scale, offset_x, offset_y = self.get_scale_and_offset()

        new_w = max(1, int(self.width * scale))
        new_h = max(1, int(self.height * scale))

        scaled = pygame.transform.smoothscale(self.screen, (new_w, new_h))

        self.display_surface.fill(BLACK)
        self.display_surface.blit(scaled, (int(offset_x), int(offset_y)))
        pygame.display.flip()

    def toggle_fullscreen(self):
        """Alterna entre janela redimensionável e tela cheia."""
        if not self.is_fullscreen:
            self.windowed_size = self.display_surface.get_size()
            self.display_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.is_fullscreen = True
        else:
            self.display_surface = pygame.display.set_mode(
                self.windowed_size, pygame.RESIZABLE
            )
            self.is_fullscreen = False

    def toggle_legacy_window(self):
        """Alterna o modo janela entre Full HD (1920x1080) e a resolução antiga (1280x720).

        A renderização continua em Full HD; no modo 1280x720 a imagem é
        reduzida para a janela. Em tela cheia, sai direto para a janela 1280x720.
        """
        if self.is_fullscreen or self.windowed_size != LEGACY_WINDOW_SIZE:
            self.windowed_size = LEGACY_WINDOW_SIZE
        else:
            self.windowed_size = (self.width, self.height)
        self.is_fullscreen = False
        self.display_surface = pygame.display.set_mode(
            self.windowed_size, pygame.RESIZABLE
        )

    def handle_window_event(self, event):
        """Trata redimensionamento, F11 (tela cheia) e F10 (janela 1280x720).

        Retorna True se o evento foi consumido.
        """
        if event.type == pygame.VIDEORESIZE:
            if not self.is_fullscreen:
                self.windowed_size = (event.w, event.h)
                self.display_surface = pygame.display.set_mode(
                    self.windowed_size, pygame.RESIZABLE
                )
            return True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                self.toggle_fullscreen()
                return True
            if event.key == pygame.K_F10:
                self.toggle_legacy_window()
                return True

        return False

    def get_fullscreen_button_rect(self):
        return pygame.Rect(-1000, -1000, 1, 1)

    def draw_fullscreen_button(self, font=None):
        return
