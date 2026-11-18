"""Inventário individual e ciclo de vida da run, sem dependência gráfica."""
from copy import deepcopy
from uuid import uuid4

from src.systems.card_catalog import AVAILABLE_CARD_NAMES, CARD_BY_NAME

PROFILE_FIELDS = ('tutorial_concluido', 'intro_vista', 'pos_tutorial_visto',
                  'guia_mapa_visto', 'ultimates_desbloqueadas', 'ultimate_equipada')
FRAGMENTS = (1, 1, 2, 2, 3, 3, 5)
ROAD_GOLD = (35, 40, 40, 45, 45, 50, 50)
BOSS_GOLD = (60, 65, 70, 75, 80, 85, 100)
MATERIAL_PRICE = 15
MATERIAL_LIMIT = 9
UPGRADE_LIMIT = 3
CARD_PRICES = dict(zip(
    ('Soco Simples', 'Esfera Protetora', 'Investida', 'Disparo de Arco',
     'Lança Perfurante', 'Machados Gêmeos', 'Aura Rubra', 'Poção Fragilizante',
     'Poção Purificadora', 'Totem Protetor', 'Zarabatana Venenosa', 'Poção Venenosa',
     'Adaga Sangrenta', 'Bola de Fogo', 'Esfera Escudo', 'Machado Quebra-Escudo',
     'Amuleto Dissipador', 'Poção de Cura', 'Máscara Ancestral', 'Surto de Energia'),
    (30, 35, 40, 55, 65, 85, 65, 45, 45, 75, 75, 50, 60, 55, 65, 35, 60, 75, 90, 40)))
UPGRADE_PRICES = dict(zip(CARD_PRICES,
    (40, 40, 45, 55, 60, 70, 65, 50, 50, 65, 65, 55, 55, 55, 60, 40, 55, 65, 75, 45)))
LEVEL_TWO_VALUES = dict(zip(CARD_PRICES,
    (9, 14, 24, 26, 38, 50, 8, 3, 0, 1, 16, 2, 14, 18, 42, 0, 0, 26, 24, 3)))
EXTRA_BLOCK = {'Poção Fragilizante': 5, 'Totem Protetor': 8,
               'Poção Venenosa': 6, 'Machado Quebra-Escudo': 8, 'Amuleto Dissipador': 8}
PREPARATION = ('Investida', 'Disparo de Arco', 'Poção Purificadora',
               'Lança Perfurante', 'Esfera Escudo', 'Poção Venenosa')


def normalize_inventory(progress):
    """Cria três instâncias por tipo; editar espaços nunca produz materiais."""
    copies = progress.setdefault('copies', [])
    if not isinstance(copies, list) or any(not isinstance(c, dict) for c in copies):
        raise ValueError('Inventário de cópias inválido.')
    for name in progress['cartas_colecao']:
        if name not in AVAILABLE_CARD_NAMES:
            continue
        existing = [c for c in copies if c['name'] == name]
        for _ in range(3 - len(existing)):
            copies.append({'id': uuid4().hex, 'name': name, 'level': 1})
    ids = set()
    for c in copies:
        if (not isinstance(c, dict) or c.get('name') not in AVAILABLE_CARD_NAMES
                or type(c.get('level')) is not int or c.get('level') not in (1, 2)
                or not isinstance(c.get('id'), str)
                or c['id'] in ids):
            raise ValueError('Inventário de cópias inválido.')
        ids.add(c['id'])
    if any(sum(c['name'] == name for c in copies) > 3 for name in AVAILABLE_CARD_NAMES):
        raise ValueError('Mais de três cópias equipáveis do mesmo tipo.')
    previous = progress.get('copy_slots', [])
    chosen, used = [], set()
    for i, name in enumerate(progress['deck_slots']):
        available = [c for c in copies if c['name'] == name and c['id'] not in used]
        old = previous[i] if i < len(previous) else None
        card = next((c for c in available if c['id'] == old), None)
        card = card or next(iter(sorted(available, key=lambda c: -c['level'])), None)
        chosen.append(card['id'] if card else None)
        if card:
            used.add(card['id'])
    progress['copy_slots'] = chosen
    materials = progress.setdefault('materials', {})
    if (not isinstance(materials, dict) or any(k not in AVAILABLE_CARD_NAMES or
            type(v) is not int or not 0 <= v <= MATERIAL_LIMIT for k, v in materials.items())):
        raise ValueError('Reserva de materiais inválida.')
    count = progress.setdefault('upgrades_purchased', 0)
    if type(count) is not int or not 0 <= count <= UPGRADE_LIMIT:
        raise ValueError('Contador de evoluções inválido.')
    if sum(c['level'] == 2 for c in copies) != count:
        raise ValueError('Contador de evoluções diverge das cópias.')


