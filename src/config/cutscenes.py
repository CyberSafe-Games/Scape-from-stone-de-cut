# Edite "image" e "text" em cada quadro: texto vazio não exibe caixa;
# "position" aceita "bottom" ou "top"; use \n para quebra manual.

INTRO_CUTSCENE = [
        {
        "image": "cutscenes/intro_01.png",
        "music_context": "battle",
        "dialogues": [
            ("Jaum Manel", "Moravamos em terras isoládas do resto do mundo, conhecida pelos estrangeiros como Stone de Cut, respeitavamos a natureza e assim vivíamos em paz."),
            ("Jaum Manel", "Porém mal sabíamos que essa paz estava prestes a se acabar..."),
        ],
        "position": "bottom",
    },
    {
        "image": "cutscenes/intro_02.png",
        "music_context": "boss",
        "dialogues": [
            ("Jaum Manel", "Nossa aldeia foi invadida por um grupo de estrangeiros."),
            ("Jaum Manel", "Em questão de minutos nossa aldeia estava cercada."),
        ],
        "position": "bottom",
    },
    {
        "image": "cutscenes/intro_03.png",
        "music_context": "boss",
        "dialogues": [
            ("Jaum Manel", "Eles queimaram nossas casas, capturaram nossa tribo, não tivemos chance de reagir..."),
            ("Jaum Manel", "Eles eram monstros que atacavam sem piedade, toda tribo foi capturada."),
        ],
        "position": "bottom",
    },
    {
        "image": "cutscenes/intro_04.png",
        "music_context": "boss",
        "dialogues": [
            ("Jaum Manel", "Eles festejavam, se aproveitando de nossa cultura e de nossas sagradas terras."),
            ("Jaum Manel", "Estávamos já sem forças, porém nossa esperança não iria se acabar tão facilmente."),
        ],
        "position": "bottom",
    },
    {
        "image": "cutscenes/intro_05.png",
        "music_context": "boss",
        "dialogues": [
            ("Jaum Manel", "Ao anoitecer, uma brasa das fogueiras enfraqueceu as cordas da minha cela, parecia que nossas terras estavam tentando me ajudar..."),
            ("Jaum Manel", "Passei a noite inteira tentando me libertar, e ao nascer do sol consegui escapar da prisão."),
            ("Jaum Manel", "Porém um dos inimigos ainda estava de tocaia..."),
        ],
        "position": "bottom",
    },
]

POST_TUTORIAL_CUTSCENE = [
    {
        "image": "cutscenes/pos_tutorial.png",
        "music_context": "menu",
        "dialogues": [
            ("Jaum Manel", "Ouvindo minha tribo torcendo por mim, consegui derrotar o primeiro inimigo"),
            ("Jaum Manel", "Porém eu sabia que minha jornada estava apenas começando."),
            ("Jaum Manel", "Preciso ficar mais forte para conseguir libertar minha tribo, nossas terras estão do meu lado."),
            ("Jaum Manel", "Prometo que vou voltar, e trarei a liberdade para nós..."),
        ],
        "position": "bottom",
    }
]

