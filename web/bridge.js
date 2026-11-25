/* APIs do navegador ficam nesta fronteira, fora de regras/cenas. */
(() => {
  let focused = document.hasFocus(), resume = 0, lastActive = true;
  const active = () => !document.hidden && focused && !window.scapePWA?.updating && !(window.scapeMobile && JSON.parse(window.scapeMobile.viewport()).blocked);
  const overlay = document.createElement("div");
  overlay.id = "web-paused";
  overlay.textContent = "PAUSADO · VOLTE À JANELA PARA CONTINUAR";
  overlay.hidden = true;
  document.body.appendChild(overlay);
  const refresh = () => {
    const current = active();
    if (current && !lastActive) resume++;
    lastActive = current;
    overlay.hidden = current;
  };
  document.addEventListener("visibilitychange", refresh);
  window.addEventListener("blur", () => { focused = false; refresh(); });
  window.addEventListener("focus", () => { focused = true; refresh(); });
  const button = document.createElement("button");
  button.id = "web-fullscreen";
  button.textContent = "TELA CHEIA";
  button.hidden = !document.fullscreenEnabled;
  document.body.appendChild(button);
  let persistenceRequest;
  const service = {
    // A propriedade em si pode lançar SecurityError em iframe com sandbox.
    serviceWorker: () => { try { return navigator.serviceWorker || null; } catch (_) { return null; } },
    embedded: window.self !== window.top,
    requestPersistence: () => {
      if (!persistenceRequest) persistenceRequest = (async () => {
        try {
          const storage = navigator.storage;
          if (await storage?.persisted?.()) return true;
          return Boolean(await storage?.persist?.());
        } catch (_) { return false; }
      })();
      return persistenceRequest;
    },
    lastFullscreenError: null,
    refresh,
    // SDL possui o canvas: somente Python altera o backing buffer via set_mode.
    renderViewport: () => {
      const rect = document.querySelector("#canvas")?.getBoundingClientRect();
      return JSON.stringify({width: rect?.width || 1280, height: rect?.height || 720,
        dpr: window.scapeMobile && JSON.parse(window.scapeMobile.viewport()).compact ? 1 : Math.min(2, Math.max(1, window.devicePixelRatio || 1))});
    },
    snapshot: () => JSON.stringify({ active: active(), resume, fullscreen: Boolean(document.fullscreenElement),
      checkpoint: window.scapeStorage?.status.lifecycle_checkpoint || 0 }),
    toggleFullscreen: () => {
      const request = document.fullscreenElement ? document.exitFullscreen() :
        document.documentElement.requestFullscreen?.();
      if (request?.catch) request.catch(error => {
        service.lastFullscreenError = error.name;
      });
    }
  };
  document.addEventListener("fullscreenchange", () => {
    button.textContent = document.fullscreenElement ? "SAIR DA TELA CHEIA" : "TELA CHEIA";
  });
  button.addEventListener("click", () => service.toggleFullscreen());
  window.addEventListener("keydown", event => {
    if (event.key === "F11") { event.preventDefault(); service.toggleFullscreen(); }
  });
  window.scapePlatform = service;
  void service.requestPersistence();
  refresh();
})();

