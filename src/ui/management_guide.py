"""Guia ancestral com spotlight nos controles reais, sem alterar suas posições."""
from dataclasses import dataclass
import pygame
from src.config.colors import GOLD, WHITE
from src.config.settings import WIDTH, HEIGHT
from src.systems.management_tutorials import normalize_guides, complete_guide
from src.ui import dark_fantasy_theme as theme
from src.ui.helpers import wrap_text, draw_text
from src.ui.frames import gold_outline


@dataclass(frozen=True)
class GuideStep:
    title: str
    text: str
    target: object


def steps_for(scene, key):
    if key == 'shop':
        return (
            GuideStep('Tesouros do mercador', 'O ouro compra um tipo de carta ainda não adquirido. Suas três cópias ficam no acervo; equipe-as depois na Mochila. A compra não altera o deck ativo.', lambda: next(iter(scene.card_rects.values())).union(next(iter(scene.offer_rects.values())))),
            GuideStep('Bálsamo e limites da jornada', 'A cura recupera até 20 de vida atual. Custa 30, depois 45 e 60 de ouro, até três compras por run. Vida cheia não cobra. Tipos adquiridos e cartas indisponíveis não podem ser comprados novamente.', lambda: pygame.Rect(60,640,420,291)),
            GuideStep('Mais ofertas e o altar', 'Use Anterior e Próxima para ver as ofertas. Ouro insuficiente ou uma batalha em andamento impede compras. O Altar de Aprimoramento evolui uma cópia que você já possui.', lambda: scene.workshop_button),
        )
    if key == 'backpack':
        return (
            GuideStep('Acervo não é baralho', 'O acervo reúne as cópias adquiridas. Só as cartas equipadas nos compartimentos à esquerda entram em combate. Clique numa carta da reserva para adicionar uma cópia disponível.', lambda: pygame.Rect(768,267,606,660)),
            GuideStep('Prepare entre 6 e 18 cartas', 'Cada espaço contém uma cópia. Clique num espaço preenchido para removê-la; use até três cópias por tipo. Um rascunho com menos de seis cartas não substitui o último deck válido e impede sair.', lambda: scene.deck_panel),
            GuideStep('Inspecione antes de equipar', 'O painel de inspeção mostra nível, custo atual e efeito da cópia. Filtros e páginas ajudam a encontrar cartas; a moldura prateada identifica LV2.', lambda: scene.visuals.PREVIEW_RECT),
            GuideStep('Escolha sua Ultimate', 'Na aba Ultimates, selecione o poder equipado. As três custam 2 de energia e exigem carga 20. Essa escolha é independente dos 18 espaços do baralho.', lambda: scene.ultimate_tab_rect),
        )
    return (
        GuideStep('Escolha o tipo e a cópia', 'Selecione um tipo à esquerda e depois a cópia desejada no topo. A evolução afeta somente essa cópia, que mantém sua identificação e posição no baralho.', lambda: pygame.Rect(60,188,438,760)),
        GuideStep('Antes e depois do encantamento', 'Compare ANTES, LV1, com DEPOIS, LV2. A moldura de prata identifica o aprimoramento. Os valores e efeitos vêm do código; não presuma redução do custo de energia.', lambda: scene.after_rect),
        GuideStep('Materiais e ouro', 'Aprimorar consome três materiais do tipo mais o ouro indicado. Materiais custam 15 de ouro cada, com reserva de até nove por tipo. Você pode evoluir até três cópias por run; LV2 é o limite.', lambda: scene.upgrade_button),
    )


