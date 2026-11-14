"""Coleção e deck equipado: espaços individuais, uma cópia por espaço.

O deck possui DECK_SLOT_LIMIT espaços; cada carta possui no máximo
COPIES_PER_CARD cópias no deck. A ordem dos espaços não influencia o jogo:
o baralho de combate é embaralhado ao iniciar cada luta. Durante a edição
o deck pode ficar com zero cartas; DECK_MIN_CARDS vale apenas para sair da
Mochila. Na Mochila, as alterações acontecem em um rascunho em memória:
somente um deck válido é promovido a deck oficial e gravado no save.
O desbloqueio pertence à RUN. A ultimate é independente do deck.
"""

import random
from collections import Counter

from src.systems.card_catalog import AVAILABLE_CARD_NAMES, CARD_BY_NAME, UNAVAILABLE_CARD_NAMES
from src.systems.card_definitions import migrate_card_name

CARD_NAMES = frozenset(CARD_BY_NAME)
DECK_SLOT_LIMIT = 18  # Quantidade máxima de espaços individuais no deck. Pode mudar no futuro.
DECK_MIN_CARDS = 6    # Mínimo de cópias para sair da Mochila (cada espaço preenchido conta 1).
COPIES_PER_CARD = 3   # Limite de cópias do mesmo tipo de carta no deck.
# Alvo do "Deck aleatório"; limitado ao total de cópias possíveis da coleção.
RANDOM_DECK_SIZE = DECK_SLOT_LIMIT
INITIAL_STARTERS = ["Soco Simples", "Esfera Protetora"]
INITIAL_SLOTS = (
    [name for name in INITIAL_STARTERS for _ in range(COPIES_PER_CARD)]
    + [None] * (DECK_SLOT_LIMIT - len(INITIAL_STARTERS) * COPIES_PER_CARD)
)
LEGACY_SLOT_COUNT = 6  # Formato antigo (SAVE_VERSION <= 8): um espaço por tipo, 3 cópias cada.


def deck_cards(slots):
    """Cartas preenchidas nos espaços, na ordem. O combate embaralha a pilha."""
    return [name for name in slots if isinstance(name, str)]


def deck_copy_count(slots):
    """Conta cópias ocupando espaços, não tipos distintos de carta."""
    return len(deck_cards(slots or ()))


def deck_is_ready_for_exit(slots):
    """Indica se o deck tem o mínimo de cópias para sair da Mochila."""
    return deck_copy_count(slots) >= DECK_MIN_CARDS


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


def initial_deck_slots(collection):
    """Deck inicial do tutorial restrito às cartas que o jogador possui.

    O deck novo nasce com INITIAL_STARTERS (3 cópias de cada), formando
    DECK_MIN_CARDS cartas. Este fallback só usa cartas da coleção e do
    catálogo jogável, nunca altera a coleção e nunca lança exceção.
    """
    owned = {
        name
        for name in collection or ()
        if isinstance(name, str) and name in AVAILABLE_CARD_NAMES
    }
    slots = []
    for name in INITIAL_STARTERS:
        if name in owned:
            slots.extend([name] * COPIES_PER_CARD)
    return (slots + [None] * DECK_SLOT_LIMIT)[:DECK_SLOT_LIMIT]


def random_deck_capacity(collection):
    """Quantas cópias o deck aleatório consegue montar com a coleção atual.

    Cada carta possuída e jogável contribui com até COPIES_PER_CARD cópias,
    sempre respeitando DECK_SLOT_LIMIT e o alvo RANDOM_DECK_SIZE.
    """
    owned = {
        name
        for name in collection or ()
        if isinstance(name, str) and name in AVAILABLE_CARD_NAMES
    }
    return min(DECK_SLOT_LIMIT, RANDOM_DECK_SIZE, len(owned) * COPIES_PER_CARD)


def build_random_deck(collection, rng=None):
    """Sorteia um deck a partir da coleção, sem alterar o save.

    Retorna uma lista com DECK_SLOT_LIMIT espaços (cópias sorteadas e None no
    restante) ou None quando a coleção não permite atingir DECK_MIN_CARDS.
    `rng` pode receber um random.Random com semente fixa para testes.
    """
    rng = rng if rng is not None else random.Random()
    owned = sorted({
        name
        for name in collection or ()
        if isinstance(name, str) and name in AVAILABLE_CARD_NAMES
    })
    target = min(RANDOM_DECK_SIZE, DECK_SLOT_LIMIT, len(owned) * COPIES_PER_CARD)
    if target < DECK_MIN_CARDS:
        return None
    pool = [name for name in owned for _ in range(COPIES_PER_CARD)]
    chosen = rng.sample(pool, target)
    return chosen + [None] * (DECK_SLOT_LIMIT - len(chosen))


