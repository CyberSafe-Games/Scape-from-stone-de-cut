import random
from src.models.action import Action
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


def _build_slime_actions(level):
    """Gera as ações específicas do Slime escaladas pelo andar."""
    attack_damage = 6 + level
    defense_amount = 5 + level // 2
    return [
        Action(
            name="Ataque",
            action_type="attack",
            damage=attack_damage,
            energy_cost=1,
            weight=0.70,
            visual_effect="atk",
        ),
        Action(
            name="Defesa",
            action_type="defend",
            defense=defense_amount,
            energy_cost=1,
            weight=0.30,
            visual_effect="def",
        ),
    ]


def _build_ogro_actions(level):
    """Gera as ações específicas do Ogro Ancestral (Miniboss) escaladas pelo andar."""
    fast_damage = 8 + level * 2
    heavy_damage = 16 + level * 3
    defense_amount = 10 + level
    return [
        Action(
            name="Ataque rápido",
            action_type="attack",
            damage=fast_damage,
            energy_cost=1,
            weight=0.50,
            visual_effect=None,
        ),
        Action(
            name="Ataque pesado",
            action_type="attack",
            damage=heavy_damage,
            energy_cost=2,
            weight=0.30,
            visual_effect=None,
        ),
        Action(
            name="Defesa",
            action_type="defend",
            defense=defense_amount,
            energy_cost=1,
            weight=0.20,
            visual_effect=None,
        ),
    ]


def create_enemy(level, is_miniboss=False):
    """Gera proceduralmente uma instância balanceada de inimigo."""
    pool = MINIBOSS_TYPES if is_miniboss else ENEMY_TYPES
    name, base_hp, hp_per_level = random.choice(pool)
    hp = base_hp + level * hp_per_level

    actions = None
    max_energy = 3

    # Demonstração da nova arquitetura para Slime e Ogro Ancestral (Miniboss)
    if name == "Slime":
        actions = _build_slime_actions(level)
    elif name == "Ogro Ancestral":
        actions = _build_ogro_actions(level)

    enemy = Enemy(
        name=name,
        hp=hp,
        energy=max_energy,
        max_energy=max_energy,
        actions=actions,
        is_miniboss=is_miniboss,
    )
    return enemy


def choose_enemy_intent(enemy):
    """Calcula a próxima ação da IA do inimigo de forma genérica a partir de suas ações disponíveis."""
    # 1. IA Genérica: analisa as ações configuradas e a energia disponível no próprio Enemy
    if enemy.actions:
        valid_actions = [
            action for action in enemy.actions if action.energy_cost <= enemy.energy
        ]
        if valid_actions:
            weights = [action.weight for action in valid_actions]
            chosen_action = random.choices(valid_actions, weights=weights, k=1)[0]
            enemy.set_intent(
                intent_type=chosen_action.action_type,
                value=chosen_action.value,
                action=chosen_action,
            )
            return

    # 2. Modo Legado / Fallback para inimigos ainda não migrados
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
