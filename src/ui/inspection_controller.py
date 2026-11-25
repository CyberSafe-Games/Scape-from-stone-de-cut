"""Estado de inspeção independente de mouse/touch e do desenho das cartas."""
class InspectionController:
    def __init__(self):
        self.target=None
        self.pinned=False
        self.generation=0
    def inspect(self,target,*,pinned=False):
        if (target,pinned)!=(self.target,self.pinned):
            self.generation+=1
        self.target,self.pinned=target,pinned
        return target
    def hover(self,targets,position):
        if self.pinned:return self.target
        return self.inspect(next((key for key,rect in targets if rect.collidepoint(position)),None))
    def clear(self):
        self.inspect(None)
    @staticmethod
    def bounded_preview(size,viewport,center=None):
        import pygame
        bounds=pygame.Rect(viewport)
        width,height=size
        scale=min(1,(bounds.width-16)/max(1,width),(bounds.height-16)/max(1,height))
        rect=pygame.Rect(0,0,max(1,round(width*scale)),max(1,round(height*scale)))
        rect.center=center or bounds.center
        return rect.clamp(bounds.inflate(-16,-16))

