"""Canvas web independente dos modos de janela e do monitor nativo."""
import math
import pygame


def backing_size(css_width, css_height, dpr, maximum=(1920,1080)):
    """Densidade física limitada à arte nativa, mantendo proporção e orçamento."""
    values=tuple(float(v) for v in (css_width,css_height,dpr))
    if not all(math.isfinite(v) and v>0 for v in values):
        raise ValueError("Viewport inválido")
    width,height,density=values
    density=min(2.0,max(1.0,density))
    scale=min(width*density/maximum[0],height*density/maximum[1],1.0)
    return max(1,round(maximum[0]*scale)),max(1,round(maximum[1]*scale))

from src.config.settings import WIDTH, HEIGHT, TITLE, LEGACY_WINDOW_SIZE
from src.ui.render_cache import RenderCache


class WebWindowManager:
    def __init__(self, width=WIDTH, height=HEIGHT, title=TITLE,
                 window_size=None, platform_service=None):
        self.width, self.height, self.title = width, height, title
        self.platform = platform_service
        self.windowed_size = tuple(window_size or LEGACY_WINDOW_SIZE)
        self.display_surface = pygame.display.set_mode(self.windowed_size)
        self.screen = pygame.Surface((width, height)).convert()
        self.compact = False
        self.touch_position = None
        self.is_large_window = False
        self.render_cache = RenderCache()

    @property
    def is_fullscreen(self):
        return self.platform.fullscreen_state()

    @property
    def virtual_screen(self):
        return self.screen

    def configure_viewport(self,layout):
        """O layout não força downscale; o buffer acompanha CSS × DPR limitado."""
        if bool(layout.compact)!=self.compact:
            self.compact=bool(layout.compact)
            from src.core.mobile_canvas import MobileCanvas
            self.screen=MobileCanvas((self.width,self.height),(1280,720)) if self.compact else pygame.Surface((self.width,self.height)).convert()
            self._mobile_context=None
        self._sync_backing_size()

    def draw_scene(self,scenes):
        if not self.compact:return scenes.draw(self.screen)
        from src.core.mobile_canvas import drawing_coordinates
        context=(id(scenes.current_scene),getattr(getattr(scenes.current_scene,"asset_manager",None),"active_context",None))
        if context!=self._mobile_context:
            self._mobile_context=context
            for value in vars(getattr(scenes.current_scene,"asset_manager",scenes.assets)).values():self.screen.remember(value)
        scene=scenes.current_scene
        # Camadas geradas pelo compositor são imutáveis depois de preparadas.
        for name in ("_background_layer","_current_layer","_previous_layer"):
            self.screen.freeze(getattr(scene,name,None))
        hud=getattr(scene,"battle_hud",None)
        if hud:
            for value in vars(hud).values():self.screen.remember(value)
        for layer in (scene,*scenes.modal_stack):
            self.screen.remember(getattr(getattr(layer,"visuals",None),"scaled",{}))
        with drawing_coordinates():scenes.draw(self.screen)

    def _sync_backing_size(self):
        try:
            viewport=self.platform.render_viewport()
            size=(1280,720) if self.compact else backing_size(viewport["width"],viewport["height"],viewport["dpr"],
                              (self.width,self.height))
        except (AttributeError,TypeError,ValueError,KeyError):
            # Pilotos/bridges antigos não expõem a densidade.
            return
        if self.display_surface.get_size()!=size:
            self.display_surface=pygame.display.set_mode(size)
            self.render_cache=RenderCache()

    def get_scale_and_offset(self):
        dw, dh = self.display_surface.get_size()
        scale = max(.0001, min(dw/self.width, dh/self.height))
        return scale, (dw-self.width*scale)/2, (dh-self.height*scale)/2

    def map_to_virtual(self, point):
        scale, x, y = self.get_scale_and_offset()
        return (point[0]-x)/scale, (point[1]-y)/scale

    def get_virtual_mouse_pos(self):
        return self.touch_position if self.compact and self.touch_position is not None else self.map_to_virtual(pygame.mouse.get_pos())

    def present(self):
        self._sync_backing_size()
        scale, x, y = self.get_scale_and_offset()
        size = max(1,round(self.width*scale)), max(1,round(self.height*scale))
        # Reutiliza o destino; nenhum Surface novo por quadro.
        if self.compact:
            self.display_surface.blit(self.screen,(0,0))
            pygame.display.flip()
            return
        if size==self.screen.get_size():
            target=self.screen
        else:
            target=self.render_cache.target(size,self.display_surface)
            pygame.transform.smoothscale(self.screen,size,target)
        self.display_surface.fill((0,0,0))
        self.display_surface.blit(target, (round(x), round(y)))
        pygame.display.flip()

    def handle_window_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_F10, pygame.K_F11):
            # F11 é tratado no gesto DOM pela bridge, evitando perder a ativação.
            return True
        return event.type == pygame.VIDEORESIZE

    def toggle_fullscreen(self):
        self.platform.toggle_fullscreen()

    def apply_display_preferences(self, fullscreen=False, large_window=False):
        # Preferências nativas não forçam fullscreen nem tamanho no navegador.
        return None

    def get_fullscreen_button_rect(self):
        return pygame.Rect(-1000,-1000,1,1)

    def draw_fullscreen_button(self, font=None):
        return None