def normalize_profile(data):
    p = data['progresso']
    profile = data.setdefault('perfil', {'id': uuid4().hex, 'fragmentos': 0,
        'vida': 0, 'energia': 0, 'preparacao': 0, 'preparada': None,
        'melhor_territorio': 1, 'campanhas_concluidas': 0})
    for field, limit in (('fragmentos', None), ('vida', 3), ('energia', 1), ('preparacao', 2)):
        value = profile.get(field)
        if type(value) is not int or value < 0 or (limit is not None and value > limit):
            raise ValueError('Melhoria permanente inválida.')
    for key in PROFILE_FIELDS:
        profile[key] = deepcopy(p[key])
    p['bonus_vida_permanente'] = 5 * profile['vida']
    p['energia_inicial'] = 2 + profile['energia']
    p.setdefault('run_id', uuid4().hex)
    p.setdefault('estado', 'concluida' if len(p['territorios_concluidos']) == 7
                 and not data.get('modo_teste') else 'ativa')
    if p['estado'] not in ('ativa', 'morta', 'concluida'):
        raise ValueError('Estado da run inválido.')
    p.setdefault('received_rewards', [])
    if (not isinstance(p['received_rewards'], list)
            or any(not isinstance(key, str) for key in p['received_rewards'])
            or len(set(p['received_rewards'])) != len(p['received_rewards'])):
        raise ValueError('Registro de recompensas inválido.')
    p.setdefault('combat_snapshot', None)
    normalize_inventory(p)
    data['run'] = p


def instance_card(copy):
    card = CARD_BY_NAME[copy['name']].copy()
    card.copy_id, card.level = copy['id'], copy['level']
    if card.level == 2:
        card.value = LEVEL_TWO_VALUES[card.name]
        card.description = card.description.replace(str(CARD_BY_NAME[card.name].value), str(card.value), 1)
        extra = EXTRA_BLOCK.get(card.name)
        if extra:
            card.description += f' Receba também {extra} de Escudo.'
        if card.name == 'Poção Purificadora':
            card.description += ' Recupere 6 de vida.'
        if card.name == 'Máscara Ancestral':
            card.description = 'Recupere 24 de vida e receba 28 de Escudo por 2 turnos.'
    return card


def transact(manager, data, mutate):
    """Restaura o documento completo se a operação não puder ser persistida."""
    before = deepcopy(data)
    from src.systems.save_manager import SaveError
    try:
        message = mutate()
        manager.save(data)
    except (OSError, ValueError, TypeError, RuntimeError, SaveError) as exc:
        data.clear()
        data.update(before)
        data['run'] = data['progresso']
        return False, str(exc)
    return True, message


def purchase_material(manager, data, name):
    def mutate():
        p = data['progresso']
        if p['estado'] != 'ativa' or p.get('combat_snapshot') or name not in p['cartas_colecao']:
            raise ValueError('Adquira o tipo durante uma run ativa primeiro.')
        if p['materials'].get(name, 0) >= MATERIAL_LIMIT or p['moedas'] < MATERIAL_PRICE:
            raise ValueError('Sem ouro ou reserva já completa (9).')
        p['moedas'] -= MATERIAL_PRICE
        p['materials'][name] = p['materials'].get(name, 0) + 1
        return 'Um material adicionado à reserva.'
    return transact(manager, data, mutate)


def upgrade_copy(manager, data, copy_id):
    def mutate():
        p = data['progresso']
        c = next((c for c in p['copies'] if c['id'] == copy_id), None)
        if p['estado'] != 'ativa' or p.get('combat_snapshot') or not c or c['level'] != 1:
            raise ValueError('Escolha uma cópia nível 1 de uma run ativa.')
        name = c['name']
        if p['upgrades_purchased'] >= 3:
            raise ValueError('Limite de três evoluções nesta run.')
        if p['materials'].get(name, 0) < 3 or p['moedas'] < UPGRADE_PRICES[name]:
            raise ValueError('Precisa de três materiais desse tipo e ouro suficiente.')
        p['materials'][name] -= 3
        p['moedas'] -= UPGRADE_PRICES[name]
        c['level'] = 2
        p['upgrades_purchased'] += 1
        return f'{name}: somente a cópia escolhida evoluiu para LV2.'
    return transact(manager, data, mutate)


def purchase_permanent(manager, data, kind):
    def mutate():
        profile = data['perfil']
        if data['progresso']['estado'] == 'ativa':
            raise ValueError('Melhorias permanentes são compradas entre runs.')
        prices = {'vida': (3, 5, 8), 'energia': (12,), 'preparacao': (4, 6)}
        if kind not in prices or profile[kind] >= len(prices[kind]):
            raise ValueError('Limite permanente atingido.')
        price = prices[kind][profile[kind]]
        if profile['fragmentos'] < price:
            raise ValueError('Fragmentos insuficientes.')
        profile['fragmentos'] -= price
        profile[kind] += 1
        return 'Melhoria permanente comprada; vale na próxima run.'
    return transact(manager, data, mutate)
