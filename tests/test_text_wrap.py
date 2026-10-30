"""Testes da quebra automática de linha usada pelas caixas de texto."""
import os
import unittest

import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

from src.ui.helpers import wrap_text, truncate_text


class WrapTextTests(unittest.TestCase):
    def setUp(self):
        self.font = pygame.font.SysFont(None, 20)

    def test_short_text_stays_on_one_line(self):
        self.assertEqual(wrap_text("Energia insuficiente!", self.font, 400), ["Energia insuficiente!"])

    def test_long_text_never_exceeds_width(self):
        text = "Quando a barra atingir 100%, sua habilidade suprema desperta e uma carta dourada aparece."
        lines = wrap_text(text, self.font, 160)
        self.assertGreater(len(lines), 1)
        for line in lines:
            self.assertLessEqual(self.font.size(line)[0], 160)
        self.assertEqual(" ".join(lines).split(), text.split())

    def test_word_wider_than_box_is_split(self):
        lines = wrap_text("início " + "A" * 60 + " fim", self.font, 120)
        for line in lines:
            self.assertLessEqual(self.font.size(line)[0], 120)
        self.assertEqual("".join(lines).replace(" ", ""), "início" + "A" * 60 + "fim")

    def test_explicit_newlines_are_kept(self):
        self.assertEqual(wrap_text("linha um\nlinha dois", self.font, 400), ["linha um", "linha dois"])

    def test_empty_text(self):
        self.assertEqual(wrap_text("", self.font, 100), [])

    def test_truncate_text_fits_width(self):
        text = "PASSO 01/09  ·  UM SUBTÍTULO MUITO LONGO PARA O CABEÇALHO"
        short = truncate_text(text, self.font, 150)
        self.assertLessEqual(self.font.size(short)[0], 150)
        self.assertTrue(short.endswith("…"))
        self.assertEqual(truncate_text("curto", self.font, 150), "curto")


if __name__ == "__main__":
    unittest.main()
