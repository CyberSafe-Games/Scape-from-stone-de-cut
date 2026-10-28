import random

from src.models.action import Action
from src.models.enemy import Enemy
from src.config.layout import MINIBOSS_INTERVAL
from src.models.effects.crimson_vigor_effect import CrimsonVigorEffect
from src.systems.normal_enemy_catalog import biome_enemy_names, NORMAL_SPRITES, NORMAL_ACTIONS

# Configuração de inimigos comuns: (Nome, HP Base, HP por Andar)
ENEMY_TYPES = [
    ("Slime", 18, 5),
    ("Vinimuth", 22, 5),
    ("Goblin", 24, 6),
    ("Guarda Sombrio", 32, 8),
]

# Configuração de Minibosses genéricos: (Nome, HP Base, HP por Andar)
MINIBOSS_TYPES = [
    ("Ogro Ancestral", 70, 14),
    ("Cavaleiro Caído", 80, 16),
    ("Behemoth de Pedra", 95, 12),
]

RUINAS_ANCESTRAIS_TERRITORY = "ruinas_ancestrais"
CORPO_SECO_TERRITORY = "fortaleza_caida"


def is_miniboss_level(level):
    """Determina se o andar atual é um confronto de miniboss."""
    return level % MINIBOSS_INTERVAL == 0


def _build_slime_actions(level):
    attack_damage = 6 + level
    defense_amount = 5 + level // 2
    return [
        Action("Ataque", "attack", damage=attack_damage, energy_cost=1, weight=0.50, visual_effect="atk"),
        Action("Salpico ácido", "attack", damage=max(1, attack_damage - 3), energy_cost=1,
               weight=0.20, visual_effect="atk", status_effect=('poison', 2, 3)),
        Action("Defesa", "defend", defense=defense_amount, energy_cost=1, weight=0.30, visual_effect="def"),
    ]


def _build_ogro_actions(level):
    fast_damage = 8 + level * 2
    heavy_damage = 16 + level * 3
    defense_amount = 10 + level
    return [
        Action("Ataque rápido", "attack", damage=fast_damage, energy_cost=1, weight=0.50, visual_effect=None),
        Action("Ataque pesado", "attack", damage=heavy_damage, energy_cost=2, weight=0.30, visual_effect=None),
        Action("Defesa", "defend", defense=defense_amount, energy_cost=1, weight=0.20, visual_effect=None),
    ]


def _build_vinimuth_actions(level):
    return [
        Action("Golpe de palma", "attack", damage=6 + level, energy_cost=1,
               weight=0.55, visual_effect="atk1"),
        Action("Onda de energia", "attack", damage=8 + level, energy_cost=1,
               weight=0.45, visual_effect="atk2"),
    ]


def create_enemy(level, is_miniboss=False):
    """Gera proceduralmente uma instância balanceada de inimigo."""
    pool = MINIBOSS_TYPES if is_miniboss else ENEMY_TYPES
    name, base_hp, hp_per_level = random.choice(pool)
    hp = base_hp + level * hp_per_level

    actions = None
    max_energy = 3

    if name == "Slime":
        actions = _build_slime_actions(level)
    elif name == "Vinimuth":
        actions = _build_vinimuth_actions(level)
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
    """Calcula a próxima ação da IA do inimigo de forma genérica."""
    if enemy.actions:
        valid_actions = [action for action in enemy.actions if action.energy_cost <= enemy.energy]
        if valid_actions:
            weights = [action.weight for action in valid_actions]
            chosen_action = random.choices(valid_actions, weights=weights, k=1)[0]
            enemy.set_intent(intent_type=chosen_action.action_type, value=chosen_action.value, action=chosen_action)
            return

    intent_multiplier = 1.5 if enemy.is_miniboss else 1.0
    if random.random() < 0.7:
        enemy.intent = "attack"
        base_max = 10 + enemy.max_hp // 10
        enemy.intent_value = int(random.randint(6, base_max) * intent_multiplier)
    else:
        enemy.intent = "defend"
        enemy.intent_value = int(random.randint(5, 10) * intent_multiplier)


def _configure_boss(enemy, special_name, special_damage, special_visual):
    enemy.actions_per_turn = 2
    enemy.action_counter = 0
    enemy.special_interval = 8
    enemy.special_action = Action(special_name, "attack", damage=special_damage, energy_cost=1, visual_effect=special_visual)
    return enemy


