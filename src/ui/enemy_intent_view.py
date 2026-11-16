"""Ícones de habilidades em ordem e descrição detalhada sob o mouse."""
import pygame
from src.ui.helpers import draw_panel, draw_text, wrap_text
from src.systems.enemy_intents import preview_intents
from src.systems.boss_animation_kits import KITS


class EnemyIntentView:
    def __init__(self, assets):
        self.assets = assets
        self.entries = []
        self.tooltip_rect = None
        self._icons = {}
        self._illustrations = {}
        self._previews = {}

    def _preview(self, illustration, size):
        key = (illustration, size)
        if key not in self._previews:
            target = illustration.get_rect().fit(pygame.Rect((0, 0), size))
            self._previews[key] = pygame.transform.smoothscale(illustration, target.size)
        return self._previews[key]

    def icon(self, family):
        if family in self._icons: return self._icons[family]
        s = pygame.Surface((66, 66), pygame.SRCALPHA)
        gold, light = (223, 185, 103), (248, 233, 189)
        def line(points, color=light, width=5): pygame.draw.lines(s, color, False, points, width)
        if family == 'shield':
            pygame.draw.polygon(s, (54, 113, 153), [(12, 12), (33, 6), (54, 12), (50, 42), (33, 59), (17, 42)])
            pygame.draw.polygon(s, gold, [(12, 12), (33, 6), (54, 12), (50, 42), (33, 59), (17, 42)], 3)
            line([(33, 18), (33, 44)])
        elif family == 'heal':
            pygame.draw.circle(s, (35, 76, 49), (33, 33), 26)
            pygame.draw.rect(s, (136, 221, 137), (27, 14, 12, 39), border_radius=3)
            pygame.draw.rect(s, (136, 221, 137), (14, 27, 39, 12), border_radius=3)
        elif family in ('buff', 'smoke'):
            if family == 'smoke':
                for x, y, r in ((20, 41, 14), (35, 32, 17), (47, 44, 12), (32, 14, 8)):
                    pygame.draw.circle(s, (128, 161, 124), (x, y), r)
            else:
                pygame.draw.polygon(s, gold, [(22, 3), (27, 15), (40, 20), (29, 26), (32, 40), (22, 32), (12, 40), (15, 26), (4, 20), (17, 15)])
                pygame.draw.circle(s, (255, 242, 173), (22, 22), 5)
        elif family == 'scythe':
            line([(46,10),(27,59)],gold,5)
            pygame.draw.polygon(s,(164,224,184),[(46,10),(30,5),(15,10),(5,28),(19,18),(34,16)])
            line([(8,29),(16,12),(30,7)],light,2)
        elif family == 'chains':
            for x,y in ((18,17),(30,31),(42,45)):
                pygame.draw.ellipse(s,(112,216,143),(x-9,y-13,20,29),5)
            line([(10,58),(56,58)],gold,3)
        elif family == 'ferry':
            pygame.draw.polygon(s,(104,190,129),[(5,41),(60,41),(50,57),(18,57)])
            line([(34,11),(34,42)],gold,3)
            pygame.draw.polygon(s,(154,218,161),[(31,10),(11,36),(31,34)])
            line([(8,61),(58,61)],light,2)
        elif family == 'coins':
            for x, y in ((18, 41), (33, 20), (48, 44)):
                pygame.draw.circle(s, (197, 125, 38), (x, y), 14)
                pygame.draw.circle(s, gold, (x, y), 11, 3)
                line([(x, y-6), (x, y+6)], gold, 3)
        elif family == 'wave':
            for x, r in ((6, 18), (11, 30), (15, 42)):
                pygame.draw.arc(s, (93, 201, 239), (x, 33-r, r, r*2), -1.15, 1.15, 5)
            line([(9, 33), (27, 33)], gold, 3)
        elif family == 'bolt':
            pygame.draw.polygon(s, (152, 192, 255), [(36, 5), (12, 36), (30, 35), (24, 62), (56, 26), (36, 29)])
        elif family == 'poison':
            pygame.draw.rect(s, gold, (26, 8, 15, 12))
            pygame.draw.polygon(s, (85, 166, 65), [(26, 20), (41, 20), (54, 50), (47, 59), (18, 59), (12, 50)])
            pygame.draw.circle(s, (184, 238, 108), (36, 42), 8)
        elif family == 'fire':
            pygame.draw.polygon(s, (232, 102, 44), [(36, 3), (47, 26), (54, 20), (59, 44), (47, 59), (21, 59), (9, 42), (23, 17), (23, 36)])
            pygame.draw.polygon(s, (255, 215, 99), [(36, 27), (45, 48), (35, 56), (24, 48)])
        elif family == 'earth':
            for pts in ([(6, 56), (12, 24), (26, 17), (32, 56)], [(32, 56), (36, 8), (48, 24), (59, 56)]):
                pygame.draw.polygon(s, (138, 115, 80), pts)
                pygame.draw.polygon(s, gold, pts, 3)
            line([(6, 60), (60, 60)], light, 3)
        elif family == 'claw':
            for i in range(3):
                line([(15+i*14, 8), (11+i*14, 30), (20+i*14, 56)], (235, 209, 174), 6)
        elif family in ('blade', 'blades', 'spin'):
            pygame.draw.polygon(s, (191, 215, 216), [(15, 45), (44, 9), (56, 6), (53, 20), (24, 53)])
            line([(9, 39), (32, 57)], gold, 5)
            line([(11, 59), (20, 48)], (151, 100, 56), 6)
            if family == 'blades':
                pygame.draw.polygon(s, (233, 236, 211), [(45, 45), (17, 9), (6, 6), (8, 20), (38, 53)])
                line([(35, 56), (57, 39)], gold, 5)
            if family == 'spin':
                pygame.draw.arc(s, gold, (5, 5, 56, 56), .1, 4.8, 3)
                pygame.draw.polygon(s, gold, [(56, 21), (63, 29), (51, 30)])
        elif family == 'tool':
            line([(12, 53), (44, 21)], (176, 200, 203), 6)
            line([(38, 27), (56, 9)], (201, 129, 57), 12)
        elif family == 'arrow':
            line([(9, 53), (53, 9)], gold)
            line([(35, 11), (54, 8), (51, 27)])
            line([(6, 38), (20, 48), (27, 60)], gold, 3)
        elif family == 'axe':
            line([(17, 59), (44, 9)], (167, 111, 60), 8)
            pygame.draw.polygon(s, (198, 211, 207), [(24, 11), (42, 14), (57, 30), (60, 12), (45, 5)])
        else:
            pygame.draw.polygon(s, (189, 128, 75), [(11, 27), (23, 14), (45, 14), (54, 26), (53, 47), (33, 54), (15, 44)])
            for x in (21, 32, 42): line([(x, 18), (x, 33)], gold, 3)
            line([(9, 53), (21, 57)], light, 3)
        self._icons[family] = s
        return s

    def draw(self, surface, engine, mouse):
        self.entries = []
        self._illustrations.clear()
        if engine.state in ('victory', 'game_over', 'phase_complete', 'boss_transition'): return
        intents = preview_intents(engine)
        for i, intent in enumerate(intents):
            rect = pygame.Rect(1761-len(intents)*122+i*122, 234, 104, 112)
            hover = rect.collidepoint(mouse)
            border = (255, 214, 118) if hover or intent.special else (169, 124, 67) if intent.state == 'active' else (103, 96, 67)
            draw_panel(surface, rect, fill=(10, 22, 23, 242), border=border, radius=11, shadow=False)
            illustration = self.assets.get_intent_art(engine.enemy.name, intent.action.visual_effect, special=intent.special)
            art_area = pygame.Rect(rect.x+5, rect.y+5, rect.width-10, 78)
            art = self._preview(illustration, art_area.size) if illustration else self.icon(intent.family)
            if intent.state == 'done':
                art = art.copy()
                art.set_alpha(65)
            surface.blit(art, art.get_rect(center=art_area.center))
            badge = pygame.Rect(rect.right-46, rect.bottom-27, 41, 23)
            draw_text(surface, str(intent.order), self.assets.small_font, (227, 195, 121), rect.x+15, badge.centery, center=True)
            if intent.special:
                x, y = rect.centerx-8, badge.centery
                pygame.draw.polygon(surface, (255, 218, 118), [(x, y-6), (x+6, y), (x, y+6), (x-6, y)])
            if intent.state == 'done':
                pygame.draw.lines(surface, (135, 164, 126), False, [(rect.right-30, rect.bottom-15), (rect.right-23, rect.bottom-8), (rect.right-8, rect.bottom-24)], 3)
            else:
                pygame.draw.rect(surface, (11, 15, 15), badge, border_radius=5)
                color = (244, 160, 130) if intent.action.action_type == 'attack' else (169, 213, 189)
                draw_text(surface, str(intent.value), self.assets.small_font, color, badge.centerx, badge.centery, center=True)
            self.entries.append((rect, intent))
            self._illustrations[rect.topleft] = illustration if engine.enemy.name.strip().lower() in KITS else None
        if len(intents) > 1:
            x = self.entries[0][0].right+8
            y = self.entries[0][0].centery
            pygame.draw.lines(surface, (192, 157, 88), False, [(x, y-7), (x+8, y), (x, y+7)], 3)

    def draw_tooltip(self, surface, mouse):
        self.tooltip_rect = None
        bounds = surface.get_rect().inflate(-32, -32)
        for target, intent in self.entries:
            if not target.collidepoint(mouse):
                continue

            illustration = self._illustrations.get(target.topleft)
            if illustration is not None:
                art = self._preview(illustration, (min(440, bounds.width), min(519, bounds.height)))
                center = (bounds.centerx, round(surface.get_height() * .43))
                rect = art.get_rect(center=center).clamp(bounds)
                surface.blit(art, rect)
                self.tooltip_rect = rect
                return

            # Sem uma carta completa, mantém as regras em uma ficha única.
            width = min(475, bounds.width)
            lines = wrap_text(intent.description, self.assets.small_font, width-36)
            rect = pygame.Rect(0, target.bottom+10, width, 66+len(lines)*29)
            rect.centerx = target.centerx
            rect.clamp_ip(bounds)
            draw_panel(surface, rect, fill=(8, 17, 18, 250), border=(192, 145, 76), radius=12)
            draw_text(surface, intent.action.name, self.assets.small_font,
                      (245, 219, 161), rect.x+18, rect.y+16)
            for i, text in enumerate(lines):
                draw_text(surface, text, self.assets.small_font,
                          (226, 230, 207), rect.x+18, rect.y+53+i*29)
            self.tooltip_rect = rect
            return
