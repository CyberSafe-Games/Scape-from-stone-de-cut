from dataclasses import dataclass

from src.config.settings import WIDTH, HEIGHT

# ============================================================
# POSIÇÕES DOS COMBATENTES NA TELA
# ============================================================

PLAYER_X = 390
PLAYER_Y = 570

ENEMY_X = WIDTH - 390
ENEMY_Y = 570

PLAYER_GROUND_Y = PLAYER_Y + 60


# ============================================================
# DIMENSÕES E ESPAÇAMENTO DE CARTAS
# ============================================================

CARD_WIDTH = 150
CARD_HEIGHT = 258
CARD_SPACING = 18


# ============================================================
# BOTÕES DO DECK NA MOCHILA
# ============================================================

# Os dois botões ficam na mesma linha, logo abaixo do painel do deck.
BACKPACK_DECK_BUTTON_OFFSET_Y = 26
BACKPACK_DECK_BUTTON_HEIGHT = 59
BACKPACK_DECK_BUTTON_GAP = 16
BACKPACK_DECK_BUTTON_INSET_X = 8


# ============================================================
# PARÂMETROS DE ANIMAÇÃO E TIMERS (em milissegundos)
# ============================================================

FLASH_DURATION = 560
FLOAT_DURATION = 900

ATTACK_DURATION = 700
MELEE_MIN_DURATION = 1120
POSE_RECOVERY_MS = 240
PLAYER_IDLE_FRAME_MS = 210
BOSS_IDLE_FRAME_MS = 225
COMMON_IDLE_FRAME_MS = 210
VICTORY_FRAME_MS = 180
LEGACY_VICTORY_FRAME_MS = 125

APPROACH_FRAC = 0.4
STRIKE_FRAC = 0.25

APPROACH_GAP = 117

POST_ENEMY_PAUSE = 350

MINIBOSS_INTERVAL = 5


# ============================================================
# MENU DE PAUSA (MODAL)
# ============================================================
# A altura do painel é derivada do conteúdo: cabeçalho, N botões e rodapé.

PAUSE_PANEL_WIDTH = 700
PAUSE_PANEL_TOP_PADDING = 42
PAUSE_PANEL_BOTTOM_PADDING = 30

# Alturas de linha das fontes small/big na superfície virtual 1920x1080.
PAUSE_EYEBROW_HEIGHT = 26
PAUSE_TITLE_HEIGHT = 46
PAUSE_SUBTITLE_HEIGHT = 26
PAUSE_FOOTER_HEIGHT = 26

PAUSE_EYEBROW_TITLE_GAP = 12
PAUSE_SUBTITLE_DIVIDER_GAP = 40
PAUSE_DIVIDER_BUTTON_GAP = 32
PAUSE_BUTTON_FOOTER_GAP = 32

PAUSE_BUTTON_WIDTH = 400
PAUSE_BUTTON_HEIGHT = 70
PAUSE_BUTTON_GAP = 16

# Respiro mínimo entre título e subtítulo: meia altura de botão.
PAUSE_TITLE_SUBTITLE_GAP = PAUSE_BUTTON_HEIGHT // 2

# Recuo horizontal da linha decorativa em relação às bordas do painel.
PAUSE_DIVIDER_INSET = 110


@dataclass(frozen=True)
class PauseMenuLayout:
    """Coordenadas calculadas do menu de pausa, sem dependência de pygame."""

    panel: tuple[int, int, int, int]
    eyebrow_center_y: int
    title_center_y: int
    subtitle_center_y: int
    divider_x1: int
    divider_x2: int
    divider_y: int
    buttons: tuple[tuple[int, int, int, int], ...]
    footer_center_y: int


def compute_pause_menu_layout(button_count):
    """Calcula o painel e seus elementos para a quantidade informada de botões."""
    if button_count < 1:
        raise ValueError("O menu de pausa precisa de pelo menos um botão.")

    button_block_height = (
        button_count * PAUSE_BUTTON_HEIGHT
        + (button_count - 1) * PAUSE_BUTTON_GAP
    )
    content_height = (
        PAUSE_PANEL_TOP_PADDING
        + PAUSE_EYEBROW_HEIGHT
        + PAUSE_EYEBROW_TITLE_GAP
        + PAUSE_TITLE_HEIGHT
        + PAUSE_TITLE_SUBTITLE_GAP
        + PAUSE_SUBTITLE_HEIGHT
        + PAUSE_SUBTITLE_DIVIDER_GAP
        + PAUSE_DIVIDER_BUTTON_GAP
        + button_block_height
        + PAUSE_BUTTON_FOOTER_GAP
        + PAUSE_FOOTER_HEIGHT
        + PAUSE_PANEL_BOTTOM_PADDING
    )
    # Altura par garante centralização exata em uma tela de altura par.
    panel_height = content_height + content_height % 2
    panel_x = (WIDTH - PAUSE_PANEL_WIDTH) // 2
    panel_y = (HEIGHT - panel_height) // 2

    eyebrow_center_y = (
        panel_y + PAUSE_PANEL_TOP_PADDING + PAUSE_EYEBROW_HEIGHT // 2
    )
    title_top = (
        panel_y
        + PAUSE_PANEL_TOP_PADDING
        + PAUSE_EYEBROW_HEIGHT
        + PAUSE_EYEBROW_TITLE_GAP
    )
    title_center_y = title_top + PAUSE_TITLE_HEIGHT // 2
    subtitle_top = title_top + PAUSE_TITLE_HEIGHT + PAUSE_TITLE_SUBTITLE_GAP
    subtitle_center_y = subtitle_top + PAUSE_SUBTITLE_HEIGHT // 2
    divider_y = (
        subtitle_top + PAUSE_SUBTITLE_HEIGHT + PAUSE_SUBTITLE_DIVIDER_GAP
    )

    first_button_top = divider_y + PAUSE_DIVIDER_BUTTON_GAP
    button_x = panel_x + (PAUSE_PANEL_WIDTH - PAUSE_BUTTON_WIDTH) // 2
    buttons = tuple(
        (
            button_x,
            first_button_top + index * (PAUSE_BUTTON_HEIGHT + PAUSE_BUTTON_GAP),
            PAUSE_BUTTON_WIDTH,
            PAUSE_BUTTON_HEIGHT,
        )
        for index in range(button_count)
    )

    footer_top = first_button_top + button_block_height + PAUSE_BUTTON_FOOTER_GAP
    footer_center_y = footer_top + PAUSE_FOOTER_HEIGHT // 2

    return PauseMenuLayout(
        panel=(panel_x, panel_y, PAUSE_PANEL_WIDTH, panel_height),
        eyebrow_center_y=eyebrow_center_y,
        title_center_y=title_center_y,
        subtitle_center_y=subtitle_center_y,
        divider_x1=panel_x + PAUSE_DIVIDER_INSET,
        divider_x2=panel_x + PAUSE_PANEL_WIDTH - PAUSE_DIVIDER_INSET,
        divider_y=divider_y,
        buttons=buttons,
        footer_center_y=footer_center_y,
    )
