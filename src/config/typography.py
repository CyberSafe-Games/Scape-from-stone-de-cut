import os

from src.config.settings import ASSETS_DIR, UI_SCALE

# ============================================================
# TIPOGRAFIA DO JOGO (configuração centralizada)
# ============================================================
# Fonte autoral "Igarape Pixel" em dois estilos: Regular (textos corridos,
# HUD e rótulos) e Destaque (menus, títulos e logotipo; só maiúsculas, as
# minúsculas são desenhadas como versaletes). Para trocar a fonte do jogo
# inteiro, basta substituir os arquivos abaixo e, se preciso, ajustar FONT_STYLES.

FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")

FONT_FILES = {
    "regular": os.path.join(FONTS_DIR, "IgarapePixel-Regular.ttf"),
    "destaque": os.path.join(FONTS_DIR, "IgarapePixel-Destaque.ttf"),
}

# Estilo nomeado -> (arquivo, tamanho em px na arte de referência 1280x720).
# O tamanho real é multiplicado por UI_SCALE (1,5 em Full HD), como o restante
# do layout. Os valores foram calibrados com os textos do próprio jogo para que
# ocupem praticamente a mesma largura de antes, preservando o encaixe em
# botões, painéis e caixas de diálogo (em Full HD: 26, 30, 32, 46 e 78 px).
FONT_STYLES = {
    "default": ("regular", 20),    # textos informativos, diálogos e descrições
    "small": ("regular", 17),      # HUD, botões, legendas e rótulos
    "menu": ("destaque", 21),      # opções do menu e nomes de combatentes
    "big": ("destaque", 31),       # títulos de tela e de modais
    "title": ("destaque", 52),     # logotipo do menu principal
}


def scaled_font_size(size):
    """Converte o tamanho de referência (1280x720) para a resolução do jogo."""
    return max(1, round(size * UI_SCALE))

# Altura de linha (múltiplo do tamanho) usada nos textos de várias linhas que
# consultam font.get_linesize(), como diálogos do tutorial e mensagens de combate.
# A fonte pixelada tem caixa justa; sem este respiro as linhas ficam coladas.
LINE_HEIGHT = 1.3

# Usada apenas para símbolos que a fonte autoral não possui (ex.: ∞, ×, ✕, ▸, |),
# renderizados no meio do texto sem trocar a fonte do restante.
SYMBOL_FALLBACK_FONTS = ["segoeuisymbol", "dejavusans", "notosanssymbols", "arialunicodems"]
