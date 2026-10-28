import os
import pygame
from src.ui.sprite_cleanup import remove_white_fringe, recolor_green_aura_red
from src.systems.normal_enemy_catalog import NORMAL_SPRITES, NORMAL_RANGED

from src.config.settings import (
    WIDTH,
    HEIGHT,
    BACKGROUND_PATH,
    PLAYER_ASSETS_DIR,
    CARD_ASSETS_DIR,
    CARD_EFFECTS_DIR,
    COIN_ICON_PATH,
    UI_ASSETS_DIR,
    ULTIMATE_ASSETS_DIR,
)
from src.config.colors import WHITE

# Escala visual do Corpo Seco: 0.74 * ~170 px de corpo = ~126 px no jogo.
# Mantém o miniboss proporcional ao Jaum Manel (~130 px) e ao cenário.
CORPO_SECO_RENDER_SCALE = 0.74
GOBLIN_NERD_RENDER_SCALE = 0.72


class AssetManager:
    """Carrega e armazena em cache todos os recursos visuais (fontes, sprites,

    texturas de cartas e animações).
    """

    from src.systems.card_definitions import CARD_SPECS
    CARD_IMAGE_FILES = {s[1]: s[0] + '.png' for s in CARD_SPECS}
    CARD_ACTION_FILES = {s[1]: s[0] for s in CARD_SPECS}

    def __init__(self):
        self._fonts = {}
        self._card_images = {}
        self._card_action_sprites = {}
        self._player_sprites = {}
        self._enemy_sprites = {}
        self._enemy_projectiles = {}
        self._background = None
        self._background_tutorial = None
        self._territory_backgrounds = {}
        self._fallback_sprite = None
        self._coin_icon = None
        self._ui_images = {}
        self._status_icons = {}
        self._projectile_images = {}
        self._ultimate_images = {}
        self._ultimate_effect_sprites = {}
        self._boss_ultimate_sprites = {}
        self._boss_ultimate_effects = {}

        self._init_fonts()
        self._load_background()
        self._load_tutorial_background()
        self._load_territory_backgrounds()
        self._load_player_sprites()
        self._load_enemy_sprites()
        self._load_card_action_sprites()
        self._load_boss_ultimate_sprites()
        self._load_coin_icon()
        self._load_ui_images()
        self._load_ultimate_images()

    @staticmethod
    def _pick_font(preferred_names, size, bold=False):
        """Usa uma família instalada; evita fallback silencioso na primeira opção."""
        for name in preferred_names:
            path = pygame.font.match_font(name, bold=bold)
            if path:
                font = pygame.font.Font(path, size)
                font.set_bold(bold)
                return font
        return pygame.font.SysFont(None, size, bold=bold)

    def _init_fonts(self):
        """Serifa só nos títulos, legibilidade neutra em controles e informações."""
        headings = ["cinzel", "constantia", "georgia", "liberationserif", "dejavuserif"]
        body = ["segoeui", "trebuchetms", "liberationsans", "dejavusans"]
        self._fonts["default"] = self._pick_font(body, 20)
        self._fonts["big"] = self._pick_font(headings, 33, bold=True)
        self._fonts["title"] = self._pick_font(headings, 56, bold=True)
        self._fonts["menu"] = self._pick_font(headings, 23, bold=True)
        self._fonts["small"] = self._pick_font(body, 16)

    def get_font(self, name="default"):
        return self._fonts.get(name, self._fonts["default"])

    def get_status_icon(self, name):
        if name not in self._status_icons:
            path = os.path.join(os.path.dirname(BACKGROUND_PATH), 'status', name + '.png')
            try:
                self._status_icons[name] = pygame.image.load(path).convert_alpha()
            except (pygame.error, FileNotFoundError):
                self._status_icons[name] = None
        return self._status_icons[name]

    def get_projectile_image(self, name):
        if name not in self._projectile_images:
            path = os.path.join(os.path.dirname(BACKGROUND_PATH), 'projectiles', name + '.png')
            try:
                self._projectile_images[name] = pygame.image.load(path).convert_alpha()
            except (pygame.error, FileNotFoundError):
                self._projectile_images[name] = None
        return self._projectile_images[name]

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

    def _load_tutorial_background(self):
        """Carrega o cenário didático opcional, mantendo fallback ao cenário normal."""
        path = os.path.join(os.path.dirname(BACKGROUND_PATH), "background_tutorial.png")
        try:
            self._background_tutorial = pygame.transform.smoothscale(
                pygame.image.load(path).convert(), (WIDTH, HEIGHT)
            )
        except (pygame.error, FileNotFoundError):
            self._background_tutorial = self._background

    @property
    def background_tutorial(self):
        return self._background_tutorial if self._background_tutorial is not None else self._background

    def _load_territory_backgrounds(self):
        """Carrega fundos opcionais específicos de território."""
        mapping = {1: 'background_pedra_do_corte.png', 2: "background_mata_sombria.png", 3: 'background_ruinas_ancestrais.png',
                   5: 'background_fortaleza_caida.png', 6: 'background_pico_da_vigilia.png'}
        for level, filename in mapping.items():
            path = os.path.join(os.path.dirname(BACKGROUND_PATH), filename)
            try:
                image = pygame.image.load(path).convert()
                self._territory_backgrounds[level] = pygame.transform.smoothscale(image, (WIDTH, HEIGHT))
            except (pygame.error, FileNotFoundError):
                self._territory_backgrounds[level] = self._background

    def get_battle_background(self, level=None):
        if level in self._territory_backgrounds:
            return self._territory_backgrounds[level]
        return self._background

    def _load_coin_icon(self):
        """Carrega o icone de moeda (48x48). Fallback: circulo dourado procedural."""
        ICON_SIZE = 48
        try:
            raw = pygame.image.load(COIN_ICON_PATH).convert_alpha()
            self._coin_icon = pygame.transform.smoothscale(raw, (ICON_SIZE, ICON_SIZE))
        except (pygame.error, FileNotFoundError):
            # Fallback procedural: círculo dourado
            surf = pygame.Surface((ICON_SIZE, ICON_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 200, 50), (ICON_SIZE // 2, ICON_SIZE // 2), ICON_SIZE // 2)
            pygame.draw.circle(surf, (220, 160, 20), (ICON_SIZE // 2, ICON_SIZE // 2), ICON_SIZE // 2, 3)
            self._coin_icon = surf
            print(f"[AVISO] Ícone de moeda não encontrado: {COIN_ICON_PATH}")

    @property
    def coin_icon(self):
        return self._coin_icon

    def _load_ui_images(self):
        """Carrega elementos decorativos da interface."""
        mapping = {
            "battle_hud_frame": "battle_hud_frame_top.png",
            "battle_hud_frame_alt": "battle_hud_frame_bottom.png",
            "hud_hand_tray": "hud_hand_tray.png",
            "hud_portrait": "hud_portrait.png",
            "hud_health": "hud_health.png",
            "hud_cemetery": "hud_cemetery.png",
            "world_map": "world_map.png",
        }
        for key, filename in mapping.items():
            path = os.path.join(UI_ASSETS_DIR, filename)
            try:
                self._ui_images[key] = pygame.image.load(path).convert_alpha()
            except (pygame.error, FileNotFoundError):
                self._ui_images[key] = None

    def _load_ultimate_images(self):
        """Compõe cartas lendárias com regras sempre atualizadas."""
        from src.models.effects.ultimate_effect import ULTIMATE_METADATA
        from src.ui.ultimate_card_art import build_ultimate_card
        for key, meta in ULTIMATE_METADATA.items():
            path = os.path.join(ULTIMATE_ASSETS_DIR, key + '_art_v2.png')
            try:
                art = pygame.image.load(path).convert_alpha()
            except (pygame.error, FileNotFoundError):
                art = None
            self._ultimate_images[key] = build_ultimate_card(art, meta, self)

    def get_ui_image(self, key):
        return self._ui_images.get(key)

    def get_ultimate_image(self, ultimate_id):
        return self._ultimate_images.get(ultimate_id)


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
            for i in range(1, 5):
                path = os.path.join(CARD_EFFECTS_DIR, f"{prefix}_{i}.png")
                try:
                    img = pygame.image.load(path).convert_alpha()
                    frame = img.convert_alpha()
                    if frame is not None:
                        frames.append(frame)
                except (pygame.error, FileNotFoundError):
                    pass
            self._card_action_sprites[name] = frames
        from src.systems.ultimate_animations import ULTIMATE_ANIMATIONS
        for name, spec in ULTIMATE_ANIMATIONS.items():
            folder = os.path.join(os.path.dirname(ULTIMATE_ASSETS_DIR), 'ultimate_effects', spec.ultimate_id)
            for prefix, destination in (('cast', self._card_action_sprites), ('effect', self._ultimate_effect_sprites)):
                frames = []
                for i in range(1, 5):
                    path = os.path.join(folder, f'{prefix}_{i}.png')
                    try:
                        frames.append(pygame.image.load(path).convert_alpha())
                    except (pygame.error, FileNotFoundError):
                        pass
                destination[name] = frames

    def get_ultimate_effect_sprites(self, action_name):
        return self._ultimate_effect_sprites.get(action_name, [])

    def _load_boss_ultimate_sprites(self):
        from src.systems.boss_ultimate_animations import BOSS_ULTIMATE_ANIMATIONS, BOSS_ORIGINAL_CASTS
        for name, spec in BOSS_ULTIMATE_ANIMATIONS.items():
            folder = os.path.join(os.path.dirname(ULTIMATE_ASSETS_DIR), 'boss_ultimate_effects', spec.asset_id)
            casts = []
            for group, index in BOSS_ORIGINAL_CASTS[name]:
                originals = self.get_enemy_sprite_group(name, group)
                if originals:
                    source = originals[min(index, len(originals)-1)]
                    if name == 'goblin nerd':
                        # Os recortes antigos trazem pequenos fragmentos de
                        # células vizinhas; preserva a silhueta principal inteira.
                        parts = pygame.mask.from_surface(source, 12).connected_components()
                        if parts:
                            main = max(parts, key=lambda part: part.count())
                            source = source.copy()
                            source.blit(main.to_surface(setcolor=(255, 255, 255, 255),
                                                        unsetcolor=(0, 0, 0, 0)), (0, 0),
                                        special_flags=pygame.BLEND_RGBA_MULT)
                        # O disparo antigo foi desenhado em escala menor que
                        # o idle. Normaliza a altura com pixels originais, sem
                        # inventar outro rosto ou trocar a arma por um canhão.
                        if group == 'atk2':
                            idle = self.get_enemy_sprite_group(name, 'idle')[0]
                            ratio = idle.get_bounding_rect(min_alpha=50).height/source.get_bounding_rect(min_alpha=50).height
                            source = pygame.transform.scale(source, (round(source.get_width()*ratio), round(source.get_height()*ratio)))
                    frame = pygame.Surface((448, 320), pygame.SRCALPHA)
                    rect = source.get_rect(midbottom=(224, 318))
                    # As folhas antigas têm margens inferiores diferentes;
                    # alinha os pés, sem mudar a escala ou desenhar outro corpo.
                    rect.y += source.get_height()-source.get_bounding_rect(min_alpha=50).bottom
                    if name == 'goblin nerd':
                        floor = source.get_bounding_rect(min_alpha=50).bottom
                        feet = source.subsurface((0, floor-6, source.get_width(), 6)).get_bounding_rect(min_alpha=50)
                        rect.x += source.get_width()//2-feet.centerx
                    frame.blit(source, rect)
                    casts.append(frame)
            self._boss_ultimate_sprites[name] = casts
            effects = []
            for i in range(1, 5):
                try:
                    effects.append(pygame.image.load(os.path.join(folder, f'effect_{i}.png')).convert_alpha())
                except (pygame.error, FileNotFoundError):
                    pass
            self._boss_ultimate_effects[name] = effects

    def get_boss_ultimate_sprites(self, name, effects=False):
        return (self._boss_ultimate_effects if effects else self._boss_ultimate_sprites).get(name.lower(), [])

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

    @staticmethod
    def _prepare_uniform_enemy_frame(image, render_scale):
        """Escala quadros em canvas padronizado para evitar pulos visuais."""
        image = image.convert_alpha()
        source_width, source_height = image.get_size()
        if source_width == 0 or source_height == 0:
            return None
        render_width = max(1, round(source_width * render_scale))
        render_height = max(1, round(source_height * render_scale))
        return pygame.transform.smoothscale(image, (render_width, render_height))

    @staticmethod
    def _prepare_corpo_seco_frame(image, group):
        """Renderiza todos os frames do chefe com escala e pivô uniformes."""
        return AssetManager._prepare_uniform_enemy_frame(image, CORPO_SECO_RENDER_SCALE)

    @staticmethod
    def _prepare_goblin_nerd_frame(image, group):
        """Mantém o Goblin Nerd menor e estável, combinando com o cenário."""
        return AssetManager._prepare_uniform_enemy_frame(image, GOBLIN_NERD_RENDER_SCALE)

    def _load_enemy_sprites(self):
        """Carrega conjuntos de sprites para inimigos com suporte a idle, atk e def."""
        from src.config.settings import ASSETS_DIR

        slime_dir = os.path.join(ASSETS_DIR, "slime")
        if os.path.isdir(slime_dir):
            def load_frames(prefix, count):
                frames = []
                for i in range(1, count + 1):
                    path = os.path.join(slime_dir, f"{prefix}{i}.png")
                    if os.path.exists(path):
                        try:
                            img = pygame.image.load(path).convert_alpha()
                            frame = self.fit_character_sprite(img, target_height=110, max_width=150)
                            if frame is not None:
                                frames.append(frame)
                        except pygame.error:
                            pass
                return frames

            self._enemy_sprites["slime"] = {
                "idle": load_frames("idle", 3),
                "atk": load_frames("atk", 3),
                "def": load_frames("def", 3),
            }

        # Sprites do Corpo Seco, alinhados ao mesmo pivô e virados ao herói.
        boss_dir = os.path.join(ASSETS_DIR, "corpo_seco")
        if os.path.isdir(boss_dir):
            groups = {}
            for group in ("idle", "atk1", "atk3", "atk4", "dano", "healer2"):
                frames = []
                for idx in range(1, 5):
                    path = os.path.join(boss_dir, f"{group}_{idx}.png")
                    if os.path.isfile(path):
                        try:
                            img = pygame.image.load(path).convert_alpha()
                            frame = self._prepare_corpo_seco_frame(img, group)
                            if frame is not None:
                                frames.append(frame)
                        except pygame.error:
                            pass
                groups[group] = frames
            groups["atk"] = groups["atk1"]
            groups["def"] = groups["healer2"]
            self._enemy_sprites["corpo seco"] = groups

        goblin_dir = os.path.join(ASSETS_DIR, "goblin_nerd")
        if os.path.isdir(goblin_dir):
            groups = {}
            for group in ("idle", "atk1", "atk2", "atk3", "dano", "healer2"):
                frames = []
                for idx in range(1, 5):
                    path = os.path.join(goblin_dir, f"{group}_{idx}.png")
                    if os.path.isfile(path):
                        try:
                            img = pygame.image.load(path).convert_alpha()
                            frame = self._prepare_goblin_nerd_frame(img, group)
                            if frame is not None:
                                frames.append(frame)
                        except pygame.error:
                            pass
                groups[group] = frames
            groups["atk"] = groups["atk1"]
            groups["def"] = groups["healer2"]
            groups["atk4"] = groups["atk2"]
            self._enemy_sprites["goblin nerd"] = groups

        monge_dir = os.path.join(ASSETS_DIR, "goblin_monge")
        if os.path.isdir(monge_dir):
            groups = {}
            for group in ("idle", "dano", "atk1", "atk2"):
                frames = []
                for idx in range(1, 5):
                    path = os.path.join(monge_dir, f"{group}_{idx}.png")
                    if os.path.isfile(path):
                        frames.append(remove_white_fringe(pygame.image.load(path).convert_alpha()))
                groups[group] = frames
            groups["atk"] = groups["atk1"]
            self._enemy_sprites["vinimuth"] = groups
            path = os.path.join(monge_dir, "onda.png")
            if os.path.isfile(path):
                self._enemy_projectiles[("vinimuth", "atk2")] = remove_white_fringe(pygame.image.load(path).convert_alpha())

        guardian_dir = os.path.join(ASSETS_DIR, 'guardiao_da_pedra')
        if os.path.isdir(guardian_dir):
            groups = {}
            for group in ('idle', 'atk1', 'atk2', 'def', 'healer2', 'dano'):
                frames = []
                for idx in range(1, 5):
                    path = os.path.join(guardian_dir, f'{group}_{idx}.png')
                    if os.path.isfile(path):
                        frames.append(remove_white_fringe(pygame.image.load(path).convert_alpha()))
                groups[group] = frames
            groups['atk'] = groups['atk1']
            self._enemy_sprites['guardião da pedra'] = groups
            path = os.path.join(guardian_dir, 'urso_espiritual.png')
            if os.path.isfile(path):
                self._enemy_projectiles[('guardião da pedra', 'atk2')] = remove_white_fringe(pygame.image.load(path).convert_alpha())

        carrasco_dir = os.path.join(ASSETS_DIR, 'carrasco_da_vigilia')
        if os.path.isdir(carrasco_dir):
            groups = {}
            for group in ('idle', 'atk1', 'atk2', 'atk3', 'healer2', 'dano'):
                frames = []
                for idx in range(1, 5):
                    path = os.path.join(carrasco_dir, f'{group}_{idx}.png')
                    if os.path.isfile(path):
                        frame = pygame.image.load(path).convert_alpha()
                        if group == 'healer2':
                            frame = recolor_green_aura_red(frame)
                        frames.append(frame)
                groups[group] = frames
            groups['atk'] = groups['atk1']
            self._enemy_sprites['carrasco da vigília'] = groups

        for name, (slug, action_groups, _, _) in NORMAL_SPRITES.items():
            folder = os.path.join(ASSETS_DIR, 'enemies', slug)
            groups = {}
            for group in action_groups:
                groups[group] = [pygame.image.load(os.path.join(folder, f'{group}_{i}.png')).convert_alpha()
                                 for i in range(1, 5)]
            groups['atk'] = groups['atk1']
            self._enemy_sprites[name.lower()] = groups
            for action in NORMAL_RANGED.get(name.lower(), {}):
                path = os.path.join(folder, f'projectile_{action}.png')
                self._enemy_projectiles[(name.lower(), action)] = pygame.image.load(path).convert_alpha()

    def get_enemy_projectile(self, enemy_name, action):
        return self._enemy_projectiles.get((enemy_name.strip().lower(), action))

    def has_enemy_sprites(self, enemy_name):
        """Verifica se existem sprites customizados carregados para o inimigo."""
        if not enemy_name:
            return False
        key = enemy_name.strip().lower()
        groups = self._enemy_sprites.get(key, {})
        return any(bool(frames) for frames in groups.values())

    def get_enemy_sprite_group(self, enemy_name, group_name="idle"):
        """Retorna a lista de frames para a ação solicitada do inimigo."""
        if not enemy_name:
            return []
        key = enemy_name.strip().lower()
        groups = self._enemy_sprites.get(key, {})
        return groups.get(group_name, [])

    def get_enemy_sprite(self, enemy_name, group_name="idle", index=0):
        """Retorna um frame específico para o inimigo."""
        frames = self.get_enemy_sprite_group(enemy_name, group_name)
        if not frames:
            return None
        return frames[index % len(frames)]
