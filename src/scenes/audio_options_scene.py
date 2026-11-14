"""Controles de volume com aplicação imediata e preferências locais."""
import pygame
from src.scenes.base_scene import BaseScene
from src.systems.audio_preferences import AudioPreferences, DEFAULT_VOLUMES
from src.ui import dark_fantasy_theme as theme
from src.ui.helpers import draw_text
from src.config.colors import GOLD, WHITE, GRAY

ROWS = (
    ('master_volume', 'VOLUME GERAL', 'Todos os sons do jogo'),
    ('music_volume', 'MÚSICA', 'Trilha sonora dos menus e batalhas'),
    ('combat_volume', 'COMBATE', 'Armas, movimentos e poderes'),
    ('damage_volume', 'IMPACTOS DE DANO', 'Acertos, colisões e sangramento'),
)


class AudioOptionsScene(BaseScene):
    def __init__(self, scene_manager, window_manager, asset_manager, return_scene=None):
        super().__init__(scene_manager, window_manager, asset_manager)
        self.audio = scene_manager.audio_manager
        self.preferences = getattr(scene_manager, 'audio_preferences', None) or AudioPreferences()
        self.return_scene = return_scene
        self.selected = 0
        self.dragging = None
        self.message = 'As alterações são aplicadas na hora e salvas neste computador.'
        self.sliders = {key:pygame.Rect(940, 356+i*120, 360, 14) for i,(key,_,_) in enumerate(ROWS)}
        self.minus = {key:pygame.Rect(875, 341+i*120, 42, 44) for i,(key,_,_) in enumerate(ROWS)}
        self.plus = {key:pygame.Rect(1320, 341+i*120, 42, 44) for i,(key,_,_) in enumerate(ROWS)}
        self.back_button = pygame.Rect(500, 845, 235, 64)
        self.defaults_button = pygame.Rect(1030, 845, 390, 64)

    @property
    def music_context(self):
        return getattr(self.return_scene, 'music_context', 'menu')

    def update(self, dt):
        pass

    def _set(self, key, value):
        getattr(self.audio, 'set_'+key)(max(0, min(1, value)))

    def _persist(self):
        try:
            self.preferences.save(self.audio)
            self.message = 'Volumes salvos.'
        except OSError:
            self.message = 'Não foi possível salvar. Os ajustes valem nesta sessão.'

    def _slide(self, key, x):
        rect = self.sliders[key]
        self._set(key, (x-rect.left)/rect.width)

    def _back(self):
        self._persist()
        self.play_ui_sound('ui.click')
        if self.return_scene is None:
            from src.scenes.menu_scene import MenuScene
            self.return_scene = MenuScene(self.scene_manager, self.window_manager, self.asset_manager)
        self.scene_manager.change_scene(self.return_scene)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            point = self.window_manager.map_to_virtual(event.pos)
            if self.back_button.collidepoint(point):
                self._back()
                return
            if self.defaults_button.collidepoint(point):
                for key,value in DEFAULT_VOLUMES.items():self._set(key,value)
                self._persist();self.play_ui_sound('ui.confirm')
                return
            for index,(key,_,_) in enumerate(ROWS):
                if self.sliders[key].inflate(28,44).collidepoint(point):
                    self.selected=index;self.dragging=key;self._slide(key,point[0]);return
                for rect,step in ((self.minus[key],-.05),(self.plus[key],.05)):
                    if rect.collidepoint(point):
                        self.selected=index;self._set(key,getattr(self.audio,key)+step)
                        self._persist();self.play_ui_sound('ui.click');return
        elif event.type == pygame.MOUSEMOTION and self.dragging is not None:
            self._slide(self.dragging,self.window_manager.map_to_virtual(event.pos)[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging is not None:self._persist()
            self.dragging=None
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:self._back()
            elif event.key in (pygame.K_DOWN,pygame.K_TAB):self.selected=(self.selected+1)%len(ROWS)
            elif event.key == pygame.K_UP:self.selected=(self.selected-1)%len(ROWS)
            elif event.key in (pygame.K_LEFT,pygame.K_RIGHT):
                key=ROWS[self.selected][0]
                self._set(key,getattr(self.audio,key)+(.05 if event.key==pygame.K_RIGHT else -.05))
                self._persist()

    def draw(self, surface):
        assets=self.asset_manager
        theme.backdrop(surface, assets.background, opacity=208)
        theme.panel(surface, pygame.Rect(430,135,1060,800))
        draw_text(surface,'OPÇÕES DE ÁUDIO',assets.big_font,GOLD,960,205,center=True)
        draw_text(surface,'Encontre o equilíbrio entre a trilha e os efeitos.',assets.small_font,GRAY,960,270,center=True)
        mouse=self.window_manager.get_virtual_mouse_pos()
        for index,(key,label,description) in enumerate(ROWS):
            y=340+index*120;rect=self.sliders[key];value=getattr(self.audio,key)
            draw_text(surface,label,assets.font,WHITE,500,y)
            draw_text(surface,description,assets.small_font,GRAY,500,y+39)
            pygame.draw.rect(surface,(37,48,45),rect,border_radius=7)
            fill=rect.copy();fill.width=round(rect.width*value)
            if fill.width:pygame.draw.rect(surface,(145,122,70),fill,border_radius=7)
            knob=(round(rect.left+rect.width*value),rect.centery)
            pygame.draw.circle(surface,(15,24,22),knob,16)
            pygame.draw.circle(surface,GOLD if index==self.selected else (160,143,98),knob,13,3)
            for button,text in ((self.minus[key],'-'),(self.plus[key],'+')):
                theme.button(surface,button,text,assets.small_font,hover=button.collidepoint(mouse))
            draw_text(surface,f'{round(value*100)}%',assets.font,GOLD,1410,rect.centery,center=True)
        theme.button(surface,self.back_button,'VOLTAR',assets.font,hover=self.back_button.collidepoint(mouse))
        theme.button(surface,self.defaults_button,'RESTAURAR PADRÃO',assets.font,hover=self.defaults_button.collidepoint(mouse))
        draw_text(surface,self.message,assets.small_font,GRAY,960,969,center=True)
        theme.footer(surface,'ARRASTE OU USE AS SETAS  ·  ESC VOLTAR',assets.small_font)
