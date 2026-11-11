import pygame
from src.config.settings import WIDTH, HEIGHT, TITLE, LEGACY_WINDOW_SIZE
from src.config.colors import BLACK, BUTTON_BG, BUTTON_HOVER, GOLD, WHITE
from src.ui import dark_fantasy_theme as theme


# Tamanhos de janela 16:9 tentados, do maior para o menor.
WINDOW_SIZE_CANDIDATES = ((1920, 1080), (1600, 900), LEGACY_WINDOW_SIZE)
# Folga para barra de título, bordas e barra de tarefas do sistema.
WINDOW_MARGIN = (40, 110)
# Tempo em que eventos de redimensionamento gerados pela própria troca de modo são ignorados.
MODE_CHANGE_SETTLE_MS = 400


class WindowManager:
    """Gerencia a janela real do Pygame, alternância de tela cheia,

    resolução virtual (1920x1080) e mapeamento de coordenadas do mouse.
    """

    def __init__(self, width=WIDTH, height=HEIGHT, title=TITLE, window_size=None):
        self.width = width
        self.height = height
        self.title = title

        self.is_fullscreen = False
        # Janela grande (F10): o maior 16:9 que cabe na tela (até 1920x1080).
        self.large_window_size = self._fit_window_size()
        # O jogo abre em janela 1280x720; F11 alterna entre ela e a tela cheia.
        self.windowed_size = tuple(window_size) if window_size else LEGACY_WINDOW_SIZE
        self._mode_changed_at = 0

        self.display_surface = pygame.display.set_mode(
            self.windowed_size, pygame.RESIZABLE
        )
        pygame.display.set_caption(self.title)

        # Superfície interna de tamanho fixo usada por todo o desenho
        self.screen = pygame.Surface((self.width, self.height))

    @staticmethod
    def _desktop_size():
        try:
            sizes = pygame.display.get_desktop_sizes()
        except (pygame.error, AttributeError):
            sizes = []
        return sizes[0] if sizes else None

    def _fit_window_size(self):
        """Maior tamanho 16:9 de janela que cabe inteiro na área do desktop."""
        desktop = self._desktop_size()
        if not desktop:
            return (self.width, self.height)
        max_w = desktop[0] - WINDOW_MARGIN[0]
        max_h = desktop[1] - WINDOW_MARGIN[1]
        for size in WINDOW_SIZE_CANDIDATES:
            if size[0] <= max_w and size[1] <= max_h:
                return size
        # Telas pequenas: reduz mantendo 16:9.
        scale = min(max_w / self.width, max_h / self.height)
        return (max(320, int(self.width * scale)), max(180, int(self.height * scale)))

    def _apply_mode(self):
        """Aplica o modo atual (tela cheia ou janela) e descarta os ecos de redimensionamento."""
        if self.is_fullscreen:
            self.display_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            if not self.display_surface.get_flags() & pygame.FULLSCREEN:
                # Alguns drivers ignoram a troca via set_mode; tenta o método nativo.
                try:
                    pygame.display.toggle_fullscreen()
                except pygame.error:
                    pass
                self.display_surface = pygame.display.get_surface()
        else:
            self.display_surface = pygame.display.set_mode(
                self.windowed_size, pygame.RESIZABLE
            )
        self._mode_changed_at = pygame.time.get_ticks()
        pygame.event.clear(pygame.VIDEORESIZE)

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
        """Alterna entre tela cheia (sem barra de título) e a janela 1280x720."""
        self.is_fullscreen = not self.is_fullscreen
        if not self.is_fullscreen:
            self.windowed_size = LEGACY_WINDOW_SIZE
        self._apply_mode()

    def toggle_legacy_window(self):
        """Alterna o modo janela entre a janela grande (até 1920x1080) e a resolução antiga (1280x720).

        A renderização continua em Full HD; a imagem é ajustada ao tamanho da
        janela. Em tela cheia, sai direto para a janela 1280x720.
        """
        if self.is_fullscreen or self.windowed_size != LEGACY_WINDOW_SIZE:
            self.windowed_size = LEGACY_WINDOW_SIZE
        else:
            self.windowed_size = self.large_window_size
        self.is_fullscreen = False
        self._apply_mode()

    def handle_window_event(self, event):
        """Trata redimensionamento, F11 (tela cheia / janela 1280x720) e F10 (tamanho da janela).

        Retorna True se o evento foi consumido.
        """
        if event.type == pygame.VIDEORESIZE:
            # No Pygame 2 a janela redimensionável já ajusta a própria superfície;
            # chamar set_mode aqui desfaria a troca de modo recém-aplicada.
            settling = pygame.time.get_ticks() - self._mode_changed_at < MODE_CHANGE_SETTLE_MS
            if not self.is_fullscreen and not settling:
                self.windowed_size = (event.w, event.h)
            surface = pygame.display.get_surface()
            if surface is not None:
                self.display_surface = surface
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
