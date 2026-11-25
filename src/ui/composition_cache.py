"""Composições RGB equivalentes; a campanha web opta por usá-las."""
from collections import OrderedDict
import hashlib
import weakref
import pygame

class CompositionCache:
    def __init__(self,limit=24*1024*1024):
        self.images=OrderedDict()
        self.bytes=0
        self.limit=limit
        self.regions=weakref.WeakKeyDictionary()
    def _put(self,key,image):
        amount=image.get_pitch()*image.get_height()
        while self.images and self.bytes+amount>self.limit:
            _,old=self.images.popitem(last=False)
            self.bytes-=old.get_pitch()*old.get_height()
        self.images[key]=image
        self.bytes+=amount
        return image
    def backdrop(self,surface,key,draw):
        cache_key=("backdrop",key,surface.get_size())
        image=self.images.get(cache_key)
        if image is None:
            image=surface.copy().convert(surface)
            draw(image)
            self._put(cache_key,image)
        surface.blit(image,(0,0))
    def panel(self,surface,rect,selected,draw):
        rect=pygame.Rect(rect)
        area=rect.union(rect.move(6,9)).inflate(4,4).clip(surface.get_rect())
        if not area.width or not area.height:return
        source=surface.subsurface(area)
        digest=hashlib.sha256(pygame.image.tobytes(source,"RGBA")).digest()
        key=("panel",tuple(rect),selected,digest)
        image=self.images.get(key)
        if image is None:
            image=source.copy().convert(surface)
            draw(image,rect.move(-area.x,-area.y),selected)
            self._put(key,image)
        surface.blit(image,area)
    def begin_frame(self):
        self.covered=[]
    def root_panel(self,surface,rect,selected,draw):
        rect=pygame.Rect(rect)
        area=rect.union(rect.move(6,9)).inflate(4,4).clip(surface.get_rect())
        overlaps=any(area.colliderect(old) for old in self.covered)
        self.covered.append(area)
        if overlaps:
            return draw(surface,rect,selected)
        key=("root-panel",tuple(rect),selected)
        image=self.images.get(key)
        if image is None:
            image=surface.subsurface(area).copy().convert(surface)
            draw(image,rect.move(-area.x,-area.y),selected)
            self._put(key,image)
        surface.blit(image,area)
    def sparse_blit(self,surface,image,position,edge=30):
        if image not in self.regions:
            width,height=image.get_size()
            middle=pygame.Rect(edge,edge,max(0,width-2*edge),max(0,height-2*edge))
            if middle.width and middle.height and not pygame.mask.from_surface(image.subsurface(middle),0).count():
                self.regions[image]=[
                    pygame.Rect(0,0,width,edge),pygame.Rect(0,height-edge,width,edge),
                    pygame.Rect(0,edge,edge,height-2*edge),
                    pygame.Rect(width-edge,edge,edge,height-2*edge)]
            else:self.regions[image]=[image.get_rect()]
        for area in self.regions[image]:
            surface.blit(image,(position[0]+area.x,position[1]+area.y),area)

def optimize_visuals(visuals):
    if hasattr(visuals,"_web_composition"):return
    cache=visuals._web_composition=CompositionCache()
    backdrop=visuals.backdrop
    def draw_backdrop(surface):
        cache.begin_frame()
        cache.backdrop(surface,"scene",backdrop)
    visuals.backdrop=draw_backdrop
    # Painéis raiz destas telas ficam sobre o fundo imutável; painéis sobrepostos
    # conservam a composição alpha original (incluindo previews e seleção).
    if visuals.__class__.__name__ in ("MerchantWorkshopView","BackpackView"):
        panel=visuals.panel
        visuals.panel=lambda surface,rect,selected=False:cache.root_panel(surface,rect,selected,panel)
    if hasattr(visuals,"frame"):
        frame=visuals.frame
        def sparse_frame(surface,rect):
            rect=pygame.Rect(rect)
            image=visuals.scaled.get(("ornament-nine-slice",rect.size))
            if image is None:return frame(surface,rect)
            cache.sparse_blit(surface,image,rect.topleft)
        visuals.frame=sparse_frame

