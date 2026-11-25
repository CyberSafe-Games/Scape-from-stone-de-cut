/* Instalação e cache são serviços do host, independentes de IndexedDB/saves. */
(() => {
  const bar=document.createElement("aside");bar.id="pwa-status";bar.setAttribute("aria-live","polite");
  const label=document.createElement("span"),install=document.createElement("button"),update=document.createElement("button");
  install.textContent="INSTALAR";install.hidden=true;update.textContent="ATUALIZAR";update.hidden=true;
  bar.append(label,install,update);document.body.append(bar);
  const state={supported:"serviceWorker" in navigator,offlineReady:false,updating:false,waiting:false,warning:"",version:null};
  window.scapePWA=state;
  let registration,promptEvent,lastController=navigator.serviceWorker?.controller,refreshTimer;
  const metrics=()=>{try{return JSON.parse(window.webStorageMetrics||"null");}catch{return null;}};
  const safe=()=>{const m=metrics();return Boolean(m&&m.scene==="CampaignMenu"&&!m.modal&&!m.saving);};
  function render(){
    const offline=!navigator.onLine?"SEM CONEXÃO · ":"";
    label.textContent=offline+(state.requiresConnection?"Pacote ainda precisa de conexão":
      state.offlineReady?"Offline pronto · território inicial":
      state.essentialTotal?"Preparando offline "+state.essentialAvailable+"/"+state.essentialTotal:
      "Preparando recursos offline…");
    if(state.warning)label.textContent+=" · "+state.warning;
    state.waiting=Boolean(registration?.waiting);
    update.hidden=!state.waiting||!safe();
    if(state.waiting)label.textContent+=safe()?" · Nova versão pronta":" · Atualização disponível ao voltar ao menu";
    document.documentElement.classList.toggle("pwa-actions",!install.hidden||!update.hidden);
    bar.classList.toggle("updating",state.updating);
    if(state.updating)label.textContent="Aplicando atualização segura…";
  }
  function lock(value){
    state.updating=value;
    window.scapeMobile?.cancel();
    window.scapePlatform?.refresh();
    render();
  }
  for(const type of ["pointerdown","click","keydown"])document.addEventListener(type,event=>{
    if(state.updating){event.preventDefault();event.stopImmediatePropagation();}
  },true);
  async function refresh(){
    const worker=navigator.serviceWorker.controller;
    if(!worker)return;
    const channel=new MessageChannel();
    channel.port1.onmessage=event=>{Object.assign(state,event.data);render();channel.port1.close();};
    worker.postMessage({type:"STATUS"},[channel.port2]);
  }
  navigator.serviceWorker?.addEventListener("message",event=>{
    const message=event.data||{};
    if(message.type==="PWA_STATUS"){Object.assign(state,message);render();}
    if(message.type==="PREPARE_UPDATE"){
      const approved=safe();
      if(approved)lock(true);
      event.source.postMessage({type:"UPDATE_APPROVAL",token:message.token,safe:approved});
    }
    if(message.type==="UPDATE_CANCEL"){lock(false);state.warning=message.message;render();}
  });
  navigator.serviceWorker?.addEventListener("controllerchange",()=>{
    const previous=lastController;lastController=navigator.serviceWorker.controller;
    if(previous&&state.updating){location.reload();return;}
    navigator.serviceWorker.controller?.postMessage({type:"PREPARE_OFFLINE"});
    refresh();
  });
  window.addEventListener("beforeinstallprompt",event=>{
    event.preventDefault();promptEvent=event;install.hidden=false;render();
  });
  install.addEventListener("click",async()=>{
    if(promptEvent){await promptEvent.prompt();await promptEvent.userChoice;promptEvent=null;install.hidden=true;}
  });
  window.addEventListener("appinstalled",()=>{install.hidden=true;render();});
  update.addEventListener("click",()=>{
    if(safe()&&registration?.waiting)registration.waiting.postMessage({type:"APPLY_UPDATE"});
  });
  if(/iPhone|iPad|iPod/.test(navigator.userAgent)&&!navigator.standalone){
    install.hidden=false;install.textContent="ADICIONAR À TELA INICIAL";
    install.addEventListener("click",()=>{state.warning="Use Compartilhar → Adicionar à Tela de Início.";render();});
  }
  window.addEventListener("online",()=>{navigator.serviceWorker.controller?.postMessage({type:"PREPARE_OFFLINE"});refresh();});
  window.addEventListener("offline",render);
  if(state.supported&&window.isSecureContext){
    function configure(reg){
      registration=reg;
      const watch=worker=>{
        worker?.addEventListener("statechange",()=>{
          if(worker.state==="redundant"&&!reg.active)state.warning="Não foi possível preparar o cache inicial. Reconecte e recarregue.";
          render();if(worker.state==="installed")refresh();
        });
      };
      reg.addEventListener("updatefound",()=>watch(reg.installing));watch(reg.installing);
      refresh();
      if(!refreshTimer)refreshTimer=setInterval(()=>{refresh();render();},3000);
      navigator.serviceWorker.ready.then(()=>{
        navigator.serviceWorker.controller?.postMessage({type:"PREPARE_OFFLINE"});
        refresh();
      });
      navigator.storage?.persist?.().catch(()=>{});
      render();
    }
    (async()=>{
      const existing=await navigator.serviceWorker.getRegistration();
      if(existing&&navigator.serviceWorker.controller){
        // Uma abertura offline não depende de buscar novamente o script do SW.
        configure(existing);
        if(navigator.onLine)existing.update().catch(()=>{});
      }else{
        configure(await navigator.serviceWorker.register("service-worker.js",{scope:"./",updateViaCache:"none"}));
      }
    })().catch(error=>{state.warning="Cache offline indisponível: "+error.message;render();});
  }else{state.warning="Instalação offline requer HTTPS ou localhost.";render();}
  window.addEventListener("pagehide",()=>clearInterval(refreshTimer));
  render();
})();

