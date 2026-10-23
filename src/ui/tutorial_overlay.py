"""Componente visual e interativo para exibição do tutorial guiado.

Renderiza balões flutuantes dinâmicos posicionados estrategicamente próximos
aos elementos ensinados, setas direcionais animadas, destaques (spotlights)
e transições fluidas de aparecimento/desaparecimento baseadas em cliques na tela.
"""
import math
from dataclasses import dataclass
from typing import Callable, Optional, Sequence

import pygame

from src.config.colors import (
    BG,
    BLACK,
    WHITE,
    GOLD,
    GRAY,
    RED,
    BLUE,
    GREEN,
)
from src.config.settings import WIDTH, HEIGHT
from src.ui.helpers import draw_text, draw_panel
from src.ui import dark_fantasy_theme as theme


def draw_tutorial_arrow(
    surface: pygame.Surface,
    origin: tuple[int, int],
    target: tuple[int, int],
    color: tuple[int, int, int] = GOLD,
    pulse: float = 0.0,
    alpha: int = 255,
    head_size: float = 18.0,
):
    """Desenha uma seta direcional estilizada com sombra e pulso dinâmico."""
    if alpha <= 5:
        return

    ox, oy = origin
    tx, ty = target

    dx = tx - ox
    dy = ty - oy
    dist = math.hypot(dx, dy)
    if dist < 4.0:
        return

    ux = dx / dist
    uy = dy / dist
    px = -uy
    py = ux

    # Oscilação suave na direção do alvo
    offset = math.sin(pulse * 3.0) * 4.0
    cur_tx = tx + ux * offset
    cur_ty = ty + uy * offset
    cur_ox = ox
    cur_oy = oy

    bx = cur_tx - ux * head_size
    by = cur_ty - uy * head_size
    head_w = head_size * 0.52

    pts = [
        (cur_tx, cur_ty),
        (bx + px * head_w, by + py * head_w),
        (bx + ux * 2.5, by + uy * 2.5),
        (bx - px * head_w, by - py * head_w),
    ]

    arrow_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    # Sombra projetada
    shadow_pts = [(x + 2, y + 2) for x, y in pts]
    pygame.draw.line(arrow_surf, (0, 0, 0, int(150 * (alpha / 255))), (cur_ox + 2, cur_oy + 2), (bx + 2, by + 2), 5)
    pygame.draw.polygon(arrow_surf, (0, 0, 0, int(150 * (alpha / 255))), shadow_pts)

    # Haste
    pygame.draw.line(arrow_surf, (35, 28, 16, alpha), (cur_ox, cur_oy), (bx, by), 5)
    pygame.draw.line(arrow_surf, (*color, alpha), (cur_ox, cur_oy), (bx, by), 3)

    # Ponta da seta
    pygame.draw.polygon(arrow_surf, (*color, alpha), pts)
    pygame.draw.polygon(arrow_surf, (255, 245, 205, alpha), pts, 1)

    # Anel rúnico no ponto de origem
    pygame.draw.circle(arrow_surf, (20, 15, 10, alpha), (int(cur_ox), int(cur_oy)), 5)
    pygame.draw.circle(arrow_surf, (*color, alpha), (int(cur_ox), int(cur_oy)), 4)
    pygame.draw.circle(arrow_surf, (255, 255, 255, alpha), (int(cur_ox), int(cur_oy)), 2)

    surface.blit(arrow_surf, (0, 0))


