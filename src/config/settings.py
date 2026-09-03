import os

# ============================================================
# CONFIGURAÇÕES GERAIS DA APLICAÇÃO
# ============================================================

WIDTH = 1280
HEIGHT = 720
FPS = 60

TITLE = "Scape From Stone de Cut"

# Caminhos do projeto
SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(SRC_DIR)

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
PLAYER_ASSETS_DIR = os.path.join(ASSETS_DIR, "player")
CARD_ASSETS_DIR = os.path.join(ASSETS_DIR, "cards")
CARD_EFFECTS_DIR = os.path.join(ASSETS_DIR, "card_effects")
BACKGROUND_PATH = os.path.join(ASSETS_DIR, "background.png")
