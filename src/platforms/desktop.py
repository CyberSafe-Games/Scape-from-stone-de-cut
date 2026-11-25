"""Recursos somente leitura e dados locais preservam o contrato PyInstaller."""
import os
import sys
from .capabilities import detect_capabilities


class DesktopPlatform:
    capabilities = detect_capabilities("desktop")

    def __init__(self, base_dir=None):
        self.base_dir = os.fspath(base_dir) if base_dir is not None else os.getcwd()

    def resource_path(self, *parts):
        return os.path.join(getattr(sys, "_MEIPASS", self.base_dir), *parts)

    def user_data_path(self, *parts):
        root = self.base_dir
        if getattr(sys, "frozen", False):
            local = os.environ.get("LOCALAPPDATA")
            if not local:
                local = os.path.join(os.path.expanduser("~"), "AppData", "Local")
            root = os.path.join(local, "ScapeFromStoneDeCut")
        return os.path.join(root, *parts)

    def exit_action(self):
        return "stop"

    def lifecycle_state(self):
        return True, 0

    def create_window(self, *args, **kwargs):
        from src.core.window import WindowManager
        return WindowManager(*args, **kwargs)

