"""Mapa interativo de sete territórios, integrado aos três saves.

A interface usa a resolução virtual e a paleta do projeto, sem dependência
em imagens externas. A lógica de progressão vive em systems/territory_map.py.
"""
import math
import pygame

from src.config.settings import WIDTH, HEIGHT
from src.config.colors import BG, BLACK, WHITE, GOLD, GRAY, BUTTON_BG, BUTTON_HOVER, GREEN
from src.scenes.base_scene import BaseScene
from src.systems.save_manager import SaveError
from src.systems.territory_map import (
    TERRITORIES, status, completed_count,
)
from src.models.effects.ultimate_effect import ULTIMATE_METADATA, DEFAULT_ULTIMATE_ID
from src.ui.helpers import draw_text, wrap_text
from src.ui import dark_fantasy_theme as theme


MAP_AREA = pygame.Rect(30, 92, 879, 587)
PANEL = pygame.Rect(929, 91, 321, 590)


class MapScene(BaseScene):
    """Permite inspecionar, escolher e iniciar confrontos liberados."""

    def __init__(self, scene_manager, window_manager, asset_manager,
                 save_manager, save_data):
        super().__init__(scene_manager, window_manager, asset_manager)
        self.save_manager = save_manager
        self.save_data = save_data
        available = [t for t in TERRITORIES if status(save_data, t.id) == "available"]
        self.selected = available[-1].id if available else TERRITORIES[-1].id
        self.back_button = pygame.Rect(38, 20, 155, 45)
        self.play_button = pygame.Rect(956, 558, 267, 54)
        self.shop_button = pygame.Rect(956, 622, 267, 43)
        self.guide_button = pygame.Rect(510, 481, 260, 55)
        self.guide_open = not save_data["progresso"].get("guia_mapa_visto", False)
        self.error = ""
        self.elapsed = 0

    def update(self, dt):
        self.elapsed += min(dt, 100)

    def _button(self, surface, rect, title, enabled=True, outline=GOLD):
        hovered = enabled and rect.collidepoint(self.window_manager.get_virtual_mouse_pos())
        theme.button(surface, rect, title, self.asset_manager.small_font,
                     hover=hovered, prominent=(rect == self.play_button), enabled=enabled)

    def _background(self, surface):
        theme.backdrop(surface, self.asset_manager.background, opacity=226)
        theme.panel(surface, MAP_AREA, fill=(12, 21, 20, 243))
        # Mapa topográfico abstrato. Evita massas brilhantes e ícones infantis.
        land = pygame.Surface(MAP_AREA.size, pygame.SRCALPHA)
        pygame.draw.polygon(land, (29, 54, 43, 173), [
            (33, 117), (187, 49), (364, 106), (524, 43), (735, 69),
            (849, 194), (786, 353), (829, 508), (660, 551),
            (506, 477), (322, 542), (145, 473), (24, 511)])
        pygame.draw.polygon(land, (51, 63, 48, 166), [
            (42, 388), (162, 291), (262, 346), (359, 201),
            (480, 271), (586, 202), (800, 224), (780, 464),
            (616, 452), (497, 506), (345, 453), (169, 505)])
        for inset in (19, 37, 58, 78):
            pts = [(inset, 88+inset//4), (212+inset//2, 77),
                   (418, 59+inset), (692-inset//4, 98+inset//3),
                   (814-inset, 294), (733-inset//2, 491-inset//4),
                   (404, 516-inset//4), (105+inset//3, 460-inset//3)]
            pygame.draw.lines(land, (84, 101, 74, 90), True, pts, 1)
        surface.blit(land, MAP_AREA.topleft)
        # Montanhas talhadas em pedra e pinheiros escurecidos.
        for x, y, scale in [(92, 207, 1.1), (314, 114, 1.2), (568, 144, .95),
                            (745, 438, 1.1), (403, 514, .85), (96, 432, .8)]:
            x, y, s = x + MAP_AREA.x, y + MAP_AREA.y, int(31 * scale)
            pygame.draw.polygon(surface, (47, 62, 57), [(x-s, y+s//2),
                (x, y-s), (x+s, y+s//2)])
            pygame.draw.line(surface, (92, 104, 89), (x-s, y+s//2), (x, y-s), 1)
            pygame.draw.line(surface, (92, 104, 89), (x, y-s), (x+s, y+s//2), 1)
        for x, y in [(88, 390), (188, 166), (261, 580), (450, 170),
                     (544, 527), (728, 365), (835, 502), (65, 232), (765, 106)]:
            cx, cy = x+10, y+55
            pygame.draw.polygon(surface, (29, 65, 50), [(cx-15,cy+10), (cx,cy-22), (cx+15,cy+10)])
            pygame.draw.polygon(surface, (43, 83, 58), [(cx-12,cy+1), (cx,cy-23), (cx+12,cy+1)], 1)
            pygame.draw.line(surface, (91, 74, 54), (cx,cy+7), (cx,cy+19), 2)

    def _routes(self, surface):
        for first, second in zip(TERRITORIES, TERRITORIES[1:]):
            accessible = status(self.save_data, second.id) != "locked"
            route_color = (177, 142, 70) if accessible else (79, 75, 79)
            distance = math.dist(first.position, second.position)
            steps = max(1, int(distance / 14))
            for step in range(steps):
                t = step / steps
                px = int(first.position[0] + (second.position[0] - first.position[0]) * t)
                py = int(first.position[1] + (second.position[1] - first.position[1]) * t)
                pygame.draw.circle(surface, (11, 12, 17), (px, py), 5)
                pygame.draw.circle(surface, route_color, (px, py), 2 if accessible else 1)

    def _territories(self, surface):
        cursor = self.window_manager.get_virtual_mouse_pos()
        pulse = 1.0 + 0.06 * math.sin(self.elapsed * 0.004)
        for territory in TERRITORIES:
            x, y = territory.position
            state = status(self.save_data, territory.id)
            chosen = territory.id == self.selected
            hovered = math.dist(cursor, (x, y)) <= 32
            radius = 27 if chosen else 24
            if chosen:
                pygame.draw.circle(surface, (9, 16, 15), (x, y), 39)
                pygame.draw.circle(surface, (174, 135, 71), (x, y), int(35 * pulse), 1)
            fill = (35, 81, 57) if state == "completed" else (80, 65, 43) if state == "available" else (30, 35, 34)
            border = GOLD if (chosen or hovered and state != "locked") else (91, 133, 98) if state == "completed" else (76, 83, 78)
            pygame.draw.circle(surface, (5, 9, 9), (x + 3, y + 5), radius + 6)
            pts = [(x, y-radius), (x+radius, y), (x, y+radius), (x-radius, y)]
            pygame.draw.polygon(surface, fill, pts)
            pygame.draw.lines(surface, border, True, pts, 2)
            inner = [(x,y-radius+7), (x+radius-7,y), (x,y+radius-7), (x-radius+7,y)]
            pygame.draw.lines(surface, (119, 111, 82), True, inner, 1)
            symbol = "V" if state == "completed" else str(territory.level) if state == "available" else "×"
            draw_text(surface, symbol, self.asset_manager.menu_font,
                      WHITE if state != "locked" else GRAY, x, y, center=True)
            font = self.asset_manager.small_font
            label_width = min(192, font.size(territory.title)[0] + 26)
            label_rect = pygame.Rect(0, 0, label_width, 30)
            label_rect.center = (x, y+49)
            pygame.draw.rect(surface, (12, 20, 19), label_rect, border_radius=2)
            pygame.draw.rect(surface, (89, 77, 58) if state != "locked" else (48, 56, 53), label_rect, 1, border_radius=2)
            draw_text(surface, territory.title, font,
                      WHITE if state != "locked" else GRAY, x, label_rect.centery, center=True)

    def _sidebar(self, surface):
        theme.panel(surface, PANEL, fill=(11, 18, 18, 244))
        center = PANEL.centerx
        selected_territory = next(t for t in TERRITORIES if t.id == self.selected)
        state = status(self.save_data, selected_territory.id)
        progress = self.save_data["progresso"]
        draw_text(surface, "SUA EXPEDIÇÃO", self.asset_manager.menu_font, GOLD,
                  center, 127, center=True)
        draw_text(surface, self.save_data["nome"][:26], self.asset_manager.small_font,
                  GRAY, center, 161, center=True)
        if self.asset_manager.coin_icon is not None:
            icon = pygame.transform.smoothscale(self.asset_manager.coin_icon, (28, 28))
            surface.blit(icon, (center - 68, 183))
        draw_text(surface, f"{progress['moedas']} MOEDAS", self.asset_manager.font, WHITE,
                  center - 29, 183)
        completed = completed_count(self.save_data)
        pygame.draw.rect(surface, (36, 46, 42), pygame.Rect(954, 226, 268, 12), border_radius=6)
        if completed:
            pygame.draw.rect(surface, (69, 117, 80),
                             pygame.Rect(954, 226, int(268 * completed / len(TERRITORIES)), 12), border_radius=6)
        draw_text(surface, f"{completed} DE {len(TERRITORIES)} TERRITÓRIOS CONCLUÍDOS",
                  self.asset_manager.small_font, GRAY, center, 261, center=True)
        pygame.draw.line(surface, (91, 76, 52), (956, 287), (1223, 287), 1)
        ultimate_id = progress.get("ultimate_equipada", DEFAULT_ULTIMATE_ID)
        ultimate_name = ULTIMATE_METADATA.get(ultimate_id, ULTIMATE_METADATA[DEFAULT_ULTIMATE_ID])["name"]
        draw_text(surface, "ULTIMATE EQUIPADA", self.asset_manager.small_font,
                  (147, 164, 142), center, 312, center=True)
        draw_text(surface, ultimate_name.upper(), self.asset_manager.small_font,
                  WHITE, center, 337, center=True)
        draw_text(surface, f"FASE {selected_territory.level:02d}", self.asset_manager.small_font,
                  GOLD, center, 372, center=True)
        draw_text(surface, selected_territory.title, self.asset_manager.font, WHITE,
                  center, 406, center=True)
        draw_text(surface, selected_territory.subtitle.upper(), self.asset_manager.small_font,
                  GRAY, center, 438, center=True)
        label, color = {
            "locked": ("BLOQUEADA", (159, 101, 96)),
            "available": ("DISPONÍVEL", (177, 143, 87)),
            "completed": ("CONCLUÍDA", (103, 159, 113)),
        }[state]
        pill = pygame.Rect(center - 97, 462, 194, 33)
        pygame.draw.rect(surface, (24, 34, 31), pill, border_radius=16)
        pygame.draw.rect(surface, color, pill, 2, border_radius=16)
        draw_text(surface, label, self.asset_manager.small_font, color,
                  pill.centerx, pill.centery, center=True)
        for line_i, line in enumerate(wrap_text(selected_territory.description,
                                                 self.asset_manager.small_font, 252)[:3]):
            draw_text(surface, line, self.asset_manager.small_font, WHITE,
                      964, 510 + 25 * line_i)
        if state == "locked":
            draw_text(surface, "Conclua a fase anterior para liberar.",
                      self.asset_manager.small_font, (188, 135, 122), 964, 588)
        play_label = "FASE BLOQUEADA" if state == "locked" else "JOGAR NOVAMENTE" if state == "completed" else "INICIAR FASE"
        self._button(surface, self.play_button, play_label, enabled=state != "locked")
        self._button(surface, self.shop_button, "LOJA (EM BREVE)")

    def _guide(self, surface):
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((3, 9, 9, 218))
        surface.blit(shade, (0, 0))
        rect = pygame.Rect(334, 166, 612, 398)
        theme.panel(surface, rect, highlighted=True)
        draw_text(surface, "CARTOGRAFIA DA JORNADA", self.asset_manager.big_font,
                  GOLD, WIDTH // 2, 217, center=True)
        steps = (
            "01  Escolha um dos pontos do mapa para ver sua fase.",
            "02  Inicie apenas territórios disponíveis ou concluídos.",
            "03  Vença, escolha a recompensa e libere a próxima fase.",
            "04  Volte ao mapa sempre que sair de um combate.",
        )
        for i, line in enumerate(steps):
            draw_text(surface, line, self.asset_manager.small_font, WHITE,
                      rect.x + 31, rect.y + 120 + i * 47)
        self._button(surface, self.guide_button, "ENTENDI, CONTINUAR")

    def draw(self, surface):
        self._background(surface)
        self._routes(surface)
        self._territories(surface)
        self._sidebar(surface)
        draw_text(surface, "TERRITÓRIOS ESQUECIDOS", self.asset_manager.big_font, WHITE, 224, 18)
        self._button(surface, self.back_button, "< MENU")
        self.window_manager.draw_fullscreen_button(self.asset_manager.small_font)
        draw_text(surface, "BRONZE · SELECIONADO     VERDE · CONCLUÍDO     CINZA · BLOQUEADO     SETAS / 1–7 · NAVEGAR",
                  self.asset_manager.small_font, GRAY, 62, 694)
        if self.error:
            draw_text(surface, self.error[:100], self.asset_manager.small_font,
                      (245, 126, 126), 45, 656)
        if self.guide_open:
            self._guide(surface)
            if self.error:
                draw_text(surface, self.error[:88], self.asset_manager.small_font,
                          (245, 126, 126), WIDTH // 2, 576, center=True)

    def handle_event(self, event):
        if self.window_manager.handle_window_event(event):
            return
        if self.guide_open:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self._dismiss_guide()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.guide_button.collidepoint(self.window_manager.map_to_virtual(event.pos)):
                    self._dismiss_guide()
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                current = next(i for i, territory in enumerate(TERRITORIES)
                               if territory.id == self.selected)
                delta = -1 if event.key == pygame.K_LEFT else 1
                self.selected = TERRITORIES[(current + delta) % len(TERRITORIES)].id
                self.error = ""
                return
            numeric_keys = {
                pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2,
                pygame.K_4: 3, pygame.K_5: 4, pygame.K_6: 5, pygame.K_7: 6,
            }
            if event.key in numeric_keys:
                self.selected = TERRITORIES[numeric_keys[event.key]].id
                self.error = ""
                return
            if event.key == pygame.K_ESCAPE:
                self._back()
                return
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._start_selected()
                return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            point = self.window_manager.map_to_virtual(event.pos)
            if self.window_manager.get_fullscreen_button_rect().collidepoint(point):
                self.window_manager.toggle_fullscreen()
                return
            if self.back_button.collidepoint(point):
                self._back()
                return
            if self.shop_button.collidepoint(point):
                from src.scenes.shop_scene import ShopScene
                self.scene_manager.change_scene(ShopScene(
                    self.scene_manager, self.window_manager, self.asset_manager,
                    self.save_manager, self.save_data,
                ))
                return
            if self.play_button.collidepoint(point):
                self._start_selected()
                return
            for territory in TERRITORIES:
                if math.dist(point, territory.position) <= 34:
                    self.selected = territory.id
                    self.error = ""
                    return

    def _dismiss_guide(self):
        self.save_data["progresso"]["guia_mapa_visto"] = True
        try:
            self.save_manager.save(self.save_data)
            self.guide_open = False
            self.error = ""
        except (OSError, ValueError, SaveError) as exc:
            self.save_data["progresso"]["guia_mapa_visto"] = False
            self.error = f"Não foi possível salvar o guia: {exc}"

    def _start_selected(self):
        territory = next(t for t in TERRITORIES if t.id == self.selected)
        if status(self.save_data, territory.id) == "locked":
            self.error = "Território bloqueado! Conclua a fase anterior."
            return
        from src.scenes.battle_scene import BattleScene
        self.scene_manager.change_scene(BattleScene(
            self.scene_manager, self.window_manager, self.asset_manager,
            save_manager=self.save_manager, save_data=self.save_data,
            map_mode=True, selected_level=territory.level,
        ))

    def _back(self):
        from src.scenes.menu_scene import MenuScene
        self.scene_manager.change_scene(MenuScene(
            self.scene_manager, self.window_manager, self.asset_manager,
        ))