def create_goblin_nerd(level=3):
    """Miniboss das Ruínas Ancestrais: engenhocas e duas ações por rodada."""
    actions = [
        Action("Chave arremessada", "attack", damage=8 + level, energy_cost=1, weight=0.35, visual_effect="atk1"),
        Action("Descarga improvisada", "attack", damage=10 + level, energy_cost=1, weight=0.30, visual_effect="atk2"),
        Action("Baforada tóxica", "attack", damage=9 + level, energy_cost=1, weight=0.20, visual_effect="atk3", status_effect=('poison', 2, 5)),
        Action("Escudo rúnico", "defend", defense=8 + level, energy_cost=1, weight=0.15, visual_effect="healer2"),
    ]
    boss = Enemy("Goblin Nerd", hp=92 + level * 4, energy=4, max_energy=4, actions=actions, is_miniboss=True)
    return _configure_boss(boss, "Descarga Sobrecarregada", 17 + level, "atk2")


def create_guardiao_da_pedra(level=1):
    """Primeiro miniboss: garras, defesa e recuperação, com rugido espiritual."""
    actions = [
        Action('Golpe de Garras', 'attack', damage=6 + level, energy_cost=1,
               weight=0.55, visual_effect='atk1'),
        Action('Pele Rochosa', 'defend', defense=7 + level, energy_cost=1,
               weight=0.30, visual_effect='def'),
        Action('Vigor Selvagem', 'heal', defense=8, energy_cost=1,
               weight=0.15, visual_effect='healer2'),
    ]
    boss = Enemy('Guardião da Pedra', hp=74 + level * 4, energy=4,
                 max_energy=4, actions=actions, is_miniboss=True)
    return _configure_boss(boss, 'Rugido Espiritual', 13 + level, 'atk2')


def create_corpo_seco(level=5):
    """Corpo Seco: duas ações por rodada; giro no 8º, 16º... ato."""
    actions = [
        Action("Corte rápido", "attack", damage=7 + level // 2, energy_cost=1, weight=0.55, visual_effect="atk1"),
        Action("Lâminas cruzadas", "attack", damage=10 + level // 2, energy_cost=1, weight=0.30, visual_effect="atk3"),
        Action("Postura defensiva", "defend", defense=8 + level // 2, energy_cost=1, weight=0.15, visual_effect="def"),
    ]
    boss = Enemy("Corpo Seco", hp=125, energy=4, max_energy=4, actions=actions, is_miniboss=True)
    return _configure_boss(boss, "Ataque Giratório", 19, "atk4")


def create_carrasco_da_vigilia(level=6):
    """Guardião do Pico: machado pesado e recuperação com aura escarlate."""
    actions = [
        Action('Corte do Carrasco', 'attack', damage=10 + level // 2,
               energy_cost=1, weight=0.45, visual_effect='atk1'),
        Action('Varredura Escarlate', 'attack', damage=14 + level // 2,
               energy_cost=2, weight=0.35, visual_effect='atk2'),
        Action('Vigor Escarlate', 'buff', defense=14, energy_cost=1,
               weight=0.20, visual_effect='healer2', effect=CrimsonVigorEffect()),
    ]
    boss = Enemy('Carrasco da Vigília', hp=134 + 2 * level, energy=4,
                 max_energy=4, actions=actions, is_miniboss=True)
    return _configure_boss(boss, 'Execução Escarlate', 18 + level, 'atk3')


def create_point_enemy(level):
    """Resolve chefes territoriais específicos antes do fallback genérico."""
    if level == 1:
        return create_guardiao_da_pedra(level)
    if level == 3:
        return create_goblin_nerd(level)
    if level == 5:
        return create_corpo_seco(level)
    if level == 6:
        return create_carrasco_da_vigilia(level)
    return create_enemy(level, is_miniboss_level(level))


def create_road_enemy(level):
    """Escolhe somente os habitantes do bioma, preservando os chefes."""
    name = random.choice(biome_enemy_names(level))
    if name == "Vinimuth":
        return Enemy("Vinimuth", hp=22 + 5 * level, energy=3, max_energy=3,
                     actions=_build_vinimuth_actions(level), is_miniboss=False)
    if name == 'Slime':
        return Enemy("Slime", hp=18 + 5 * level, energy=3, max_energy=3, actions=_build_slime_actions(level), is_miniboss=False)
    _, _, base_hp, scaling = NORMAL_SPRITES[name]
    actions = []
    for title, kind, base, weight, visual, status in NORMAL_ACTIONS[name]:
        value = base + level if kind != 'heal' else base
        actions.append(Action(title, kind, damage=value if kind == 'attack' else 0,
                              defense=value if kind != 'attack' else 0,
                              energy_cost=1, weight=weight, visual_effect=visual,
                              status_effect=status))
    return Enemy(name, hp=base_hp + scaling * level, energy=3, max_energy=3,
                 actions=actions, is_miniboss=False)


def choose_next_action(enemy):
    """Prepara o próximo ato; ataques especiais respeitam intervalos do chefe."""
    if getattr(enemy, "special_interval", 0) and (enemy.action_counter + 1) % enemy.special_interval == 0:
        special = enemy.special_action
        enemy.set_intent(special.action_type, special.value, special)
    else:
        choose_enemy_intent(enemy)
