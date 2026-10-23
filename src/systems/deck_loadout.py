"""Coleção e deck equipado: seis espaços, três cartas por tipo escolhido.

A quantidade de cópias é fixa; apenas o tipo do espaço pode ser alterado.
O desbloqueio pertence à RUN. A ultimate é independente do deck.
"""

from collections import Counter
from src.systems.card_catalog import CARD_POOL

CARD_NAMES = frozenset(card.name for card in CARD_POOL)
SLOT_COUNT = 6
COPIES_PER_SLOT = 3
INITIAL_SLOTS = ["Golpe", "Defesa", None, None, None, None]


def normalize_collection_and_slots(progress):
    """Migra saves antigos conservando os tipos conhecidos, sem duplicar slots."""
    legacy = [name for name in progress.get('cartas', []) if name in CARD_NAMES]
    owned = progress.get('cartas_colecao')
    if not isinstance(owned, list):
        owned = list(dict.fromkeys(legacy))
    owned = list(dict.fromkeys(name for name in owned if isinstance(name, str) and name in CARD_NAMES))
    if not owned:
        owned = ['Golpe', 'Defesa']
    slots = progress.get('deck_slots')
    if not isinstance(slots, list):
        slots = list(dict.fromkeys(legacy))[:SLOT_COUNT]
        slots.extend([None] * (SLOT_COUNT-len(slots)))
    slots = (slots + [None]*SLOT_COUNT)[:SLOT_COUNT]
    seen = set()
    for i, name in enumerate(slots):
        if name not in owned or name in seen:
            slots[i] = None
        else:
            seen.add(name)
    if not seen:
        slots[0] = owned[0]
    progress['cartas_colecao'] = owned
    progress['deck_slots'] = slots
    progress['cartas'] = expand_slots(slots)
    return progress


def expand_slots(slots):
    return [name for name in slots if name is not None for _ in range(COPIES_PER_SLOT)]


def equip_card_type(save_manager, data, slot_index, name):
    """Equipa um tipo em um espaço. Não altera quantidade nem usa moeda.

    Aceita None para esvaziar, desde que ao menos um espaço continue ativo.
    """
    from copy import deepcopy
    if type(slot_index) is not int or not 0 <= slot_index < SLOT_COUNT:
        return False, "Espaço inválido."
    p = data['progresso']
    normalize_collection_and_slots(p)
    slots = list(p['deck_slots'])
    if name is not None:
        if name not in p['cartas_colecao']:
            return False, "Carta não encontrada na coleção."
        if name in slots and slots[slot_index] != name:
            return False, "Essa carta já está equipada em outro espaço."
    slots[slot_index] = name
    if all(item is None for item in slots):
        return False, "O deck precisa ter pelo menos um tipo de carta."
    before = deepcopy(p)
    p['deck_slots'] = slots
    p['cartas'] = expand_slots(slots)
    try:
        save_manager.save(data)
    except (OSError, ValueError, TypeError):
        data['progresso'] = before
        return False, "Falha ao gravar a alteração; deck preservado."
    return True, "Deck atualizado. Cada tipo equipado possui 3 cartas."
