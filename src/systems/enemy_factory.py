import random
from src.models.enemy import Enemy
from src.config.layout import MINIBOSS_INTERVAL

# Configuração de inimigos comuns: (Nome, HP Base, HP por Andar)
ENEMY_TYPES = [
    ("Slime", 18, 5),
    ("Goblin", 24, 6),
    ("Guarda Sombrio", 32, 8),
]

# Configuração de Minibosses: (Nome, HP Base, HP por Andar)
MINIBOSS_TYPES = [
    ("Ogro Ancestral", 70, 14),
    ("Cavaleiro Caído", 80, 16),
    ("Behemoth de Pedra", 95, 12),
]


def is_miniboss_level(level):
    """Determina se o andar atual é um confronto de miniboss."""
    return level % MINIBOSS_INTERVAL == 0


def create_enemy(level, is_miniboss=False):
    """Gera proceduralmente uma instância balanceada de inimigo."""
    pool = MINIBOSS_TYPES if is_miniboss else ENEMY_TYPES
    name, base_hp, hp_per_level = random.choice(pool)
    hp = base_hp + level * hp_per_level

    enemy = Enemy(name=name, hp=hp, is_miniboss=is_miniboss)
    return enemy


def choose_enemy_intent(enemy):
    """Calcula a próxima ação da inteligência artificial do inimigo."""
    intent_multiplier = 1.5 if enemy.is_miniboss else 1.0

    if random.random() < 0.7:
        enemy.intent = "attack"
        base_max = 10 + enemy.max_hp // 10
        enemy.intent_value = int(
            random.randint(6, base_max) * intent_multiplier
        )
    else:
        enemy.intent = "defend"
        enemy.intent_value = int(
            random.randint(5, 10) * intent_multiplier
        )
