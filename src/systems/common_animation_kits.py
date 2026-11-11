"""Kits comuns em oito poses; tempos e origens dos projéteis em coordenadas da arena."""
from src.systems.normal_enemy_catalog import NORMAL_SPRITES

COMMON_KITS = {name.lower(): (spec[0], spec[1]) for name, spec in NORMAL_SPRITES.items()}
COMMON_KITS.update({
    'vinimuth': ('vinimuth', ('idle','dano','atk1','atk2')),
    'slime': ('slime', ('idle','dano','atk','def')),
})

# x a partir do centro do ator; y acima dos pés; altura final do impacto.
PROJECTILE_ORIGINS = {
    ('golem das ruínas','atk1'): (158, 150, 98),
    ('centauro vigia','atk1'): (150, 143, 98),
    ('putrefato do pântano','atk1'): (120, 108, 98),
    ('morcego sombrio','atk2'): (105, 135, 98),
    ('mago do santuário','atk1'): (98, 96, 98),
    ('mago do santuário','atk2'): (98, 27, 27),
    ('vinimuth','atk2'): (128, 126, 98),
    ('slime','atk'): (60, 53, 83),
}
