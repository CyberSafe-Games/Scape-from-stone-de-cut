/* Gerado com configuração imutável; nunca ativa uma atualização durante combate. */
const CONFIG=__SCAPE_CONFIG__;
const scope=new URL(self.registration.scope);
const absolute=value=>new URL(value,scope).href.split("#")[0];
const PREFIX="scape:"+scope.pathname+":";
const SHELL=PREFIX+"shell-"+CONFIG.version;
const RUNTIME=PREFIX+"runtime-"+CONFIG.runtimeVersion;
const PACKS=PREFIX+"packs";
const shells=new Map(CONFIG.shell.map(r=>[absolute(r.url),r]));
const runtimes=new Map(CONFIG.runtime.map(r=>[absolute(r.url),r]));
const packs=new Map(CONFIG.packs.map(r=>[absolute(r.url),r]));
let preparing=null,warning="",requiresConnection="",updating=null;
const approvals=new Map(),inflight=new Map();
const digest=async buffer=>Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",buffer))).map(b=>b.toString(16).padStart(2,"0")).join("");
async function downloadVerified(record,cacheName,allowUncached) {
  const cache=await caches.open(cacheName),url=absolute(record.url);
  const cached=await cache.match(url);
  if(cached)return cached;
  const response=await fetch(url,{cache:"no-cache",mode:"cors",credentials:new URL(url).origin===scope.origin?"same-origin":"omit"});
  if(response.status!==200||response.type==="opaque")throw new Error("Download incompleto: "+record.url);
  const data=await response.clone().arrayBuffer();
  if(data.byteLength!==record.bytes||await digest(data)!==record.sha256)throw new Error("Integridade inválida: "+record.url);
  try{await cache.put(url,response.clone());}
  catch(error){if(!allowUncached)throw error;warning="Sem espaço para cache; este recurso exige conexão."; } // Nunca publicar parcial.
  return response;
}
async function verified(record,cacheName,allowUncached=false){
  const key=cacheName+":"+absolute(record.url);
  if(inflight.has(key))return (await inflight.get(key)).clone();
  const task=downloadVerified(record,cacheName,allowUncached);inflight.set(key,task);
  try{return (await task).clone();}finally{inflight.delete(key);}
}
async function windows() {
  return (await self.clients.matchAll({type:"window",includeUncontrolled:true})).filter(c=>c.url.startsWith(scope.href));
}
async function status() {
  const cache=await caches.open(PACKS);
  let available=0;
  for(const record of CONFIG.essential)if(await cache.match(absolute(record.url)))available++;
  return {version:CONFIG.version,essentialTotal:CONFIG.essential.length,essentialAvailable:available,
    offlineReady:available===CONFIG.essential.length,preparing:Boolean(preparing),warning,requiresConnection};
}
async function broadcast(value) {for(const client of await windows())client.postMessage(value);}
async function announce(){await broadcast({type:"PWA_STATUS",...await status()});}
async function prepare() {
  if(preparing)return preparing;
  preparing=(async()=>{
    try{
      for(const record of CONFIG.essential){await verified(record,PACKS);await announce();}
      warning="";requiresConnection="";
    }catch(error){warning=error.name==="QuotaExceededError"?"Sem espaço para concluir o cache offline.":error.message;}
  })();
  try{await preparing;}finally{preparing=null;await announce();}
}
self.addEventListener("install",event=>{
  event.waitUntil((async()=>{
    try{
      for(const record of CONFIG.runtime)await verified(record,RUNTIME);
      for(const record of CONFIG.shell)await verified(record,SHELL);
    }catch(error){await caches.delete(SHELL);throw error;}
    // Sem skipWaiting: versões existentes permanecem intactas.
  })());
});
self.addEventListener("activate",event=>{
  event.waitUntil((async()=>{
    await self.clients.claim();
    for(const name of await caches.keys()){
      if(name.startsWith(PREFIX+"shell-")&&name!==SHELL)await caches.delete(name);
      if(name.startsWith(PREFIX+"runtime-")&&name!==RUNTIME)await caches.delete(name);
    }
    await announce();
  })());
});
self.addEventListener("fetch",event=>{
  if(event.request.method!=="GET")return;
  const url=new URL(event.request.url);url.hash="";
  const key=url.href;
  if(event.request.mode==="navigate"&&url.origin===scope.origin&&
    (url.pathname===scope.pathname||url.pathname===new URL("index.html",scope).pathname)){
    event.respondWith(caches.open(SHELL).then(cache=>cache.match(absolute("index.html"))).then(r=>r||fetch(event.request)));
    return;
  }
  const record=packs.get(key)||shells.get(key)||runtimes.get(key);
  if(!record)return;
  const cacheName=packs.has(key)?PACKS:runtimes.has(key)?RUNTIME:SHELL;
  event.respondWith((async()=>{
    try{
      const response=await verified(record,cacheName,true);
      if(packs.has(key)){requiresConnection="";event.waitUntil(announce());}
      return response;
    }catch(error){
      warning=error.name==="QuotaExceededError"?"Sem espaço no cache offline.":error.message;
      requiresConnection=record.url;
      event.waitUntil(announce());
      return new Response(JSON.stringify({message:"Este recurso ainda precisa de conexão. Reconecte e tente novamente."}),
        {status:503,headers:{"Content-Type":"application/json","X-Scape-Offline":"missing"}});
    }
  })());
});
async function activateSafely() {
  const clients=await windows();
  const token=crypto.randomUUID();
  const responses=new Map();
  const completion=new Promise(resolve=>{
    approvals.set(token,{responses,resolve,expected:clients.map(c=>c.id)});
    setTimeout(()=>resolve(false),3000);
  });
  for(const client of clients)client.postMessage({type:"PREPARE_UPDATE",token});
  const approved=clients.length===0||await completion;
  approvals.delete(token);
  if(approved)await self.skipWaiting();
  else await broadcast({type:"UPDATE_CANCEL",message:"Atualização adiada: outra aba está em uso ou ainda não confirmou."});
}
self.addEventListener("message",event=>{
  const message=event.data||{};
  if(message.type==="UPDATE_APPROVAL"){
    const task=approvals.get(message.token);
    if(task&&task.expected.includes(event.source.id)){
      task.responses.set(event.source.id,Boolean(message.safe));
      if(!message.safe)task.resolve(false);
      else if(task.responses.size===task.expected.length)task.resolve(true);
    }
    return;
  }
  if(message.type==="STATUS"){
    event.waitUntil(status().then(value=>event.ports[0]?.postMessage(value)));
  }else if(message.type==="PREPARE_OFFLINE"){
    event.waitUntil(prepare());
  }else if(message.type==="APPLY_UPDATE"){
    if(!updating)updating=activateSafely().finally(()=>{updating=null;});
    event.waitUntil(updating);
  }
});

