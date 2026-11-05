"""Ícones de habilidades em ordem e descrição detalhada sob o mouse."""
import pygame
from src.ui.helpers import draw_panel, draw_text, wrap_text
from src.systems.enemy_intents import preview_intents


class EnemyIntentView:
    def __init__(self, assets):
        self.assets = assets
        self.entries = []
        self.tooltip_rect = None
        self._icons = {}

    def icon(self, family):
        if family in self._icons: return self._icons[family]
        s = pygame.Surface((44, 44), pygame.SRCALPHA)
        gold, light = (223, 185, 103), (248, 233, 189)
        def line(points, color=light, width=3): pygame.draw.lines(s, color, False, points, width)
        if family == 'shield':
            pygame.draw.polygon(s, (54, 113, 153), [(8, 8), (22, 4), (36, 8), (33, 28), (22, 39), (11, 28)])
            pygame.draw.polygon(s, gold, [(8, 8), (22, 4), (36, 8), (33, 28), (22, 39), (11, 28)], 2)
            line([(22, 12), (22, 29)])
        elif family == 'heal':
            pygame.draw.circle(s, (35, 76, 49), (22, 22), 17)
            pygame.draw.rect(s, (136, 221, 137), (18, 9, 8, 26), border_radius=2)
            pygame.draw.rect(s, (136, 221, 137), (9, 18, 26, 8), border_radius=2)
        elif family in ('buff', 'smoke'):
            if family == 'smoke':
                for x, y, r in ((13, 27, 9), (23, 21, 11), (31, 29, 8), (21, 9, 5)):
                    pygame.draw.circle(s, (128, 161, 124), (x, y), r)
            else:
                pygame.draw.polygon(s, gold, [(22, 3), (27, 15), (40, 20), (29, 26), (32, 40), (22, 32), (12, 40), (15, 26), (4, 20), (17, 15)])
                pygame.draw.circle(s, (255, 242, 173), (22, 22), 5)
        elif family == 'coins':
            for x, y in ((12, 27), (22, 13), (32, 29)):
                pygame.draw.circle(s, (197, 125, 38), (x, y), 9)
                pygame.draw.circle(s, gold, (x, y), 7, 2)
                line([(x, y-4), (x, y+4)], gold, 2)
        elif family == 'wave':
            for x, r in ((4, 12), (7, 20), (10, 28)):
                pygame.draw.arc(s, (93, 201, 239), (x, 22-r, r, r*2), -1.15, 1.15, 3)
            line([(6, 22), (18, 22)], gold, 2)
        elif family == 'bolt':
            pygame.draw.polygon(s, (152, 192, 255), [(24, 3), (8, 24), (20, 23), (16, 41), (37, 17), (24, 19)])
        elif family == 'poison':
            pygame.draw.rect(s, gold, (17, 5, 10, 8))
            pygame.draw.polygon(s, (85, 166, 65), [(17, 13), (27, 13), (36, 33), (31, 39), (12, 39), (8, 33)])
            pygame.draw.circle(s, (184, 238, 108), (24, 28), 5)
        elif family == 'fire':
            pygame.draw.polygon(s, (232, 102, 44), [(24, 2), (31, 17), (36, 13), (39, 29), (31, 39), (14, 39), (6, 28), (15, 11), (15, 24)])
            pygame.draw.polygon(s, (255, 215, 99), [(24, 18), (30, 32), (23, 37), (16, 32)])
        elif family == 'earth':
            for pts in ([(4, 37), (8, 16), (17, 11), (21, 37)], [(21, 37), (24, 5), (32, 16), (39, 37)]):
                pygame.draw.polygon(s, (138, 115, 80), pts)
                pygame.draw.polygon(s, gold, pts, 2)
            line([(4, 40), (40, 40)], light, 2)
        elif family == 'claw':
            for i in range(3):
                line([(10+i*9, 5), (7+i*9, 20), (13+i*9, 37)], (235, 209, 174), 4)
        elif family in ('blade', 'blades', 'spin'):
            pygame.draw.polygon(s, (191, 215, 216), [(10, 30), (29, 6), (37, 4), (35, 13), (16, 35)])
            line([(6, 26), (21, 38)], gold, 3)
            line([(7, 39), (13, 32)], (151, 100, 56), 4)
            if family == 'blades':
                pygame.draw.polygon(s, (233, 236, 211), [(30, 30), (11, 6), (4, 4), (5, 13), (25, 35)])
                line([(23, 37), (38, 26)], gold, 3)
            if family == 'spin':
                pygame.draw.arc(s, gold, (3, 3, 37, 37), .1, 4.8, 2)
                pygame.draw.polygon(s, gold, [(37, 14), (42, 19), (34, 20)])
        elif family == 'tool':
            line([(8, 35), (29, 14)], (176, 200, 203), 4)
            line([(25, 18), (37, 6)], (201, 129, 57), 8)
        elif family == 'arrow':
            line([(6, 35), (35, 6)], gold)
            line([(23, 7), (36, 5), (34, 18)])
            line([(4, 25), (13, 32), (18, 40)], gold, 2)
        elif family == 'axe':
            line([(11, 39), (29, 6)], (167, 111, 60), 5)
            pygame.draw.polygon(s, (198, 211, 207), [(16, 7), (28, 9), (38, 20), (40, 8), (30, 3)])
        else:
            pygame.draw.polygon(s, (189, 128, 75), [(7, 18), (15, 9), (30, 9), (36, 17), (35, 31), (22, 36), (10, 29)])
            for x in (14, 21, 28): line([(x, 12), (x, 22)], gold, 2)
            line([(6, 35), (14, 38)], light, 2)
        self._icons[family] = s
        return s

    def draw(self, surface, engine, mouse):
        self.entries = []
        if engine.state in ('victory', 'game_over', 'phase_complete', 'boss_transition'): return
        intents = preview_intents(engine)
        for i, intent in enumerate(intents):
            rect = pygame.Rect(1174-len(intents)*76+i*76, 156, 64, 59)
            hover = rect.collidepoint(mouse)
            border = (255, 214, 118) if hover or intent.special else (169, 124, 67) if intent.state == 'active' else (103, 96, 67)
            draw_panel(surface, rect, fill=(10, 22, 23, 242), border=border, radius=7, shadow=False)
            art = self.icon(intent.family).copy()
            if intent.state == 'done': art.set_alpha(65)
            surface.blit(art, (rect.x+10, rect.y+7))
            draw_text(surface, str(intent.order), self.assets.small_font, (227, 195, 121), rect.x+8, rect.y+6)
            if intent.special:
                pygame.draw.polygon(surface, (255, 218, 118), [(rect.right-8, rect.y+3), (rect.right-3, rect.y+8), (rect.right-8, rect.y+13), (rect.right-13, rect.y+8)])
            if intent.state == 'done':
                pygame.draw.lines(surface, (135, 164, 126), False, [(rect.right-20, rect.bottom-10), (rect.right-15, rect.bottom-5), (rect.right-5, rect.bottom-16)], 2)
            else:
                badge = pygame.Rect(rect.right-29, rect.bottom-19, 27, 17)
                pygame.draw.rect(surface, (11, 15, 15), badge, border_radius=3)
                color = (244, 160, 130) if intent.action.action_type == 'attack' else (169, 213, 189)
                draw_text(surface, str(intent.value), self.assets.small_font, color, badge.centerx, badge.centery, center=True)
            self.entries.append((rect, intent))
        if len(intents) > 1:
            x = self.entries[0][0].right+5
            pygame.draw.lines(surface, (192, 157, 88), False, [(x, 180), (x+5, 185), (x, 190)], 2)

    def draw_tooltip(self, surface, mouse):
        self.tooltip_rect = None
        for target, intent in self.entries:
            if not target.collidepoint(mouse): continue
            lines = wrap_text(intent.description, self.assets.small_font, 320)
            rect = pygame.Rect(min(surface.get_width()-362, max(12, target.right-350)), 225, 350, 65+len(lines)*19)
            self.tooltip_rect = rect
            draw_panel(surface, rect, fill=(8, 17, 18, 250), border=(192, 145, 76), radius=8)
            font = self.assets.font if self.assets.font.size(intent.action.name)[0] < 320 else self.assets.small_font
            draw_text(surface, intent.action.name, font, (245, 219, 161), rect.x+14, rect.y+10)
            state = {'pending': 'PLANEJADA', 'active': 'EM EXECUÇÃO', 'done': 'CONCLUÍDA'}[intent.state]
            draw_text(surface, f'{intent.order}ª AÇÃO / {intent.total} · {state}', self.assets.small_font, (162, 177, 158), rect.x+14, rect.y+36)
            for i, text in enumerate(lines):
                draw_text(surface, text, self.assets.small_font, (226, 225, 207), rect.x+14, rect.y+59+i*19)
            break
