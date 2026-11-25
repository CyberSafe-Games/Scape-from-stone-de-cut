/* Entrada DOM apenas no modo compacto. Nenhuma regra de combate ou save vive aqui. */
(() => {
  const root=document.querySelector("#mobile-ui"), rotate=document.querySelector("#mobile-rotate");
  const safe=document.createElement("div");
  safe.style.cssText="position:fixed;visibility:hidden;pointer-events:none;padding:env(safe-area-inset-top,0px) env(safe-area-inset-right,0px) env(safe-area-inset-bottom,0px) env(safe-area-inset-left,0px)";
  document.body.append(safe);
  let queue=[], epoch="", last="", model=null, generation=0, pressed=null, lastPublish=0;
  const coarse=()=>matchMedia("(pointer: coarse)").matches || (navigator.maxTouchPoints>0&&!matchMedia("(pointer: fine)").matches);
  function viewport() {
    const vv=window.visualViewport;
    const style=getComputedStyle(safe);
    const insets=[style.paddingTop,style.paddingRight,style.paddingBottom,style.paddingLeft].map(v=>parseFloat(v)||0);
    return {width:vv?.width||innerWidth,height:vv?.height||innerHeight,insets,coarse:coarse(),
      compact:coarse()||(vv?.width||innerWidth)<1000||(vv?.height||innerHeight)<600};
  }
  function cancel() {pressed=null;generation++;queue=[];window.dispatchEvent(new Event("scape-pointer-cancel"));}
  function resize() {
    const v=viewport(), blocked=v.coarse&&v.height>v.width;
    rotate.hidden=!blocked;
    document.documentElement.classList.toggle("compact",v.compact);
    document.documentElement.classList.toggle("portrait-blocked",blocked);
    root.hidden=!v.compact||!model;
    cancel(); window.scapePlatform?.refresh?.();
    if(model)spotlight();
  }
  function emit(id,value) {queue.push({id,value,epoch,generation});}
  function button(item) {
    const b=document.createElement("button");
    b.type="button";b.textContent=item.label;b.dataset.action=item.id;
    b.disabled=Boolean(item.disabled);b.addEventListener("click",e=>{e.stopPropagation();emit(item.id);});
    return b;
  }
  function text(tag,value,cls) {const el=document.createElement(tag);el.textContent=value||"";if(cls)el.className=cls;return el;}
  function spotlight() {
    root.querySelectorAll(".spotlight").forEach(e=>e.classList.remove("spotlight"));
    const target=model?.guide?.target;
    const el=target&&root.querySelector('[data-region="'+target+'"]');
    if(el)el.classList.add("spotlight");
  }
  function render(data) {
    model=data;
    const key=JSON.stringify(data);
    if(key===last)return;
    last=key;epoch=data.epoch;
    // Conservar a posição de leitura/rolagem ao atualizar preço, energia ou seleção.
    const scrolls=[...root.querySelectorAll("[data-scroll]")].map(e=>[e.dataset.scroll,e.scrollTop,e.scrollLeft]);
    root.replaceChildren();root.dataset.kind=data.kind;
    root.style.backgroundImage=data.background ? "linear-gradient(90deg,#07120cd9,#07120c99),url("+data.background+")" : "";
    const header=text("header","","mobile-header");
    header.append(text("h1",data.title));
    if(data.hud)header.append(text("p",data.hud,"hp-text"));
    const nav=document.createElement("nav");nav.dataset.region="navigation";
    (data.navigation||[]).forEach(i=>nav.append(button(i)));
    if(data.combatants){
      header.replaceChildren();header.classList.add("combat-header");
      const entities=data.combatants.map(c=>{
        const block=text("section","","compact-combatant");
        if(c.portrait){const img=document.createElement("img");img.src=c.portrait;img.alt=c.name;block.append(img);}
        const stat=text("div","","compact-vitals");stat.append(text("span",c.name));
        const bar=text("div","","compact-health");
        const fill=text("i","","");fill.style.width=Math.max(0,Math.min(100,100*c.hp/Math.max(1,c.max_hp)))+"%";
        bar.append(fill,text("b",c.hp+"/"+c.max_hp));stat.append(bar);block.append(stat);return block;
      });
      const center=text("div","","compact-center");center.append(nav,text("small",data.hud?.split("\n")[1]||""));
      header.append(entities[0],center,entities[1]);
    }else{header.append(nav);}
    root.append(header);
    const body=text("main","","mobile-body");body.dataset.scroll="body";
    if(data.tabs?.length){const tabs=text("nav","","mobile-tabs");tabs.dataset.region="tabs";data.tabs.forEach(i=>tabs.append(button(i)));body.append(tabs);}
    if(data.message)body.append(text("p",data.message,"mobile-message"));
    const grid=text("div","","mobile-grid");grid.dataset.region="items";
    (data.items||[]).forEach(i=>{
      const b=button(i);b.classList.add("mobile-item");
      if(i.image){const img=document.createElement("img");img.src=i.image;img.alt=i.label;img.draggable=false;b.prepend(img);}
      grid.append(b);
    });body.append(grid);
    (data.ranges||[]).forEach(r=>{
      const row=text("div","","mobile-range");const label=text("label",r.label);label.htmlFor="range-"+r.id;
      const range=document.createElement("input");range.type="range";range.min=0;range.max=100;
      range.value=r.value;range.id=label.htmlFor;range.setAttribute("aria-label",r.label);
      range.addEventListener("change",()=>emit(r.id,Number(range.value)/100));
      row.append(label,button(r.minus),range,button(r.plus));body.append(row);
    });
    if(data.paragraph){body.classList.add("has-paragraph");body.append(text("p",data.paragraph,"mobile-paragraph"));}
    root.append(body);
    const footer=text("footer","","mobile-footer");footer.dataset.region="actions";
    (data.actions||[]).forEach(i=>footer.append(button(i)));root.append(footer);
    if(data.selection) {
      const shade=text("div","","inspection-shade");shade.setAttribute("role","dialog");shade.setAttribute("aria-modal","true");
      shade.setAttribute("aria-label",data.selection.title);
      shade.addEventListener("click",e=>{if(e.target===shade)emit("close-inspection");});
      const panel=text("section","","inspection-panel ancestral-panel");panel.dataset.region="preview";
      if(data.selection.image){const img=document.createElement("img");img.src=data.selection.image;img.alt=data.selection.title;panel.append(img);}
      const content=text("div","","inspection-content");
      content.append(text("h2",data.selection.title),text("p",data.selection.text));
      (data.selection.actions||[]).forEach(i=>content.append(button(i)));
      panel.append(content);shade.append(panel);root.append(shade);
    }
    if(data.guide){
      const box=text("aside","","mobile-guide ancestral-panel");box.setAttribute("role","dialog");
      box.append(text("h2",data.guide.title),text("p",data.guide.text));
      data.guide.actions.forEach(i=>box.append(button(i)));root.append(box);
    }
    if(data.pending){const pending=text("div",data.kind==="loading" ? (data.message+" · "+Math.round(100*(data.progress||0))+"%") : "Confirmando progresso…","mobile-pending");pending.setAttribute("role","status");root.append(pending);}
    root.querySelectorAll("button,input").forEach(el=>{if(data.pending || (data.guide&&!el.closest(".mobile-guide")))el.disabled=true;});
    for(const [key,top,left] of scrolls){const el=root.querySelector('[data-scroll="'+key+'"]');if(el){el.scrollTop=top;el.scrollLeft=left;}}
    spotlight();root.hidden=!viewport().compact;
  }
  window.scapeMobile={
    viewport:()=>JSON.stringify({...viewport(),generation,blocked:!rotate.hidden}),
    drain:()=>{const copy=queue;queue=[];return JSON.stringify(copy);},
    publish:raw=>{render(JSON.parse(raw));lastPublish=performance.now();},
    cancel, status:()=>({epoch,generation,queued:queue.length,lastPublish})
  };
  // Captura apenas o canvas compacto; eventos de mouse em Web PC não são alterados.
  document.addEventListener("pointerdown",e=>{
    if(!viewport().compact||e.target.id!=="canvas")return;
    e.preventDefault();e.stopImmediatePropagation();pressed=e.pointerId;
    if(model?.selection)emit("close-inspection");
  },true);
  document.addEventListener("pointerup",e=>{
    if(e.pointerId===pressed){e.preventDefault();e.stopImmediatePropagation();pressed=null;}
  },true);
  document.addEventListener("pointercancel",cancel,true);
  window.addEventListener("blur",cancel);document.addEventListener("visibilitychange",()=>{if(document.hidden)cancel();});
  window.addEventListener("resize",resize);window.visualViewport?.addEventListener("resize",resize);
  window.addEventListener("orientationchange",resize);
  resize();
})();

