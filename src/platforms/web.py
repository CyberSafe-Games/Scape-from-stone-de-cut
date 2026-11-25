"""Serviços do navegador; persistência durável pertence à Etapa 3."""
import json
import posixpath
from .capabilities import detect_capabilities


class WebPlatform:
    capabilities = detect_capabilities("emscripten")

    def __init__(self, base_dir=None, bridge=None):
        self.base_dir = str(base_dir or ".")
        self._bridge = bridge

    @property
    def bridge(self):
        if self._bridge is None:
            import platform
            self._bridge = platform.window.scapePlatform
        return self._bridge

    def resource_path(self, *parts):
        return posixpath.join(self.base_dir, *parts)

    def user_data_path(self, *parts):
        # Caminho de sessão no FS virtual, jamais confundir com IndexedDB/save durável.
        return posixpath.join("/tmp/scape-from-stone-session", *parts)

    def exit_action(self):
        return "home"

    def lifecycle_state(self):
        state = json.loads(str(self.bridge.snapshot()))
        return bool(state["active"]), int(state["resume"])

    def checkpoint_serial(self):
        return int(json.loads(str(self.bridge.snapshot())).get("checkpoint",0))

    def fullscreen_state(self):
        return bool(json.loads(str(self.bridge.snapshot())).get("fullscreen", False))

    def toggle_fullscreen(self):
        self.bridge.toggleFullscreen()

    def create_window(self, *args, **kwargs):
        from src.core.web_window import WebWindowManager
        return WebWindowManager(*args, platform_service=self, **kwargs)

