"""Canvas físico reduzido com coordenadas artísticas originais, exclusivo da Web."""
from collections import OrderedDict
from contextlib import contextmanager
import weakref
import math
import pygame


class MobileCanvas(pygame.Surface):
    def __new__(cls, logical=(1920,1080), physical=(960,540), flags=0):
        return super().__new__(cls)
    def __init__(self, logical=(1920,1080), physical=(960,540), flags=0):
        super().__init__(physical,flags)
        self.logical=tuple(logical)
        self.mobile_scale=physical[0]/logical[0]
        self.frozen=weakref.WeakSet()
        self.scaled=OrderedDict()
        self.cache_bytes=0
        self.cache_limit=24*1024*1024
        self.cache_hits=0
        self.cache_misses=0
        self.text_cache=OrderedDict()
        self.text_bytes=0
        self.button_hits=[]
        self.layers=OrderedDict();self.layer_bytes=0
        self.pool=OrderedDict();self.pool_bytes=0;self.pool_used={}
        self.pool_created=0;self.scale_operations=0;self.text_renders=0
        self.raster_diagnostics=False;self.miss_details=[];self.native_scale_calls=0
    def get_size(self):return self.logical
    def get_width(self):return self.logical[0]
    def get_height(self):return self.logical[1]
    def get_rect(self,**kwargs):return pygame.Rect((0,0),self.logical).move(0,0) if not kwargs else self._rect(kwargs)
    def _rect(self,values):
        rect=pygame.Rect((0,0),self.logical)
        for key,value in values.items():setattr(rect,key,value)
        return rect
    def point(self,p):return tuple(round(v*self.mobile_scale) for v in p)
    def rect(self,r):
        r=pygame.Rect(r);x,y=self.point(r.topleft);right,bottom=self.point(r.bottomright)
        return pygame.Rect(x,y,right-x,bottom-y)
    def logical_rect(self,r):
        r=pygame.Rect(r);s=self.mobile_scale
        return pygame.Rect(round(r.x/s),round(r.y/s),round(r.w/s),round(r.h/s))
    def freeze(self,image):
        if isinstance(image,pygame.Surface) and image is not self:self.frozen.add(image)
    def remember(self,value,depth=0):
        if depth>5:return
        if isinstance(value,pygame.Surface):self.freeze(value)
        elif isinstance(value,dict):
            for item in value.values():self.remember(item,depth+1)
        elif isinstance(value,(tuple,list)):
            for item in value:self.remember(item,depth+1)
    def fill(self,color,rect=None,special_flags=0):
        result=pygame.Surface.fill(self,color,self.rect(rect) if rect is not None else None,special_flags)
        return self.logical_rect(result)
    def blit(self,source,dest,area=None,special_flags=0):
        position=dest.topleft if isinstance(dest,pygame.Rect) else dest[:2]
        if isinstance(source,MobileCanvas):
            return self.logical_rect(pygame.Surface.blit(self,source,self.point(position),
                source.rect(area) if area else None,special_flags))
        region=pygame.Rect(area) if area is not None else source.get_rect()
        region=region.clip(source.get_rect())
        if not region.width or not region.height:return pygame.Rect(position,(0,0))
        parent=source.get_abs_parent()
        immutable=source in self.frozen or parent in self.frozen
        # Escalar a imagem inteira uma vez também atende recortes animados
        # (ex.: derrota do Slime), sem reescalar uma tira a cada frame.
        base=parent if parent in self.frozen else source
        offset=source.get_abs_offset() if base is parent else (0,0)
        absolute=region.move(offset)
        sample=base.get_rect() if immutable else absolute
        if not immutable:base=source;sample=region;offset=(0,0)
        size=tuple(max(1,round(v*self.mobile_scale)) for v in sample.size)
        key=(weakref.ref(base),size,special_flags)
        image=self.scaled.get(key) if immutable else None
        if image is None:
            image=pygame.transform.smoothscale(base if immutable else source.subsurface(region),size)
            self.scale_operations+=1
            if self.raster_diagnostics and len(self.miss_details)<12:
                import sys
                caller=sys._getframe(1)
                self.miss_details.append([caller.f_code.co_name,list(source.get_size()),immutable])
            self.cache_misses+=1
            if immutable:
                amount=image.get_pitch()*image.get_height()
                while self.scaled and self.cache_bytes+amount>self.cache_limit:
                    _,old=self.scaled.popitem(last=False)
                    self.cache_bytes-=old.get_pitch()*old.get_height()
                if amount<=self.cache_limit:
                    self.scaled[key]=image;self.cache_bytes+=amount
        else:
            self.cache_hits+=1;self.scaled.move_to_end(key)
        image.set_alpha(source.get_alpha())
        if immutable:
            crop=self.rect(absolute).clip(image.get_rect())
            origin=self.point((position[0]-region.x-offset[0],position[1]-region.y-offset[1]))
            destination=(origin[0]+crop.x,origin[1]+crop.y)
            return self.logical_rect(pygame.Surface.blit(self,image,destination,crop,special_flags))
        return self.logical_rect(pygame.Surface.blit(self,image,self.point(position),special_flags=special_flags))
    def begin_frame(self):
        self.pool_used.clear();self.miss_details=[];self.native_scale_calls=0
        self.scale_operations=0;self.text_renders=0;self.pool_created=0
    def cached_layer(self,key,factory):
        image=self.layers.get(key)
        if image is None:
            image=factory()
            amount=image.get_pitch()*image.get_height()
            while self.layers and self.layer_bytes+amount>8*1024*1024:
                _,old=self.layers.popitem(last=False);self.layer_bytes-=old.get_pitch()*old.get_height()
            if amount<=8*1024*1024:self.layers[key]=image;self.layer_bytes+=amount
            self.freeze(image)
        else:self.layers.move_to_end(key)
        return image
    def scratch(self,size,flags,key,physical=True):
        size=tuple(map(int,size));slot=self.pool_used.get(key,0);self.pool_used[key]=slot+1
        cache_key=(key,slot,size,flags,physical)
        image=self.pool.get(cache_key)
        if image is None:
            if physical:
                target=tuple(max(1,math.ceil(v*self.mobile_scale)) for v in size)
                image=MobileCanvas(size,target,flags)
                image.mobile_scale=self.mobile_scale
            else:image=pygame.Surface(size,flags)
            amount=image.get_pitch()*pygame.Surface.get_height(image)
            while self.pool and self.pool_bytes+amount>8*1024*1024:
                _,old=self.pool.popitem(last=False);self.pool_bytes-=old.get_pitch()*pygame.Surface.get_height(old)
            if amount<=8*1024*1024:self.pool[cache_key]=image;self.pool_bytes+=amount
            self.pool_created+=1
        else:self.pool.move_to_end(cache_key)
        image.set_clip(None);image.set_alpha(255 if flags & pygame.SRCALPHA else None);image.fill((0,0,0,0))
        return image
    def begin_owner(self,owner):
        self.button_hits=[]
    def register_hit(self,rect,label):
        self.button_hits.append(dict(label=str(label),rect=pygame.Rect(rect)))
    def render_text(self,font,text,color):
        key=(font,str(text),tuple(pygame.Color(color)))
        image=self.text_cache.get(key)
        if image is None:
            image=font.render(str(text),True,color)
            self.text_renders+=1
            amount=image.get_pitch()*image.get_height()
            while self.text_cache and self.text_bytes+amount>8*1024*1024:
                _,old=self.text_cache.popitem(last=False);self.text_bytes-=old.get_pitch()*old.get_height()
            if amount<=8*1024*1024:self.text_cache[key]=image;self.text_bytes+=amount
            self.freeze(image)
        else:self.text_cache.move_to_end(key)
        return image
    def copy(self):
        # Compositores legados criam sua camada imutável uma vez em coordenadas lógicas.
        return pygame.transform.scale(self,self.logical)
    def subsurface(self,rect):
        r=pygame.Rect(rect);part=pygame.Surface.subsurface(self,self.rect(r))
        return pygame.transform.scale(part,r.size)
    def get_clip(self):return self.logical_rect(pygame.Surface.get_clip(self))
    def set_clip(self,rect=None):return pygame.Surface.set_clip(self,self.rect(rect) if rect is not None else None)


