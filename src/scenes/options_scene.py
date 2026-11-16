"""Menu de Opções com abas de áudio, vídeo, jogo e controles."""

import pygame

from src.config.colors import GOLD, GRAY, WHITE
from src.config.options_layout import (
    AUDIO_LABEL_X,
    AUDIO_MINUS_LEFT,
    AUDIO_PERCENT_X,
    AUDIO_PLUS_LEFT,
    AUDIO_SLIDER_HEIGHT,
    AUDIO_SLIDER_LEFT,
    AUDIO_SLIDER_TOP,
    AUDIO_SLIDER_WIDTH,
    AUDIO_STEP_BUTTON_SIZE,
    AUDIO_STEP_BUTTON_TOP,
    CONTROLS_DESCRIPTION_X,
    CONTROLS_LABEL_X,
    CONTROLS_LINE_HEIGHT,
    CONTROLS_TOP,
    OPTIONS_BACK_BUTTON,
    OPTIONS_CONTENT_TOP,
    OPTIONS_DEFAULTS_BUTTON,
    OPTIONS_DIVIDER_Y,
    OPTIONS_FOOTER,
    OPTIONS_MESSAGE_Y,
    OPTIONS_PANEL,
    OPTIONS_ROW_CONTROL_OFFSET,
    OPTIONS_ROW_DESCRIPTION_OFFSET,
    OPTIONS_ROW_HEIGHT,
    OPTIONS_SUBTITLE_Y,
    OPTIONS_TABS_GAP,
    OPTIONS_TABS_HEIGHT,
    OPTIONS_TABS_LEFT,
    OPTIONS_TABS_RIGHT,
    OPTIONS_TABS_Y,
    OPTIONS_TITLE_Y,
    SETTING_CONTROL_HEIGHT,
    SETTING_CONTROL_LEFT,
    SETTING_CONTROL_WIDTH,
    SETTING_LABEL_X,
    SETTING_WIDE_ROW_HEIGHT,
)
from src.config.preferences import (
    ENEMY_SPEED_OPTIONS,
    OPTIONS_TABS,
    TAB_AUDIO,
    TAB_CONTROLS,
    TAB_GAME,
    TAB_VIDEO,
    VOLUME_MAX,
    VOLUME_MIN,
    VOLUME_STEP,
    WINDOW_SIZE_LARGE,
    WINDOW_SIZE_LEGACY,
    WINDOW_SIZE_OPTIONS,
)
from src.scenes.base_scene import BaseScene
from src.systems.game_preferences import GamePreferences
from src.ui import dark_fantasy_theme as theme
from src.ui.helpers import draw_text

AUDIO_ROWS = (
    ("master_volume", "VOLUME GERAL", "Todos os sons do jogo"),
    ("music_volume", "MÚSICA", "Trilha sonora dos menus e batalhas"),
    ("combat_volume", "COMBATE", "Armas, movimentos e poderes"),
    ("damage_volume", "IMPACTOS DE DANO", "Acertos, colisões e sangramento"),
)

CONTROL_ROWS = (
    ("MOUSE ESQUERDO", "Seleciona cartas, habilidades e botões."),
    ("ESC", "Volta/cancela; na batalha abre a pausa."),
    ("ESC NO MENU", "Encerra o jogo a partir da tela inicial."),
    ("MENU", "Abre a pausa na batalha e no tutorial."),
    ("C", "Abre o Cemitério no seu turno."),
    ("O", "Abre as Opções no menu principal."),
    ("F11", "Alterna entre tela cheia e janela."),
    ("F10", "Alterna o tamanho da janela."),
)

INITIAL_MESSAGE = "As alterações são aplicadas na hora e salvas neste computador."


