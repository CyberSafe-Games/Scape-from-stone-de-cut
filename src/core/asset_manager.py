import os
import pygame

from src.config.settings import (
    WIDTH,
    HEIGHT,
    BACKGROUND_PATH,
    PLAYER_ASSETS_DIR,
    CARD_ASSETS_DIR,
    CARD_EFFECTS_DIR,
)
from src.config.colors import WHITE


class AssetManager:
    """Carrega e armazena em cache todos os recursos visuais (fontes, sprites,

    texturas de cartas e animações).
    """

    CARD_IMAGE_FILES = {
        "Golpe": "card_golpe.png",
        "Defesa": "card_defesa.png",
        "Investida": "card_investida.png",
        "Fortalecer": "card_fortalecer.png",
        "Fúria": "card_furia.png",
        "Golpe Duplo": "card_golpe_duplo.png",
    }

    CARD_ACTION_FILES = {
        "Golpe": "golpe",
        "Defesa": "defesa",
        "Investida": "investida",
        "Fortalecer": "fortalecer",
        "Fúria": "furia",
        "Golpe Duplo": "golpe_duplo",
    }

    def __init__(self):
        self._fonts = {}
        self._card_images = {}
        self._card_action_sprites = {}
        self._player_sprites = {}
        self._background = None
        self._fallback_sprite = None

        self._init_fonts()
        self._load_background()
        self._load_player_sprites()
        self._load_card_action_sprites()

    def _init_fonts(self):
        """Inicializa as fontes tipográficas do jogo."""
        self._fonts["default"] = pygame.font.SysFont("arial", 22)
        self._fonts["big"] = pygame.font.SysFont("arial", 40, bold=True)
        self._fonts["title"] = pygame.font.SysFont("arial", 66, bold=True)
        self._fonts["menu"] = pygame.font.SysFont("arial", 28, bold=True)
        self._fonts["small"] = pygame.font.SysFont("arial", 18)

    def get_font(self, name="default"):
        return self._fonts.get(name, self._fonts["default"])

    @property
    def font(self):
        return self._fonts["default"]

    @property
    def big_font(self):
        return self._fonts["big"]

    @property
    def title_font(self):
        return self._fonts["title"]

    @property
    def menu_font(self):
        return self._fonts["menu"]

    @property
    def small_font(self):
        return self._fonts["small"]

    def _load_background(self):
        """Carrega a imagem de fundo do cenário."""
        try:
            image = pygame.image.load(BACKGROUND_PATH).convert()
            self._background = pygame.transform.smoothscale(image, (WIDTH, HEIGHT))
        except (pygame.error, FileNotFoundError):
            print(f"[AVISO] Fundo não encontrado: {BACKGROUND_PATH}")
            self._background = None

    @property
    def background(self):
        return self._background

    @staticmethod
    def fit_character_sprite(image, target_height=130, max_width=105):
        """Recorta transparência e mantém todos os frames com escala proporcional."""
        image = image.convert_alpha()
        bbox = image.get_bounding_rect(min_alpha=1)
        if bbox.width <= 0 or bbox.height <= 0:
            return None
        image = image.subsurface(bbox).copy()
        w, h = image.get_size()
        scale = min(target_height / h, max_width / w)
        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        return pygame.transform.smoothscale(image, (nw, nh))

    def load_sprite(self, filename, target_height=130):
        path = os.path.join(PLAYER_ASSETS_DIR, filename)
        try:
            image = pygame.image.load(path).convert_alpha()
        except (pygame.error, FileNotFoundError):
            return None
        return self.fit_character_sprite(image, target_height)

    def load_sprite_group(self, prefix, count, target_height=130):
        sprites = []
        for index in range(1, count + 1):
            sprite = self.load_sprite(f"{prefix}_{index}.png", target_height)
            if sprite is not None:
                sprites.append(sprite)
        return sprites

    def _load_player_sprites(self):
        """Carrega as animações do personagem jogador."""
        self._player_sprites = {
            "idle": self.load_sprite_group("idle", 2),
            "soco": self.load_sprite_group("soco", 3),
            "dano": self.load_sprite_group("dano", 3),
            "vitoria": self.load_sprite_group("vitoria", 2),
        }

    def get_fallback_sprite(self):
        """Desenha proceduralmente um personagem simples (boneco palito) caso os sprites faltem."""
        if self._fallback_sprite is not None:
            return self._fallback_sprite

        surface = pygame.Surface((80, 130), pygame.SRCALPHA)
        pygame.draw.circle(surface, WHITE, (40, 25), 16, 4)
        pygame.draw.line(surface, WHITE, (40, 41), (40, 90), 4)
        pygame.draw.line(surface, WHITE, (40, 90), (20, 125), 4)
        pygame.draw.line(surface, WHITE, (40, 90), (60, 125), 4)
        pygame.draw.line(surface, WHITE, (40, 55), (15, 75), 4)
        pygame.draw.line(surface, WHITE, (40, 55), (65, 75), 4)

        self._fallback_sprite = surface
        return surface

    def get_player_sprite(self, group_name, index=0):
        sprites = self._player_sprites.get(group_name, [])
        if not sprites:
            return self.get_fallback_sprite()
        return sprites[index % len(sprites)]

    def get_player_sprite_group(self, group_name):
        return self._player_sprites.get(group_name, [])

    def _load_card_action_sprites(self):
        """Carrega os frames de animação acionados ao jogar cada tipo de carta."""
        for name, prefix in self.CARD_ACTION_FILES.items():
            frames = []
            for i in range(1, 4):
                path = os.path.join(CARD_EFFECTS_DIR, f"{prefix}_{i}.png")
                try:
                    img = pygame.image.load(path).convert_alpha()
                    frame = self.fit_character_sprite(img, 130, 105)
                    if frame is not None:
                        frames.append(frame)
                except (pygame.error, FileNotFoundError):
                    pass
            self._card_action_sprites[name] = frames

    def get_card_action_sprites(self, action_name):
        return self._card_action_sprites.get(action_name, [])

    def get_card_image(self, card_name):
        """Retorna a textura gráfica de uma carta pelo seu nome."""
        filename = self.CARD_IMAGE_FILES.get(card_name)
        if not filename:
            return None

        if filename not in self._card_images:
            path = os.path.join(CARD_ASSETS_DIR, filename)
            try:
                self._card_images[filename] = pygame.image.load(path).convert_alpha()
            except (pygame.error, FileNotFoundError):
                self._card_images[filename] = None

        return self._card_images[filename]
