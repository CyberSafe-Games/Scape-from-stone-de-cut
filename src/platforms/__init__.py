"""Serviços de ambiente sem dependência de Pygame no momento da importação."""
from .capabilities import detect_capabilities


def get_platform(base_dir=None):
    if detect_capabilities().is_web:
        from .web import WebPlatform
        return WebPlatform(base_dir)
    from .desktop import DesktopPlatform
    return DesktopPlatform(base_dir)

