"""Retratos fornecidos pelo usuário: arquivo, recorte relativo e enquadramento."""
PORTRAITS = {}

for name, file in (
    ('Lutador Mascarado', '01.png'), ('Golem das Ruínas', '02.png'),
    ('Mago do Santuário', '03.png'), ('Lagarto Couraçado', '04.png'),
    ('Crocodilo Abissal', '05.png'), ('Vinimuth', '06.png'),
    ('Esqueleto Saqueador', '07.png'), ('Guerreiro da Mata', '08.png'),
    ('Putrefato do Pântano', '09.png'), ('Morcego Sombrio', '10.png'),
    ('Centauro Vigia', '11.png'),
):
    PORTRAITS[name.lower()] = ('enemies/'+file, (.09, .32, .82, .64), 'cover')

FRAMED_PORTRAITS = {
    'jaum manel': 'manel', 'guardião da pedra': 'guardiao',
    'álvaro e tex': 'alvaro_tex', 'álvaro e tex · pequeno': 'tex',
    'goblin nerd': 'goblin_nerd', 'gordofera': 'gordofera',
    'corpo seco': 'corpo_seco', 'carrasco da vigília': 'carrasco',
    'zanzara': 'manel', 'viniurgo': 'viniurgo',
}
PORTRAITS.update({
    name: (f'framed/{file}.png', (0, 0, 1, 1), 'framed')
    for name, file in FRAMED_PORTRAITS.items()
    if name != 'zanzara'
})

# Preserva o rosto aprovado usando a mesma moldura do protagonista.
PORTRAITS['zanzara'] = ('bosses/zanzara-necromante-v8.png', (0, 0, 1, 1), 'framed-content')