class ManagementGuide:
    HELP_RECT = pygame.Rect(1320, 62, 174, 58)

    def __init__(self, scene, key):
        self.scene, self.key = scene, key
        self.steps = steps_for(scene, key)
        self.active = not normalize_guides(scene.save_data['progresso'])[key]
        self.index = 0
        self.error = ''

    def open(self):
        self.active, self.index, self.error = True, 0, ''
        self.scene.play_ui_sound('ui.click')

    def finish(self):
        if getattr(self.scene.save_manager,"async_commands",False) is True:
            def complete(result):
                if result[0]:
                    self.active, self.error = False, ""
                    self.scene.play_ui_sound("ui.confirm")
                else:
                    self.error = result[1]
            self.scene.persist_command(lambda m,d:complete_guide(m,d,self.key),complete)
            return False
        ok, message = complete_guide(self.scene.save_manager, self.scene.save_data, self.key)
        if ok:
            self.active, self.error = False, ''
            self.scene.play_ui_sound('ui.confirm')
        else:
            self.error = 'Não foi possível salvar. Tente novamente ou pressione Esc para sair sem registrar.'
        return ok

    def target_rect(self):
        return pygame.Rect(self.steps[self.index].target()).clip(pygame.Rect(12,12,WIDTH-24,HEIGHT-24))

    def layout(self):
        target = self.target_rect()
        w, h = 660, 330
        candidates = [pygame.Rect(42,180,w,h), pygame.Rect(WIDTH-w-42,180,w,h),
                      pygame.Rect(42,HEIGHT-h-45,w,h), pygame.Rect(WIDTH-w-42,HEIGHT-h-45,w,h)]
        box = min(candidates, key=lambda b:b.clip(target.inflate(34,34)).width*b.clip(target.inflate(34,34)).height)
        return box, pygame.Rect(box.x+24,box.bottom-66,148,44), pygame.Rect(box.right-218,box.bottom-66,194,44), pygame.Rect(box.right-68,box.y+18,44,38)

    def handle_event(self, event):
        if not self.active:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.HELP_RECT.collidepoint(self.scene.window_manager.map_to_virtual(event.pos)):
                    self.open()
                    return True
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.error:
                    self.active = False
                else:
                    self.finish()
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_RIGHT):
                self.advance()
            elif event.key == pygame.K_LEFT:
                self.index = max(0,self.index-1)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            point = self.scene.window_manager.map_to_virtual(event.pos)
            _, previous, following, close = self.layout()
            if close.collidepoint(point):
                self.finish()
            elif previous.collidepoint(point):
                self.index = max(0,self.index-1)
            elif following.collidepoint(point):
                self.advance()
        # Um clique do guia nunca chega à compra, equipamento ou evolução.
        return True

    def advance(self):
        if self.index == len(self.steps)-1:
            self.finish()
        else:
            self.index += 1
            self.scene.play_ui_sound('ui.navigate', volume=.45)

    def draw(self, surface):
        a = self.scene.asset_manager
        mouse = self.scene.window_manager.get_virtual_mouse_pos()
        theme.button(surface,self.HELP_RECT,'?  AJUDA',a.small_font,hover=self.HELP_RECT.collidepoint(mouse))
        if not self.active:
            return
        box, previous, following, close = self.layout()
        target = self.target_rect().inflate(14,14).clip(surface.get_rect().inflate(-12,-12))
        veil = pygame.Surface(surface.get_size(),pygame.SRCALPHA)
        veil.fill((2,6,5,198))
        pygame.draw.rect(veil,(0,0,0,0),target,border_radius=8)
        surface.blit(veil,(0,0))
        gold_outline(surface,target,True)
        theme.panel(surface,box,highlighted=True,fill=(30,27,18,252))
        step=self.steps[self.index]
        draw_text(surface,f'GUIA ANCESTRAL  ·  {self.index+1}/{len(self.steps)}',a.small_font,GOLD,box.x+25,box.y+23)
        draw_text(surface,step.title,a.menu_font,WHITE,box.x+25,box.y+68)
        lines=wrap_text(step.text,a.small_font,box.width-52)
        for i,line in enumerate(lines):
            draw_text(surface,line,a.small_font,(226,216,186),box.x+25,box.y+113+i*a.small_font.get_linesize())
        if self.error:
            draw_text(surface,'Falha ao salvar · tente concluir novamente.',a.small_font,(240,153,120),box.x+25,box.bottom-105)
        theme.button(surface,previous,'ANTERIOR',a.small_font,enabled=self.index>0,hover=previous.collidepoint(mouse))
        theme.button(surface,following,'CONCLUIR' if self.index==len(self.steps)-1 else 'PRÓXIMO',a.small_font,prominent=True,hover=following.collidepoint(mouse))
        theme.button(surface,close,'×',a.small_font,hover=close.collidepoint(mouse))
