/* APIs do navegador ficam nesta fronteira, fora de regras/cenas. */
(() => {
  let focused = document.hasFocus(), resume = 0, lastActive = true;
  const active = () => !document.hidden && focused;
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
  const service = {
    lastFullscreenError: null,
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
  refresh();
})();

