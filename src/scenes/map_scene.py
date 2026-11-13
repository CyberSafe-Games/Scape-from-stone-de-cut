"""Mapa interativo de sete territórios, integrado aos três saves.

A interface usa a resolução virtual e a paleta do projeto, sem dependência
em imagens externas. A lógica de progressão vive em systems/territory_map.py.
"""

import math
import pygame

from src.config.settings import WIDTH, HEIGHT
from src.config.colors import (
    BG,
    BLACK,
    WHITE,
    GOLD,
    GRAY,
    BUTTON_BG,
    BUTTON_HOVER,
    GREEN,
)
from src.scenes.base_scene import BaseScene
from src.systems.save_manager import SaveError
from src.systems.territory_map import (
    ROAD_FIGHTS,
    TERRITORIES,
    status,
    completed_count,
    encounter_status,
    encounter_positions,
)
from src.models.effects.ultimate_effect import ULTIMATE_METADATA, DEFAULT_ULTIMATE_ID
from src.ui.helpers import draw_text, wrap_text
from src.ui import dark_fantasy_theme as theme
from src.systems.normal_enemy_catalog import biome_enemy_names


MAP_AREA = pygame.Rect(45, 138, 1319, 881)
PANEL = pygame.Rect(1394, 137, 482, 885)
# Lado (px) dos ícones de território (assets/ui/map_icons/<id>.png, centrados no
# losango). O boss final recebe um leve destaque de tamanho.
MAP_ICON_SIZE = 157
FINAL_BOSS_ICON_SIZE = 168


