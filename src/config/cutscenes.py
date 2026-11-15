# Edite "image" e "text" em cada quadro: texto vazio não exibe caixa;
# "position" aceita "bottom" ou "top"; use \n para quebra manual.

INTRO_CUTSCENE = [
    {
        "image": "cutscenes/intro_01.png",
        "dialogues": [
            ("Narrador", "Nossa tribo vivia em paz."),
            ("Narrador", "Mas aquela paz não duraria para sempre."),
        ],
        "position": "bottom",
    },
    {
        "image": "cutscenes/intro_02.png",
        "dialogues": [
            ("Jaum Manel", "O que foi esse barulho?"),
            ("Narrador", "Invasores cercavam a aldeia."),
        ],
        "position": "bottom",
    },
    {
        "image": "cutscenes/intro_03.png",
        "dialogues": [
            ("Jaum Manel", "Protejam as crianças!"),
            ("Narrador", "A batalha começou sem piedade."),
        ],
        "position": "bottom",
    },
]

POST_TUTORIAL_CUTSCENE = [
    {
        "image": "cutscenes/pos_tutorial.png",
        "dialogues": [
            ("Jaum Manel", "Esse foi só o começo."),
            ("Jaum Manel", "Preciso encontrar os invasores e libertar meu povo."),
        ],
        "position": "bottom",
    }
]

CROSSFADE_DURATION_MS = 500
FADE_IN_DURATION_MS = 500
FADE_OUT_DURATION_MS = 500

CONTINUE_HINT = "Clique ou Espaço para continuar"
SKIP_HINT = "Esc para pular"
INTRO_LAST_HINT = "Clique para começar"
