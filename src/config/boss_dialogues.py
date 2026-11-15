"""Falas antes dos confrontos com chefes.

Edite apenas as listas de falas. Cada fala é um par (personagem, texto).
Use 'Jaum Manel' ou o nome exato do inimigo. Deixe () para não exibir diálogo.
"""

BOSS_DIALOGUES = {
    "guardião da pedra": (
        ("Guardião da Pedra", "Você não irá passar!"),
        ("Jaum Manel", "Preciso salvar meu povo."),
    ),
    "álvaro e tex": (),
    "goblin nerd": (),
    "gordofera": (),
    "corpo seco": (),
    "carrasco da vigília": (),
    "zanzara": (),
    # Minibosses genéricos (caso apareçam no modo de jogo usado):
    "ogro ancestral": (),
    "cavaleiro caído": (),
    "behemoth de pedra": (),
}


def dialogue_for(enemy):
    """Obtém falas somente para confrontos contra chefes/minibosses."""
    if not (
        getattr(enemy, "is_miniboss", False)
        or getattr(enemy, "is_final_boss", False)
        or getattr(enemy, "boss_id", None)
    ):
        return ()
    name = getattr(enemy, "name", "").strip().lower()
    return tuple(BOSS_DIALOGUES.get(name, ()))
