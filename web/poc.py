"""Prova limitada: menu e combate real contra Slime, sem persistência."""
import asyncio
import json
import os
import sys
import time
import pygame

from src.core.application import Application
from src.core.asset_manager import AssetManager
from src.core.audio_manager import AudioManager
from src.core.scene_manager import SceneManager
from src.core.window import create_window_manager
from src.platforms import get_platform
from src.config.settings import ASSETS_DIR
from src.config.music import MUSIC_VOLUME
from src.systems.game_preferences import GamePreferences
from src.scenes.menu_scene import MenuScene
from src.scenes.battle_scene import BattleScene
from src.systems.enemy_factory import _build_slime_actions, choose_next_action
from src.models.enemy import Enemy


class SessionPreferences(GamePreferences):
    def load(self):
        return dict(self.values)

    def save(self, *args, **kwargs):
        # Etapa 1 não acessa disco, localStorage, IndexedDB ou slots v15.
        return None


def ProofWindow():
    return create_window_manager()


class ProofFont:
    """Cache limitado de rasterização; cópias impedem vazamento de alpha entre textos."""
    def __init__(self, font):
        self.font = font
        self.cache = {}

    def __getattr__(self, name):
        return getattr(self.font, name)

    def render(self, text, antialias, color, bgcolor=None, **kwargs):
        key = (str(text), antialias, tuple(color), tuple(bgcolor) if bgcolor else None,
               tuple(sorted(kwargs.items())))
        if key not in self.cache:
            if len(self.cache) >= 128:
                self.cache.clear()
            self.cache[key] = self.font.render(text, antialias, color, bgcolor, **kwargs)
        return self.cache[key].copy()


class ProofAssets(AssetManager):
    def __init__(self):
        super().__init__(preload=False)
        self._fonts = {name: ProofFont(font) for name,font in self._fonts.items()}
        self.combat_ready = False

    def prepare_combat(self):
        # Cada lote devolve controle antes de carregar o próximo conjunto.
        for group in ("idle", "dano", "soco", "vitoria"):
            folder, count = ("eight_frames", 8) if group in ("idle", "dano") else ("twelve_frames", 12)
            self._player_sprites[group] = self.frames("player/" + folder, group, count)
            yield group
        for name in ("Soco Simples", "Esfera Protetora", "Mana Ancestral"):
            from src.systems.ultimate_animations import ULTIMATE_ANIMATIONS
            prefix = self.CARD_ACTION_FILES.get(name)
            if prefix is None:
                prefix = ULTIMATE_ANIMATIONS[name].ultimate_id
            self._card_action_sprites[name] = self.frames("player/twelve_frames", prefix, 12)
            if name == "Mana Ancestral":
                self._ultimate_effect_sprites[name] = self.frames("player/twelve_frames", prefix + "_effect", 12)
            yield name
        self._enemy_sprites["slime"] = {}
        for group in ("idle", "dano", "atk", "def"):
            self._enemy_sprites["slime"][group] = self.frames("enemies/eight_frames/slime", group, 8)
            yield group
        self._enemy_projectiles[("slime", "atk")] = self.image("enemies/eight_frames/slime/projectile_atk.png")
        self._load_coin_icon()
        self._load_ui_images()
        self._load_ultimate_images()
        yield "HUD"
        # Regra de composição e custo dinâmico permanecem no AssetManager.
        for name in ("Soco Simples", "Esfera Protetora"):
            from src.systems.card_catalog import CARD_BY_NAME
            self.get_card_image(name)
        self.combat_ready = True

    @staticmethod
    def image(relative):
        return pygame.image.load(os.path.join(ASSETS_DIR, relative)).convert_alpha()

    def frames(self, folder, prefix, count):
        return [self.image(folder + "/" + prefix + "_" + str(i) + ".png") for i in range(1, count + 1)]


class ProofBattle(BattleScene):
    def __init__(self, scenes, window, assets):
        super().__init__(scenes, window, assets)
        self.engine.enemy = Enemy(name="Slime", hp=23, energy=2, max_energy=2,
                                  actions=_build_slime_actions(1), is_miniboss=False)
        choose_next_action(self.engine.enemy)
        self.engine.start_combat()
        self.boss_dialogue = None
        self._static_background = None
        self.draw_times = {}
        def instrument(owner, name, label):
            original = getattr(owner, name)
            def measured(*args, **kwargs):
                before = time.perf_counter()
                result = original(*args, **kwargs)
                self.draw_times[label] = (time.perf_counter()-before)*1000
                return result
            setattr(owner, name, measured)
        for name in dir(self):
            if name.startswith("_draw_") and callable(getattr(self, name)):
                instrument(self, name, name)
        for name in ("draw_enemy", "draw_player", "draw_enemy_projectile"):
            instrument(self.entity_view, name, name)
        instrument(self.intent_view, "draw", "intent")

    def _draw_background(self, surface):
        if self._static_background is None:
            self._static_background = pygame.Surface(surface.get_size()).convert()
            super()._draw_background(self._static_background)
        surface.blit(self._static_background, (0,0))

    def _draw_bottom_hud(self, surface):
        view = self.entity_view
        if view.player_action in ("Mana Ancestral", "Forças Ancestrais", "Rugido da Floresta"):
            return super()._draw_bottom_hud(surface)
        rect = pygame.Rect(12, 756, 1896, 324)
        if not hasattr(self, "_opaque_tray"):
            self._opaque_tray = self._static_background.subsurface(rect).copy()
            self.battle_hud.art(self._opaque_tray, "hud_hand_tray", self._opaque_tray.get_rect())
        surface.blit(self._opaque_tray, rect)

    def handle_event(self, event):
        # A prova não navega para campanha, preferências persistentes ou saves.
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.scene_manager.change_scene(ProofMenu(self.scene_manager, self.window_manager, self.asset_manager))
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.menu_button_rect.collidepoint(self.window_manager.map_to_virtual(event.pos)):
                self.scene_manager.change_scene(ProofMenu(self.scene_manager, self.window_manager, self.asset_manager))
                return
        if self.engine.state in ("victory", "game_over"):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.scene_manager.change_scene(ProofBattle(self.scene_manager, self.window_manager, self.asset_manager))
            return
        super().handle_event(event)