class MapScene(BaseScene):
    """Permite inspecionar, escolher e iniciar confrontos liberados."""

    def __init__(
        self, scene_manager, window_manager, asset_manager, save_manager, save_data
    ):
        super().__init__(scene_manager, window_manager, asset_manager)
        self.save_manager = save_manager
        self.save_data = save_data
        available = [t for t in TERRITORIES if status(save_data, t.id) == "available"]
        self.selected = available[-1].id if available else TERRITORIES[-1].id
        count = (
            save_data["progresso"]
            .get("encontros_por_territorio", {})
            .get(self.selected, 0)
        )
        self.selected_encounter = count if available and count < ROAD_FIGHTS else None
        self._map_art = None
        self.back_button = pygame.Rect(57, 30, 233, 68)
        self.play_button = pygame.Rect(1434, 851, 401, 72)
        self.shop_button = pygame.Rect(1434, 941, 401, 59)
        self.backpack_button = pygame.Rect(1431, 30, 396, 66)
        self.guide_button = pygame.Rect(765, 722, 390, 83)
        self.guide_open = not save_data["progresso"].get("guia_mapa_visto", False)
        self.error = ""
        self.elapsed = 0

    def update(self, dt):
        self.elapsed += min(dt, 100)

    def _button(self, surface, rect, title, enabled=True, outline=GOLD):
        hovered = enabled and rect.collidepoint(
            self.window_manager.get_virtual_mouse_pos()
        )
        theme.button(
            surface,
            rect,
            title,
            self.asset_manager.small_font,
            hover=hovered,
            prominent=(rect == self.play_button),
            enabled=enabled,
        )

    def _background(self, surface):
        theme.backdrop(surface, self.asset_manager.background, opacity=226)
        theme.panel(surface, MAP_AREA, fill=(12, 21, 20, 243))
        art = self.asset_manager.get_ui_image("world_map")
        if isinstance(art, pygame.Surface):
            inner = MAP_AREA.inflate(-30, -30)
            if self._map_art is None:
                self._map_art = pygame.transform.smoothscale(art, inner.size)
            surface.blit(self._map_art, inner)
            return
        # Mapa topográfico abstrato. Evita massas brilhantes e ícones infantis.
        land = pygame.Surface(MAP_AREA.size, pygame.SRCALPHA)
        pygame.draw.polygon(
            land,
            (29, 54, 43, 173),
            [
                (50, 176),
                (281, 74),
                (546, 159),
                (786, 65),
                (1103, 104),
                (1274, 291),
                (1179, 530),
                (1244, 762),
                (990, 827),
                (759, 716),
                (483, 813),
                (218, 710),
                (36, 767),
            ],
        )
        pygame.draw.polygon(
            land,
            (51, 63, 48, 166),
            [
                (63, 582),
                (243, 437),
                (393, 519),
                (539, 302),
                (720, 407),
                (879, 303),
                (1200, 336),
                (1170, 696),
                (924, 678),
                (746, 759),
                (518, 680),
                (254, 758),
            ],
        )
        for inset in (29, 56, 87, 117):
            pts = [
                (inset, 132 + inset // 4),
                (318 + inset // 2, 116),
                (627, 89 + inset),
                (1038 - inset // 4, 147 + inset // 3),
                (1221 - inset, 441),
                (1100 - inset // 2, 737 - inset // 4),
                (606, 774 - inset // 4),
                (158 + inset // 3, 690 - inset // 3),
            ]
            pygame.draw.lines(land, (84, 101, 74, 90), True, pts, 2)
        surface.blit(land, MAP_AREA.topleft)
        # Montanhas talhadas em pedra e pinheiros escurecidos.
        for x, y, scale in [
            (138, 311, 1.1),
            (471, 171, 1.2),
            (852, 216, 0.95),
            (1118, 657, 1.1),
            (605, 771, 0.85),
            (144, 648, 0.8),
        ]:
            x, y, s = x + MAP_AREA.x, y + MAP_AREA.y, int(47 * scale)
            pygame.draw.polygon(
                surface,
                (47, 62, 57),
                [(x - s, y + s // 2), (x, y - s), (x + s, y + s // 2)],
            )
            pygame.draw.line(surface, (92, 104, 89), (x - s, y + s // 2), (x, y - s), 2)
            pygame.draw.line(surface, (92, 104, 89), (x, y - s), (x + s, y + s // 2), 2)
        for x, y in [
            (132, 585),
            (282, 249),
            (392, 870),
            (675, 255),
            (816, 791),
            (1092, 548),
            (1253, 753),
            (98, 348),
            (1148, 159),
        ]:
            cx, cy = x + 15, y + 83
            pygame.draw.polygon(
                surface,
                (29, 65, 50),
                [(cx - 23, cy + 15), (cx, cy - 33), (cx + 23, cy + 15)],
            )
            pygame.draw.polygon(
                surface,
                (43, 83, 58),
                [(cx - 18, cy + 2), (cx, cy - 35), (cx + 18, cy + 2)],
                2,
            )
            pygame.draw.line(surface, (91, 74, 54), (cx, cy + 11), (cx, cy + 29), 3)

    def _routes(self, surface):
        previous = (68, 990)
        for territory in TERRITORIES:
            positions = (*encounter_positions(territory.id), territory.position)
            for index, position in enumerate(positions):
                state = encounter_status(
                    self.save_data, territory.id, index if index < ROAD_FIGHTS else None
                )
                color = (
                    (133, 156, 112)
                    if state == "completed"
                    else (207, 163, 85)
                    if state == "available"
                    else (74, 83, 79)
                )
                pygame.draw.line(surface, (9, 18, 18), previous, position, 9)
                pygame.draw.line(surface, color, previous, position, 3)
                previous = position

    def _encounters(self, surface):
        cursor = self.window_manager.get_virtual_mouse_pos()
        for territory in TERRITORIES:
            for index, (x, y) in enumerate(encounter_positions(territory.id)):
                state = encounter_status(self.save_data, territory.id, index)
                selected = (
                    self.selected == territory.id and self.selected_encounter == index
                )
                hovered = math.dist(cursor, (x, y)) <= 21
                fill = (
                    (42, 91, 68)
                    if state == "completed"
                    else (106, 77, 35)
                    if state == "available"
                    else (26, 38, 38)
                )
                edge = (
                    (220, 178, 99)
                    if selected or hovered
                    else (127, 164, 122)
                    if state == "completed"
                    else (100, 114, 104)
                )
                if selected:
                    radius = 26 + round(1.5 * math.sin(self.elapsed * 0.004))
                    pygame.draw.circle(surface, (234, 191, 112), (x, y), radius, 2)
                pygame.draw.circle(surface, (5, 12, 12), (x + 2, y + 3), 20)
                pygame.draw.circle(surface, fill, (x, y), 17)
                pygame.draw.circle(surface, edge, (x, y), 17, 3)
                draw_text(
                    surface,
                    str(index + 1),
                    self.asset_manager.small_font,
                    WHITE if state != "locked" else GRAY,
                    x,
                    y,
                    center=True,
                )

    def _territories(self, surface):
        cursor = self.window_manager.get_virtual_mouse_pos()
        pulse = 1.0 + 0.06 * math.sin(self.elapsed * 0.004)
        for territory in TERRITORIES:
            x, y = territory.position
            state = encounter_status(self.save_data, territory.id)
            chosen = territory.id == self.selected and self.selected_encounter is None
            hovered = math.dist(cursor, (x, y)) <= 48
            radius = 41 if chosen else 36
            is_final_boss = territory.level == len(TERRITORIES)
            icon_size = FINAL_BOSS_ICON_SIZE if is_final_boss else MAP_ICON_SIZE
            if chosen:
                icon_size = round(icon_size * 1.1)
            icon = self.asset_manager.get_map_icon(
                territory.id, icon_size, dimmed=(state == "locked")
            )
            has_icon = isinstance(icon, pygame.Surface)
            if has_icon:
                # Ícone exclusivo do chefe; o losango central segue mostrando o estado.
                if chosen:
                    pygame.draw.circle(surface, (9, 16, 15), (x, y), int(icon_size * 0.54 * pulse), 5)
                    pygame.draw.circle(surface, (234, 191, 112), (x, y), int(icon_size * 0.54 * pulse), 2)
                surface.blit(icon, icon.get_rect(center=(x, y)))
                radius = round(icon_size * 0.17)
            elif chosen:
                pygame.draw.circle(surface, (9, 16, 15), (x, y), 59)
                pygame.draw.circle(surface, (174, 135, 71), (x, y), int(53 * pulse), 2)
            fill = (
                (35, 81, 57)
                if state == "completed"
                else (80, 65, 43)
                if state == "available"
                else (30, 35, 34)
            )
            border = (
                GOLD
                if (chosen or hovered and state != "locked")
                else (91, 133, 98)
                if state == "completed"
                else (76, 83, 78)
            )
            pts = [(x, y - radius), (x + radius, y), (x, y + radius), (x - radius, y)]
            if not has_icon:
                pygame.draw.circle(surface, (5, 9, 9), (x + 5, y + 8), radius + 9)
            pygame.draw.polygon(surface, fill, pts)
            pygame.draw.lines(surface, border, True, pts, 3)
            if not has_icon:
                inner = [
                    (x, y - radius + 11),
                    (x + radius - 11, y),
                    (x, y + radius - 11),
                    (x - radius + 11, y),
                ]
                pygame.draw.lines(surface, (119, 111, 82), True, inner, 2)
            symbol = (
                "V"
                if state == "completed"
                else str(territory.level)
                if state == "available"
                else "×"
            )
            # Chefe concluído: caveira no lugar do antigo "V" (vermelha no boss final).
            skull = None
            if state == "completed":
                skull = self.asset_manager.get_map_marker(
                    "final_boss_skull" if is_final_boss else "miniboss_skull"
                )
            if isinstance(skull, pygame.Surface):
                surface.blit(skull, skull.get_rect(center=(x, y)))
            else:
                draw_text(
                    surface,
                    symbol,
                    self.asset_manager.menu_font,
                    WHITE if state != "locked" else GRAY,
                    x,
                    y,
                    center=True,
                )
            font = self.asset_manager.small_font
            label_width = min(288, font.size(territory.title)[0] + 39)
            label_rect = pygame.Rect(0, 0, label_width, 45)
            offsets = (
                (165, 6),
                (165, 8),
                (-12, -87),
                (0, -63),
                (18, 66),
                (165, 30),
                (-45, -63),
            )
            if has_icon:
                # Os ícones são maiores que o losango antigo: afasta os nomes.
                offsets = (
                    (188, 6),
                    (178, 8),
                    (-12, -102),
                    (0, -100),
                    (44, 102),
                    (182, 30),
                    (-222, -8),
                )
            dx, dy = offsets[territory.level - 1]
            label_rect.center = (x + dx, y + dy)
            pygame.draw.rect(surface, (12, 20, 19), label_rect, border_radius=3)
            pygame.draw.rect(
                surface,
                (89, 77, 58) if state != "locked" else (48, 56, 53),
                label_rect,
                2,
                border_radius=3,
            )
            draw_text(
                surface,
                territory.title,
                font,
                WHITE if state != "locked" else GRAY,
                label_rect.centerx,
                label_rect.centery,
                center=True,
            )

    def _sidebar(self, surface):
        theme.panel(surface, PANEL, fill=(11, 18, 18, 244))
        center = PANEL.centerx
        selected_territory = next(t for t in TERRITORIES if t.id == self.selected)
        state = encounter_status(
            self.save_data, selected_territory.id, self.selected_encounter
        )
        progress = self.save_data["progresso"]
        draw_text(
            surface,
            "SUA EXPEDIÇÃO",
            self.asset_manager.menu_font,
            GOLD,
            center,
            191,
            center=True,
        )
        draw_text(
            surface,
            self.save_data["nome"][:26],
            self.asset_manager.small_font,
            GRAY,
            center,
            242,
            center=True,
        )
        if self.asset_manager.coin_icon is not None:
            icon = pygame.transform.smoothscale(self.asset_manager.coin_icon, (42, 42))
            surface.blit(icon, (center - 102, 275))
        draw_text(
            surface,
            f"{progress['moedas']} MOEDAS",
            self.asset_manager.font,
            WHITE,
            center - 44,
            275,
        )
        completed = completed_count(self.save_data)
        pygame.draw.rect(
            surface, (36, 46, 42), pygame.Rect(1431, 339, 402, 18), border_radius=9
        )
        if completed:
            pygame.draw.rect(
                surface,
                (69, 117, 80),
                pygame.Rect(1431, 339, int(402 * completed / len(TERRITORIES)), 18),
                border_radius=9,
            )
        draw_text(
            surface,
            f"{completed} DE {len(TERRITORIES)} TERRITÓRIOS CONCLUÍDOS",
            self.asset_manager.small_font,
            GRAY,
            center,
            392,
            center=True,
        )
        pygame.draw.line(surface, (91, 76, 52), (1434, 431), (1835, 431), 2)
        ultimate_id = progress.get("ultimate_equipada", DEFAULT_ULTIMATE_ID)
        ultimate_name = ULTIMATE_METADATA.get(
            ultimate_id, ULTIMATE_METADATA[DEFAULT_ULTIMATE_ID]
        )["name"]
        draw_text(
            surface,
            "ULTIMATE EQUIPADA",
            self.asset_manager.small_font,
            (147, 164, 142),
            center,
            468,
            center=True,
        )
        draw_text(
            surface,
            ultimate_name.upper(),
            self.asset_manager.small_font,
            WHITE,
            center,
            506,
            center=True,
        )
        draw_text(
            surface,
            f"FASE {selected_territory.level:02d}",
            self.asset_manager.small_font,
            GOLD,
            center,
            558,
            center=True,
        )
        draw_text(
            surface,
            selected_territory.title,
            self.asset_manager.font,
            WHITE,
            center,
            609,
            center=True,
        )
        subtitle = (
            f"ENCONTRO {self.selected_encounter + 1} / {ROAD_FIGHTS} · CAMINHO"
            if self.selected_encounter is not None
            else selected_territory.subtitle.upper()
        )
        draw_text(
            surface,
            subtitle,
            self.asset_manager.small_font,
            GRAY,
            center,
            657,
            center=True,
        )
        label, color = {
            "locked": ("BLOQUEADA", (159, 101, 96)),
            "available": ("DISPONÍVEL", (177, 143, 87)),
            "completed": ("CONCLUÍDA", (103, 159, 113)),
        }[state]
        pill = pygame.Rect(center - 146, 693, 291, 50)
        pygame.draw.rect(surface, (24, 34, 31), pill, border_radius=24)
        pygame.draw.rect(surface, color, pill, 3, border_radius=24)
        draw_text(
            surface,
            label,
            self.asset_manager.small_font,
            color,
            pill.centerx,
            pill.centery,
            center=True,
        )
        description = (
            "Conclua os dois encontros para liberar o chefe."
            if state == "locked" and self.selected_encounter is None
            else "Conclua o ponto anterior para liberar este encontro."
            if state == "locked"
            else "Você pode repetir este encontro sem avançar o caminho."
            if state == "completed" and self.selected_encounter is not None
            else "Vitória libera o próximo ponto do caminho."
            if self.selected_encounter is not None
            else selected_territory.description
        )
        if self.selected_encounter is not None:
            description = (
                "Habitantes: "
                + " ou ".join(biome_enemy_names(selected_territory.level))
                + "."
            )
        for line_i, line in enumerate(
            wrap_text(description, self.asset_manager.small_font, 378)[:2]
        ):
            draw_text(
                surface,
                line,
                self.asset_manager.small_font,
                WHITE,
                1446,
                752 + 30 * line_i,
            )
        count = progress.get("encontros_por_territorio", {}).get(
            selected_territory.id, 0
        )
        count = (
            ROAD_FIGHTS if status(self.save_data, selected_territory.id) == "completed"
            else min(count, ROAD_FIGHTS)
        )
        if status(self.save_data, selected_territory.id) != "locked":
            draw_text(
                surface,
                f"CAMINHO  {count}/{ROAD_FIGHTS} ENCONTROS",
                self.asset_manager.small_font,
                GOLD,
                1452,
                813,
            )
            for j in range(ROAD_FIGHTS):
                color = (109, 158, 115) if j < count else (88, 86, 74)
                pygame.draw.circle(surface, color, (1796 + 14 * j, 825), 6)
        if status(self.save_data, selected_territory.id) == "locked":
            draw_text(
                surface,
                "Conclua a fase anterior para liberar.",
                self.asset_manager.small_font,
                (188, 135, 122),
                1446,
                815,
            )
        play_label = (
            "PONTO BLOQUEADO"
            if state == "locked"
            else "REPETIR ENCONTRO"
            if state == "completed" and self.selected_encounter is not None
            else "REPETIR TERRITÓRIO"
            if state == "completed"
            else f"JOGAR ENCONTRO {self.selected_encounter + 1}"
            if self.selected_encounter is not None
            else "CONFRONTO DO TERRITÓRIO"
        )
        self._button(surface, self.play_button, play_label, enabled=state != "locked")
        self._button(surface, self.shop_button, "ACESSAR LOJA")

    def _guide(self, surface):
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((3, 9, 9, 218))
        surface.blit(shade, (0, 0))
        rect = pygame.Rect(501, 249, 918, 597)
        theme.panel(surface, rect, highlighted=True)
        draw_text(
            surface,
            "CARTOGRAFIA DA JORNADA",
            self.asset_manager.big_font,
            GOLD,
            WIDTH // 2,
            326,
            center=True,
        )
        steps = (
            "01  Círculos são encontros; losangos são territórios.",
            "02  Vença os dois encontros para liberar o losango.",
            "03  Após o confronto principal, abra o próximo caminho.",
            "04  Volte e repita qualquer ponto verde já concluído.",
        )
        for i, line in enumerate(steps):
            draw_text(
                surface,
                line,
                self.asset_manager.small_font,
                WHITE,
                rect.x + 47,
                rect.y + 180 + i * 71,
            )
        self._button(surface, self.guide_button, "ENTENDI, CONTINUAR")

    def draw(self, surface):
        self._background(surface)
        self._routes(surface)
        # Encontros por cima: os efeitos dos ícones não podem esconder os círculos.
        self._territories(surface)
        self._encounters(surface)
        self._sidebar(surface)
        draw_text(
            surface,
            "TERRITÓRIOS ESQUECIDOS",
            self.asset_manager.big_font,
            WHITE,
            336,
            27,
        )
        self._button(surface, self.back_button, "< MENU")
        self._button(surface, self.backpack_button, "MOCHILA  /  DECK [B]")
        # Ícone de mochila/bolsa de couro estilizado, sem assets externos.
        bag = pygame.Rect(
            self.backpack_button.x + 15, self.backpack_button.y + 18, 26, 30
        )
        pygame.draw.rect(surface, (102, 76, 43), bag, border_radius=5)
        pygame.draw.rect(surface, (185, 145, 82), bag, 3, border_radius=5)
        pygame.draw.arc(
            surface, (185, 145, 82), (bag.x + 6, bag.y - 12, 14, 21), 0, 3.14, 3
        )
        self.window_manager.draw_fullscreen_button(self.asset_manager.small_font)
        draw_text(
            surface,
            "CÍRCULOS · ENCONTROS     LOSANGOS · TERRITÓRIOS     VERDE · CONCLUÍDO     SETAS · NAVEGAR",
            self.asset_manager.small_font,
            GRAY,
            93,
            1041,
        )
        if self.error:
            draw_text(
                surface,
                self.error[:100],
                self.asset_manager.small_font,
                (245, 126, 126),
                68,
                984,
            )
        if self.guide_open:
            self._guide(surface)
            if self.error:
                draw_text(
                    surface,
                    self.error[:88],
                    self.asset_manager.small_font,
                    (245, 126, 126),
                    WIDTH // 2,
                    864,
                    center=True,
                )

    def handle_event(self, event):
        if self.window_manager.handle_window_event(event):
            return

        if self.guide_open:
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_RETURN,
                pygame.K_SPACE,
                pygame.K_ESCAPE,
            ):
                self._dismiss_guide()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.guide_button.collidepoint(
                    self.window_manager.map_to_virtual(event.pos)
                ):
                    self._dismiss_guide()
            return

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                points = [
                    (t.id, index) for t in TERRITORIES
                    for index in (*range(ROAD_FIGHTS), None)
                ]
                current = points.index((self.selected, self.selected_encounter))
                delta = -1 if event.key in (pygame.K_LEFT, pygame.K_UP) else 1
                self.selected, self.selected_encounter = points[
                    (current + delta) % len(points)
                ]
                self.error = ""
                self.play_ui_sound("ui.navigate")
                return

            numeric_keys = {
                pygame.K_1: 0,
                pygame.K_2: 1,
                pygame.K_3: 2,
                pygame.K_4: 3,
                pygame.K_5: 4,
                pygame.K_6: 5,
                pygame.K_7: 6,
            }

            if event.key in numeric_keys:
                self.selected = TERRITORIES[numeric_keys[event.key]].id
                count = (
                    self.save_data["progresso"]
                    .get("encontros_por_territorio", {})
                    .get(self.selected, 0)
                )
                self.selected_encounter = (
                    count
                    if count < ROAD_FIGHTS
                    and status(self.save_data, self.selected) != "completed"
                    else None
                )
                self.error = ""
                self.play_ui_sound("ui.navigate")
                return

            if event.key == pygame.K_b:
                self._open_backpack()
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
                self.play_ui_sound("ui.click")
                return

            if self.backpack_button.collidepoint(point):
                self._open_backpack()
                return

            if self.back_button.collidepoint(point):
                self._back()
                return

            if self.shop_button.collidepoint(point):
                from src.scenes.shop_scene import ShopScene

                self.play_ui_sound("ui.navigate")
                self.scene_manager.change_scene(
                    ShopScene(
                        self.scene_manager,
                        self.window_manager,
                        self.asset_manager,
                        self.save_manager,
                        self.save_data,
                    )
                )
                return

            if self.play_button.collidepoint(point):
                self._start_selected()
                return

            for territory in TERRITORIES:
                for index, position in enumerate(encounter_positions(territory.id)):
                    if math.dist(point, position) <= 21:
                        self.selected = territory.id
                        self.selected_encounter = index
                        self.error = ""
                        self.play_ui_sound("ui.navigate")
                        return

            for territory in TERRITORIES:
                if math.dist(point, territory.position) <= 51:
                    self.selected = territory.id
                    self.selected_encounter = None
                    self.error = ""
                    self.play_ui_sound("ui.navigate")
                    return

    def _open_backpack(self):
        from src.scenes.backpack_scene import BackpackScene

        self.play_ui_sound("ui.navigate")
        self.scene_manager.change_scene(
            BackpackScene(
                self.scene_manager,
                self.window_manager,
                self.asset_manager,
                self.save_manager,
                self.save_data,
            )
        )

    def _dismiss_guide(self):
        self.save_data["progresso"]["guia_mapa_visto"] = True
        try:
            self.save_manager.save(self.save_data)
            self.guide_open = False
            self.error = ""
            self.play_ui_sound("ui.confirm")
        except (OSError, ValueError, SaveError) as exc:
            self.save_data["progresso"]["guia_mapa_visto"] = False
            self.error = f"Não foi possível salvar o guia: {exc}"

    def _start_selected(self):
        territory = next(t for t in TERRITORIES if t.id == self.selected)

        if (
            encounter_status(self.save_data, territory.id, self.selected_encounter)
            == "locked"
        ):
            self.error = "Ponto bloqueado! Conclua os encontros anteriores do caminho."
            return

        self.play_ui_sound("ui.confirm")

        from src.scenes.battle_scene import BattleScene

        self.scene_manager.change_scene(
            BattleScene(
                self.scene_manager,
                self.window_manager,
                self.asset_manager,
                save_manager=self.save_manager,
                save_data=self.save_data,
                map_mode=True,
                selected_level=territory.level,
                encounter_kind="road"
                if self.selected_encounter is not None
                else "point",
                encounter_index=self.selected_encounter,
            )
        )

    def _back(self):
        from src.scenes.menu_scene import MenuScene

        self.play_ui_sound("ui.navigate")
        self.scene_manager.change_scene(
            MenuScene(
                self.scene_manager,
                self.window_manager,
                self.asset_manager,
            )
        )