def draw_tutorial_spotlight(
    surface: pygame.Surface,
    rect: pygame.Rect,
    pulse: float = 0.0,
    alpha: int = 255,
    color: tuple[int, int, int] = GOLD,
):
    """Desenha um contorno rúnico iluminado e cantoneiras ao redor do elemento em foco."""
    if alpha <= 5:
        return

    r = rect.inflate(8, 8)
    glow_alpha = int((160 + 60 * math.sin(pulse * 3.0)) * (alpha / 255))
    glow_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    # Halo externo
    pygame.draw.rect(
        glow_surf,
        (*color, max(0, min(255, glow_alpha // 3))),
        r.inflate(6, 6),
        width=3,
        border_radius=10,
    )
    pygame.draw.rect(
        glow_surf,
        (*color, max(0, min(255, glow_alpha))),
        r,
        width=2,
        border_radius=8,
    )

    # Cantoneiras ornamentais
    corner_len = 9
    corners = [
        (r.left, r.top, 1, 1),
        (r.right, r.top, -1, 1),
        (r.left, r.bottom, 1, -1),
        (r.right, r.bottom, -1, -1),
    ]
    for cx, cy, sx, sy in corners:
        pygame.draw.line(glow_surf, (255, 245, 200, alpha), (cx, cy), (cx + sx * corner_len, cy), 2)
        pygame.draw.line(glow_surf, (255, 245, 200, alpha), (cx, cy), (cx, cy + sy * corner_len), 2)

    surface.blit(glow_surf, (0, 0))


@dataclass
class TutorialStep:
    id: str
    title: str
    subtitle: str
    lines: Sequence[str]
    target_rect_fn: Optional[Callable[[], Optional[pygame.Rect]]] = None
    bubble_pos: tuple[int, int] = (400, 200)  # Posição do balão flutuante (x, y)
    bubble_size: tuple[int, int] = (460, 192)  # Largura e altura do balão
    arrow_origin_fn: Optional[Callable[[], Optional[tuple[int, int]]]] = None
    arrow_target_fn: Optional[Callable[[], Optional[tuple[int, int]]]] = None


class TutorialOverlay:
    """Gerencia a navegação e a renderização fluida do guia flutuante por cliques na tela."""

    TRANSITION_IN_TIME = 0.20   # Segundos para fade-in e slide
    TRANSITION_OUT_TIME = 0.10  # Segundos para fade-out ao avançar

    def __init__(self, steps: list[TutorialStep], on_complete: Optional[Callable[[], None]] = None):
        self.steps = steps
        self.on_complete = on_complete
        self.step_index = 0
        self.is_active = True
        self.elapsed = 0.0

        # Animação fluida de transição
        # "in", "active", "out", "closing"
        self.anim_state = "in"
        self.anim_timer = 0.0
        self.current_alpha = 0
        self.offset_y = 12.0

        # Botão sutil para pular tutorial no topo direito
        self.skip_button_rect = pygame.Rect(WIDTH - 150, 16, 134, 30)

    @property
    def current_step(self) -> TutorialStep:
        return self.steps[self.step_index]

    def update(self, dt: int):
        if not self.is_active:
            return

        dt_sec = max(0.001, min(dt, 1000) / 1000.0)
        self.elapsed += dt_sec

        if self.anim_state == "in":
            self.anim_timer += dt_sec
            t = min(1.0, self.anim_timer / self.TRANSITION_IN_TIME)
            ease = 1.0 - (1.0 - t) ** 3
            self.current_alpha = int(255 * ease)
            self.offset_y = (1.0 - ease) * 12.0
            if t >= 1.0:
                self.anim_state = "active"
                self.anim_timer = 0.0
                self.current_alpha = 255
                self.offset_y = 0.0

        elif self.anim_state == "out":
            self.anim_timer += dt_sec
            t = min(1.0, self.anim_timer / self.TRANSITION_OUT_TIME)
            ease = t * t
            self.current_alpha = int(255 * (1.0 - ease))
            self.offset_y = ease * -8.0
            if t >= 1.0:
                if self.step_index < len(self.steps) - 1:
                    self.step_index += 1
                    self.anim_state = "in"
                    self.anim_timer = 0.0
                else:
                    self._complete_finish()

        elif self.anim_state == "closing":
            self.anim_timer += dt_sec
            t = min(1.0, self.anim_timer / self.TRANSITION_OUT_TIME)
            self.current_alpha = int(255 * (1.0 - t))
            if t >= 1.0:
                self._complete_finish()

    def advance(self):
        """Avança suavemente o tutorial através do clique na tela."""
        if not self.is_active:
            return

        if self.anim_state in ("in", "active"):
            self.anim_state = "out"
            self.anim_timer = 0.0
        elif self.anim_state == "out":
            # Duplo clique acelera para o próximo passo
            if self.step_index < len(self.steps) - 1:
                self.step_index += 1
                self.anim_state = "in"
                self.anim_timer = 0.0
            else:
                self._complete_finish()

    def next_step(self):
        """Avanço direto imediato."""
        if self.step_index < len(self.steps) - 1:
            self.step_index += 1
            self.anim_state = "active"
            self.current_alpha = 255
            self.offset_y = 0.0
        else:
            self.finish()

    def prev_step(self):
        """Retorno direto imediato."""
        if self.step_index > 0:
            self.step_index -= 1
            self.anim_state = "active"
            self.current_alpha = 255
            self.offset_y = 0.0

    def skip(self):
        """Pula o tutorial com animação rápida de fechamento."""
        if not self.is_active:
            return
        self.anim_state = "closing"
        self.anim_timer = 0.0

    def finish(self, immediate: bool = True):
        if immediate:
            self._complete_finish()
        else:
            self.skip()

    def _complete_finish(self):
        self.is_active = False
        self.current_alpha = 0
        if self.on_complete:
            self.on_complete()

    def reset(self):
        self.step_index = 0
        self.is_active = True
        self.anim_state = "in"
        self.anim_timer = 0.0
        self.current_alpha = 0
        self.offset_y = 12.0

    def draw(self, surface: pygame.Surface, asset_manager, mouse_pos: tuple[int, int]):
        if not self.is_active or self.current_alpha <= 2:
            return

        step = self.current_step
        alpha = self.current_alpha

        # 1. Véu escuro transparente com fade
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil_alpha = int(135 * (alpha / 255))
        veil.fill((3, 8, 8, veil_alpha))
        surface.blit(veil, (0, 0))

        # 2. Destaque (spotlight) ao redor do elemento em foco
        target_rect = step.target_rect_fn() if step.target_rect_fn else None
        if target_rect is not None:
            draw_tutorial_spotlight(surface, target_rect, pulse=self.elapsed, alpha=alpha, color=GOLD)

        # 3. Flutuação suave contínua do balão
        float_hover = math.sin(self.elapsed * 2.8) * 3.5
        bx, by = step.bubble_pos
        bw, bh = step.bubble_size
        actual_y = by + self.offset_y + float_hover

        bubble_rect = pygame.Rect(bx, int(actual_y), bw, bh)

        # 4. Seta direcional apontando do balão para o elemento alvo
        if step.arrow_origin_fn and step.arrow_target_fn:
            orig = step.arrow_origin_fn()
            target = step.arrow_target_fn()
            if orig and target:
                dyn_orig = (orig[0], int(orig[1] + self.offset_y + float_hover))
                draw_tutorial_arrow(surface, dyn_orig, target, color=GOLD, pulse=self.elapsed, alpha=alpha)

        # 5. Superfície transparente do balão flutuante
        bubble_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)

        # Fundo do balão com cantos arredondados e preenchimento escuro elegante
        bg_alpha = int(242 * (alpha / 255))
        border_alpha = int(210 * (alpha / 255))
        pygame.draw.rect(
            bubble_surf,
            (11, 18, 18, bg_alpha),
            pygame.Rect(0, 0, bw, bh),
            border_radius=12,
        )
        # Borda dourada ornamentada
        pygame.draw.rect(
            bubble_surf,
            (196, 160, 94, border_alpha),
            pygame.Rect(0, 0, bw, bh),
            width=2,
            border_radius=12,
        )
        # Cantoneiras internas
        c_len = 8
        c_pts = [
            (0, 0, 1, 1),
            (bw - 1, 0, -1, 1),
            (0, bh - 1, 1, -1),
            (bw - 1, bh - 1, -1, -1),
        ]
        for cx, cy, sx, sy in c_pts:
            pygame.draw.line(bubble_surf, (255, 245, 195, border_alpha), (cx, cy), (cx + sx * c_len, cy), 2)
            pygame.draw.line(bubble_surf, (255, 245, 195, border_alpha), (cx, cy), (cx, cy + sy * c_len), 2)

        # Cabeçalho do balão
        step_indicator = f"PASSO {self.step_index + 1:02d}/{len(self.steps):02d}  ·  {step.subtitle.upper()}"
        theme.eyebrow(bubble_surf, step_indicator, asset_manager.small_font, 20, 15)
        draw_text(bubble_surf, step.title, asset_manager.menu_font, GOLD, 20, 31)

        # Divisor rúnico
        pygame.draw.line(bubble_surf, (80, 68, 48, border_alpha), (20, 60), (bw - 20, 60), 1)

        # Linhas de texto explicativas
        text_y = 69
        for line in step.lines:
            draw_text(bubble_surf, line, asset_manager.font, WHITE, 20, text_y)
            text_y += 22

        # Rodapé com instrução de clique pulsante
        click_prompt = "CLIQUE EM QUALQUER LUGAR PARA AVANÇAR  ▸"
        draw_text(
            bubble_surf,
            click_prompt,
            asset_manager.small_font,
            GOLD,
            bw // 2,
            bh - 22,
            center=True,
        )

        # Blita o balão flutuante na tela
        bubble_surf.set_alpha(alpha)
        surface.blit(bubble_surf, (bx, int(actual_y)))

        # 6. Botão sutil "✕ Pular Tutorial" no canto superior direito
        skip_hover = self.skip_button_rect.collidepoint(mouse_pos)
        skip_surf = pygame.Surface(self.skip_button_rect.size, pygame.SRCALPHA)
        btn_bg = (30, 22, 18, int(190 * (alpha / 255))) if skip_hover else (16, 18, 18, int(150 * (alpha / 255)))
        border_col = (210, 160, 90, alpha) if skip_hover else (120, 105, 75, alpha)
        pygame.draw.rect(skip_surf, btn_bg, pygame.Rect(0, 0, *self.skip_button_rect.size), border_radius=6)
        pygame.draw.rect(skip_surf, border_col, pygame.Rect(0, 0, *self.skip_button_rect.size), width=1, border_radius=6)
        draw_text(
            skip_surf,
            "✕ PULAR GUIA",
            asset_manager.small_font,
            GOLD if skip_hover else GRAY,
            self.skip_button_rect.width // 2,
            self.skip_button_rect.height // 2,
            center=True,
        )
        surface.blit(skip_surf, self.skip_button_rect.topleft)

    def handle_event(self, event, mouse_pos: tuple[int, int]) -> bool:
        if not self.is_active:
            return False

        # Clique do mouse em qualquer lugar da tela avança o tutorial
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.skip_button_rect.collidepoint(mouse_pos):
                self.skip()
                return True

            # Qualquer clique na tela avança o tutorial
            self.advance()
            return True

        # Suporte complementar via teclado para acessibilidade
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_RIGHT):
                self.advance()
                return True
            if event.key in (pygame.K_LEFT, pygame.K_BACKSPACE):
                self.prev_step()
                return True
            if event.key == pygame.K_ESCAPE:
                self.skip()
                return True
            return True

        return False
