"""Nomes narrativos dos chefes, independentes das chaves de combate e arte."""

import unicodedata


BOSS_DISPLAY_NAMES = {
    'guardiao da pedra': 'Octav, o lobisomem',
    'alvaro e tex': 'Alvar & Tekks, Rastreadores',
    'alvaro e tex · pequeno': 'Tekks',
    'gordofera': 'Sir Thomas, a Besta Fera',
    'carrasco da vigilia': 'Labrro, o Carrasco',
    'corpo seco': 'Jan-Pietro, o Imortal',
    'goblin nerd': 'Jozephino, o Inventor',
    'zanzara': 'Zanzara, Líder do Clã Moskar',
}


def normalize_character_name(name):
    normalized = unicodedata.normalize('NFKD', name.casefold())
    return ' '.join(''.join(char for char in normalized if not unicodedata.combining(char)).split())


def boss_display_name(name):
    return BOSS_DISPLAY_NAMES.get(normalize_character_name(name), name)
