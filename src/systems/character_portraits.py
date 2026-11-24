"""Retratos dedicados: fontes, recortes individuais e composição sem cortes."""
from src.systems.normal_enemy_catalog import BIOME_ENEMIES

# Retiram apenas a borda antiga e o espaço vazio acima do personagem.
# Cada fonte mantém rosto, orelhas, crista, chifres ou focinho visíveis.
COMMON_PORTRAIT_SPECS = {
    'lutador mascarado': ('enemies/01.png', (.04,.23,.92,.73), 'framed-contain'),
    'golem das ruínas': ('enemies/02.png', (.04,.17,.92,.79), 'framed-contain'),
    'mago do santuário': ('enemies/03.png', (.04,.17,.92,.79), 'framed-contain'),
    'lagarto couraçado': ('enemies/04.png', (.04,.21,.92,.75), 'framed-contain'),
    'crocodilo abissal': ('enemies/05.png', (.04,.30,.92,.66), 'framed-contain'),
    'vinimuth': ('enemies/06.png', (.04,.07,.92,.89), 'framed-contain'),
    'esqueleto saqueador': ('enemies/07.png', (.04,.19,.92,.77), 'framed-contain'),
    'guerreiro da mata': ('enemies/08.png', (.04,.18,.92,.78), 'framed-contain'),
    'putrefato do pântano': ('enemies/09.png', (.04,.15,.92,.81), 'framed-contain'),
    'morcego sombrio': ('enemies/10.png', (.04,.18,.92,.78), 'framed-contain'),
    'centauro vigia': ('enemies/11.png', (.04,.17,.92,.79), 'framed-contain'),
    'viniurgo': ('framed/viniurgo.png', (.04,.03,.92,.94), 'framed-contain'),
    'slime': ('dedicated/slime.png', (0,0,1,1), 'framed-contain'),
    'macaco selvagem': ('dedicated/macaco_selvagem.png', (0,0,1,1), 'framed-contain'),
}

FRAMED_PORTRAITS = {
    'jaum manel': 'manel', 'guardião da pedra': 'guardiao',
    'álvaro e tex': 'alvaro_tex', 'álvaro e tex · pequeno': 'tex',
    'goblin nerd': 'goblin_nerd', 'gordofera': 'gordofera',
    'corpo seco': 'corpo_seco', 'carrasco da vigília': 'carrasco',
    'zanzara': 'manel',
}
PORTRAITS = {
    name: (f'framed/{file}.png', (0,0,1,1), 'framed')
    for name,file in FRAMED_PORTRAITS.items() if name != 'zanzara'
}
# Zanzara mantém a composição e a face já aprovadas.
PORTRAITS['zanzara'] = ('bosses/zanzara-necromante-v8.png', (0,0,1,1), 'framed-content')
PORTRAITS['zanzara · diálogo'] = ('bosses/zanzara-necromante-dialogo.png', (0,0,1,1), 'framed-content')
PORTRAITS.update(COMMON_PORTRAIT_SPECS)
for names in BIOME_ENEMIES.values():
    for name in names:
        FRAMED_PORTRAITS.setdefault(name.lower(),'manel')

# Dois comuns adicionais registrados no gerador aleatório legado.
LEGACY_COMMON_PORTRAIT_SPECS = {
    'goblin': ('dedicated/goblin.png', (0,0,1,1), 'framed-contain'),
    'guarda sombrio': ('dedicated/guarda_sombrio.png', (0,0,1,1), 'framed-contain'),
}
PORTRAITS.update(LEGACY_COMMON_PORTRAIT_SPECS)
FRAMED_PORTRAITS.update({name:'manel' for name in LEGACY_COMMON_PORTRAIT_SPECS})
