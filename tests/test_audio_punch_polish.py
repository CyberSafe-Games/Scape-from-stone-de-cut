"""Verifica o recurso real e a janela curta usada pelo golpe, sem reproduzir áudio."""
import array
import ast
import math
from pathlib import Path
import unittest
import pygame
from src.config.audio_mix import SOUND_VOLUMES


class PunchPolishTests(unittest.TestCase):
    def test_registered_punch_has_headroom_and_keeps_contact_in_short_window(self):
        root = Path(__file__).resolve().parents[1]
        tree = ast.parse((root/'main.py').read_text(encoding='utf-8'))
        sounds = next(ast.literal_eval(n.args[0]) for n in ast.walk(tree)
                      if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                      and n.func.attr == 'register_sounds')
        pygame.mixer.init(frequency=44100, size=-16, channels=2)
        try:
            old = pygame.mixer.Sound(str(root/'assets/audio/dragon-studio-hard-punch-sfx-515251_sync.ogg'))
            new = pygame.mixer.Sound(str(root/'assets/audio'/sounds['gameplay.attack.punch']))
            samples = array.array('h', new.get_raw())
            self.assertAlmostEqual(new.get_length(), old.get_length(), delta=.025)
            self.assertLess(max(map(abs, samples))*SOUND_VOLUMES['gameplay.attack.punch']/32768,
                            10**(-15/20))
            self.assertEqual(sum(abs(v)>=32767 for v in samples), 0)
            # O contato do jogador limita a reprodução a 160 ms: o impacto deve
            # continuar nessa janela, sem introduzir silêncio no começo.
            contact = samples[:int(44100*.16)*2]
            self.assertGreater(max(map(abs, contact))/32768, .02)
            old_contact = array.array('h', old.get_raw())[:len(contact)]
            rms = lambda xs: math.sqrt(sum(v*v for v in xs)/len(xs))/32768
            self.assertLess(rms(contact), rms(old_contact)*.14*.8)
        finally:
            pygame.mixer.quit()
