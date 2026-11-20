# Edite "image" e "text" em cada quadro: texto vazio não exibe caixa;
# "position" aceita "bottom" ou "top"; use \n para quebra manual.

INTRO_CUTSCENE = [
        {
        "image": "cutscenes/intro_01.png",
        "dialogues": [
            ("Jaum Manel", "Moravamos em terras isoládas do resto do mundo, conhecida pelos estrangeiros como Stone de Cut, respeitavamos a natureza e assim vivíamos em paz."),
            ("Jaum Manel", "Porém mal sabíamos que essa paz estava prestes a se acabar..."),
        ],
        "position": "bottom",
    },
    {
        "image": "cutscenes/intro_02.png",
        "dialogues": [
            ("Jaum Manel", "Nossa aldeia foi invadida por um grupo de estrangeiros."),
            ("Jaum Manel", "Em questão de minutos nossa aldeia estava cercada."),
        ],
        "position": "bottom",
    },
    {
        "image": "cutscenes/intro_03.png",
        "dialogues": [
            ("Jaum Manel", "Eles queimaram nossas casas, capturaram nossa tribo, não tivemos chance de reagir..."),
            ("Jaum Manel", "Eles eram monstros que atacavam sem piedade, toda tribo foi capturada."),
        ],
        "position": "bottom",
    },
    {
        "image": "cutscenes/intro_04.png",
        "dialogues": [
            ("Jaum Manel", "Eles festejavam, se aproveitando de nossa cultura e de nossas sagradas terras."),
            ("Jaum Manel", "Estávamos já sem forças, porém nossa esperança não iria se acabar tão facilmente."),
        ],
        "position": "bottom",
    },
    {
        "image": "cutscenes/intro_05.png",
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
        "dialogues": dialogues,
        "position": "bottom",
    }
    for number, dialogues in enumerate(
        [
            [],  # 01
            [],  # 02
            [],  # 03
            [],  # 04
            [],  # 05
            [],  # 06
            [],  # 07
            [],  # 08
            [],  # 09
            [],  # 10
        ],
        start=1,
    )
]

CROSSFADE_DURATION_MS = 500
FADE_IN_DURATION_MS = 500
FADE_OUT_DURATION_MS = 500

CONTINUE_HINT = "Clique ou Espaço para continuar"
SKIP_HINT = "Esc para pular"
INTRO_LAST_HINT = "Clique para começar"
