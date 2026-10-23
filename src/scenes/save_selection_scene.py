"""Tela com três espaços independentes de progresso.

Mantém a identidade do menu: fundo original escurecido, cartões roxos,
contornos dourados e os mesmos tipos de letra e controles de fullscreen.
"""
from datetime import datetime

import pygame

from src.config.colors import BG, BLACK, WHITE, GOLD, GRAY, BUTTON_BG, BUTTON_HOVER
from src.config.settings import WIDTH, HEIGHT
from src.scenes.base_scene import BaseScene
from src.scenes.confirmation_modal import ConfirmationModal
from src.systems.save_manager import (
    SLOT_COUNT, SaveManager, SaveCorruptedError, SaveNotFoundError, SaveError
)
from src.ui.helpers import draw_text
from src.ui import dark_fantasy_theme as theme


class SaveSelectionScene(BaseScene):
    """Mostra saves ocupados, vazios e corrompidos sem sobrescrevê-los."""

    def __init__(self, scene_manager, window_manager, asset_manager, save_manager=None):
        super().__init__(scene_manager, window_manager, asset_manager)
        self.save_manager = save_manager or SaveManager()
        self.back_button = pygame.Rect(38, 32, 160, 44)
        self.card_rects = [pygame.Rect(135 + index * 338, 208, 320, 352) for index in range(3)]
        self.delete_rects = [pygame.Rect(r.centerx - 65, r.bottom - 52, 130, 32)
                             for r in self.card_rects]
        self.slots = []
        self.error = ""
        self.refresh()

    def refresh(self):
        """Lê cada slot diretamente do disco, para não confundir posições."""
        self.slots = []
        for slot in range(1, SLOT_COUNT + 1):
            slot_id = self.save_manager.slot_id(slot)
            try:
                self.slots.append(("occupied", self.save_manager.load_save(slot_id)))
            except SaveNotFoundError:
                self.slots.append(("empty", None))
            except SaveCorruptedError:
                self.slots.append(("corrupted", None))

    def update(self, dt):
        pass

    def _button(self, surface, rect, label, danger=False):
        hovered = rect.collidepoint(self.window_manager.get_virtual_mouse_pos())
        theme.button(surface, rect, label, self.asset_manager.small_font,
                     hover=hovered, danger=danger)

    def draw(self, surface):
        theme.backdrop(surface, self.asset_manager.background, opacity=210)
        self._button(surface, self.back_button, "← VOLTAR")
        self.window_manager.draw_fullscreen_button(self.asset_manager.small_font)
        theme.eyebrow(surface, "ARQUIVO DE JORNADAS", self.asset_manager.small_font,
                      WIDTH // 2, 95, center=True)
        draw_text(surface, "ESCOLHA SEU DESTINO", self.asset_manager.big_font,
                  WHITE, WIDTH // 2, 128, center=True)
        draw_text(surface, "Cada jornada preserva suas conquistas e cicatrizes.",
                  self.asset_manager.font, GRAY, WIDTH // 2, 171, center=True)
        theme.divider(surface, 404, 876, 192)

        cursor = self.window_manager.get_virtual_mouse_pos()
        for index, rect in enumerate(self.card_rects):
            state, data = self.slots[index]
            hovered = rect.collidepoint(cursor)
            theme.panel(surface, rect, highlighted=hovered)
            theme.eyebrow(surface, f"CRÔNICA {index + 1:02d}", self.asset_manager.small_font,
                          rect.centerx, rect.top + 27, center=True)
            pygame.draw.line(surface, (91, 76, 52), (rect.x + 29, rect.y + 64),
                             (rect.right - 29, rect.y + 64), 1)

            if state == "occupied":
                progress = data["progresso"]
                draw_text(surface, data["nome"][:22], self.asset_manager.menu_font,
                          WHITE, rect.centerx, rect.y + 94, center=True)
                draw_text(surface, f"ANDAR {progress['andar']:02d}", self.asset_manager.big_font,
                          GOLD, rect.centerx, rect.y + 147, center=True)
                theme.divider(surface, rect.x + 72, rect.right - 72, rect.y + 179)
                draw_text(surface, f"MOEDAS     {progress['moedas']}", self.asset_manager.font,
                          WHITE, rect.centerx, rect.y + 200, center=True)
                draw_text(surface, f"CARTAS      {len(progress['cartas'])}", self.asset_manager.font,
                          WHITE, rect.centerx, rect.y + 229, center=True)
                try:
                    when = datetime.fromisoformat(data["atualizado_em"]).strftime("%d/%m/%Y · %H:%M")
                except (ValueError, TypeError):
                    when = "Data desconhecida"
                draw_text(surface, when, self.asset_manager.small_font, GRAY,
                          rect.centerx, rect.y + 265, center=True)
                draw_text(surface, "SELECIONAR PARA CONTINUAR", self.asset_manager.small_font,
                          GOLD if hovered else GRAY, rect.centerx, rect.y + 291, center=True)
                self._button(surface, self.delete_rects[index], "EXCLUIR", danger=True)
            elif state == "empty":
                pygame.draw.circle(surface, (83, 75, 56), (rect.centerx, rect.y + 154), 43, 1)
                pygame.draw.polygon(surface, GOLD, [
                    (rect.centerx, rect.y + 128), (rect.centerx + 23, rect.y + 154),
                    (rect.centerx, rect.y + 180), (rect.centerx - 23, rect.y + 154)], 2)
                pygame.draw.line(surface, GOLD, (rect.centerx-11, rect.y+154),
                                 (rect.centerx+11, rect.y+154), 2)
                draw_text(surface, "JORNADA NÃO INICIADA", self.asset_manager.font,
                          WHITE, rect.centerx, rect.y + 233, center=True)
                draw_text(surface, "INICIAR UMA NOVA CRÔNICA", self.asset_manager.small_font,
                          GOLD if hovered else GRAY, rect.centerx, rect.y + 285, center=True)
            else:
                draw_text(surface, "REGISTRO DANIFICADO", self.asset_manager.menu_font,
                          (188, 110, 101), rect.centerx, rect.y + 147, center=True)
                draw_text(surface, "Não foi possível restaurar a jornada.",
                          self.asset_manager.small_font, GRAY,
                          rect.centerx, rect.y + 208, center=True)
                draw_text(surface, "Exclua o registro para liberar o espaço.",
                          self.asset_manager.small_font, GRAY,
                          rect.centerx, rect.y + 239, center=True)
                self._button(surface, self.delete_rects[index], "EXCLUIR", danger=True)

        if self.error:
            draw_text(surface, self.error[:100], self.asset_manager.small_font,
                      (210, 116, 103), WIDTH // 2, HEIGHT - 91, center=True)
        theme.footer(surface, "ESC  ·  VOLTAR                       1–3  ·  SELECIONAR                       F11  ·  TELA CHEIA",
                     self.asset_manager.small_font)

    def handle_event(self, event):
        if self.window_manager.handle_window_event(event):
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._back()
                return
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_KP1, pygame.K_KP2, pygame.K_KP3):
                key_to_index = {
                    pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2,
                    pygame.K_KP1: 0, pygame.K_KP2: 1, pygame.K_KP3: 2,
                }
                self._select(key_to_index[event.key])
                return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            point = self.window_manager.map_to_virtual(event.pos)
            if self.window_manager.get_fullscreen_button_rect().collidepoint(point):
                self.window_manager.toggle_fullscreen()
                return
            if self.back_button.collidepoint(point):
                self._back()
                return
            for index, rect in enumerate(self.card_rects):
                if self.delete_rects[index].collidepoint(point) and self.slots[index][0] != "empty":
                    self._request_delete(index)
                    return
                if rect.collidepoint(point):
                    self._select(index)
                    return

    def _back(self):
        from src.scenes.menu_scene import MenuScene
        self.scene_manager.change_scene(
            MenuScene(self.scene_manager, self.window_manager, self.asset_manager)
        )

    def _select(self, index):
        status, data = self.slots[index]
        if status == "corrupted":
            self.error = "Save danificado. Exclua o arquivo para poder criar um novo."
            return
        try:
            if status == "empty":
                data = self.save_manager.create_save(
                    self.save_manager.slot_id(index + 1),
                    display_name=f"Jornada {index + 1:02d}",
                )
            if not data["progresso"].get("tutorial_concluido", True):
                from src.scenes.tutorial_scene import TutorialScene
                next_scene = TutorialScene(
                    self.scene_manager, self.window_manager, self.asset_manager,
                    save_manager=self.save_manager, save_data=data,
                )
            else:
                from src.scenes.map_scene import MapScene
                next_scene = MapScene(
                    self.scene_manager, self.window_manager, self.asset_manager,
                    save_manager=self.save_manager, save_data=data,
                )
            self.scene_manager.change_scene(next_scene)
        except (OSError, ValueError, SaveError) as exc:
            self.error = f"Falha ao acessar save: {exc}"
            self.refresh()

    def _request_delete(self, index):
        self.scene_manager.push_modal(ConfirmationModal(
            self.scene_manager, self.window_manager, self.asset_manager,
            on_confirm=lambda: self._delete(index),
            title="EXCLUIR SAVE?",
            message=f"Espaço {index + 1:02d}: esta ação não pode ser desfeita.",
            confirm_label="SIM, EXCLUIR",
        ))

    def _delete(self, index):
        try:
            self.save_manager.delete_save(self.save_manager.slot_id(index + 1))
            self.error = ""
        except OSError as exc:
            self.error = f"Não foi possível excluir: {exc}"
        self.refresh()
