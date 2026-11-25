import os
import sys

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

# Cura concedida ao vencer um miniboss/chefe de território, como fração da
# VIDA MÁXIMA atual (não da vida atual). Calculada no momento da cura, por
# isso acompanha futuros upgrades de vida máxima. Arredondada para o inteiro
# mais próximo (+0.5, truncado); nunca ultrapassa a vida máxima (min).
# Exemplos: 60 → 18 HP; 80 → 24 HP. Ajustar somente esta linha.
MINIBOSS_HEAL_PERCENT = 0.30

# Caminhos de recursos: no executável, o PyInstaller define _MEIPASS para a
# pasta interna do pacote; no modo fonte, os arquivos continuam na raiz do repo.
SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(SRC_DIR)


def resource_path(*parts):
    """Recursos empacotados somente leitura; não armazenar dados do usuário aqui."""
    from src.platforms import get_platform
    return get_platform(BASE_DIR).resource_path(*parts)


def user_data_path(*parts):
    """Dados locais no desktop; na web, apenas FS temporário de sessão."""
    from src.platforms import get_platform
    return get_platform(BASE_DIR).user_data_path(*parts)


ASSETS_DIR = resource_path("assets")
PLAYER_ASSETS_DIR = os.path.join(ASSETS_DIR, "player")
CARD_ASSETS_DIR = os.path.join(ASSETS_DIR, "cards")
CARD_EFFECTS_DIR = os.path.join(ASSETS_DIR, "card_effects")
BACKGROUND_PATH = os.path.join(ASSETS_DIR, "background.png")
COIN_ICON_PATH = os.path.join(ASSETS_DIR, "icons", "moeda.png")
UI_ASSETS_DIR = os.path.join(ASSETS_DIR, "ui")
ULTIMATE_ASSETS_DIR = os.path.join(ASSETS_DIR, "ultimates")

# Um arquivo JSON por jornada (até três espaços na seleção).
SAVES_DIR = user_data_path("saves")

# Preferências globais do computador (áudio, vídeo e jogo), independentes dos saves.
SETTINGS_DIR = user_data_path("settings")
PREFERENCES_PATH = os.path.join(SETTINGS_DIR, "audio.json")
