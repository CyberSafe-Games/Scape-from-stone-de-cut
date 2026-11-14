# Edite "image" e "text" em cada quadro: texto vazio não exibe caixa;
# "position" aceita "bottom" ou "top"; use \n para quebra manual.

INTRO_CUTSCENE = [
    {"image": f"cutscenes/intro_{index:02d}.png", "text": "", "position": "bottom"}
    for index in range(1, 6)
]

POST_TUTORIAL_CUTSCENE = [
    {"image": "cutscenes/pos_tutorial.png", "text": "", "position": "bottom"},
]

CROSSFADE_DURATION_MS = 500
FADE_IN_DURATION_MS = 500
FADE_OUT_DURATION_MS = 500

CONTINUE_HINT = "Clique ou Espaço para continuar"
SKIP_HINT = "Esc para pular"
INTRO_LAST_HINT = "Clique para começar"
