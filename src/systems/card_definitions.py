"""Fonte única das cartas comuns: id, nome, custo, tipo, valor, regra, animação, texto."""
CARD_SPECS = [
 ('esfera_protetora', 'Esfera Protetora', 1, 'skill', 10, 'shield', 'self', 'Receba 10 de Escudo por 2 turnos.'),
 ('soco_simples', 'Soco Simples', 1, 'attack', 6, 'damage', 'melee', 'Cause 6 de dano.'),
 ('investida', 'Investida', 2, 'attack', 10, 'damage', 'melee', 'Cause 10 de dano.'),
 ('aura_rubra', 'Aura Rubra', 3, 'power', 8, 'aura', 'self', 'Seus ataques causam +8 de dano por 3 turnos. Reaplicar renova a duração.'),
 ('pocao_fragilizante', 'Poção Fragilizante', 3, 'skill', 3, 'vulnerable', 'ranged', 'Por 3 turnos, o inimigo recebe 25% a mais de dano de ataques.'),
 ('pocao_purificadora', 'Poção Purificadora', 3, 'skill', 0, 'cleanse', 'self', 'Remova todos os seus efeitos negativos.'),
 ('totem_protetor', 'Totem Protetor', 5, 'skill', 1, 'totem', 'self', 'Ignore o próximo ataque inimigo inteiro. Não bloqueia dano de efeitos.'),
 ('zarabatana_venenosa', 'Zarabatana Venenosa', 3, 'attack', 10, 'darts', 'ranged', 'Dispare 3 dardos: 10 de dano total e Veneno 5 por 3 turnos.'),
 ('disparo_de_arco', 'Disparo de Arco', 2, 'attack', 20, 'damage', 'ranged', 'Cause 20 de dano à distância.'),
 ('esfera_escudo', 'Esfera Escudo', 4, 'skill', 30, 'shield', 'self', 'Receba 30 de Escudo por 2 turnos.'),
 ('machado_quebra_escudo', 'Machado Quebra-Escudo', 5, 'skill', 0, 'break', 'melee', 'Destrua todo o Escudo do inimigo.'),
 ('amuleto_dissipador', 'Amuleto Dissipador', 4, 'skill', 0, 'dispel', 'ranged', 'Remova todos os efeitos do inimigo, positivos e negativos, incluindo Escudo e Força.'),
 ('adaga_sangrenta', 'Adaga Sangrenta', 3, 'attack', 5, 'bleed', 'melee', 'Cause 5 de dano. Por 2 turnos, o primeiro ataque do alvo causa 4 de Sangramento nele, ignorando Escudo.'),
 ('mascara_ancestral', 'Máscara Ancestral', 6, 'skill', 20, 'mask', 'self', 'Recupere 20 de vida e receba 20 de Escudo por 2 turnos.'),
 ('machados_gemeos', 'Machados Gêmeos', 4, 'attack', 40, 'damage', 'melee', 'Cause 40 de dano.'),
 ('lanca_perfurante', 'Lança Perfurante', 3, 'attack', 30, 'damage', 'melee', 'Cause 30 de dano.'),
 ('bola_de_fogo', 'Bola de Fogo', 4, 'attack', 10, 'fire', 'ranged', 'Cause 10 de dano e Fogo por 3 turnos: 3 de dano por intensidade ao fim do turno. Acumula até 3 intensidades e atinge Escudo primeiro.'),
 ('pocao_de_cura', 'Poção de Cura', 3, 'skill', 20, 'heal', 'self', 'Recupere 20 de vida, sem ultrapassar a vida máxima.'),
 ('surto_de_energia', 'Surto de Energia', 2, 'skill', 2, 'energy', 'self', 'Ganhe 2 de energia extra no próximo turno, até o limite de 8. Não aumenta sua energia máxima.'),
 ('pocao_venenosa', 'Poção Venenosa', 4, 'skill', 5, 'poison', 'ranged', 'Veneno: 5 de dano direto à vida ao fim do turno por 4 turnos. Reaplicar renova a duração, sem acumular dano.'),
]
SPECS_BY_NAME = {s[1]: s for s in CARD_SPECS}
LEGACY_CARD_NAMES = {'Golpe': 'Soco Simples', 'Defesa': 'Esfera Protetora', 'Fortalecer': 'Esfera Escudo', 'Fúria': 'Aura Rubra', 'Golpe Duplo': 'Machados Gêmeos'}


def migrate_card_name(name):
    return LEGACY_CARD_NAMES.get(name, name) if isinstance(name, str) else name
