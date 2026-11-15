
"""Diálogos de introdução de chefes, sem executar lógica de combate."""

import unicodedata

import pygame

from src.config.settings import WIDTH, HEIGHT


class BossDialogueOverlay:
    """Mostra cenário, retratos e diálogos animados antes da batalha."""

    # CONFIGURAÇÕES DA ANIMAÇÃO
    TYPING_SPEED = 35
    DIALOGUE_DELAY_MS = 1000
    PORTRAIT_SIZE = (300, 330)

    # NOMES PERSONALIZADOS DOS CHEFES
    # Esquerda: nome original do jogo, sem acentos.
    # Direita: nome que aparecerá na caixa de diálogo.
    DISPLAY_NAMES = {
        "guardiao da pedra": "Octavius, o Predador",
        "alvaro e tex": "Álvaro e Texx, Caçadores de Recompensas",
        "gordofera": "Sir Thomas, a Besta Fera",
        "carrasco da vigilia": "Labrro, o Carrasco",
        "corpo seco": "Corpo Seco, o Assassino",
        "goblin nerd": "Jozephino, o Inventor",
        "zanzara": "Zanzara, Líder do Clã Moskar",
    }

    @staticmethod
    def _normalize_name(name):
        """Remove diferenças de acentos, maiúsculas e espaços."""
        normalized = unicodedata.normalize(
            "NFKD",
            name.strip().casefold()
        )

        normalized = "".join(
            char for char in normalized
            if not unicodedata.combining(char)
        )

        return " ".join(normalized.split())

    def __init__(self, assets, enemy_name, lines, background_level):
        self.assets = assets
        self.enemy_name = enemy_name
        self.lines = tuple(lines)
        self.background_level = background_level

        self.index = 0
        self.visible_count = 0
        self.elapsed_ms = 0.0
        self.delay_remaining_ms = self.DIALOGUE_DELAY_MS

        self.finished = not bool(self.lines)
        self._fallback_font = None

        self._validate_lines()

    def _validate_lines(self):
        """Verifica se as falas possuem o formato correto."""
        for line in self.lines:
            if (
                not isinstance(line, (tuple, list))
                or len(line) != 2
                or not all(isinstance(item, str) for item in line)
            ):
                raise ValueError(
                    "Cada diálogo deve ser (nome_do_personagem, texto)."
                )

    @property
    def current(self):
        if self.finished:
            return None

        return self.lines[self.index]

    @property
    def text_complete(self):
        return (
            self.finished
            or self.visible_count >= len(self.current[1])
        )

    def update(self, dt):
        """Atualiza a animação utilizando dt em milissegundos."""
        if self.finished:
            return

        delta_ms = max(0.0, dt)

        # Pausa inicial para mostrar o cenário.
        if self.delay_remaining_ms > 0:
            remaining = self.delay_remaining_ms

            self.delay_remaining_ms = max(
                0.0,
                remaining - delta_ms
            )

            delta_ms = max(0.0, delta_ms - remaining)

        if self.delay_remaining_ms > 0 or self.text_complete:
            return

        # Efeito de digitação.
        self.elapsed_ms += delta_ms

        chars = int(
            self.elapsed_ms * self.TYPING_SPEED / 1000.0
        )

        if chars:
            self.visible_count = min(
                len(self.current[1]),
                self.visible_count + chars
            )

            self.elapsed_ms -= (
                chars * 1000.0 / self.TYPING_SPEED
            )

    def advance(self):
        """Revela a fala ou avança para a próxima."""
        if self.finished:
            return

        # Primeiro clique durante a pausa mostra a caixa.
        if self.delay_remaining_ms > 0:
            self.delay_remaining_ms = 0.0
            return

        # Revela todo o texto atual.
        if not self.text_complete:
            self.visible_count = len(self.current[1])
            self.elapsed_ms = 0.0

        # Avança para a próxima fala.
        elif self.index + 1 < len(self.lines):
            self.index += 1
            self.visible_count = 0
            self.elapsed_ms = 0.0

        # Finaliza os diálogos e libera o combate.
        else:
            self.finished = True

    def handle_event(self, event):
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            self.advance()

        elif (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_SPACE
            and not getattr(event, "repeat", False)
        ):
            self.advance()

    def _portrait(self, surface, name, rect, *, active=True):
        """Desenha retratos com destaque para quem está falando."""
        image = self.assets.get_character_portrait(
            name,
            rect.size
        )

        if image is None:
            from src.ui.battle_hud import BattleHUD

            if not hasattr(self, "_hud"):
                self._hud = BattleHUD(self.assets)

            image = pygame.Surface(
                rect.size,
                pygame.SRCALPHA
            )

            self._hud.portrait(
                image,
                image.get_rect(),
                name,
                player=self._normalize_name(name) == "jaum manel"
            )

        if not active:
            image = image.copy()
            image.set_alpha(120)

        surface.blit(image, rect)

    @staticmethod
    def _wrap(text, font, max_width):
        """Quebra textos longos preservando mudanças de linha."""
        lines = []

        for paragraph in text.split("\n"):
            words = paragraph.split(" ")
            current = ""

            for word in words:
                trial = (current + " " + word).strip()

                if (
                    current
                    and font.size(trial)[0] > max_width
                ):
                    lines.append(current)
                    current = word
                else:
                    current = trial

            lines.append(current)

        return lines

    def _get_display_name(self, name):
        """Retorna o nome personalizado sem alterar o nome interno."""
        normalized_name = self._normalize_name(name)

        return self.DISPLAY_NAMES.get(
            normalized_name,
            name
        )

    def draw(self, surface):
        if self.finished:
            return

        # CENÁRIO DA BATALHA
        bg = self.assets.get_battle_background(
            self.background_level
        )

        if bg is not None:
            surface.blit(bg, (0, 0))
        else:
            surface.fill((20, 28, 28))

        # Escurecimento sutil do cenário.
        tint = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )
        tint.fill((0, 0, 0, 48))
        surface.blit(tint, (0, 0))

        # IDENTIFICAÇÃO DOS PERSONAGENS
        # Os retratos continuam usando os nomes originais.
        name, full_text = self.current

        speaker = self._normalize_name(name)
        enemy_internal_name = self._normalize_name(
            self.enemy_name
        )

        player_speaking = speaker == "jaum manel"
        enemy_speaking = speaker == enemy_internal_name

        # POSICIONAMENTO DOS RETRATOS
        bottom_y = HEIGHT - 330
        center_player_x = 245
        center_enemy_x = WIDTH - 245

        def portrait_rect(center_x, speaking):
            if speaking:
                w, h = (340, 370)
            else:
                w, h = (270, 297)

            return pygame.Rect(
                center_x - w // 2,
                bottom_y - h,
                w,
                h
            )

        player_rect = portrait_rect(
            center_player_x,
            player_speaking
        )

        enemy_rect = portrait_rect(
            center_enemy_x,
            enemy_speaking
        )

        self._portrait(
            surface,
            "jaum manel",
            player_rect,
            active=player_speaking
        )

        self._portrait(
            surface,
            self.enemy_name,
            enemy_rect,
            active=enemy_speaking
        )

        # PAUSA ANTES DO DIÁLOGO
        if self.delay_remaining_ms > 0:
            return

        # CAIXA DE DIÁLOGO
        panel = pygame.Rect(
            65,
            HEIGHT - 328,
            WIDTH - 130,
            269
        )

        shadow = pygame.Surface(
            (panel.width, panel.height),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            shadow,
            (0, 0, 0, 210),
            shadow.get_rect(),
            border_radius=16
        )

        pygame.draw.rect(
            shadow,
            (153, 125, 79, 195),
            shadow.get_rect(),
            3,
            border_radius=16
        )

        surface.blit(shadow, panel.topleft)

        # NOME PERSONALIZADO
        # Apenas este nome será exibido na caixa.
        display_name = self._get_display_name(name)

        name_font = self.assets.menu_font
        text_font = self.assets.font

        accent = (
            (242, 202, 116)
            if speaker == "jaum manel"
            else (238, 153, 126)
        )

        surface.blit(
            name_font.render(
                display_name,
                True,
                accent
            ),
            (panel.x + 35, panel.y + 23)
        )

        pygame.draw.line(
            surface,
            (120, 109, 93),
            (panel.x + 35, panel.y + 71),
            (panel.right - 35, panel.y + 71),
            2
        )

        # TEXTO COM ANIMAÇÃO DE DIGITAÇÃO
        visible_text = full_text[:self.visible_count]

        max_width = panel.width - 76
        line_y = panel.y + 91

        line_height = max(
            39,
            text_font.get_height() + 9
        )

        for line in self._wrap(
            visible_text,
            text_font,
            max_width
        ):
            if line_y + line_height > panel.bottom - 30:
                break

            surface.blit(
                text_font.render(
                    line,
                    True,
                    (245, 242, 235)
                ),
                (panel.x + 38, line_y)
            )

            line_y += line_height

        # INSTRUÇÃO PARA AVANÇAR
        hint = (
            "CLIQUE OU ESPAÇO PARA CONTINUAR"
            if self.text_complete
            else "CLIQUE OU ESPAÇO PARA REVELAR"
        )

        hint_font = self.assets.small_font

        hint_image = hint_font.render(
            hint,
            True,
            (178, 175, 164)
        )

        surface.blit(
            hint_image,
            (
                panel.right - hint_image.get_width() - 35,
                panel.bottom - hint_image.get_height() - 15
            )
        )
