"""Definições e regras de progressão da campanha; independente do Pygame.

Cada território corresponde a um confronto do motor atual (andares 1–7).
A campanha tem um ponto de entrada: não é possível saltar etapas bloqueadas.
"""
from dataclasses import dataclass
from src.config.boss_names import boss_display_name


@dataclass(frozen=True)
class Territory:
    id: str
    title: str
    subtitle: str
    description: str
    level: int
    position: tuple[int, int]
    boss_key: str

    @property
    def boss_name(self):
        return boss_display_name(self.boss_key)


TERRITORIES = (
    Territory("stone_the_cut", "Stone de Cut", "O despertar", "Monólitos ancestrais marcam a clareira.", 1, (197, 822), "Guardião da Pedra"),
    Territory("mata_sombria", "Mata Sombria", "O chamado", "A dupla espreita entre as árvores.", 2, (395, 678), "Álvaro e Tex"),
    Territory("ruinas_ancestrais", "Ruínas Ancestrais", "Ecos do passado", "Artefatos esquecidos alimentam engenhocas no meio das ruínas.", 3, (249, 476), "Goblin Nerd"),
    Territory("pantano_abissal", "Pântano Abissal", "Águas escuras", "Garras e chifres guardam a lama ancestral.", 4, (534, 353), "Gordofera"),
    Territory("fortaleza_caida", "Fortaleza Caída", "O cerco", "Antigos muros guardam os segredos da fortaleza.", 5, (755, 596), "Corpo Seco"),
    Territory("pico_da_vigilia", "Pico da Vigília", "Última subida", "Um carrasco guarda a passagem entre os picos.", 6, (962, 422), "Carrasco da Vigília"),
    Territory("santuario_de_pedra", "Santuário de Pedra", "O destino", "Uma foice e artes espectrais guardam o último portal.", 7, (1182, 246), "Zanzara"),
)

TERRITORY_IDS = tuple(item.id for item in TERRITORIES)
FIRST_TERRITORY_ID = TERRITORY_IDS[0]
ROAD_FIGHTS = 2


def by_id(territory_id):
    for territory in TERRITORIES:
        if territory.id == territory_id:
            return territory
    raise ValueError(f"Território desconhecido: {territory_id}")


def by_level(level):
    if type(level) is not int or not 1 <= level <= len(TERRITORIES):
        raise ValueError(f"Andar fora do mapa: {level}")
    return TERRITORIES[level - 1]


def status(data, territory_id):
    """Retorna 'completed', 'available' ou 'locked' a partir do save."""
    by_id(territory_id)
    progress = data["progresso"]
    if territory_id in progress["territorios_concluidos"]:
        return "completed"
    if territory_id in progress["territorios_desbloqueados"]:
        return "available"
    return "locked"


def complete(data, territory_id):
    """Marca vitória após recompensa e libera somente o território seguinte.

    Retorna o próximo território ou None para a fase final; é idempotente.
    """
    territory = by_id(territory_id)
    if status(data, territory_id) == "locked":
        raise ValueError("Não é possível concluir uma fase bloqueada.")
    progress = data["progresso"]
    completed = progress["territorios_concluidos"]
    if territory_id not in completed:
        completed.append(territory_id)
    if territory.level < len(TERRITORIES):
        nxt = by_level(territory.level + 1)
        if nxt.id not in progress["territorios_desbloqueados"]:
            progress["territorios_desbloqueados"].append(nxt.id)
        return nxt
    return None


def completed_count(data):
    return sum(id_ in data["progresso"]["territorios_concluidos"] for id_ in TERRITORY_IDS)


def encounter_status(data, territory_id, index=None):
    """Estado do ponto principal (None) ou de um encontro da rota."""
    territory_state = status(data, territory_id)
    if index is not None and (type(index) is not int or not 0 <= index < ROAD_FIGHTS):
        raise ValueError('Encontro fora do caminho.')
    if territory_state == 'locked':
        return 'locked'
    if territory_state == 'completed':
        return 'completed'
    count = data['progresso'].get('encontros_por_territorio', {}).get(territory_id, 0)
    if index is None:
        return 'available' if count >= ROAD_FIGHTS else 'locked'
    return 'completed' if index < count else 'available' if index == count else 'locked'


def encounter_positions(territory_id):
    territory = by_id(territory_id)
    start = by_level(territory.level - 1).position if territory.level > 1 else (68, 990)
    end = territory.position
    fractions = (step / (ROAD_FIGHTS + 1) for step in range(1, ROAD_FIGHTS + 1))
    return tuple((round(start[0] + (end[0] - start[0]) * t),
                  round(start[1] + (end[1] - start[1]) * t)) for t in fractions)