# Em cada lista, adicione pares como ("Jaum Manel", "Sua fala aqui.").
FINAL_CUTSCENE = [
    {
        "image": f"cutscenes/final_{number:02d}.png",
        "music_context": None if number == 3 else "final_boss" if number <= 2 else "farewell",
        **({"dialogue_music_context": "farewell"} if number == 3 else {}),
        "dialogues": dialogues,
        "position": "bottom",
    }
    for number, dialogues in enumerate(
        [
            [
                ("", "Após uma batalha intensa, os dois se encontram exaustos, sem forças para finalizarem um ao outro..."),
                ("Zanzara", "Você não passa de um verme!! \n Meu Clã já deve estar de volta, é questão de tempo até eles chegarem aqui. \n Acabou para você!!"),
                ("Jaum Manel", "Eu cheguei tão longe, depois de tudo que aconteceu... \n Eu não posso desistir. \n Mas meu corpo simplesmente não responde mais!!"),
            ],  # 01
            [
                ("????", "Mesmo com todo esse poder, ainda está de joelhos na frente desse garoto?! \n PATÉTICO... Você não é mais digno. \n Chegou a hora de pagar sua dívida Zanzara."),
                ("Zanzara", "Ah não pode ser!! \n Eu não posso ser derrotado, não aqui! \n Não agora..."),
                ("Jaum Manel", "Parece que chegou a hora de pagar pelo que fez!"),
                ("Zanzara", "Minha família está vindo. \n Estou tão perto! \n Eu não mereço ir assim..."),
                ("Zanzara", "Meu clã não merece desaparecer desse jeito..."),
                ("Zanzara", "Não pense que vai ser tão fácil assim garoto..."),
            ],  # 02
            [
                ("Octav", "Parece que Zanzara se foi..."),
                ("Octav", "Parece que a caça finalmente acabou. \n Espero não precisar de usar essas garras em outra vida...")
            ],  # 03
            [
                ("Alvar", "Finalmente vamos ter uma nova terra para chamar de lar irmão!"),
                ("Tekks", "Obrigado por tudo irmão! \n Estaremos sempre juntos, não importa onde!"),
                ("Alvar & Tekks", "SEMPRE!!")
            ],  # 04
            [
               ("Sir Thomas","Realmente, todo reinado tem seu fim. \n Gratidão Zanzara! \n Em outra vida, se eu tiver o prazer de ser da realiza novamente, juro que meu reino aceitará a todos! \n até mesmo os \"Monstros\" semelhantes a nós!")
            ],  # 05
            [
              ("Jozephino", "Uma lástima... \n Me conforma saber que essas belezinhas ainda estarão aqui após eu partir! \n Minha marca vai ficar nesse mundo.")
            ],  # 06
            [
             ("Labrro", "VERME MALDITO!! \n Um Moleque daqueles, como isso foi acontecer?!  \n FRACOS, TODOS VOCÊS!"),
             ("Labrro", "Não interessa aonde eu estarei, EU VOU SER O MAIS FORTE!! \n Até mais que você Zanzara! \n Eu preciso ficar mais fo...")
            ],  # 07
            [
             ("Jan-Pietro", "Eu consigo sentir, ele... \n Ele conseguiu! \n Mas a que preço afinal?"),
             ("Jan-Pietro", "Finalmente nós podemos descansar. \n Vou me encontrar com meus irmãos, obrigado!"),
             ("Jan-Pietro", "Sei que não consegue me ouvir, mas por favor, não se torne igual a ele! \n Sua jornada está apenas no início... \n Boa Sorte Jaum Manel!!")
            ],  # 08
            [
             ("????", "Você tem meu respeito! \n Mas vamos ver quanto tempo consegue se manter dessa maneira, \n Mas dessa ver vou engolir meu orgulho..."),
             ("????", "Descanse garoto! \n Liberte seu povo, você ainda tem muito a fazer. \n Estou contando com você...")
            ],  # 09
            [
             ("Jaum Manel", "Essas mãos agora carregam o peso de uma guerra... \n Carregam o peso de um ciclo de matanças, da história e da cultura de vários povos!"),
             ("Jaum Manel", "No final eu... \n EU não fui forte o bastante para dar o golpe final em Zanzara. \n Será se ele se foi realmente? \n Há outros como ele? \n Sinto que não vou conseguir dormir bem tão cedo hahahaha"),
             ("Jaum Manel", "Apesar de tudo, sinto que no inicio, todos eles eram boas pessoas... \n Não sei onde ou porque se perderam, mas prometo que vou carregas suas vontades!"),
             ("Jaum Manel", "E essa marca... \n Não sei bem o que aconteceu depois que fiquei desacordado, mas me sinto diferente... \n ..."),
             ("Jaum Manel", "Não importa, o importante é que agora minha tribo está segura, \n E eu prometo, ninguem nunca mais vai nos fazer mal..."),
             ("Jaum Manel", "NINGUÉM!!")
            ],  # 10
        ],
        start=1,
    )
]

# Tela preta entre as imagens 02 e 03. Use "" como nome para narrar sem personagem.
FINAL_CUTSCENE.insert(2, {
    "image": None,
    "music_context": None,
    "dialogues": [("", "Quando o som da batalha cessou, só era possível ouivr as correntes arrastando Zanzara para o além. A floresta ficou em silêncio."),
                  ("","Enquanto isso, a existência de seu clã ia desaparecendo aos poucos...")],
    "position": "bottom",
})

CROSSFADE_DURATION_MS = 500
FADE_IN_DURATION_MS = 500
FADE_OUT_DURATION_MS = 500

CONTINUE_HINT = "Clique ou Espaço para continuar"
SKIP_HINT = "Esc para pular"
INTRO_LAST_HINT = "Clique para começar"
