"""Backup manual com escolha explícita do slot e confirmação de substituição."""
from pathlib import Path
import pygame
from src.scenes.base_scene import BaseScene
from src.ui import dark_fantasy_theme as theme
from src.ui.helpers import draw_text


class BackupModal(BaseScene):
    def __init__(self, owner, operation):
        super().__init__(owner.scene_manager, owner.window_manager, owner.asset_manager)
        self.owner, self.operation = owner, operation
        self.buttons=[pygame.Rect(660,330+i*100,600,72) for i in range(3)]
        self.close=pygame.Rect(760,690,400,60)
        self.message="Escolha o espaço da jornada."
    def update(self,dt): pass
    def draw(self,surface):
        veil=pygame.Surface(surface.get_size(),pygame.SRCALPHA)
        veil.fill((0,0,0,200));surface.blit(veil,(0,0))
        theme.panel(surface,pygame.Rect(600,230,720,570))
        draw_text(surface,"EXPORTAR BACKUP" if self.operation=="export" else "IMPORTAR BACKUP",
                  self.asset_manager.menu_font,(230,200,145),960,280,center=True)
        for index,rect in enumerate(self.buttons):
            theme.button(surface,rect,f"ESPAÇO {index+1}",self.asset_manager.menu_font)
        theme.button(surface,self.close,"CANCELAR",self.asset_manager.small_font)
        draw_text(surface,self.message[:90],self.asset_manager.small_font,(230,200,145),960,650,center=True)
    def handle_event(self,event):
        if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
            self.scene_manager.pop_modal();return
        if event.type!=pygame.MOUSEBUTTONDOWN or event.button!=1:return
        point=self.window_manager.map_to_virtual(event.pos)
        if self.close.collidepoint(point):self.scene_manager.pop_modal();return
        for index,rect in enumerate(self.buttons):
            if rect.collidepoint(point):
                slot=index+1
                if self.operation=="import" and self.owner.save_manager.exists(f"slot_{slot}"):
                    from src.scenes.confirmation_modal import ConfirmationModal
                    self.scene_manager.push_modal(ConfirmationModal(
                        self.scene_manager,self.window_manager,self.asset_manager,
                        on_confirm=lambda:self.execute(slot,True),
                        title="SUBSTITUIR JORNADA?",message="O backup substituirá o espaço escolhido.",
                        confirm_label="SIM, IMPORTAR"))
                else:self.execute(slot,False)
                break

    def execute(self,slot,replace):
        manager=self.owner.save_manager
        def complete(message):
            self.owner.refresh()
            self.owner.error=message
            if self in self.scene_manager.modal_stack:
                self.scene_manager.modal_stack.remove(self)
        if getattr(manager,"async_commands",False) is True:
            async def work():
                from src.storage.backup import choose_browser_import
                if self.operation=="export":
                    await manager.refresh()
                    text=manager.export_json(f"slot_{slot}")
                    import json
                    text=json.dumps(json.loads(text),ensure_ascii=True,indent=4)
                    manager.browser_store.bridge.download(f"scape-slot-{slot}.json",text)
                    return "Backup exportado."
                text=await choose_browser_import(manager.browser_store)
                if text is None:return "Importação cancelada."
                await manager.run(None,lambda m,d:m.import_json(text,slot,replace))
                return "Backup importado e validado."
            self.scene_manager.submit(work,complete,lambda error:setattr(self,"message",str(error)))
        else:
            try:
                from src.storage.backup import desktop_file
                filename=desktop_file(self.operation)
                if not filename:return
                if self.operation=="export":
                    Path(filename).write_text(manager.export_json(f"slot_{slot}"),encoding="utf-8")
                else:
                    manager.import_json(Path(filename).read_text(encoding="utf-8-sig"),slot,replace)
                complete("Backup exportado." if self.operation=="export" else "Backup importado e validado.")
            except Exception as error:
                self.message=str(error)

