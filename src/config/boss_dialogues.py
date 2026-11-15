"""Falas antes dos confrontos com chefes.

Edite apenas as listas de falas. Cada fala é um par (personagem, texto).
Use 'Jaum Manel' ou o nome exato do inimigo. Deixe () para não exibir diálogo.
"""

BOSS_DIALOGUES = {
    "guardião da pedra": (
        ("guardião da pedra", "Parece que uma das presas conseguiu sair do cativeiro..."),
        ("Jaum Manel", "Para vocês meu povo não passa de presas? Vocês vao pagar pelo que fizeram com nossas terras!"),
        ("guardião da pedra", "Uma caça sem uma luta não tem adrenalina alguma! \n Me mostre o que você sabe fazer, indiozinho!"),
    ),
    "álvaro e tex": (
        ("Jaum Manel", "Você é humano, porque ataca nossa tribo? Nós nunca fizemos mal a vocês! \n Muito menos aos goblins!"),
        ("alvaro e tex", "O clã Moskar nos ofereceu abrigo quando precisávamos de ajuda, devemos nossa lealdade a eles!"),
        ("alvaro e tex", "E eu não sou um goblin! \n Nossa cidade foi contaminada com uma bactéria que deixou minha pele verde!"),
        ("Jaum Manel", "Mentiroso! \n Se isso é verdade, porque só um de vocês é verde?"),
        ("alvaro e tex", "Digamos que meu parceiro nunca foi muito fã de banhos... \n Agora chega de conversa, esta terra vai ser o nosso novo lar, prepare-se!"),

    ),
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
