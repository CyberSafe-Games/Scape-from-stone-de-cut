"""Capacidades do host; tamanho de tela não identifica a plataforma."""
from dataclasses import dataclass
import sys


@dataclass(frozen=True)
class Capabilities:
    is_web: bool
    native_window: bool
    persistent_storage: bool
    cooperative_loop: bool
    requires_audio_gesture: bool


def detect_capabilities(platform_name=None):
    web = (sys.platform if platform_name is None else platform_name) == "emscripten"
    return Capabilities(web, not web, True, web, web)