class OptionsScene(BaseScene):
    """Preferências globais com aplicação imediata e persistência local."""

    def __init__(self, scene_manager, window_manager, asset_manager, return_scene=None, modal=False):
        super().__init__(scene_manager, window_manager, asset_manager)
        self.audio = scene_manager.audio_manager
        self.preferences = getattr(scene_manager, "audio_preferences", None)
        if self.preferences is None:
            self.preferences = GamePreferences()
        self.return_scene = return_scene
        self.modal = modal
        self.tab = TAB_AUDIO
        self.selected = 0
        self.dragging = None
        self.message = INITIAL_MESSAGE
        self.panel_rect = pygame.Rect(OPTIONS_PANEL)
        self.back_button = pygame.Rect(OPTIONS_BACK_BUTTON)
        self.defaults_button = pygame.Rect(OPTIONS_DEFAULTS_BUTTON)

        self.tab_rects = {}
        tabs_width = OPTIONS_TABS_RIGHT - OPTIONS_TABS_LEFT
        tab_width = (tabs_width - OPTIONS_TABS_GAP * (len(OPTIONS_TABS) - 1)) // len(
            OPTIONS_TABS
        )
        for index, (tab_id, _label) in enumerate(OPTIONS_TABS):
            self.tab_rects[tab_id] = pygame.Rect(
                OPTIONS_TABS_LEFT + index * (tab_width + OPTIONS_TABS_GAP),
                OPTIONS_TABS_Y,
                tab_width,
                OPTIONS_TABS_HEIGHT,
            )

        self.sliders = {}
        self.minus = {}
        self.plus = {}
        for index, (key, _label, _description) in enumerate(AUDIO_ROWS):
            row_top = OPTIONS_CONTENT_TOP + index * OPTIONS_ROW_HEIGHT
            self.sliders[key] = pygame.Rect(
                AUDIO_SLIDER_LEFT,
                row_top + AUDIO_SLIDER_TOP,
                AUDIO_SLIDER_WIDTH,
                AUDIO_SLIDER_HEIGHT,
            )
            self.minus[key] = pygame.Rect(
                AUDIO_MINUS_LEFT,
                row_top + AUDIO_STEP_BUTTON_TOP,
                *AUDIO_STEP_BUTTON_SIZE,
            )
            self.plus[key] = pygame.Rect(
                AUDIO_PLUS_LEFT,
                row_top + AUDIO_STEP_BUTTON_TOP,
                *AUDIO_STEP_BUTTON_SIZE,
            )

        control_half = (SETTING_CONTROL_WIDTH - 10) // 2
        self.window_size_buttons = {}
        for index, (size_id, _label) in enumerate(WINDOW_SIZE_OPTIONS):
            self.window_size_buttons[size_id] = pygame.Rect(
                SETTING_CONTROL_LEFT + index * (control_half + 10),
                OPTIONS_CONTENT_TOP
                + SETTING_WIDE_ROW_HEIGHT
                + OPTIONS_ROW_CONTROL_OFFSET,
                control_half,
                SETTING_CONTROL_HEIGHT,
            )
        self.enemy_speed_buttons = {}
        for index, (speed_id, _label) in enumerate(ENEMY_SPEED_OPTIONS):
            self.enemy_speed_buttons[speed_id] = pygame.Rect(
                SETTING_CONTROL_LEFT + index * (control_half + 10),
                OPTIONS_CONTENT_TOP + OPTIONS_ROW_CONTROL_OFFSET,
                control_half,
                SETTING_CONTROL_HEIGHT,
            )
        self.fullscreen_button = pygame.Rect(
            SETTING_CONTROL_LEFT,
            OPTIONS_CONTENT_TOP + OPTIONS_ROW_CONTROL_OFFSET,
            SETTING_CONTROL_WIDTH,
            SETTING_CONTROL_HEIGHT,
        )
        self.fps_button = pygame.Rect(
            SETTING_CONTROL_LEFT,
            OPTIONS_CONTENT_TOP
            + 2 * SETTING_WIDE_ROW_HEIGHT
            + OPTIONS_ROW_CONTROL_OFFSET,
            SETTING_CONTROL_WIDTH,
            SETTING_CONTROL_HEIGHT,
        )
        self.damage_numbers_button = pygame.Rect(
            SETTING_CONTROL_LEFT,
            OPTIONS_CONTENT_TOP
            + SETTING_WIDE_ROW_HEIGHT
            + OPTIONS_ROW_CONTROL_OFFSET,
            SETTING_CONTROL_WIDTH,
            SETTING_CONTROL_HEIGHT,
        )

    # ------------------------------------------------------------------
    # Persistência e aplicação imediata
    # ------------------------------------------------------------------
    def _persist(self, message="Alterações salvas."):
        try:
            self.preferences.save(self.audio)
            self.message = message
        except OSError:
            self.message = "Não foi possível salvar. Os ajustes valem nesta sessão."

    def _set_audio(self, key, value):
        value = max(VOLUME_MIN, min(VOLUME_MAX, value))
        getattr(self.audio, "set_" + key)(value)
        self.preferences.set(key, value)

    def _slide(self, key, x):
        rect = self.sliders[key]
        self._set_audio(key, (x - rect.left) / rect.width)

    def _restore_defaults(self):
        if self.tab == TAB_CONTROLS:
            self.message = "A aba CONTROLES é apenas informativa."
            self.play_ui_sound("ui.click")
            return
        self.preferences.restore_tab(self.tab)
        if self.tab == TAB_AUDIO:
            self.preferences.apply_audio(self.audio)
            self.message = "Padrões de áudio restaurados."
        elif self.tab == TAB_VIDEO:
            self.preferences.apply_video(self.window_manager)
            self.message = "Padrões de vídeo restaurados."
        else:
            self.message = "Padrões de jogo restaurados."
        self._persist(self.message)
        self.play_ui_sound("ui.confirm")

    # ------------------------------------------------------------------
    # Navegação e ações
    # ------------------------------------------------------------------
    def _switch_tab(self, tab):
        if tab not in self.tab_rects:
            return
        self.tab = tab
        self.selected = 0
        self.dragging = None
        self.message = INITIAL_MESSAGE
        self.play_ui_sound("ui.click")

    def _back(self):
        self._persist()
        self.play_ui_sound("ui.click")
        if self.modal:
            self.scene_manager.pop_modal()
            return
        if self.return_scene is None:
            from src.scenes.menu_scene import MenuScene

            self.return_scene = MenuScene(
                self.scene_manager, self.window_manager, self.asset_manager
            )
        self.scene_manager.change_scene(self.return_scene)

    def _toggle_fullscreen(self):
        self.window_manager.set_fullscreen(not self.window_manager.is_fullscreen)
        self.preferences.set("fullscreen", self.window_manager.is_fullscreen)
        self.preferences.set(
            "window_size",
            WINDOW_SIZE_LARGE
            if self.window_manager.is_large_window
            else WINDOW_SIZE_LEGACY,
        )
        self._persist("Modo de vídeo atualizado.")

    def _select_window_size(self, size_id):
        self.window_manager.set_window_size(size_id == WINDOW_SIZE_LARGE)
        self.preferences.set("fullscreen", False)
        self.preferences.set("window_size", size_id)
        self._persist("Tamanho da janela atualizado.")

    def _toggle_fps(self):
        self.preferences.set("show_fps", not self.preferences.get("show_fps"))
        self._persist("Contador de FPS atualizado.")

    def _select_enemy_speed(self, speed_id):
        self.preferences.set("enemy_speed", speed_id)
        self._persist("Velocidade do inimigo atualizada.")

    def _toggle_damage_numbers(self):
        self.preferences.set(
            "damage_numbers", not self.preferences.get("damage_numbers")
        )
        self._persist("Números de dano atualizados.")

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------
    def update(self, dt):
        pass

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            point = self.window_manager.map_to_virtual(event.pos)
            for tab_id, rect in self.tab_rects.items():
                if rect.collidepoint(point):
                    self._switch_tab(tab_id)
                    return
            if self.back_button.collidepoint(point):
                self._back()
                return
            if self.defaults_button.collidepoint(point):
                self._restore_defaults()
                return
            if self.tab == TAB_AUDIO:
                self._handle_audio_click(point)
            elif self.tab == TAB_VIDEO:
                self._handle_video_click(point)
            elif self.tab == TAB_GAME:
                self._handle_game_click(point)
        elif event.type == pygame.MOUSEMOTION and self.dragging is not None:
            self._slide(
                self.dragging, self.window_manager.map_to_virtual(event.pos)[0]
            )
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging is not None:
                self._persist("Volumes salvos.")
            self.dragging = None
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._back()
            elif self.tab == TAB_AUDIO:
                self._handle_audio_key(event)

    def _handle_audio_click(self, point):
        for index, (key, _label, _description) in enumerate(AUDIO_ROWS):
            if self.sliders[key].inflate(28, 44).collidepoint(point):
                self.selected = index
                self.dragging = key
                self._slide(key, point[0])
                return
            for rect, step in (
                (self.minus[key], -VOLUME_STEP),
                (self.plus[key], VOLUME_STEP),
            ):
                if rect.collidepoint(point):
                    self.selected = index
                    self._set_audio(key, getattr(self.audio, key) + step)
                    self._persist("Volumes salvos.")
                    self.play_ui_sound("ui.click")
                    return

    def _handle_video_click(self, point):
        if self.fullscreen_button.collidepoint(point):
            self._toggle_fullscreen()
            self.play_ui_sound("ui.click")
            return
        for size_id, rect in self.window_size_buttons.items():
            if rect.collidepoint(point):
                self._select_window_size(size_id)
                self.play_ui_sound("ui.click")
                return
        if self.fps_button.collidepoint(point):
            self._toggle_fps()
            self.play_ui_sound("ui.click")

    def _handle_game_click(self, point):
        for speed_id, rect in self.enemy_speed_buttons.items():
            if rect.collidepoint(point):
                self._select_enemy_speed(speed_id)
                self.play_ui_sound("ui.click")
                return
        if self.damage_numbers_button.collidepoint(point):
            self._toggle_damage_numbers()
            self.play_ui_sound("ui.click")

    def _handle_audio_key(self, event):
        if event.key in (pygame.K_DOWN, pygame.K_TAB):
            self.selected = (self.selected + 1) % len(AUDIO_ROWS)
        elif event.key == pygame.K_UP:
            self.selected = (self.selected - 1) % len(AUDIO_ROWS)
        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            key = AUDIO_ROWS[self.selected][0]
            step = VOLUME_STEP if event.key == pygame.K_RIGHT else -VOLUME_STEP
            self._set_audio(key, getattr(self.audio, key) + step)
            self._persist("Volumes salvos.")

    # ------------------------------------------------------------------
    # Desenho
    # ------------------------------------------------------------------
    def draw(self, surface):
        assets = self.asset_manager
        theme.backdrop(surface, assets.background, opacity=208)
        theme.panel(surface, self.panel_rect)
        draw_text(surface, "OPÇÕES", assets.big_font, GOLD, 960, OPTIONS_TITLE_Y, center=True)
        draw_text(
            surface,
            "Áudio, vídeo e ritmo da jornada em um só lugar.",
            assets.small_font,
            GRAY,
            960,
            OPTIONS_SUBTITLE_Y,
            center=True,
        )
        mouse = self.window_manager.get_virtual_mouse_pos()
        for tab_id, label in OPTIONS_TABS:
            rect = self.tab_rects[tab_id]
            theme.button(
                surface,
                rect,
                label,
                assets.small_font,
                hover=rect.collidepoint(mouse),
                prominent=tab_id == self.tab,
            )
        theme.divider(surface, 500, 1420, OPTIONS_DIVIDER_Y)

        if self.tab == TAB_AUDIO:
            self._draw_audio(surface, mouse)
        elif self.tab == TAB_VIDEO:
            self._draw_video(surface, mouse)
        elif self.tab == TAB_GAME:
            self._draw_game(surface, mouse)
        else:
            self._draw_controls(surface)

        theme.button(
            surface,
            self.back_button,
            "VOLTAR",
            assets.font,
            hover=self.back_button.collidepoint(mouse),
        )
        theme.button(
            surface,
            self.defaults_button,
            "RESTAURAR PADRÃO",
            assets.font,
            hover=self.defaults_button.collidepoint(mouse),
        )
        draw_text(
            surface,
            self.message,
            assets.small_font,
            GRAY,
            960,
            OPTIONS_MESSAGE_Y,
            center=True,
        )
        theme.footer(surface, OPTIONS_FOOTER, assets.small_font)

    def _draw_audio(self, surface, mouse):
        assets = self.asset_manager
        for index, (key, label, description) in enumerate(AUDIO_ROWS):
            row_top = OPTIONS_CONTENT_TOP + index * OPTIONS_ROW_HEIGHT
            rect = self.sliders[key]
            value = getattr(self.audio, key)
            draw_text(surface, label, assets.font, WHITE, AUDIO_LABEL_X, row_top)
            draw_text(
                surface,
                description,
                assets.small_font,
                GRAY,
                AUDIO_LABEL_X,
                row_top + OPTIONS_ROW_DESCRIPTION_OFFSET,
            )
            pygame.draw.rect(surface, (37, 48, 45), rect, border_radius=7)
            fill = rect.copy()
            fill.width = round(rect.width * value)
            if fill.width:
                pygame.draw.rect(surface, (145, 122, 70), fill, border_radius=7)
            knob = (round(rect.left + rect.width * value), rect.centery)
            pygame.draw.circle(surface, (15, 24, 22), knob, 16)
            pygame.draw.circle(
                surface,
                GOLD if index == self.selected else (160, 143, 98),
                knob,
                13,
                3,
            )
            for button, text in ((self.minus[key], "-"), (self.plus[key], "+")):
                theme.button(
                    surface,
                    button,
                    text,
                    assets.small_font,
                    hover=button.collidepoint(mouse),
                )
            draw_text(
                surface,
                f"{round(value * 100)}%",
                assets.font,
                GOLD,
                AUDIO_PERCENT_X,
                rect.centery,
                center=True,
            )

    def _draw_setting_row(self, surface, row_top, label, description):
        assets = self.asset_manager
        draw_text(surface, label, assets.font, WHITE, SETTING_LABEL_X, row_top)
        draw_text(
            surface,
            description,
            assets.small_font,
            GRAY,
            SETTING_LABEL_X,
            row_top + OPTIONS_ROW_DESCRIPTION_OFFSET,
        )

    def _draw_video(self, surface, mouse):
        assets = self.asset_manager
        row = OPTIONS_CONTENT_TOP
        self._draw_setting_row(
            surface, row, "TELA CHEIA", "Alterna janela e tela cheia (F11)."
        )
        fullscreen = bool(getattr(self.window_manager, "is_fullscreen", False))
        theme.button(
            surface,
            self.fullscreen_button,
            "ATIVADA" if fullscreen else "DESATIVADA",
            assets.font,
            hover=self.fullscreen_button.collidepoint(mouse),
            prominent=fullscreen,
        )

        row += SETTING_WIDE_ROW_HEIGHT
        self._draw_setting_row(
            surface,
            row,
            "TAMANHO DA JANELA",
            "Reaproveita o ajuste de tamanho do F10.",
        )
        current_size = (
            WINDOW_SIZE_LARGE
            if getattr(self.window_manager, "is_large_window", False)
            else WINDOW_SIZE_LEGACY
        )
        for size_id, label in WINDOW_SIZE_OPTIONS:
            button = self.window_size_buttons[size_id]
            theme.button(
                surface,
                button,
                label,
                assets.small_font,
                hover=button.collidepoint(mouse),
                prominent=size_id == current_size and not fullscreen,
            )

        row += SETTING_WIDE_ROW_HEIGHT
        self._draw_setting_row(
            surface,
            row,
            "MOSTRAR FPS",
            "Exibe o contador de FPS no topo.",
        )
        show_fps = bool(self.preferences.get("show_fps"))
        theme.button(
            surface,
            self.fps_button,
            "ATIVADO" if show_fps else "DESATIVADO",
            assets.font,
            hover=self.fps_button.collidepoint(mouse),
            prominent=show_fps,
        )

    def _draw_game(self, surface, mouse):
        assets = self.asset_manager
        row = OPTIONS_CONTENT_TOP
        self._draw_setting_row(
            surface,
            row,
            "VELOCIDADE DO INIMIGO",
            "Encurta as pausas antes das ações inimigas.",
        )
        current_speed = self.preferences.get("enemy_speed")
        for speed_id, label in ENEMY_SPEED_OPTIONS:
            button = self.enemy_speed_buttons[speed_id]
            theme.button(
                surface,
                button,
                label,
                assets.small_font,
                hover=button.collidepoint(mouse),
                prominent=speed_id == current_speed,
            )

        row += SETTING_WIDE_ROW_HEIGHT
        self._draw_setting_row(
            surface,
            row,
            "NÚMEROS DE DANO",
            "Mostra números de dano no combate.",
        )
        damage_numbers = bool(self.preferences.get("damage_numbers"))
        theme.button(
            surface,
            self.damage_numbers_button,
            "ATIVADOS" if damage_numbers else "DESATIVADOS",
            assets.font,
            hover=self.damage_numbers_button.collidepoint(mouse),
            prominent=damage_numbers,
        )

    def _draw_controls(self, surface):
        assets = self.asset_manager
        for index, (label, description) in enumerate(CONTROL_ROWS):
            y = CONTROLS_TOP + index * CONTROLS_LINE_HEIGHT
            draw_text(surface, label, assets.font, GOLD, CONTROLS_LABEL_X, y)
            draw_text(
                surface,
                description,
                assets.small_font,
                WHITE,
                CONTROLS_DESCRIPTION_X,
                y + 6,
            )


# Nome anterior preservado para imports existentes.
AudioOptionsScene = OptionsScene
