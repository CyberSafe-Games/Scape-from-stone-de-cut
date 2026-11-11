import os

# ============================================================
# CONFIGURAÇÕES GERAIS DA APLICAÇÃO
# ============================================================

# Resolução de referência (Full HD, 16:9). Todo o layout é expresso nesta escala.
WIDTH = 1920
HEIGHT = 1080

# Fator entre a resolução de referência e a resolução original de autoria da
# arte (1280x720). Usado para ampliar sprites e quadros de animação carregados
# no tamanho nativo dos arquivos, preservando a composição original.
UI_SCALE = WIDTH / 1280

# Tamanhos de janela disponíveis no modo janela. O jogo sempre renderiza em
# WIDTH x HEIGHT; no modo 1280x720 a imagem é reduzida para caber na janela.
FULL_HD_WINDOW_SIZE = (WIDTH, HEIGHT)
LEGACY_WINDOW_SIZE = (1280, 720)
FPS = 60

TITLE = "Scape From Stone de Cut"

# Regras de mão e cartas
HAND_SIZE_START = 3
HAND_SIZE_MAX = 5

# Caminhos do projeto
SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(SRC_DIR)

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
PLAYER_ASSETS_DIR = os.path.join(ASSETS_DIR, "player")
CARD_ASSETS_DIR = os.path.join(ASSETS_DIR, "cards")
CARD_EFFECTS_DIR = os.path.join(ASSETS_DIR, "card_effects")
BACKGROUND_PATH = os.path.join(ASSETS_DIR, "background.png")
COIN_ICON_PATH = os.path.join(ASSETS_DIR, "icons", "moeda.png")
UI_ASSETS_DIR = os.path.join(ASSETS_DIR, "ui")
ULTIMATE_ASSETS_DIR = os.path.join(ASSETS_DIR, "ultimates")

# Um arquivo JSON por jornada (até três espaços na seleção).
SAVES_DIR = os.path.join(BASE_DIR, "saves")
