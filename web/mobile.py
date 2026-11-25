"""Apresentação compacta do host; ações delegadas às cenas e transações nativas."""
from collections import OrderedDict
from io import BytesIO
import base64
import json
import pygame
from src.config.responsive_layout import resolve_layout
from src.ui.inspection_controller import InspectionController

class MobileInterface:
    def __init__(self, scenes, bridge):
        self.scenes,self.bridge=scenes,bridge
        self.layout=resolve_layout(1920,1080)
        self.inspection=InspectionController()
        self.selection=None
        self.callbacks={}
        self.images=OrderedDict()
        self.scene_key=None
        self.epoch=0
        self.last_model=None
        self.tab="reserve"
        self.page=0
        self.generation=-1
        self.last_view=None

    def cancel(self):
        self.selection=None
        self.inspection.clear()
        scene=self.scenes.current_scene
        for obj in (scene,*self.scenes.modal_stack):
            if hasattr(obj,"dragging"):obj.dragging=None
        self.callbacks.clear()

    def poll(self):
        target=self.scenes.modal_stack[-1] if self.scenes.modal_stack else self.scenes.current_scene
        if self.scene_key is not None and self.scene_key!=(id(self.scenes.current_scene),id(target)):
            self.cancel()
        state=json.loads(str(self.bridge.viewport()))
        layout=resolve_layout(state["width"],state["height"],web=True,coarse=state["coarse"],insets=state.get("insets",(0,0,0,0)))
        if state["generation"]!=self.generation or layout!=self.layout:
            self.cancel()
            self.generation=state["generation"]
        changed=layout.compact!=self.layout.compact
        self.layout=layout
        self.scenes.window.configure_viewport(layout)
        from src.config.visual_quality import set_compact_effects
        set_compact_effects(layout.compact)
        commands=json.loads(str(self.bridge.drain()))
        if not layout.compact:
            scene=self.scenes.current_scene
            if "_mobile_page_size" in vars(scene):
                scene.PAGE_SIZE=scene._mobile_page_size
                del scene._mobile_page_size
                if hasattr(scene,"_set_page"):scene._set_page(scene.page)
            return
        if layout.portrait_blocked:return
        if changed:
            self.last_model=None
        for command in commands:
            if (command.get("epoch")!=str(self.epoch) or
                command.get("generation")!=self.generation or self.scenes.saving):continue
            callback=self.callbacks.get(command["id"])
            if callback:
                self.scenes.audio_manager.unlock_after_interaction()
                callback(command.get("value"))
                # Um gesto confirmado invalida a lista anterior, inclusive duplo clique.
                self.callbacks.clear()
                break

    def image(self, source, key, bounds=(316,489)):
        if source is None:return None
        if key not in self.images:
            size=source.get_rect().fit(pygame.Rect((0,0),bounds)).size
            image=pygame.transform.smoothscale(source,size)
            output=BytesIO();pygame.image.save(image,output,"preview.png")
            self.images[key]="data:image/png;base64,"+base64.b64encode(output.getvalue()).decode("ascii")
            if len(self.images)>48:self.images.popitem(last=False)
        return self.images[key]

    def card_image(self, card):
        return self.image(self.scenes.assets.get_card_image(card.name,getattr(card,"level",1),
            cost=card.cost,description=card.description),
            ("card",card.name,getattr(card,"level",1),card.cost,card.description))

    def click(self,scene,rect):
        # Apenas eventos programáticos autenticados pelo registro de ações.
        scale,x,y=self.scenes.window.get_scale_and_offset()
        pos=(round(rect.centerx*scale+x),round(rect.centery*scale+y))
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos,touch=False))
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP,button=1,pos=pos,touch=False))

    def key(self,scene,key):
        scene.handle_event(pygame.event.Event(pygame.KEYDOWN,key=key,unicode=""))

    def button(self,label,callback,*,disabled=False,key=None):
        key=key or "action-"+str(len(self.callbacks))
        self.callbacks[key]=lambda value:callback()
        return dict(id=key,label=label,disabled=disabled)

    def select(self,title,text,image,callback=None,label="CONFIRMAR"):
        self.inspection.touch_select(title)
        self.selection=dict(title=title,text=text,image=image,callback=callback,label=label)

    def item(self,key,title,text,image,callback=None,label="CONFIRMAR"):
        button=self.button(title,lambda:self.select(title,text,image,callback,label),key=key)
        button["image"]=image
        return button

    def native_button(self,scene,attr,label):
        rect=getattr(scene,attr,None)
        if isinstance(rect,pygame.Rect):
            return self.button(label,lambda:self.click(scene,rect))
        return None

    def publish(self):
        if not self.layout.compact:return
        scene=self.scenes.modal_stack[-1] if self.scenes.modal_stack else self.scenes.current_scene
        key=(id(self.scenes.current_scene),id(scene))
        if key!=self.scene_key:
            self.cancel();self.images.clear();self.page=0;self.tab="reserve"
            self.scene_key=key
        self.callbacks={}
        model=dict(kind="management",title="SCAPE FROM STONE",navigation=[],items=[],actions=[],tabs=[],
            pending=self.scenes.saving,message=self.scenes.storage_error or "")
        self.model=model
        self.build(scene)
        if model["kind"]!="battle":
            visuals=getattr(scene,"visuals",None)
            name=getattr(visuals,"background",None)
            source=self.scenes.assets.get_service_image(name) if isinstance(name,str) else getattr(visuals,"source",None)
            if source is None:source=self.scenes.assets.background
            if isinstance(source,pygame.Surface):
                model["background"]=self.image(source,("background",type(scene).__name__),(960,540))
        guide=getattr(scene,"management_guide",None)
        if guide:
            model["navigation"].append(self.button("AJUDA",guide.open))
            if guide.active:
                step=guide.steps[guide.index]
                targets={"shop":("items","actions","navigation"),
                         "backpack":("items","tabs","items","tabs"),
                         "workshop":("items","items","actions")}
                model["guide"]=dict(title=f"{guide.index+1}/{len(guide.steps)} · {step.title}",
                    text=step.text.replace("Clique","Toque").replace("clique","toque").replace("à esquerda","na área de seleção")+" Toque para inspecionar e confirme no botão de ação.",target=targets[guide.key][guide.index],
                    actions=[self.button("ANTERIOR",lambda:setattr(guide,"index",max(0,guide.index-1))),
                             self.button("PRÓXIMO" if guide.index+1<len(guide.steps) else "CONCLUIR",guide.advance),
                             self.button("FECHAR",guide.finish)])
        if guide and guide.active:
            allowed={b["id"] for b in model["guide"]["actions"]}
            self.callbacks={k:v for k,v in self.callbacks.items() if k in allowed}
        if self.selection and not (guide and guide.active):
            selected=self.selection
            def close():self.selection=None;self.inspection.clear()
            buttons=[self.button("FECHAR",close,key="close-inspection")]
            for label,image in selected.get("variants",()):
                buttons.append(self.button(label,lambda img=image:self.selection.update(image=img)))
            if selected["callback"]:
                def confirm():
                    if not self.inspection.confirm(selected["title"]):return
                    close()
                    selected["callback"]()
                buttons.insert(0,self.button(selected["label"],confirm,key="confirm-inspection"))
            model["selection"]={k:selected[k] for k in ("title","text","image")}
            model["selection"]["actions"]=buttons
        # A época só muda ao alterar conteúdo/ações; FPS e relógios não invalidam gestos.
        signature=json.dumps(model,ensure_ascii=True,sort_keys=True)
        if signature!=self.last_model:
            self.epoch+=1;self.last_model=signature
        else:return
        model["epoch"]=str(self.epoch)
        self.bridge.publish(json.dumps(model,ensure_ascii=True))

    def build(self,scene):
        from src.scenes.battle_scene import BattleScene
        from src.scenes.shop_scene import ShopScene
        from src.scenes.backpack_scene import BackpackScene
        from src.scenes.roguelite_scene import RogueliteScene
        from src.scenes.options_scene import OptionsScene
        from src.scenes.map_scene import MapScene
        from src.scenes.menu_scene import MenuScene
        from src.scenes.save_selection_scene import SaveSelectionScene
        from src.scenes.cutscene_scene import CutsceneScene
        from src.scenes.cemetery_modal import CemeteryModal
        m=self.model
        if type(scene).__name__=="LoadingScene":
            m["kind"]="loading";m["title"]="PREPARANDO A JORNADA"
            m["message"]=self.scenes.assets.label
            m["progress"]=self.scenes.assets.progress
            if self.scenes.storage_error:m["actions"]=[self.button("TENTAR NOVAMENTE",scene.retry)]
            return
        data=getattr(scene,"save_data",None)
        if data:
            p=data["progresso"]
            m["message"]=self.scenes.storage_error or str(getattr(scene,"message",getattr(scene,"notice",getattr(scene,"error",""))))
            m["hud"]=f'{p.get("moedas",0)} ouro'
        if isinstance(scene,BattleScene):return self.battle(scene)
        if isinstance(scene,ShopScene):return self.shop(scene)
        if isinstance(scene,BackpackScene):return self.backpack(scene)
        if isinstance(scene,RogueliteScene):return self.workshop(scene)
        if isinstance(scene,OptionsScene):return self.options(scene)
        if isinstance(scene,MapScene):
            from src.systems.territory_map import TERRITORIES,ROAD_FIGHTS,status
            m["title"]="TERRITÓRIOS"
            if scene.guide_open:
                m["paragraph"]="Escolha um território e conclua dois encontros antes de enfrentar seu chefe. Prepare o deck na Mochila e visite o Mercado."
                m["actions"].append(self.button("ENTENDI",scene._dismiss_guide));return
            for territory in TERRITORIES:
                def choose(t=territory):
                    scene.selected=t.id
                    count=data["progresso"].get("encontros_por_territorio",{}).get(t.id,0)
                    scene.selected_encounter=count if count<ROAD_FIGHTS and status(data,t.id)!="completed" else None
                m["items"].append(self.button(territory.title,choose,disabled=status(data,territory.id)=="locked"))
            from src.systems.territory_map import encounter_status
            for index,label in ((0,"ENCONTRO 1"),(1,"ENCONTRO 2"),(None,"CHEFE")):
                m["tabs"].append(self.button(label,lambda i=index:setattr(scene,"selected_encounter",i),
                    disabled=encounter_status(data,scene.selected,index)=="locked"))
            m["paragraph"]=f"Território selecionado: {scene.selected}"
            for attr,label in (("back_button","MENU"),("backpack_button","MOCHILA"),("shop_button","LOJA"),("play_button","JOGAR")):
                m["actions"].append(self.native_button(scene,attr,label))
            return
        if isinstance(scene,MenuScene):
            m["title"]="SCAPE FROM STONE"
            m["paragraph"]="A floresta resiste. Prepare sua estratégia e defenda sua terra."
            m["items"]=[self.native_button(scene,"play_button","JOGAR"),self.native_button(scene,"options_button","CONFIGURAÇÕES")]
            return
        if isinstance(scene,SaveSelectionScene):
            m["title"]="SUAS JORNADAS"
            for i,rect in enumerate(scene.card_rects):
                m["items"].append(self.button(f"JORNADA {i+1}",lambda i=i:scene._select(i)))
                m["items"].append(self.button(f"EXCLUIR {i+1}",lambda i=i:scene._request_delete(i)))
            m["actions"].append(self.native_button(scene,"back_button","VOLTAR"))
            for op,rect in scene.backup_buttons.items():
                m["actions"].append(self.button("EXPORTAR" if op=="export" else "IMPORTAR",lambda r=rect:self.click(scene,r)))
            return
        if isinstance(scene,CutsceneScene):
            m["title"]="MEMÓRIAS DA TRIBO";m["kind"]="battle"
            frame=scene.scenes[scene.index]
            dialogues=frame.get("dialogues",[])
            if dialogues:
                speaker,text=dialogues[min(scene._dialogue_index,len(dialogues)-1)]
                m["paragraph"]=speaker+" · "+text
            else:m["paragraph"]=frame.get("text","")
            m["actions"]=[self.native_button(scene,"skip_button","PULAR / CONTINUAR"),
                          self.button("PRÓXIMA",lambda:self.key(scene,pygame.K_SPACE))]
            return
        if isinstance(scene,CemeteryModal):
            m["title"]="CEMITÉRIO"
            for i,card in enumerate(scene.engine.hand):
                m["items"].append(self.item(f"cemetery-{i}",card.name,card.description,self.card_image(card),
                    lambda i=i:setattr(scene,"selected_index",i),"SELECIONAR"))
            for attr,label in (("discard_button_rect","DESCARTAR · 1 ENERGIA"),("swap_button_rect","TROCAR"),("close_button_rect","FECHAR")):
                m["actions"].append(self.native_button(scene,attr,label))
            return
        # Modais nativos: confirmação, pausa, biblioteca e backup conservam handlers.
        titles={"PauseMenuModal":"JORNADA PAUSADA","BackupModal":"BACKUP DA JORNADA","GuideLibraryScene":"GUIAS ANCESTRAIS"}
        m["title"]=getattr(scene,"title",titles.get(type(scene).__name__,"SCAPE FROM STONE"))
        m["paragraph"]=getattr(scene,"message","")
        labels={"confirm_button":getattr(scene,"confirm_label","CONFIRMAR"),"cancel_button":"CANCELAR",
            "resume_button":"RETORNAR AO COMBATE","continue_button":"RETORNAR AO COMBATE",
            "exit_button":getattr(scene,"exit_label","SAIR"),"options_button":"CONFIGURAÇÕES","menu_button":"MENU",
            "back_button":"VOLTAR","back":"VOLTAR","previous":"ANTERIOR","following":"PRÓXIMO",
            "close_button":"FECHAR","close":"FECHAR","new_run_rect":"PREPARAR NOVA RUN"}
        for attr,label in labels.items():
            b=self.native_button(scene,attr,label)
            if b:m["actions"].append(b)
        if hasattr(scene,"tabs"):
            for name,rect in scene.tabs.items():m["tabs"].append(self.button(str(name).upper(),lambda r=rect:self.click(scene,r)))
            if hasattr(scene,"key") and hasattr(scene,"index"):
                from src.ui.management_guide import steps_for
                step=steps_for(None,scene.key)[scene.index]
                m["paragraph"]=step.title+"\n"+step.text
        # Backup usa nomes export_rect/import_rect definidos no modal.
        for attr,rect in vars(scene).items():
            if isinstance(rect,pygame.Rect) and ("export" in attr or "import" in attr):
                m["actions"].append(self.button("EXPORTAR" if "export" in attr else "IMPORTAR",lambda r=rect:self.click(scene,r)))
        if type(scene).__name__=="BackupModal":
            for i,rect in enumerate(scene.buttons):
                m["items"].append(self.button(f"ESPAÇO {i+1}",lambda r=rect:self.click(scene,r)))
        if not m["actions"]:
            m["actions"].append(self.button("CONTINUAR",lambda:self.key(scene,pygame.K_SPACE)))
            m["navigation"].append(self.button("VOLTAR",lambda:self.key(scene,pygame.K_ESCAPE)))
        m["actions"]=[b for b in m["actions"] if b]

    def battle(self,s):
        e=s.engine;m=self.model
        from src.config.boss_names import boss_display_name
        from src.ui.status_badges import INFO
        from src.models.entity import STACK_STATUS_DAMAGE
        m["title"]=boss_display_name(e.enemy.name)
        m["kind"]="battle"
        m["hud"]=f"Jaum {e.player.hp}/{e.player.max_hp}  ·  Inimigo {e.enemy.hp}/{e.enemy.max_hp}\nEnergia {e.energy} · Ultimate {e.ultimate_charge}/20"
        m["combatants"]=[]
        for entity,label in ((e.player,"JAUM"),(e.enemy,boss_display_name(e.enemy.name))):
            portrait=self.scenes.assets.get_character_portrait(entity.name,(96,128))
            m["combatants"].append(dict(name=label,hp=entity.hp,max_hp=entity.max_hp,
                portrait=self.image(portrait,("portrait",entity.name),(96,128))))
        m["navigation"]=[self.button("MENU",s._open_menu_confirmation)]
        overlay=getattr(s,"overlay",None)
        if overlay and overlay.is_active:
            
            m["paragraph"]=overlay.current_step.title+"\n"+"\n".join(overlay.current_step.lines)
            m["actions"]=[self.button("CONTINUAR",overlay.next_step),
                          self.button("PULAR GUIA",overlay.skip)]
            return
        if s.boss_dialogue and not s.boss_dialogue.finished:
            m["actions"]=[self.button("CONTINUAR DIÁLOGO",lambda:self.key(s,pygame.K_SPACE))];return
        if hasattr(s,"_complete_tutorial") and e.state=="victory":
            m["actions"]=[self.button("CONCLUIR TUTORIAL",s._complete_tutorial)]
            return
        if s._victory_ready:
            m["title"]="ESPÓLIOS DA VITÓRIA";m["kind"]="management"
            from src.systems.card_catalog import CARD_BY_NAME
            for option,rect in s.reward_view.offers(e,s._reward_progress()):
                kind,value=option
                card=e.reward_cards[value] if kind=="card" else CARD_BY_NAME[value]
                can_choose=s.reward_view.enabled(option,e,s._reward_progress())
                item=self.item(f"reward-{kind}-{value}",card.name,card.description,self.card_image(card),
                    (lambda o=option:s.reward_view.confirm(o)) if can_choose else None,"ESCOLHER")
                m["items"].append(item)
            m["actions"]=[self.button("MATERIAIS / CARTAS",lambda:self.click(s,s.reward_view.MATERIALS)),
                          self.button("PULAR",lambda:s.reward_view.confirm(("skip",None)))]
            return
        if s._game_over_ready:
            m["actions"]=[self.button("NOVA RUN",lambda:self.key(s,pygame.K_r)),
                          self.button("MENU",lambda:self.key(s,pygame.K_ESCAPE))]
            return
        from src.systems.enemy_intents import preview_intents
        for i,intent in enumerate(preview_intents(e)):
            art=self.scenes.assets.get_intent_art(e.enemy.name,intent.action.visual_effect,special=intent.special)
            image=self.image(art,("intent",e.enemy.name,intent.description))
            m["navigation"].append(self.button(f"INTENÇÃO {i+1}",lambda i=intent,img=image:self.select(
                i.action.name,i.description,img)))
        for entity,label in ((e.player,"JAUM"),(e.enemy,"INIMIGO")):
            states=[]
            for name,state in entity.statuses.items():
                title,description=INFO.get(name,(name,""))
                stacks=state["potency"];turns=state["turns"]
                description+=f"\nStacks/intensidade: {stacks}. Turnos restantes: {turns}."
                if name in STACK_STATUS_DAMAGE:description+=f" Dano por gatilho: {stacks*STACK_STATUS_DAMAGE[name]}."
                states.append(title+": "+description)
            if entity.block:states.append(f"Escudo: {entity.block} · {entity.block_turns} turnos.")
            if entity.strength:states.append(f"Força: +{entity.strength}")
            if states:m["navigation"].append(self.button(label+" · STATUS",lambda st=states:self.select("EFEITOS ATIVOS","\n\n".join(st),None)))
        for i,card in enumerate(e.hand):
            def play(index=i,original=card):
                if index<len(e.hand) and e.hand[index] is original:
                    rect=s._get_battle_hand_rects()[index]
                    self.click(s,rect)
            m["items"].append(self.item(f"hand-{i}",f"{card.name} · {card.cost} E",card.description,
                self.card_image(card),play,"JOGAR"))
        if s._ultimate_in_hand():
            uid=e.player.ultimate_id if hasattr(e.player,"ultimate_id") else s.save_data["progresso"]["ultimate_equipada"]
            art=self.scenes.assets.get_ultimate_image(uid,energy_cost=2)
            m["items"].append(self.item("ultimate",e.active_ultimate_name,e.active_ultimate_description,
                self.image(art,("ultimate",uid)),lambda:self.click(s,s._get_battle_hand_rects()[-1]),"JOGAR ULTIMATE"))
        m["actions"]=[self.button("CEMITÉRIO",lambda:self.click(s,s.cemetery_button_rect),
            disabled=e.state!="player_turn"),self.button("FIM DO TURNO",lambda:self.click(s,s.end_turn_rect),
            disabled=e.state!="player_turn" or s.entity_view.player_action is not None)]

    def shop(self,s):
        from src.systems.shop_system import CARD_OFFERS,CARD_PRICES,next_heal_price
        m=self.model;m["title"]="MERCADO SILENCIOSO"
        if "_mobile_page_size" not in vars(s):s._mobile_page_size=s.PAGE_SIZE
        s.PAGE_SIZE=self.layout.cards_per_page;s._set_page(s.page)
        for name in s.card_rects:
            card=CARD_OFFERS[name]
            m["items"].append(self.item("shop-"+name,name,card.description+f"\nPreço: {CARD_PRICES[name]} ouro.",
                self.card_image(card),lambda n=name:self.click(s,s.offer_rects[n]),"COMPRAR"))
        for attr,label in (("back_button","MAPA"),("workshop_button","ALTAR"),("heal_button","CURAR")):
            m["navigation"].append(self.native_button(s,attr,label))
        self.pages(s,s.page_count)
        m["paragraph"]="Escolha uma carta para inspecionar antes de comprar."
        m["navigation"].append(self.button("CONFIGURAÇÕES",s.open_options_modal))

    def pages(self,s,count):
        self.model["actions"].extend([
            self.button("ANTERIOR",lambda:self.turn_page(s,-1),disabled=s.page<=0),
            self.button(f"PRÓXIMA · {s.page+1}/{count}",lambda:self.turn_page(s,1),disabled=s.page+1>=count)])

    def turn_page(self,s,delta):
        if hasattr(s,"_set_page"):s._set_page(s.page+delta)
        else:s._page(delta)
        self.selection=None

    def backpack(self,s):
        from src.systems.roguelite import instance_card
        from src.models.effects.ultimate_effect import ULTIMATE_METADATA
        m=self.model;p=s.save_data["progresso"]
        m["title"]="MOCHILA ANCESTRAL"
        m["hud"]+=f" · Deck {sum(n is not None for n in s.draft_slots)}/18 · mínimo 6"
        m["navigation"]=[self.button("VOLTAR",s._back),self.button("CONFIGURAÇÕES",s.open_options_modal)]
        for key,label in (("reserve","RESERVA"),("equipped","EQUIPADO"),("ultimates","ULTIMATES")):
            m["tabs"].append(self.button(label,lambda k=key:self.change_tab(k)))
        if self.tab=="ultimates":
            from src.systems.deck_loadout import equip_ultimate
            for uid in p["ultimates_desbloqueadas"]:
                meta=ULTIMATE_METADATA[uid]
                def equip(uid=uid):
                    s.persist_command(lambda manager,data:equip_ultimate(manager,data,uid),lambda r:s._notice(*r))
                m["items"].append(self.item("equip-ult-"+uid,meta["name"],meta["description"]+"\nCusto 2 · carga 20",
                    self.image(self.scenes.assets.get_ultimate_image(uid,energy_cost=2),("ultimate",uid)),equip,"EQUIPAR"))
            return
        if self.tab=="equipped":
            draft=s._inventory_preview()
            for i,name in enumerate(s.draft_slots):
                if not name:continue
                cid=draft["copy_slots"][i]
                copy=next(c for c in draft["copies"] if c["id"]==cid)
                card=instance_card(copy)
                m["items"].append(self.item(f"slot-{i}",f"{i+1} · {name} · LV{card.level}",card.description,
                    self.card_image(card),lambda i=i:s._remove_slot(i),"REMOVER"))
            m["actions"].append(self.button("ESVAZIAR DECK",s._request_clear_deck))
            m["actions"].append(self.button("DECK ALEATÓRIO",s._request_random_deck))
            return
        if "_mobile_page_size" not in vars(s):s._mobile_page_size=s.PAGE_SIZE
        s.PAGE_SIZE=self.layout.cards_per_page;s._set_page(s.page)
        for name in s.cards:
            card=s._collection_card(name)
            m["items"].append(self.item("reserve-"+name,name+f" · LV{card.level}",card.description,
                self.card_image(card),lambda n=name:s._add(n),"EQUIPAR"))
        self.pages(s,s.page_count)
        for key,label in (("owned","ADQUIRIDAS"),("type","TIPO"),("cost","ENERGIA"),("level","NÍVEL")):
            m["tabs"].append(self.button(label,lambda k=key:s._cycle_filter(k)))

    def change_tab(self,key):
        self.tab=key;self.selection=None;self.page=0

    def workshop(self,s):
        from src.systems.roguelite import instance_card,UPGRADE_PRICES,PREPARATION
        from src.scenes.roguelite_scene import upgrade_changes
        m=self.model;p=s.save_data["progresso"]
        m["title"]="PREPARAÇÃO" if s.preparation else "ALTAR ANCESTRAL"
        m["navigation"]=[self.button("VOLTAR",s._back),self.button("CONFIGURAÇÕES",s.open_options_modal)]
        if s.preparation:
            for name in p["cartas_colecao"]:
                m["items"].append(self.button("PREPARAR "+name,lambda n=name:s._choose_preparation(n)))
            m["actions"]=[self.button("INICIAR NOVA RUN",s._new_run)]
            from src.systems.roguelite import purchase_permanent
            for key in ("vida","energia","preparacao"):
                m["actions"].append(self.button(str(key),lambda k=key:s.persist_command(
                    lambda manager,data:purchase_permanent(manager,data,k),s._notify)))
            return
        names=[name for name in p["cartas_colecao"] if name in UPGRADE_PRICES]
        for copy in p["copies"]:
            if copy["name"] not in names:continue
            card=instance_card(copy)
            def compare(copy=copy):
                s.selected_copy_id=copy["id"]
                before=instance_card(dict(copy,level=1));after=instance_card(dict(copy,level=2))
                text="ANTES · "+before.description+"\n\nDEPOIS · "+after.description+"\n\n"+"\n".join(upgrade_changes(before,after))
                text+=f"\nMateriais: {p['materials'].get(copy['name'],0)}/3 · Preço: {UPGRADE_PRICES[copy['name']]} ouro."
                self.select(copy["name"]+" · Antes → Depois",text,self.card_image(after),s._upgrade_selected,"APRIMORAR")
                self.selection["variants"]=[("ANTES · LV1",self.card_image(before)),("DEPOIS · LV2",self.card_image(after))]
            m["items"].append(self.button(copy["name"]+f" · LV{copy['level']} · {copy['id'][-4:]}",compare))
        selected=s._selected_copy()
        m["paragraph"]="Selecione uma cópia para comparar os efeitos reais antes de aprimorar."
        if selected:
            m["actions"].append(self.button("MATERIAL +1 · 15 OURO",s._purchase_material))
        m["actions"].append(self.button("REVER COMPARAÇÃO",lambda:None,disabled=True))

    def options(self,s):
        from src.scenes.options_scene import AUDIO_ROWS
        m=self.model;m["title"]="SANTUÁRIO DOS AJUSTES"
        m["navigation"]=[self.button("RETORNAR",s._back)]
        for tab in s.tab_rects:
            label={"audio":"ÁUDIO","video":"VÍDEO","game":"JOGO","controls":"CONTROLES"}[tab]
            m["tabs"].append(self.button(label,lambda t=tab:s._switch_tab(t)))
        if s.tab=="audio":
            ranges=[]
            for key,label,_ in AUDIO_ROWS:
                rid="volume-"+key
                self.callbacks[rid]=lambda value,k=key:s._set_audio(k,max(0,min(1,float(value))))
                ranges.append(dict(id=rid,label=label,value=round(s.preferences.get(key)*100),
                    minus=self.button("−",lambda k=key:s._set_audio(k,max(0,s.preferences.get(k)-.05))),
                    plus=self.button("+",lambda k=key:s._set_audio(k,min(1,s.preferences.get(k)+.05)))))
            m["ranges"]=ranges
        elif s.tab=="video":
            m["items"]=[self.button("TELA CHEIA",s.window_manager.toggle_fullscreen),self.button("EXIBIR FPS",s._toggle_fps)]
        elif s.tab=="game":
            for speed in s.enemy_speed_buttons:
                m["items"].append(self.button("VELOCIDADE "+str(speed),lambda k=speed:s._select_enemy_speed(k)))
            m["items"].extend([self.button("NÚMEROS DE DANO",s._toggle_damage_numbers),
                self.button("REVER TUTORIAIS",lambda:self.click(s,s.review_button)),
                self.button("SAIR PARA O MENU",s._request_exit)])
        else:m["paragraph"]="Toque uma vez para inspecionar. Confirme em JOGAR, COMPRAR ou EQUIPAR. Use MENU para pausar. Jogue em paisagem."
        m["actions"]=[self.button("RESTAURAR PADRÕES",s._restore_defaults)]

