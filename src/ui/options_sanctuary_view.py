"""Pedra, pergaminho e ouro da interface ilustrada de Configurações."""
import math
import pygame
from src.config.colors import GOLD, WHITE
from src.config.settings import WIDTH, HEIGHT
from src.ui import dark_fantasy_theme as theme
from src.ui.frames import nine_slice, gold_outline
from src.ui.merchant_workshop_view import text_in_rect


class OptionsSanctuaryView:
    BACKGROUND = 'options/sanctuary_background'

    def __init__(self, assets):
        self.assets, self.elapsed, self.cache = assets, 0, {}
        image = assets.get_service_image(self.BACKGROUND)
        self.source = image if isinstance(image, pygame.Surface) else None
        ornament = assets.get_service_image('shop/offer_frame')
        self.ornament = ornament if isinstance(ornament, pygame.Surface) else None

    def update(self, dt):
        self.elapsed += dt

    def backdrop(self, surface):
        if self.source is None:
            theme.backdrop(surface, self.assets.background, opacity=220)
            theme.panel(surface,(430,135,1060,800),highlighted=True)
            return
        if 'backdrop' not in self.cache:
            self.cache['backdrop'] = pygame.transform.smoothscale(self.source,(WIDTH,HEIGHT))
        surface.blit(self.cache['backdrop'],(0,0))

    def tile(self, size):
        key=('stone',tuple(size))
        if key not in self.cache:
            if self.source is None:
                result=pygame.Surface(size)
                result.fill((24,27,22))
            else:
                w,h=self.source.get_size()
                patch=self.source.subsurface((round(w*.42),round(h*.38),round(w*.12),round(h*.12)))
                result=pygame.transform.smoothscale(patch,size)
                result.fill((125,139,132),special_flags=pygame.BLEND_RGB_MULT)
            self.cache[key]=result
        return self.cache[key]

    def modal_panel(self,surface,rect):
        rect=pygame.Rect(rect)
        surface.blit(self.tile(rect.size),rect)
        self.border(surface,rect)

    def border(self,surface,rect):
        rect=pygame.Rect(rect)
        key=('border',rect.size)
        if self.ornament is not None:
            if key not in self.cache:
                self.cache[key]=nine_slice(self.ornament,rect.size,margin=205,edge=min(23,rect.height//3))
            surface.blit(self.cache[key],rect)
        else:
            gold_outline(surface,rect)

    def button(self,surface,rect,label,font,hover=False,prominent=False,enabled=True,danger=False):
        rect=pygame.Rect(rect)
        pygame.draw.rect(surface,(2,5,4),rect.move(3,5),border_radius=5)
        surface.blit(self.tile(rect.size),rect)
        veil=pygame.Surface(rect.size,pygame.SRCALPHA)
        veil.fill((89,68,27,95) if prominent else (8,13,11,140 if enabled else 215))
        surface.blit(veil,rect)
        self.border(surface,rect)
        if hover and enabled:
            gold_outline(surface,rect.inflate(-4,-4),True,compact=True)
            # O brilho pulsa só nos cantos e nunca interfere no texto.
            r=3+round((math.sin(self.elapsed/220)+1)*1.3)
            for x in (rect.left+13,rect.right-14):
                pygame.draw.polygon(surface,GOLD,((x,rect.centery-r),(x+r,rect.centery),(x,rect.centery+r),(x-r,rect.centery)))
        if prominent:
            pygame.draw.circle(surface,(154,202,171),(rect.right-14,rect.top+13),3)
        color=(224,167,129) if danger else WHITE if enabled else (133,133,116)
        text_in_rect(surface,label,font,color,rect.inflate(-38 if rect.width>100 else -12,-14),True)

    def slider(self,surface,rect,value,focused=False):
        rect=pygame.Rect(rect)
        rail=rect.inflate(0,10)
        surface.blit(self.tile(rail.size),rail)
        gold_outline(surface,rail,focused,compact=True)
        fill=pygame.Rect(rect.x+3,rect.centery-3,max(0,round((rect.width-6)*value)),6)
        if fill.width:pygame.draw.rect(surface,(189,146,69),fill,border_radius=3)
        for i in range(5):
            x=rect.x+round(rect.width*i/4)
            pygame.draw.line(surface,(137,111,65),(x,rail.bottom+3),(x,rail.bottom+7),1)
        x=round(rect.left+rect.width*value)
        points=((x,rect.centery-15),(x+12,rect.centery),(x,rect.centery+15),(x-12,rect.centery))
        pygame.draw.polygon(surface,(23,32,27),points)
        pygame.draw.polygon(surface,GOLD if focused else (164,137,83),points,2)
        pygame.draw.line(surface,(171,219,180),(x,rect.centery-6),(x,rect.centery+6),2)
