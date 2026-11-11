"""Retratos fornecidos pelo usuário: arquivo, recorte relativo e enquadramento."""
PORTRAITS = {
    'guardião da pedra': ('bosses/01.jpeg', (0, 0, 1, .82), 'cover'),
    'álvaro e tex': ('bosses/02.png', (.25, 0, .75, 1), 'contain'),
    'álvaro e tex · pequeno': ('bosses/02.png', (.23, .01, .35, .72), 'cover'),
    'goblin nerd': ('bosses/03.jpeg', (0, .02, 1, .68), 'cover'),
    'gordofera': ('bosses/04.jpeg', (.06, .10, .88, .88), 'cover'),
    'corpo seco': ('bosses/05.jpeg', (0, 0, 1, 1), 'cover'),
    'carrasco da vigília': ('bosses/06.jpeg', (0, 0, 1, 1), 'cover'),
    'zanzara': ('bosses/07.jpeg', (.12, .01, .76, .98), 'cover'),
}

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
    'zanzara': 'zanzara', 'viniurgo': 'viniurgo',
}
PORTRAITS.update({
    name: (f'framed/{file}.png', (0, 0, 1, 1), 'framed')
    for name, file in FRAMED_PORTRAITS.items()
})
