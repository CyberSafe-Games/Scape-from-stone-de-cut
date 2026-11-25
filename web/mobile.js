/* Toque sobre a composição nativa. Nenhuma HUD ou tela paralela é construída. */
(() => {
  const root=document.querySelector("#mobile-ui"),rotate=document.querySelector("#mobile-rotate");
  const safe=document.createElement("div");
  safe.style.cssText="position:fixed;visibility:hidden;pointer-events:none;padding:env(safe-area-inset-top,0px) env(safe-area-inset-right,0px) env(safe-area-inset-bottom,0px) env(safe-area-inset-left,0px)";
  document.body.append(safe);
  let queue=[],epoch="",generation=0,model=null,pressed=null,last="",lastPublish=0;
  const coarse=()=>matchMedia("(pointer: coarse)").matches||(navigator.maxTouchPoints>0&&!matchMedia("(pointer: fine)").matches);
  function viewport(){
    const vv=visualViewport,style=getComputedStyle(safe);
    return {width:vv?.width||innerWidth,height:vv?.height||innerHeight,
      insets:[style.paddingTop,style.paddingRight,style.paddingBottom,style.paddingLeft].map(v=>parseFloat(v)||0),
      coarse:coarse(),compact:coarse()||(vv?.width||innerWidth)<1000||(vv?.height||innerHeight)<600};
  }
  function cancel(){pressed=null;generation++;queue=[];window.dispatchEvent(new Event("scape-pointer-cancel"));}
  function resize(){
    const v=viewport();rotate.hidden=!(v.coarse&&v.height>v.width);
    document.documentElement.classList.toggle("compact",v.compact);
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
      const shade=document.createElement("div");shade.className="art-inspection";
      shade.setAttribute("role","dialog");shade.setAttribute("aria-label",data.selection.title);shade.setAttribute("aria-modal","true");
      const art=document.createElement("section");art.className="art-inspection-content";
      if(data.selection.image){
        const image=document.createElement("img");image.src=data.selection.image;image.alt=data.selection.title;image.draggable=false;art.append(image);
      }else{
        const details=document.createElement("p");details.className="art-status-description";
        details.textContent=data.selection.title+"\n"+data.selection.text;art.append(details);
      }
      const actions=document.createElement("nav");actions.className="art-inspection-actions";
      data.selection.actions.forEach(a=>actions.append(button(a)));art.prepend(actions);
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
  document.addEventListener("pointerdown",e=>{
    if(!viewport().compact||e.target.id!=="canvas")return;
    e.preventDefault();e.stopImmediatePropagation();
    if(model?.selection||model?.pending||!rotate.hidden)return;
    pressed={id:e.pointerId,start:position(e)};e.target.setPointerCapture?.(e.pointerId);
  },true);
  document.addEventListener("pointerup",e=>{
    if(!pressed||e.pointerId!==pressed.id)return;
    e.preventDefault();e.stopImmediatePropagation();
    const p=position(e),start=pressed.start;pressed=null;
    const slider=model?.sliders?.some(r=>start[0]>=r[0]&&start[0]<=r[0]+r[2]&&start[1]>=r[1]-50&&start[1]<=r[1]+r[3]+50);
    if(slider||Math.hypot(p[0]-start[0],p[1]-start[1])<90)emit("native-tap",p);
  },true);
  document.addEventListener("pointercancel",cancel,true);
  window.addEventListener("blur",cancel);
  document.addEventListener("visibilitychange",()=>{if(document.hidden)cancel();});
  window.addEventListener("resize",resize);visualViewport?.addEventListener("resize",resize);
  window.addEventListener("orientationchange",resize);resize();
})();
