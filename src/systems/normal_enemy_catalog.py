"""Bestiário dos encontros do caminho; chefes e tutorial têm pools próprios."""

BIOME_ENEMIES = {
    1: ('Slime',),
    2: ('Macaco Selvagem', 'Guerreiro da Mata'),
    3: ('Golem das Ruínas', 'Lagarto Couraçado'),
    4: ('Putrefato do Pântano', 'Crocodilo Abissal'),
    5: ('Esqueleto Saqueador', 'Morcego Sombrio'),
    6: ('Centauro Vigia', 'Lutador Mascarado'),
    7: ('Vinimuth', 'Mago do Santuário'),
}

# slug, grupos na ordem das linhas da referência, HP base, HP por nível.
NORMAL_SPRITES = {
    'Esqueleto Saqueador': ('esqueleto', ('idle', 'dano', 'atk1', 'atk2'), 22, 5),
    'Golem das Ruínas': ('golem', ('idle', 'dano', 'atk1', 'def'), 30, 6),
    'Centauro Vigia': ('centauro', ('idle', 'dano', 'atk1', 'atk2'), 27, 6),
    'Putrefato do Pântano': ('putrefato', ('idle', 'dano', 'atk1', 'healer2'), 25, 6),
    'Guerreiro da Mata': ('guerreiro_mata', ('idle', 'dano', 'atk1', 'atk2'), 25, 5),
    'Lagarto Couraçado': ('lagarto', ('idle', 'dano', 'atk1', 'def'), 22, 5),
    'Morcego Sombrio': ('morcego', ('idle', 'dano', 'atk1', 'atk2'), 18, 5),
    'Lutador Mascarado': ('lutador', ('idle', 'dano', 'atk1', 'atk2'), 28, 6),
    'Mago do Santuário': ('mago', ('idle', 'dano', 'atk1', 'atk2'), 24, 6),
    'Crocodilo Abissal': ('crocodilo', ('idle', 'dano', 'def', 'atk1'), 30, 6),
    'Macaco Selvagem': ('macaco', ('idle', 'dano', 'atk1', 'healer2'), 21, 5),
}

# nome, tipo, valor base (+ nível para ataques/defesas), peso, animação, estado.
NORMAL_ACTIONS = {
    'Esqueleto Saqueador': (
        ('Corte Enferrujado', 'attack', 5, .55, 'atk1', ('bleed', 2, 2)),
        ('Estocada Óssea', 'attack', 9, .45, 'atk2', None)),
    'Golem das Ruínas': (
        ('Rocha Arcana', 'attack', 8, .65, 'atk1', None),
        ('Armadura de Pedra', 'defend', 10, .35, 'def', None)),
    'Centauro Vigia': (
        ('Flecha da Vigília', 'attack', 8, .6, 'atk1', None),
        ('Atropelo', 'attack', 12, .4, 'atk2', None)),
    'Putrefato do Pântano': (
        ('Cuspe Parasita', 'attack', 5, .75, 'atk1', ('poison', 3, 3)),
        ('Devorar Parasitas', 'heal', 9, .25, 'healer2', None)),
    'Guerreiro da Mata': (
        ('Varredura do Mangual', 'attack', 7, .65, 'atk1', None),
        ('Abalo da Floresta', 'attack', 11, .35, 'atk2', None)),
    'Lagarto Couraçado': (
        ('Língua Chicote', 'attack', 7, .7, 'atk1', None),
        ('Couraça Enrolada', 'defend', 9, .3, 'def', None)),
    'Morcego Sombrio': (
        ('Mordida Noturna', 'attack', 6, .6, 'atk1', ('bleed', 2, 2)),
        ('Onda Sônica', 'attack', 8, .4, 'atk2', None)),
    'Lutador Mascarado': (
        ('Chute do Vigia', 'attack', 9, .6, 'atk1', None),
        ('Investida Mascarada', 'attack', 12, .4, 'atk2', None)),
    'Mago do Santuário': (
        ('Runa Incandescente', 'attack', 5, .55, 'atk1', ('fire', 2, 3)),
        ('Ruptura da Terra', 'attack', 11, .45, 'atk2', None)),
    'Crocodilo Abissal': (
        ('Escamas Arcanas', 'defend', 10, .3, 'def', None),
        ('Cauda Abissal', 'attack', 10, .7, 'atk1', None)),
    'Macaco Selvagem': (
        ('Mordida Feroz', 'attack', 6, .8, 'atk1', None),
        ('Lanche da Selva', 'heal', 7, .2, 'healer2', None)),
}

# Lançamento sincronizado com a terceira pose, seguido por recuperação.
NORMAL_RANGED = {
    'golem das ruínas': {'atk1': (1250, .44, .80)},
    'centauro vigia': {'atk1': (1100, .44, .80)},
    'putrefato do pântano': {'atk1': (1250, .44, .80)},
    'morcego sombrio': {'atk2': (1200, .44, .80)},
    'mago do santuário': {'atk1': (1250, .44, .80), 'atk2': (1350, .44, .80)},
}

# Recortes relativos à silhueta: asas e caudas não devem virar o retrato da HUD.
NORMAL_PORTRAITS = {
    'lagarto couraçado': (0, 0, .40, .65),
    'morcego sombrio': (0, .32, .40, .60),
    'macaco selvagem': (0, .28, .45, .72),
    'putrefato do pântano': (.05, .04, .60, .55),
    'mago do santuário': (.32, .05, .60, .45),
}


def biome_enemy_names(level):
    return BIOME_ENEMIES[max(1, min(7, int(level)))]
