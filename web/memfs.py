"""Limpeza restrita aos derivados de animação no MEMFS da campanha Web."""
from pathlib import Path, PurePosixPath

# Arte de UI/retratos, fontes, JSON e OGG transmitido pelo mixer continuam legíveis.
ANIMATION_ROOTS = {"player", "card_effects", "ultimate_effects", "bosses",
                   "boss_ultimate_effects", "enemies", "goblin_nerd",
                   "goblin_monge", "guardiao_da_pedra", "slime"}


def asset_path(name):
    path = PurePosixPath(name)
    if (path.is_absolute() or ".." in path.parts or len(path.parts) < 2
            or path.parts[0] != "assets" or "\\" in name or ":" in name):
        raise OSError("Caminho de recurso inválido.")
    return Path(*path.parts)


def prune_animations(manifest, groups):
    """Só após os loaders: remove PNGs decodificados e recursos não usados do kit.

    Retorna grupos incompletos, que precisam ser reidratados antes de outro load.
    Não remove música: SDL_mixer pode continuar lendo o OGG por streaming.
    """
    removed, freed = set(), 0
    for group in groups:
        for pack in manifest["groups"].get(group, []):
            for name in pack["files"]:
                path = asset_path(name)
                if path.parts[1] in ANIMATION_ROOTS and path.suffix.lower() == ".png" and path.is_file():
                    freed += path.stat().st_size
                    path.unlink()
                    removed.add(group)
    return removed, freed