class ProofMenu(MenuScene):
    def __init__(self, *args):
        super().__init__(*args)
        self.loading = None
        self._menu_cache = {}

    def _open_options(self):
        # Navegação fora desta prova será liberada nas etapas seguintes.
        return

    def _start_game(self):
        if self.asset_manager.combat_ready:
            self.scene_manager.change_scene(ProofBattle(self.scene_manager, self.window_manager, self.asset_manager))
        elif self.loading is None:
            self.loading = self.asset_manager.prepare_combat()

    def update(self, dt):
        if self.loading is not None:
            try:
                next(self.loading)
            except StopIteration:
                self.loading = None
                self._start_game()

    def draw(self, surface):
        mouse = self.window_manager.get_virtual_mouse_pos()
        hover = next((i for i,rect in enumerate((self.play_button,self.options_button,self.quit_button))
                      if rect.collidepoint(mouse)), -1)
        if hover not in self._menu_cache:
            cached = pygame.Surface(surface.get_size()).convert()
            super().draw(cached)
            self._menu_cache[hover] = cached
        surface.blit(self._menu_cache[hover], (0,0))
        text = "CARREGANDO COMBATE..." if self.loading else "PROVA WEB · SLIME · SEM SAVES · ESC VOLTA · R REPETE"
        image = self.asset_manager.small_font.render(text, True, (240, 210, 140))
        surface.blit(image, image.get_rect(center=(960, 1030)))

    def handle_event(self, event):
        # Sair na web volta ao menu; não encerra o interpretador WASM.
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.scene_manager.request_exit()
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.quit_button.collidepoint(self.window_manager.map_to_virtual(event.pos)):
                self.scene_manager.request_exit()
                return
        super().handle_event(event)


async def main():
    # pygame.init inicializaria o mixer antes da interação.
    pygame.display.init()
    pygame.font.init()
    if sys.platform == "emscripten":
        import platform
        platform.window.config.user_canvas_managed = 1
    service = get_platform()
    window = create_window_manager(platform_service=service)
    assets = ProofAssets()
    preferences = SessionPreferences()
    audio = AudioManager(music_volume=MUSIC_VOLUME, defer_initialization=True)
    from desktop_entry import configure_audio
    configure_audio(audio)
    preferences.apply(audio)
    scenes = SceneManager(audio_manager=audio, audio_preferences=preferences, platform_service=service)
    scenes.home_factory = lambda: ProofMenu(scenes, window, assets)
    scenes.change_scene(ProofMenu(scenes, window, assets))
    app = Application(window, assets, audio, preferences, scenes)
    started = time.perf_counter()
    batch_time, batch_frames = started, 0

    def observe(application):
        nonlocal batch_time, batch_frames
        if application.frames % 5 and application._active:
            return
        now = time.perf_counter()
        scene = scenes.current_scene
        engine = getattr(scene, "engine", None)
        report = {
            "platform": service.capabilities.is_web,
            "active": application._active,
            "resume_serial": application._resume_serial,
            "scene": type(scene).__name__, "frames": application.frames,
            "fps": (application.frames - batch_frames) / max(.001, now - batch_time),
            "ready_seconds": now - started, "audio_unlocked": audio.available,
            "audio_suspended": getattr(audio, "_suspended", False),
            "music_playing": bool(audio.available and pygame.mixer.music.get_busy()),
            "draw_parts_ms": getattr(scene, "draw_times", {}),
            "frame_cost_ms": getattr(application, "frame_cost_ms", {}),
            "pygame": pygame.version.ver, "python": sys.version.split()[0],
            "surfaces_bytes": sum(s.get_width()*s.get_height()*s.get_bytesize()
                for groups in (assets._player_sprites, assets._enemy_sprites.get("slime", {}), assets._card_action_sprites)
                for frames in groups.values() for s in frames),
        }
        if engine:
            report.update(state=engine.state, player_hp=engine.player.hp, enemy_hp=engine.enemy.hp,
                          energy=engine.energy, action=scene.entity_view.player_action,
                          intents=[list(rect) for rect,intent in scene.intent_view.entries],
                          hand=[{"name":c.name, "cost":c.cost, "rect":list(rect)} for c,rect in
                                zip(engine.hand,scene._get_battle_hand_rects())])
        if sys.platform == "emscripten":
            import platform
            platform.window.webPocMetrics = json.dumps(report)
        batch_time, batch_frames = now, application.frames

    try:
        await app.run_web(observe)
    finally:
        audio.shutdown()
        pygame.quit()

