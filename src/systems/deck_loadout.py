"""Coleção e deck equipado: espaços individuais, uma cópia por espaço.

O deck possui DECK_SLOT_LIMIT espaços; cada carta possui no máximo
COPIES_PER_CARD cópias no deck. A ordem dos espaços não influencia o jogo:
o baralho de combate é embaralhado ao iniciar cada luta.
O desbloqueio pertence à RUN. A ultimate é independente do deck.
"""

from collections import Counter

from src.systems.card_catalog import AVAILABLE_CARD_NAMES, CARD_BY_NAME, UNAVAILABLE_CARD_NAMES
from src.systems.card_definitions import migrate_card_name

CARD_NAMES = frozenset(CARD_BY_NAME)
DECK_SLOT_LIMIT = 18  # Quantidade máxima de espaços individuais no deck. Pode mudar no futuro.
COPIES_PER_CARD = 3   # Limite de cópias do mesmo tipo de carta no deck.
MIN_DECK_COPIES = 1   # O deck precisa ter pelo menos uma carta para entrar em combate.
INITIAL_STARTERS = ["Soco Simples", "Esfera Protetora"]
INITIAL_SLOTS = (
    [name for name in INITIAL_STARTERS for _ in range(COPIES_PER_CARD)]
    + [None] * (DECK_SLOT_LIMIT - len(INITIAL_STARTERS) * COPIES_PER_CARD)
)
LEGACY_SLOT_COUNT = 6  # Formato antigo (SAVE_VERSION <= 8): um espaço por tipo, 3 cópias cada.


def deck_cards(slots):
    """Cartas preenchidas nos espaços, na ordem. O combate embaralha a pilha."""
    return [name for name in slots if isinstance(name, str)]


def _expand_names(names, limit=DECK_SLOT_LIMIT, copies=COPIES_PER_CARD):
    """Expande nomes em até `copies` espaços cada, respeitando o limite total."""
    slots = []
    for name in dict.fromkeys(names):
        if name not in CARD_NAMES:
            continue
        slots.extend([name] * copies)
        if len(slots) >= limit:
            return slots[:limit]
    return slots


def normalize_collection_and_slots(progress):
    """Valida deck e coleção, migrando saves antigos sem perder cartas.

    - Saves v<=8 guardavam 'deck_slots' como tipos (até 6 espaços, 3 cópias
      por tipo). Cada tipo vira COPIES_PER_CARD espaços individuais.
    - Saves v9 guardam um espaço por cópia e sempre DECK_SLOT_LIMIT entradas.
    - Deck ausente: preenche a partir das cartas antigas; se não houver,
      reparte a coleção em até COPIES_PER_CARD cópias por carta.
    - A ordem dos espaços não importa: o baralho é embaralhado no combate.
    """
    for field in ('cartas', 'cartas_colecao', 'deck_slots'):
        if isinstance(progress.get(field), list):
            progress[field] = [migrate_card_name(name) for name in progress[field]]
    legacy = [name for name in progress.get('cartas', []) if isinstance(name, str) and name in CARD_NAMES]
    owned = progress.get('cartas_colecao')
    if not isinstance(owned, list):
        owned = list(dict.fromkeys(legacy))
    owned = list(dict.fromkeys(name for name in owned if isinstance(name, str) and name in CARD_NAMES))
    playable_owned = set(owned).intersection(AVAILABLE_CARD_NAMES)
    if not playable_owned:
        starters = [name for name in INITIAL_STARTERS if name in AVAILABLE_CARD_NAMES]
        owned.extend(starters)
        playable_owned.update(starters)

    slots = progress.get('deck_slots')
    if not isinstance(slots, list):
        # Sem deck registrado: reparte as cartas antigas; sem elas, a coleção.
        playable = [name for name in legacy if name in playable_owned]
        slots = _expand_names(playable)
        if not slots:
            slots = _expand_names([name for name in owned if name in playable_owned])
    elif len(slots) <= LEGACY_SLOT_COUNT:
        # Formato antigo: um espaço por tipo, três cópias cada.
        slots = _expand_names([name for name in slots if isinstance(name, str) and name in playable_owned])
    else:
        slots = list(slots)
    slots = (slots + [None] * DECK_SLOT_LIMIT)[:DECK_SLOT_LIMIT]

    used = Counter()
    for i, name in enumerate(slots):
        if not isinstance(name, str) or name not in playable_owned or used[name] >= COPIES_PER_CARD:
            slots[i] = None
            continue
        used[name] += 1
    if not used:
        # Nunca deixa o deck vazio: começa pelas cartas jogáveis que o jogador tem.
        slots = _expand_names([name for name in owned if name in playable_owned])
        slots = (slots + [None] * DECK_SLOT_LIMIT)[:DECK_SLOT_LIMIT]
    progress['cartas_colecao'] = owned
    progress['deck_slots'] = slots
    progress['cartas'] = deck_cards(slots)
    return progress


