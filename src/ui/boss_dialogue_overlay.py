"""Diálogos de introdução de chefes, sem executar nenhuma lógica de combate."""

import pygame

from src.config.settings import WIDTH, HEIGHT


class BossDialogueOverlay:
    """Mostra cenário + retratos ampliados + falas digitadas antes da luta."""

    LETTER_INTERVAL_MS = 28
    PORTRAIT_SIZE = (300, 330)

    def __init__(self, assets, enemy_name, lines, background_level):
        self.assets = assets
        self.enemy_name = enemy_name
        self.lines = tuple(lines)
        self.background_level = background_level
        self.index = 0
        self.visible_count = 0
        self.elapsed_ms = 0.0
        self.finished = not bool(self.lines)
        self._fallback_font = None
        self._validate_lines()

    def _validate_lines(self):
        for line in self.lines:
            if (not isinstance(line, (tuple, list)) or len(line) != 2
                    or not all(isinstance(item, str) for item in line)):
                raise ValueError("Cada diálogo deve ser (nome_do_personagem, texto).")

    @property
    def current(self):
        return self.lines[self.index] if not self.finished else None

    @property
    def text_complete(self):
        return self.finished or self.visible_count >= len(self.current[1])

    def update(self, dt):
        if self.finished or self.text_complete:
            return
        self.elapsed_ms += max(0, dt)
        count = int(self.elapsed_ms / self.LETTER_INTERVAL_MS)
        if count:
            self.visible_count = min(len(self.current[1]), self.visible_count + count)
            self.elapsed_ms -= count * self.LETTER_INTERVAL_MS

    def advance(self):
        """Primeiro clique completa a fala; o seguinte avança para a próxima."""
        if self.finished:
            return
        if not self.text_complete:
            self.visible_count = len(self.current[1])
            self.elapsed_ms = 0.0
        elif self.index + 1 < len(self.lines):
            self.index += 1
            self.visible_count = 0
            self.elapsed_ms = 0.0
        else:
            self.finished = True

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.advance()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.advance()

    def _portrait(self, surface, name, rect, *, active=True):
        """Retrato em destaque para quem fala; o ouvinte fica translúcido."""
        image = self.assets.get_character_portrait(name, rect.size)
        if image is None:
            # Reaproveita a representação padrão da HUD quando não há retrato.
            from src.ui.battle_hud import BattleHUD
            if not hasattr(self, "_hud"):
                self._hud = BattleHUD(self.assets)
            image = pygame.Surface(rect.size, pygame.SRCALPHA)
            self._hud.portrait(
                image, image.get_rect(), name, player=name.casefold() == "jaum manel"
            )
        if not active:
            image = image.copy()  # Nunca alterar o asset compartilhado da HUD.
            image.set_alpha(120)
        surface.blit(image, rect)

    @staticmethod
    def _wrap(text, font, max_width):
        """Quebra linhas por largura e preserva novas linhas intencionais."""
        lines = []
        for paragraph in text.split("\n"):
            words = paragraph.split(" ")
            current = ""
            for word in words:
                trial = (current + " " + word).strip()
                if current and font.size(trial)[0] > max_width:
                    lines.append(current)
                    current = word
                else:
                    current = trial
            lines.append(current)
        return lines

    def draw(self, surface):
        if self.finished:
            return
        bg = self.assets.get_battle_background(self.background_level)
        if bg is not None:
            surface.blit(bg, (0, 0))
        else:
            surface.fill((20, 28, 28))

        # Escurecimento sutil para manter o texto e os personagens legíveis.
        tint = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        tint.fill((0, 0, 0, 48))
        surface.blit(tint, (0, 0))

        speaker = self.current[0].strip().casefold()
        player_speaking = speaker == "jaum manel"
        enemy_speaking = speaker == self.enemy_name.strip().casefold()
        # Alinhamento inferior fixo: o retrato ativo cresce sem deslocar a caixa.
        bottom_y = HEIGHT - 330
        center_player_x = 245
        center_enemy_x = WIDTH - 245
        def portrait_rect(center_x, speaking):
            w, h = (340, 370) if speaking else (270, 297)
            return pygame.Rect(center_x - w // 2, bottom_y - h, w, h)
        player_rect = portrait_rect(center_player_x, player_speaking)
        enemy_rect = portrait_rect(center_enemy_x, enemy_speaking)
        self._portrait(surface, "jaum manel", player_rect, active=player_speaking)
        self._portrait(surface, self.enemy_name, enemy_rect, active=enemy_speaking)

        panel = pygame.Rect(65, HEIGHT - 328, WIDTH - 130, 269)
        shadow = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 210), shadow.get_rect(), border_radius=16)
        pygame.draw.rect(shadow, (153, 125, 79, 195), shadow.get_rect(), 3, border_radius=16)
        surface.blit(shadow, panel.topleft)

        name, full_text = self.current
        name_font = self.assets.menu_font
        text_font = self.assets.font
        accent = (242, 202, 116) if name.strip().lower() == "jaum manel" else (238, 153, 126)
        surface.blit(name_font.render(name, True, accent), (panel.x + 35, panel.y + 23))
        pygame.draw.line(surface, (120, 109, 93),
                         (panel.x + 35, panel.y + 71),
                         (panel.right - 35, panel.y + 71), 2)

        visible_text = full_text[:self.visible_count]
        max_width = panel.width - 76
        line_y = panel.y + 91
        line_height = max(39, text_font.get_height() + 9)
        for line in self._wrap(visible_text, text_font, max_width):
            if line_y + line_height > panel.bottom - 30:
                break
            surface.blit(text_font.render(line, True, (245, 242, 235)), (panel.x + 38, line_y))
            line_y += line_height

        hint = "CLIQUE OU ESPAÇO PARA CONTINUAR" if self.text_complete else "CLIQUE OU ESPAÇO PARA REVELAR"
        hint_font = self.assets.small_font
        hint_image = hint_font.render(hint, True, (178, 175, 164))
        surface.blit(hint_image, (panel.right - hint_image.get_width() - 35,
                                  panel.bottom - hint_image.get_height() - 15))
