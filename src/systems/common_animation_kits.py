"""Kits comuns em oito poses; tempos e origens dos projéteis em coordenadas da arena."""
from src.systems.normal_enemy_catalog import NORMAL_SPRITES

COMMON_KITS = {name.lower(): (spec[0], spec[1]) for name, spec in NORMAL_SPRITES.items()}
COMMON_KITS.update({
    'vinimuth': ('vinimuth', ('idle','dano','atk1','atk2')),
    'slime': ('slime', ('idle','dano','atk','def')),
})

# x a partir do centro do ator; y acima dos pés; altura final do impacto.
PROJECTILE_ORIGINS = {
    ('golem das ruínas','atk1'): (105, 100, 65),
    ('centauro vigia','atk1'): (100, 95, 65),
    ('putrefato do pântano','atk1'): (80, 72, 65),
    ('morcego sombrio','atk2'): (70, 90, 65),
    ('mago do santuário','atk1'): (65, 64, 65),
    ('mago do santuário','atk2'): (65, 18, 18),
    ('vinimuth','atk2'): (85, 84, 65),
    ('slime','atk'): (40, 35, 55),
}