@contextmanager
def drawing_coordinates(canvas=None):
    """Adapta primitivas apenas durante o draw síncrono; sempre restaura o módulo."""
    originals={}
    transforms={}
    if canvas is not None and canvas.raster_diagnostics:
        for name in ("scale","smoothscale"):
            original=getattr(pygame.transform,name);transforms[name]=original
            def measured(*args,_original=original,**kwargs):
                canvas.native_scale_calls+=1
                return _original(*args,**kwargs)
            setattr(pygame.transform,name,measured)
    for name in ("rect","line","lines","aaline","aalines","polygon","circle","ellipse","arc"):
        original=getattr(pygame.draw,name);originals[name]=original
        def draw(surface,color,*args,_name=name,_original=original,**kwargs):
            if not isinstance(surface,MobileCanvas):return _original(surface,color,*args,**kwargs)
            values=list(args);scale=surface.mobile_scale
            if _name in ("rect","ellipse","arc"):
                if values:values[0]=surface.rect(values[0])
                elif "rect" in kwargs:kwargs["rect"]=surface.rect(kwargs["rect"])
                width_index=3 if _name=="arc" else 1
            elif _name in ("line","aaline"):
                values[0]=surface.point(values[0]);values[1]=surface.point(values[1]);width_index=2
            elif _name in ("lines","aalines"):
                values[1]=[surface.point(p) for p in values[1]];width_index=2
            elif _name=="polygon":
                values[0]=[surface.point(p) for p in values[0]];width_index=1
            else:
                values[0]=surface.point(values[0]);values[1]=max(1,round(values[1]*scale));width_index=2
            if _name not in ("aaline","aalines"):
                if len(values)>width_index and values[width_index]:
                    values[width_index]=max(1,round(values[width_index]*scale))
                if kwargs.get("width"):kwargs["width"]=max(1,round(kwargs["width"]*scale))
            for key in tuple(kwargs):
                if key.startswith("border_") and kwargs[key]>0:kwargs[key]=max(1,round(kwargs[key]*scale))
            return surface.logical_rect(_original(surface,color,*values,**kwargs))
        setattr(pygame.draw,name,draw)
    try:yield
    finally:
        for name,original in originals.items():setattr(pygame.draw,name,original)
        for name,original in transforms.items():setattr(pygame.transform,name,original)
