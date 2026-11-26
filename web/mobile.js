/* Toque sobre a composição nativa. Nenhuma HUD ou tela paralela é construída. */
(() => {
  const root=document.querySelector("#mobile-ui"),rotate=document.querySelector("#mobile-rotate");
  const safe=document.createElement("div");
  safe.style.cssText="position:fixed;visibility:hidden;pointer-events:none;padding:env(safe-area-inset-top,0px) env(safe-area-inset-right,0px) env(safe-area-inset-bottom,0px) env(safe-area-inset-left,0px)";
  document.body.append(safe);
  let queue=[],epoch="",generation=0,model=null,pressed=null,last="",lastPublish=0,gestureSequence=0;
  const HOLD_MS=220,MOVE_PX=12;
  const coarse=()=>matchMedia("(pointer: coarse)").matches||(navigator.maxTouchPoints>0&&!matchMedia("(pointer: fine)").matches);
  function viewport(){
    const vv=visualViewport,style=getComputedStyle(safe);
    return {width:vv?.width||innerWidth,height:vv?.height||innerHeight,
      insets:[style.paddingTop,style.paddingRight,style.paddingBottom,style.paddingLeft].map(v=>parseFloat(v)||0),
      coarse:coarse(),compact:coarse()||(vv?.width||innerWidth)<1000||(vv?.height||innerHeight)<600};
  }
  function dismissHold(){if(model?.selection?.holding){root.replaceChildren();model.selection=null;last="";}}
  function cancel(){if(pressed)clearTimeout(pressed.timer);pressed=null;generation++;queue=[];
    dismissHold();window.dispatchEvent(new Event("scape-pointer-cancel"));}
  function resize(){
    const v=viewport();rotate.hidden=!(v.coarse&&v.height>v.width);
    document.documentElement.classList.toggle("compact",v.compact);
    document.documentElement.classList.toggle("touch-mobile",v.coarse);
    document.documentElement.classList.toggle("portrait-blocked",!rotate.hidden);
    root.hidden=!v.compact;cancel();window.scapePlatform?.refresh?.();
  }
  function emit(id,value){if(!model?.pending)queue.push({id,value,epoch,generation});}
  function button(item){
    const b=document.createElement("button");b.type="button";b.textContent=item.label;
    b.dataset.action=item.id;b.disabled=Boolean(item.disabled||model.pending);
    b.addEventListener("click",e=>{e.stopPropagation();emit(item.id);});return b;
  }
  function render(data){
    model=data;epoch=data.epoch;root.dataset.kind=data.kind;
    document.documentElement.dataset.mobileScene=data.scene;
    if(data.edge_image)document.documentElement.style.setProperty("--mobile-edge-art","url("+data.edge_image+")");
    const key=JSON.stringify([data.selection,data.pending]);
    if(key===last)return;last=key;root.replaceChildren();root.dataset.kind=data.kind;
    if(data.selection){
      const shade=document.createElement("div");shade.className="art-inspection"+(data.selection.holding?" hold-inspection":"");
      shade.setAttribute("role","dialog");shade.setAttribute("aria-label",data.selection.title);shade.setAttribute("aria-modal","true");
      const art=document.createElement("section");art.className="art-inspection-content";
      if(data.selection.image){
        const image=document.createElement("img");image.src=data.selection.image;image.alt=data.selection.title;image.draggable=false;art.append(image);
      }else{
        const details=document.createElement("p");details.className="art-status-description";
        details.textContent=data.selection.title+"\n"+data.selection.text;art.append(details);
      }
      const actions=document.createElement("nav");actions.className="art-inspection-actions";
      if(!data.selection.holding){data.selection.actions.forEach(a=>actions.append(button(a)));art.prepend(actions);}
      shade.append(art);root.append(shade);
    }
    root.hidden=!viewport().compact;
  }
  window.scapeMobile={
    viewport:()=>JSON.stringify({...viewport(),generation,blocked:!rotate.hidden}),
    drain:()=>{const copy=queue;queue=[];return JSON.stringify(copy);},
    publish:raw=>{render(JSON.parse(raw));lastPublish=performance.now();},
    cancel,status:()=>({epoch,generation,queued:queue.length,lastPublish})
  };
  function position(e){
    const r=document.querySelector("#canvas").getBoundingClientRect();
    return [(e.clientX-r.left)*1920/r.width,(e.clientY-r.top)*1080/r.height];
  }
  function beginHold(press){
    if(pressed!==press||press.cancelled||press.held)return;
    press.held=true;
    emit("native-hold-start",{point:press.start,gesture:press.gesture});
  }
  document.addEventListener("pointerdown",e=>{
    if(!viewport().compact||e.target.id!=="canvas")return;
    e.preventDefault();e.stopImmediatePropagation();
    if(pressed){cancel();return;}
    if(model?.selection||model?.pending||!rotate.hidden)return;
    const start=position(e);
    const canHold=model?.combat_touch&&(e.pointerType==="touch"||coarse())&&
      model.hold_targets?.some(r=>start[0]>=r[0]&&start[0]<=r[0]+r[2]&&start[1]>=r[1]&&start[1]<=r[1]+r[3]);
    const press=pressed={id:e.pointerId,start,client:[e.clientX,e.clientY],at:performance.now(),
      gesture:++gestureSequence,canHold,cancelled:false,held:false};
    if(canHold)press.timer=setTimeout(()=>beginHold(press),HOLD_MS);
    e.target.setPointerCapture?.(e.pointerId);
  },true);
  document.addEventListener("pointermove",e=>{
    if(!pressed||e.pointerId!==pressed.id)return;
    if(Math.hypot(e.clientX-pressed.client[0],e.clientY-pressed.client[1])>MOVE_PX){
      clearTimeout(pressed.timer);pressed.cancelled=true;
      if(pressed.held){emit("native-hold-end",{gesture:pressed.gesture});dismissHold();pressed.held=false;}
    }
  },true);
  document.addEventListener("pointerup",e=>{
    if(!pressed||e.pointerId!==pressed.id)return;
    e.preventDefault();e.stopImmediatePropagation();
    const press=pressed,p=position(e);clearTimeout(press.timer);
    // Um callback de timer atrasado nunca transforma hold em jogada.
    if(press.canHold&&!press.cancelled&&performance.now()-press.at>=HOLD_MS)beginHold(press);
    if(Math.hypot(e.clientX-press.client[0],e.clientY-press.client[1])>MOVE_PX)press.cancelled=true;
    pressed=null;
    if(press.held){emit("native-hold-end",{gesture:press.gesture});dismissHold();return;}
    const slider=model?.sliders?.some(r=>press.start[0]>=r[0]&&press.start[0]<=r[0]+r[2]&&press.start[1]>=r[1]-50&&press.start[1]<=r[1]+r[3]+50);
    if(slider||!press.cancelled)emit("native-tap",p);
  },true);
  document.addEventListener("contextmenu",e=>{if(coarse()&&e.target.id==="canvas")e.preventDefault();},true);
  document.addEventListener("pointercancel",cancel,true);
  window.addEventListener("blur",cancel);
  document.addEventListener("visibilitychange",()=>{if(document.hidden)cancel();});
  window.addEventListener("resize",resize);visualViewport?.addEventListener("resize",resize);
  window.addEventListener("orientationchange",resize);resize();
})();