def normalize_collection_and_slots(progress):
    """Valida deck e coleção, migrando saves antigos sem perder cartas.

    - Saves v<=8 guardavam 'deck_slots' como tipos (até 6 espaços, 3 cópias
      por tipo). Cada tipo vira COPIES_PER_CARD espaços individuais.
    - Saves v9 guardam um espaço por cópia e sempre DECK_SLOT_LIMIT entradas.
    - Deck ausente: preenche a partir das cartas antigas; se não houver,
      usa o deck inicial do tutorial.
    - Entradas fora da coleção/catálogo são descartadas. Se o deck ficar
      abaixo de DECK_MIN_CARDS, ele é substituído pelo deck inicial do
      tutorial, restrito às cartas que o jogador possui. A coleção existente
      nunca é apagada nem trocada por causa disso.
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
    if not owned:
        # Save anterior à coleção (ou sem nenhuma carta registrada): garante
        # os iniciais do tutorial para o jogador poder montar o deck.
        starters = [name for name in INITIAL_STARTERS if name in AVAILABLE_CARD_NAMES]
        owned.extend(starters)
        playable_owned.update(starters)

    slots = progress.get('deck_slots')
    if not isinstance(slots, list):
        # Sem deck registrado: reparte as cartas antigas; sem elas, o inicial.
        playable = [name for name in legacy if name in playable_owned]
        slots = _expand_names(playable) if playable else initial_deck_slots(owned)
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
    if deck_copy_count(slots) < DECK_MIN_CARDS:
        # Deck vazio, incompleto ou com cartas que saíram da coleção:
        # restaura o deck inicial do tutorial, restrito ao que o jogador
        # possui. Nunca inventa cartas nem lança exceção.
        slots = initial_deck_slots(owned)
    progress['cartas_colecao'] = owned
    progress['deck_slots'] = slots
    progress['cartas'] = deck_cards(slots)
    return progress


def _draft_slots(slots):
    """Copia um rascunho garantindo DECK_SLOT_LIMIT espaços."""
    return (list(slots or ()) + [None] * DECK_SLOT_LIMIT)[:DECK_SLOT_LIMIT]


def add_card_to_slots(slots, collection, name):
    """Adiciona 1 cópia ao rascunho sem gravar no save.

    Recusa a cópia quando a carta já possui COPIES_PER_CARD exemplares no
    rascunho ou quando não há espaço livre. Retorna
    (sucesso, mensagem, novos_slots); o chamador decide quando promover o
    rascunho com commit_deck.
    """
    updated = _draft_slots(slots)
    if not isinstance(name, str) or name not in CARD_NAMES:
        return False, "Carta desconhecida.", updated
    if name in UNAVAILABLE_CARD_NAMES:
        return False, "Carta indisponível no momento.", updated
    if name not in (collection or ()):
        return False, "Carta não encontrada na coleção.", updated
    copies = sum(1 for item in updated if item == name)
    if copies >= COPIES_PER_CARD:
        return False, f"Você já tem {COPIES_PER_CARD} cópias de {name} no deck.", updated
    try:
        index = updated.index(None)
    except ValueError:
        return False, f"O deck está cheio ({DECK_SLOT_LIMIT}/{DECK_SLOT_LIMIT}).", updated
    updated[index] = name
    return True, f"{name} adicionada ao deck ({copies + 1}/{COPIES_PER_CARD}).", updated


def remove_card_from_slots(slots, slot_index):
    """Remove uma cópia do rascunho, inclusive a última, sem gravar no save.

    A remoção pode deixar o rascunho com zero cartas; o mínimo de
    DECK_MIN_CARDS vale apenas para sair da Mochila. Retorna
    (sucesso, mensagem, novos_slots).
    """
    updated = _draft_slots(slots)
    if type(slot_index) is not int or not 0 <= slot_index < DECK_SLOT_LIMIT:
        return False, "Espaço inválido.", updated
    name = updated[slot_index]
    if not isinstance(name, str):
        return False, "O espaço já está vazio.", updated
    updated[slot_index] = None
    return True, f"{name} removida do deck.", updated


def empty_deck_slots():
    """Rascunho vazio, com todos os espaços disponíveis."""
    return [None] * DECK_SLOT_LIMIT


def commit_deck(save_manager, data, slots):
    """Promove o rascunho a deck oficial somente se ele for válido.

    O deck com menos de DECK_MIN_CARDS cartas nunca sobrescreve o último
    deck válido gravado no save. Retorna (sucesso, mensagem).
    """
    from copy import deepcopy
    from src.systems.save_manager import SaveError
    candidate = _draft_slots(slots)
    if not deck_is_ready_for_exit(candidate):
        return False, (
            f"O deck precisa de pelo menos {DECK_MIN_CARDS} cartas para ser salvo."
        )
    p = data['progresso']
    before = deepcopy(p)
    p['deck_slots'] = candidate
    p['cartas'] = deck_cards(candidate)
    try:
        save_manager.save(data)
    except (OSError, ValueError, TypeError, SaveError):
        data['progresso'] = before
        return False, "Falha ao gravar a alteração; deck preservado."
    return True, "Deck salvo."


def set_random_deck(save_manager, data, rng=None):
    """Substitui o deck por um sorteio da coleção e persiste a alteração.

    O deck aleatório sempre atinge DECK_MIN_CARDS, então é promovido
    imediatamente. Não mexe na coleção. Se a coleção não permitir o mínimo,
    devolve False e preserva o deck atual.
    """
    p = data['progresso']
    slots = build_random_deck(p['cartas_colecao'], rng=rng)
    if slots is None:
        return False, (
            f"Coleção insuficiente: mínimo de {DECK_MIN_CARDS} cópias."
        )
    success, message = commit_deck(save_manager, data, slots)
    if not success:
        return False, message
    return True, f"Deck aleatório montado: {deck_copy_count(slots)} cartas."


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
