/* Save JSON v15 dentro de IndexedDB v1: são versões independentes. */
(() => {
  const DB_NAME = "scape-from-stone";
  let db = null, sequence = 0;
  const responses = new Map();
  // A fronteira de strings do runtime WASM exige JSON ASCII nos dois sentidos.
  const wireJSON = value => JSON.stringify(value).replace(/[\u007f-\uffff]/g,
    character => "\\u" + character.charCodeAt(0).toString(16).padStart(4,"0"));
  const status = { pending: false, error: "", persistent: null, available: false, lifecycle_checkpoint: 0 };
  const explain = error => {
    const name = error?.name || "StorageError";
    const messages = {
      QuotaExceededError: "Sem espaço para salvar. Libere espaço ou exporte um backup.",
      SecurityError: "O navegador bloqueou o armazenamento. Verifique as permissões ou o modo privado.",
      InvalidStateError: "IndexedDB indisponível nesta sessão. Use um navegador com armazenamento habilitado.",
      RevisionConflict: "Este slot foi alterado em outra aba. Recarregue antes de continuar.",
      VersionError: "Banco de saves de uma versão mais recente. Atualize o jogo."
    };
    return { name, message: messages[name] || error?.message || "Falha ao salvar. A operação foi desfeita." };
  };
  function open() {
    if (db) return Promise.resolve(db);
    return new Promise((resolve, reject) => {
      if (!window.indexedDB) return reject(new DOMException("IndexedDB indisponível.", "InvalidStateError"));
      const request = indexedDB.open(DB_NAME, 1);
      request.onupgradeneeded = () => {
        request.result.createObjectStore("saves", {keyPath:"id"});
        request.result.createObjectStore("backups", {keyPath:"id"});
      };
      request.onblocked = () => reject(new Error("Feche outras versões do jogo para abrir os saves."));
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        db = request.result;
        db.onversionchange = () => { db.close(); db = null; };
        status.available = true;
        resolve(db);
      };
    });
  }
  async function read(key) {
    const database = await open();
    return new Promise((resolve, reject) => {
      const tx = database.transaction("saves", "readonly");
      const request = key === undefined ? tx.objectStore("saves").getAll() : tx.objectStore("saves").get(key);
      let value;
      request.onsuccess = () => { value = request.result; };
      tx.oncomplete = () => resolve(value ?? null);
      tx.onabort = () => reject(tx.error || request.error);
    });
  }
  async function commit(changes) {
    const database = await open();
    return new Promise((resolve, reject) => {
      let tx;
      try { tx = database.transaction(["saves","backups"], "readwrite", {durability:"strict"}); }
      catch (_) { tx = database.transaction(["saves","backups"], "readwrite"); }
      const store = tx.objectStore("saves");
      const revisions = {};
      let reason = null;
      const abort = error => { reason = error; tx.abort(); };
      for (const change of changes) {
        const request = store.get(change.key);
        request.onsuccess = () => {
          if (reason) return;
          try {
          const current = request.result;
          const revision = current?.revisao || 0;
          if ((change.create_only && current) || revision !== change.expected ||
              (current && change.expected_run_id &&
               (current.run || current.progresso)?.run_id !== change.expected_run_id)) {
            abort(Object.assign(new Error("Conflito de revisão."), {name:"RevisionConflict"})); return;
          }
          const oldRun = current?.run || current?.progresso;
          const newRun = change.payload?.run || change.payload?.progresso;
          if (oldRun && newRun && oldRun.run_id === newRun.run_id &&
              ["morta","concluida"].includes(oldRun.estado) && newRun.estado === "ativa") {
            abort(Object.assign(new Error("Esta run já foi encerrada."), {name:"RevisionConflict"})); return;
          }
          if (current && (current.versao || 0) < 15) {
            tx.objectStore("backups").put({id:change.key+":v"+(current.versao || 0)+":"+revision, data:current});
          }
          if (change.delete) store.delete(change.key);
          else {
            const next = {...change.payload, id:change.key, revisao:revision+1};
            store.put(next);
            revisions[change.key] = revision+1;
          }
          } catch(error) { abort(error); }
        };
      }
      tx.oncomplete = () => resolve(revisions); // Nenhum request.onsuccess confirma compra.
      tx.onabort = () => reject(reason || tx.error || new Error("Gravação cancelada."));
      tx.onerror = () => {};
    });
  }
  const service = {
    status,
    begin(operation, text) {
      const token = ++sequence;
      responses.set(token, {pending:true});
      const args = JSON.parse(text);
      (async () => {
        switch (operation) {
          case "open": await open(); return await read();
          case "read": return await read(args.key);
          case "commit": return await commit(args.changes);
          case "persist":
            status.persistent = navigator.storage?.persist ? await navigator.storage.persist() : false;
            return status.persistent;
          default: throw new Error("Operação de armazenamento desconhecida.");
        }
      })().then(value => responses.set(token,{ok:true,value}),
                error => { const detail=explain(error); status.error=detail.message; responses.set(token,{ok:false,error:detail}); });
      return token;
    },
    poll(token) {
      const result = responses.get(token) || {pending:true};
      if (!result.pending) responses.delete(token);
      return wireJSON(result);
    },
    preferencesGet() {
      try { return wireJSON(JSON.parse(localStorage.getItem("scape.preferences.v1") || "{}")); }
      catch (_) { throw new Error("Preferências bloqueadas pelo navegador."); }
    },
    preferencesSet(text) {
      try { localStorage.setItem("scape.preferences.v1",text); return JSON.stringify({ok:true}); }
      catch (error) { return wireJSON({ok:false,...explain(error)}); }
    },
    download(name, text) {
      const link=document.createElement("a"), url=URL.createObjectURL(new Blob([text],{type:"application/json"}));
      link.href=url; link.download=name; link.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
    },
    chooseImport() {
      const token=++sequence;
      responses.set(token,{pending:true});
      const input=document.createElement("input");
      input.type="file"; input.accept=".json,application/json";
      input.oncancel=()=>responses.set(token,{ok:true,value:null});
      input.onchange=async()=>{
        try {
          if (input.files[0].size > 5*1024*1024) throw new Error("Backup maior que 5 MiB.");
          responses.set(token,{ok:true,value:await input.files[0].text()});
        } catch(error) {responses.set(token,{ok:false,error:explain(error)});}
      };
      input.click();
      return token;
    }
  };
  window.addEventListener("pagehide",()=>{status.lifecycle_checkpoint++;});
  document.addEventListener("visibilitychange",()=>{
    if(document.hidden)status.lifecycle_checkpoint++;
  });
  window.scapeStorage=service;
})();

