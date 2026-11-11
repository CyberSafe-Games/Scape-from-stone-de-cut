"""Fonte do jogo com suporte a símbolos ausentes na fonte autoral.

``GameFont`` é um ``pygame.font.Font`` comum (mesma API de ``render``/``size``),
então todas as cenas continuam funcionando sem mudanças. A diferença é que
caracteres sem glifo na fonte principal são desenhados com uma fonte de
símbolos do sistema, alinhados pela linha de base, em vez do quadrado vazio.
"""
import pygame

# Caractere de uso privado: nenhuma fonte de texto o define, então seu desenho
# é o glifo ".notdef" (quadrado vazio) usado para detectar símbolos ausentes.
_PROBE_MISSING = ""


class GameFont(pygame.font.Font):

    def __init__(self, path, size, fallback=None, line_height=None):
        super().__init__(path, size)
        self._fallback = fallback
        self._linesize = (max(super().get_linesize(), round(size * line_height))
                          if line_height else None)
        self._glyph_cache = {}
        self._notdef = self._glyph_key(_PROBE_MISSING)

    # ------------------------------------------------------------------
    # Detecção de glifos
    # ------------------------------------------------------------------
    def _glyph_key(self, char):
        surf = super().render(char, False, (255, 255, 255))
        return surf.get_size(), pygame.image.tobytes(surf, "RGBA")

    def has_glyph(self, char):
        if char in self._glyph_cache:
            return self._glyph_cache[char]
        if char.isspace():
            present = True
        else:
            present = super().size(char)[0] > 0 and self._glyph_key(char) != self._notdef
        self._glyph_cache[char] = present
        return present

    def _runs(self, text):
        """Divide o texto em trechos (fonte, texto) por disponibilidade de glifo."""
        runs = []
        for char in text:
            font = self if (self._fallback is None or self.has_glyph(char)) else self._fallback
            if runs and runs[-1][0] is font:
                runs[-1][1] += char
            else:
                runs.append([font, char])
        return runs

    # ------------------------------------------------------------------
    # API do pygame.font.Font
    # ------------------------------------------------------------------
    def get_linesize(self):
        return self._linesize or super().get_linesize()

    def size(self, text):
        text = str(text)
        runs = self._runs(text)
        if len(runs) <= 1 and (not runs or runs[0][0] is self):
            return super().size(text)
        width = sum(self._run_size(font, chunk)[0] for font, chunk in runs)
        return width, self.get_height()

    def _run_size(self, font, chunk):
        return super().size(chunk) if font is self else font.size(chunk)

    def _run_render(self, font, chunk, antialias, color, bgcolor):
        if font is self:
            return super().render(chunk, antialias, color, bgcolor)
        return font.render(chunk, antialias, color, bgcolor)

    def render(self, text, antialias, color, bgcolor=None, wraplength=0):
        text = "" if text is None else str(text)
        runs = self._runs(text)
        if len(runs) <= 1 and (not runs or runs[0][0] is self):
            return super().render(text, antialias, color, bgcolor, wraplength)

        # Mantém a altura da fonte principal (centralização idêntica aos demais
        # textos) e alinha os símbolos substitutos pela linha de base.
        pieces = [(font, self._run_render(font, chunk, antialias, color, bgcolor))
                  for font, chunk in runs]
        width = sum(piece.get_width() for _, piece in pieces)
        result = pygame.Surface((max(1, width), self.get_height()), pygame.SRCALPHA)
        if bgcolor is not None:
            result.fill(bgcolor)
        x = 0
        for font, piece in pieces:
            result.blit(piece, (x, self.get_ascent() - font.get_ascent()))
            x += piece.get_width()
        return result