def add_card_to_deck(save_manager, data, name):
    """Adiciona 1 cópia da carta ao próximo espaço livre.

    Recusa a cópia quando a carta já possui COPIES_PER_CARD exemplares no
    deck ou quando não há espaço livre. Não altera nada em caso de falha.
    """
    from copy import deepcopy
    if not isinstance(name, str) or name not in CARD_NAMES:
        return False, "Carta desconhecida."
    if name in UNAVAILABLE_CARD_NAMES:
        return False, "Carta indisponível no momento."
    p = data['progresso']
    normalize_collection_and_slots(p)
    if name not in p['cartas_colecao']:
        return False, "Carta não encontrada na coleção."
    slots = list(p['deck_slots'])
    copies = slots.count(name)
    if copies >= COPIES_PER_CARD:
        return False, f"Você já tem {COPIES_PER_CARD} cópias de {name} no deck."
    try:
        index = slots.index(None)
    except ValueError:
        return False, f"O deck está cheio ({DECK_SLOT_LIMIT}/{DECK_SLOT_LIMIT})."
    before = deepcopy(p)
    slots[index] = name
    p['deck_slots'] = slots
    p['cartas'] = deck_cards(slots)
    try:
        save_manager.save(data)
    except (OSError, ValueError, TypeError):
        data['progresso'] = before
        return False, "Falha ao gravar a alteração; deck preservado."
    return True, f"{name} adicionada ao deck ({copies + 1}/{COPIES_PER_CARD})."


def remove_card_from_deck(save_manager, data, slot_index):
    """Libera o espaço indicado, removendo apenas aquela cópia."""
    from copy import deepcopy
    if type(slot_index) is not int or not 0 <= slot_index < DECK_SLOT_LIMIT:
        return False, "Espaço inválido."
    p = data['progresso']
    normalize_collection_and_slots(p)
    slots = list(p['deck_slots'])
    name = slots[slot_index]
    if name is None:
        return False, "O espaço já está vazio."
    if sum(item is not None for item in slots) <= MIN_DECK_COPIES:
        return False, "O deck precisa ter pelo menos uma carta."
    before = deepcopy(p)
    slots[slot_index] = None
    p['deck_slots'] = slots
    p['cartas'] = deck_cards(slots)
    try:
        save_manager.save(data)
    except (OSError, ValueError, TypeError):
        data['progresso'] = before
        return False, "Falha ao gravar a alteração; deck preservado."
    return True, f"{name} removida do deck."


def equip_ultimate(save_manager, data, ultimate_id):
    """Troca a habilidade da preparação sem consumir carga nem ocupar o deck."""
    from copy import deepcopy
    from src.models.effects.ultimate_effect import ULTIMATE_METADATA
    from src.systems.save_manager import SaveError
    progress = data['progresso']
    if ultimate_id not in ULTIMATE_METADATA or ultimate_id not in progress.get('ultimates_desbloqueadas', []):
        return False, 'Ultimate indisponível.'
    before = deepcopy(progress)
    progress['ultimate_equipada'] = ultimate_id
    try:
        save_manager.save(data)
    except (OSError, ValueError, TypeError, SaveError):
        data['progresso'] = before
        return False, 'Não foi possível salvar. Sua ultimate anterior foi mantida.'
    return True, ULTIMATE_METADATA[ultimate_id]['name'] + ' equipada para os próximos combates.'
