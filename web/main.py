"""Entrada do navegador; ?render=1 preserva o piloto das etapas anteriores."""
import asyncio
import pygame
import platform

if "render=1" in str(platform.window.location.search):
    from web.poc import main
else:
    from web.persistence import main
asyncio.run(main())
