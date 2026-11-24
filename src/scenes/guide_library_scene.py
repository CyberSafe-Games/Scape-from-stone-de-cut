"""Consulta dos guias sem mudar flags, saves ou o estado da batalha."""
import pygame
from src.scenes.base_scene import BaseScene
from src.ui.options_sanctuary_view import OptionsSanctuaryView
from src.ui.management_guide import steps_for
from src.ui.helpers import draw_text,wrap_text
from src.config.colors import GOLD,WHITE


class GuideLibraryScene(BaseScene):
    def __init__(self,scene_manager,window_manager,asset_manager):
        super().__init__(scene_manager,window_manager,asset_manager)
        self.visuals=OptionsSanctuaryView(asset_manager)
        self.key,self.index='shop',0
        self.tabs={key:pygame.Rect(500+i*310,274,300,52) for i,key in enumerate(('shop','backpack','workshop'))}
        self.previous=pygame.Rect(500,825,420,60)
        self.following=pygame.Rect(1030,825,390,60)
        self.back=pygame.Rect(760,925,400,56)

    def update(self,dt):self.visuals.update(dt)

    def draw(self,surface):
        self.visuals.backdrop(surface)
        a=self.asset_manager
        mouse=self.window_manager.get_virtual_mouse_pos()
        draw_text(surface,'GUIAS DA JORNADA',a.big_font,GOLD,960,190,True)
        draw_text(surface,'Consulta livre · não altera o progresso do slot.',a.small_font,WHITE,960,236,True)
        for key,label in (('shop','MERCADO'),('backpack','MOCHILA'),('workshop','ALTAR')):
            r=self.tabs[key]
            self.visuals.button(surface,r,label,a.small_font,hover=r.collidepoint(mouse),prominent=key==self.key)
        # A biblioteca consulta somente texto; os targets continuam nas telas reais.
        steps=steps_for(None,self.key)
        step=steps[self.index]
        draw_text(surface,f'PASSO {self.index+1} / {len(steps)}',a.small_font,GOLD,515,380)
        draw_text(surface,step.title,a.menu_font,WHITE,515,435)
        for i,line in enumerate(wrap_text(step.text,a.font,870)):
            draw_text(surface,line,a.font,(226,217,190),515,500+i*a.font.get_linesize())
        for r,label,enabled in ((self.previous,'ANTERIOR',self.index>0),(self.following,'PRÓXIMO',self.index+1<len(steps)),(self.back,'VOLTAR ÀS CONFIGURAÇÕES',True)):
            self.visuals.button(surface,r,label,a.small_font,hover=r.collidepoint(mouse),enabled=enabled)

    def handle_event(self,event):
        if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
            self.scene_manager.pop_modal()
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            point=self.window_manager.map_to_virtual(event.pos)
            for key,r in self.tabs.items():
                if r.collidepoint(point):
                    self.key,self.index=key,0
                    return
            if self.back.collidepoint(point):self.scene_manager.pop_modal()
            elif self.previous.collidepoint(point):self.index=max(0,self.index-1)
            elif self.following.collidepoint(point):self.index=min(len(steps_for(None,self.key))-1,self.index+1)
