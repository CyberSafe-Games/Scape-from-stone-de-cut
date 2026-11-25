"""Entrada desktop/web normalizada sem converter coordenadas duas vezes."""
from dataclasses import dataclass
import pygame

@dataclass(frozen=True)
class RoutedInput:
    kind: str
    position: tuple | None = None
    button: int | None = None
    key: int | None = None
    wheel: tuple = (0,0)
    touch: bool = False

class InputRouter:
    def __init__(self, window):
        self.window = window
        self.last = None
    def route(self, event):
        if event.type in (pygame.FINGERDOWN,pygame.FINGERUP,pygame.FINGERMOTION):
            kind={pygame.FINGERDOWN:"down",pygame.FINGERUP:"up",pygame.FINGERMOTION:"move"}[event.type]
            value=RoutedInput(kind,(event.x*self.window.width,event.y*self.window.height),1,touch=True)
        elif event.type in (pygame.MOUSEMOTION,pygame.MOUSEBUTTONDOWN,pygame.MOUSEBUTTONUP):
            kind={pygame.MOUSEMOTION:"move",pygame.MOUSEBUTTONDOWN:"down",
                  pygame.MOUSEBUTTONUP:"up"}[event.type]
            value=RoutedInput(kind,self.window.map_to_virtual(event.pos),getattr(event,"button",None))
        elif event.type==pygame.MOUSEWHEEL:
            value=RoutedInput("wheel",self.window.get_virtual_mouse_pos(),wheel=(event.x,event.y))
        elif event.type in (pygame.KEYDOWN,pygame.KEYUP):
            value=RoutedInput("key_down" if event.type==pygame.KEYDOWN else "key_up",
                              key=event.key)
        else:value=RoutedInput("other")
        self.last=value
        return value
    def dispatch(self,event,receiver):
        self.route(event)
        receiver(event)  # Cenas legadas conservam o evento original e seus atalhos.

