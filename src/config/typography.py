import os

from src.config.settings import ASSETS_DIR, UI_SCALE

# ============================================================
# TIPOGRAFIA DO JOGO (configuração centralizada)
# ============================================================
# Fonte autoral "Igarape Pixel". Para trocar a fonte do jogo inteiro, basta
# substituir os arquivos abaixo e, se preciso, ajustar a tabela FONT_STYLES.

FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")

FONT_FILES = {
    "regular": os.path.join(FONTS_DIR, "IgarapePixel-Regular.ttf"),
    "bold": os.path.join(FONTS_DIR, "IgarapePixel-Bold.ttf"),
}

# Estilo nomeado -> (peso, tamanho em px na arte de referência 1280x720).
# O tamanho real é multiplicado por UI_SCALE (1,5 em Full HD), como o restante
# do layout. Os valores foram calibrados para que os textos ocupem praticamente
# a mesma largura das fontes anteriores (Segoe UI / Constantia), preservando o
# encaixe em botões, painéis e caixas de diálogo. A grade da fonte tem 12
# "pixels" por em; em Full HD, menu (36), títulos (54) e logotipo (90) ficam
# em múltiplos de 6 ou 12, com contornos nítidos.
FONT_STYLES = {
    "default": ("regular", 21),   # textos informativos, diálogos e descrições
    "small": ("regular", 18),     # HUD, botões, legendas e rótulos
    "menu": ("bold", 24),         # opções do menu e nomes de combatentes
    "big": ("bold", 36),          # títulos de tela e de modais
    "title": ("bold", 60),        # logotipo do menu principal
}


def scaled_font_size(size):
    """Converte o tamanho de referência (1280x720) para a resolução do jogo."""
    return max(1, round(size * UI_SCALE))

# Altura de linha (múltiplo do tamanho) usada nos textos de várias linhas que
# consultam font.get_linesize(), como diálogos do tutorial e mensagens de combate.
# A fonte pixelada tem caixa justa; sem este respiro as linhas ficam coladas.
LINE_HEIGHT = 1.3

# Usada apenas para símbolos que a fonte autoral não possui (ex.: ∞, ×, ✕, ▸),
# renderizados no meio do texto sem trocar a fonte do restante.
SYMBOL_FALLBACK_FONTS = ["segoeuisymbol", "dejavusans", "notosanssymbols", "arialunicodems"]

# Última alternativa caso os arquivos da fonte autoral não sejam encontrados.
SYSTEM_FALLBACK_FONTS = ["segoeui", "trebuchetms", "liberationsans", "dejavusans"]
