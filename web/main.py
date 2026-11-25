"""Entrada do navegador; ?render=1 preserva o piloto das etapas anteriores."""
import asyncio
import pygame
import platform
from pathlib import Path

if "render=1" in str(platform.window.location.search):
    from web.poc import main
elif "persistence=1" in str(platform.window.location.search) or not Path("web_manifest.json").exists():
    from web.persistence import main
else:
    from web.campaign import main
asyncio.run(main())
