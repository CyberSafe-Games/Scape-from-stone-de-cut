"""Geometria responsiva web pura; o Desktop mantém seu canvas original."""
from dataclasses import dataclass

@dataclass(frozen=True)
class ResponsiveLayout:
    width: float
    height: float
    compact: bool
    portrait_blocked: bool
    coarse: bool
    scale: float
    min_target: int = 44
    cards_per_page: int = 2

def resolve_layout(width, height, *, web=False, coarse=False, insets=(0,0,0,0)):
    top,right,bottom,left = (max(0,float(v)) for v in insets)
    width=max(1,float(width)-left-right)
    height=max(1,float(height)-top-bottom)
    compact=bool(web and (coarse or width<1000 or height<600))
    return ResponsiveLayout(width,height,compact,
        bool(web and coarse and height>width),bool(coarse),min(width/1920,height/1080),
        cards_per_page=2 if width<900 else 3)

def css_to_virtual(point, rect, virtual=(1920,1080)):
    x,y,w,h=rect
    if w<=0 or h<=0:return None
    if not (x<=point[0]<=x+w and y<=point[1]<=y+h):return None
    return ((point[0]-x)*virtual[0]/w,(point[1]-y)*virtual[1]/h)

