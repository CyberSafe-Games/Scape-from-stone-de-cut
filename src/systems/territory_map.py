"""Definições e regras de progressão da campanha; independente do Pygame.

Cada território corresponde a um confronto do motor atual (andares 1–7).
A campanha tem um ponto de entrada: não é possível saltar etapas bloqueadas.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Territory:
    id: str
    title: str
    subtitle: str
    description: str
    level: int
    position: tuple[int, int]


TERRITORIES = (
    Territory("stone_the_cut", "Pedra do Corte", "O despertar", "O Guardião da Pedra protege os monólitos da clareira ancestral.", 1, (131, 548)),
    Territory("mata_sombria", "Mata Sombria", "O chamado", "Uma passagem na floresta onde nem toda sombra está imóvel.", 2, (263, 452)),
    Territory("ruinas_ancestrais", "Ruínas Ancestrais", "Ecos do passado", "Marcas de uma civilização esquecida acompanham o caminho.", 3, (166, 317)),
    Territory("pantano_abissal", "Pântano Abissal", "Águas escuras", "Águas silenciosas escondem novas ameaças.", 4, (356, 235)),
    Territory("fortaleza_caida", "Fortaleza Caída", "O cerco", "Antigos muros guardam histórias e novos confrontos.", 5, (503, 397)),
    Territory("pico_da_vigilia", "Pico da Vigília", "Última subida", "O Carrasco da Vigília guarda a passagem entre os picos.", 6, (641, 281)),
    Territory("santuario_de_pedra", "Santuário de Pedra", "O destino", "O último portal da campanha aguarda sua chegada.", 7, (788, 164)),
)

TERRITORY_IDS = tuple(item.id for item in TERRITORIES)
FIRST_TERRITORY_ID = TERRITORY_IDS[0]


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
    """Estado do ponto principal (None) ou de um dos três encontros (0–2)."""
    territory_state = status(data, territory_id)
    if index is not None and (type(index) is not int or not 0 <= index < 3):
        raise ValueError('Encontro fora do caminho.')
    if territory_state == 'locked':
        return 'locked'
    if territory_state == 'completed':
        return 'completed'
    count = data['progresso'].get('encontros_por_territorio', {}).get(territory_id, 0)
    if index is None:
        return 'available' if count >= 3 else 'locked'
    return 'completed' if index < count else 'available' if index == count else 'locked'


def encounter_positions(territory_id):
    territory = by_id(territory_id)
    start = by_level(territory.level - 1).position if territory.level > 1 else (45, 660)
    end = territory.position
    return tuple((round(start[0] + (end[0] - start[0]) * t),
                  round(start[1] + (end[1] - start[1]) * t)) for t in (.25, .5, .75))
