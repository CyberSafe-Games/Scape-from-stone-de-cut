import pygame
from copy import deepcopy

from src.scenes.base_scene import BaseScene
from src.scenes.confirmation_modal import ConfirmationModal
from src.scenes.cemetery_modal import CemeteryModal
from src.systems.combat_engine import CombatEngine
from src.systems.save_manager import SaveError
from src.systems.campaign_progress import record_victory, record_road_victory
from src.ui.card_view import CardView
from src.ui.entity_view import EntityView
from src.ui.floating_text import FloatingTextManager
from src.ui.coin_hud import CoinHUD
from src.ui.energy_hud import EnergyHUD
from src.ui.battle_hud import BattleHUD
from src.ui.card_fx import draw_player_projectile
from src.ui.ultimate_fx import draw_ultimate_fx
from src.ui.boss_ultimate_fx import draw_boss_ultimate_fx
from src.systems.ultimate_animations import ULTIMATE_ANIMATIONS
from src.ui.helpers import draw_text, draw_health_bar, draw_panel, draw_vignette, wrap_text
from src.ui import dark_fantasy_theme as theme
from src.config.settings import WIDTH, HEIGHT
from src.config.colors import (
    BG,
    BLACK,
    WHITE,
    RED,
    GREEN,
    BLUE,
    GOLD,
    GRAY,
    BUTTON_BG,
    BUTTON_HOVER,
)
from src.config.layout import (
    PLAYER_X,
    ENEMY_X,
    POST_ENEMY_PAUSE,
)


class BattleScene(BaseScene):
    """Cena principal de batalha onde o combate por turnos acontece."""

    def __init__(self, scene_manager, window_manager, asset_manager,
                 save_manager=None, save_data=None, map_mode=False,
                 selected_level=None, encounter_kind="point", encounter_index=None):

        super().__init__(scene_manager, window_manager, asset_manager)

        self.save_manager = save_manager
        self.save_data = save_data
        self.map_mode = map_mode
        self.selected_level = selected_level
        self.encounter_kind = encounter_kind
        self.encounter_index = encounter_index
        self.floating_texts = FloatingTextManager()
        self.entity_view = EntityView(asset_manager)
        self.battle_hud = BattleHUD(asset_manager)
        self._ultimate_events = []
        self._ultimate_clock = 0
        self._ultimate_enemy_snapshot = None
        self._boss_events = []
        self._boss_clock = 0
        self._boss_player_snapshot = None

        # Inicializa o motor puro de combate com callbacks para efeitos visuais
        self.engine = CombatEngine(
            on_event_callback=self._handle_combat_event, map_mode=self.map_mode,
        )
        if self.save_manager is not None and self.save_data is not None:
            self.engine.resume_from_save(
                self.save_data, self.save_manager,
                level=self.selected_level if self.map_mode else None,
                encounter_kind=self.encounter_kind,
                encounter_index=self.encounter_index,
            )

        # Sistema de moedas (instanciado apos o engine para ter acesso ao player)
        self.coin_hud = CoinHUD(self.engine.player, anchor_x=66, anchor_y=102)
        self.energy_hud = EnergyHUD(self.engine.player)

        self.enemy_turn_timer = 0
        self.menu_button_rect = pygame.Rect(WIDTH - 108, 18, 86, 28)
        self.end_turn_rect = pygame.Rect(WIDTH - 120, HEIGHT - 132, 100, 100)
        self.cemetery_button_rect = pygame.Rect(28, HEIGHT - 154, 92, 124)
        self.skip_reward_rect = pygame.Rect(WIDTH // 2 - 60, HEIGHT - 100, 120, 40)
        self.ultimate_button_rect = pygame.Rect(0, 0, 0, 0)
        self.ultimate_hand_rect = None

    def _handle_combat_event(self, event_name, **kwargs):
        """Reage a eventos emitidos pelo motor de combate."""
        ultimate = ULTIMATE_ANIMATIONS.get(self.entity_view.player_action)
        if ultimate and event_name in ('floating_text', 'coin_drop'):
            self._ultimate_events.append((ultimate.duration*ultimate.impact, event_name, kwargs))
            return
        boss_ultimate = self.entity_view.enemy_ultimate
        if boss_ultimate and event_name == 'floating_text':
            self._boss_events.append((boss_ultimate.duration*boss_ultimate.impact, kwargs))
            return
        if event_name == "attack":
            if kwargs.get('ultimate'):
                self._boss_clock = 0
                self._boss_player_snapshot = deepcopy(self.engine.player)
            self.entity_view.trigger_attack(
                kwargs.get("attacker"), kwargs.get("action"),
                enemy_name=getattr(self.engine.enemy, "name", None),
                ultimate=kwargs.get('ultimate', False),
            )
        elif event_name == "flash":
            self.entity_view.trigger_flash(kwargs.get("target"))
        elif event_name == "player_action":
            self.entity_view.trigger_player_action(kwargs.get("action"))
            self._ultimate_clock = 0
            self._ultimate_enemy_snapshot = (deepcopy(self.engine.enemy)
                                             if kwargs.get('action') == 'Rugido da Floresta' else None)
        elif event_name == "enemy_action":
            self.entity_view.trigger_enemy_action(kwargs.get("action"),
                                                  enemy_name=getattr(self.engine.enemy, 'name', None))
        elif event_name == "floating_text":
            self.floating_texts.spawn(
                kwargs["x"], kwargs["y"], kwargs["text"], kwargs["color"]
            )
        elif event_name == "coin_drop":
            self.coin_hud.spawn_coins(
                kwargs["amount"], kwargs["x"], kwargs["y"]
            )
        elif event_name == "checkpoint":
            # Modo legado sem mapa: o motor ainda avança de andar sozinho.
            self._save_progress()
        elif event_name == "phase_complete":
            # Uma fase só é concluída após a escolha (ou pulo) da recompensa.
            self._finalize_map_phase(kwargs["level"])
        elif event_name == "cemetery_swap":
            card = kwargs.get("new_card")
            if card is not None:
                self.floating_texts.spawn(PLAYER_X, HEIGHT - 220,
                                          f"Carta trocada: {card.name}", (176, 184, 146))
        elif event_name == "cemetery_discard":
            card = kwargs.get("card")
            card_name = card.name if card else "Carta"
            self.floating_texts.spawn(
                PLAYER_X,
                HEIGHT - 220,
                f"{card_name} Descartada",
                (176, 153, 117),
            )

    def update(self, dt):
        self.engine.update_message(dt)
        self.entity_view.update(dt)
        self.floating_texts.update(dt)
        self.coin_hud.update(dt)
        self.energy_hud.update(dt)
        self._ultimate_clock += dt
        self._boss_clock += dt
        pending_boss = []
        for when, kwargs in self._boss_events:
            if self._boss_clock < when:
                pending_boss.append((when, kwargs))
            else:
                self.floating_texts.spawn(kwargs['x'], kwargs['y'], kwargs['text'], kwargs['color'])
        self._boss_events = pending_boss
        boss_spec = self.entity_view.enemy_ultimate
        if boss_spec is None or self._boss_clock >= boss_spec.duration*boss_spec.impact:
            self._boss_player_snapshot = None
        pending = []
        text_offsets = {}
        for when, event_name, kwargs in self._ultimate_events:
            if self._ultimate_clock < when:
                pending.append((when, event_name, kwargs))
            elif event_name == 'floating_text':
                key = (kwargs['x'], kwargs['y'])
                offset = text_offsets.get(key, 0)
                self.floating_texts.spawn(kwargs['x'], kwargs['y']-offset, kwargs['text'], kwargs['color'])
                text_offsets[key] = offset+23
            else:
                self.coin_hud.spawn_coins(kwargs['amount'], kwargs['x'], kwargs['y'])
        self._ultimate_events = pending
        spec = ULTIMATE_ANIMATIONS.get(self.entity_view.player_action)
        if spec is None or self._ultimate_clock >= spec.duration*spec.impact:
            self._ultimate_enemy_snapshot = None

        # ----------------------------------------------------
        # Turno do Inimigo
        # ----------------------------------------------------
        if self.engine.state == "enemy_turn":
            self.enemy_turn_timer += dt
            enemy = self.engine.enemy
            # No combo do Corpo Seco, a segunda ação começa pouco após
            # a primeira animação terminar, sem outra pausa longa.
            combo_followup = (getattr(enemy, "actions_per_turn", 1) > 1 and
                              getattr(self.engine, "enemy_actions_remaining", 0) <
                              getattr(enemy, "actions_per_turn", 1))
            windup_ms = 270 if combo_followup else 800
            if self.enemy_turn_timer >= windup_ms:
                self.engine.enemy_turn()
                self.entity_view.post_enemy_pause = POST_ENEMY_PAUSE
                self.enemy_turn_timer = 0
        else:
            self.enemy_turn_timer = 0

        # ----------------------------------------------------
        # Finalização da rodada do Inimigo
        # ----------------------------------------------------
        if self.engine.state == "enemy_resolving":
            if self.entity_view.is_enemy_resolving_done():
                self.engine.finish_enemy_turn()

    def _draw_background(self, surface):
        bg = self.asset_manager.get_battle_background(self.selected_level or self.engine.level)
        if bg is not None:
            surface.blit(bg, (0, 0))
        else:
            surface.fill(BG)

        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((5, 11, 10, 135))
        surface.blit(shade, (0, 0))
        draw_vignette(surface, WIDTH, HEIGHT, alpha=88)

        ground = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.ellipse(ground, (0, 0, 0, 72), pygame.Rect(PLAYER_X - 92, 422, 180, 36))
        pygame.draw.ellipse(ground, (0, 0, 0, 72), pygame.Rect(ENEMY_X - 86, 422, 170, 34))
        surface.blit(ground, (0, 0))

    def _draw_energy_gems(self, surface, x, y, current, maximum, accent=(212, 170, 75), left_to_right=True):
        step = 20
        for i in range(maximum):
            draw_x = x + i * step if left_to_right else x - i * step
            points = [
                (draw_x, y - 8),
                (draw_x + 7, y),
                (draw_x, y + 8),
                (draw_x - 7, y),
            ]
            active = i < current
            fill = accent if active else (39, 42, 51)
            border = (245, 222, 152) if active else (92, 94, 106)
            pygame.draw.polygon(surface, fill, points)
            pygame.draw.polygon(surface, border, points, 2)
            if active:
                pygame.draw.polygon(surface, (255, 241, 193), [(draw_x, y - 5), (draw_x + 4, y - 1), (draw_x, y + 3), (draw_x - 4, y - 1)])

    def _draw_energy_panel(self, surface, x, y, current, maximum, limit, align='left'):
        rect = pygame.Rect(x, y, 170, 24)
        draw_panel(surface, rect, fill=(13, 19, 18, 190), border=(126, 102, 58), radius=12, shadow=False)
        if align == 'left':
            self._draw_energy_gems(surface, rect.x + 16, rect.y + 12, current, limit, accent=(212, 170, 75), left_to_right=True)
        else:
            self._draw_energy_gems(surface, rect.right - 16, rect.y + 12, current, limit, accent=(212, 170, 75), left_to_right=False)

    def _ultimate_in_hand(self):
        return self.engine.ultimate_ready and self.engine.state in ("player_turn", "enemy_turn", "enemy_resolving")

    def _get_battle_hand_rects(self):
        total = len(self.engine.hand) + (1 if self._ultimate_in_hand() else 0)
        return CardView.get_hand_rects(total)

    def _draw_ultimate_hand_card(self, surface, rect, hovered=False):
        shadow = pygame.Surface((rect.width + 14, rect.height + 14), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 120), (7, 7, rect.width, rect.height), border_radius=14)
        surface.blit(shadow, (rect.x - 7, rect.y - 5))
        image = self.asset_manager.get_ultimate_image(self.engine.active_ultimate_id)
        draw_rect = rect.move(0, -12 if hovered else 0)
        if image is not None:
            scaled = pygame.transform.smoothscale(image, draw_rect.size)
            surface.blit(scaled, draw_rect)
        else:
            draw_panel(surface, draw_rect, fill=(16, 18, 28, 232), border=self.engine.active_ultimate_color, radius=12, shadow=False)
            draw_text(surface, self.engine.active_ultimate_name.upper(), self.asset_manager.small_font, self.engine.active_ultimate_color,
                      draw_rect.centerx, draw_rect.centery - 10, center=True)
            for i, line in enumerate(wrap_text(self.engine.active_ultimate_description, self.asset_manager.small_font, draw_rect.width - 16)[:3]):
                draw_text(surface, line, self.asset_manager.small_font, WHITE, draw_rect.centerx, draw_rect.centery + 10 + i * 14, center=True)
        glow = pygame.Surface((draw_rect.width + 18, draw_rect.height + 18), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*self.engine.active_ultimate_color, 70), (9, 9, draw_rect.width, draw_rect.height), border_radius=16, width=4)
        surface.blit(glow, (draw_rect.x - 9, draw_rect.y - 9))

    def _draw_end_turn_button(self, surface, enabled=True):
        cx, cy = self.end_turn_rect.center
        radius = self.end_turn_rect.width // 2
        shadow = pygame.Surface((radius * 2 + 24, radius * 2 + 24), pygame.SRCALPHA)
        pygame.draw.circle(shadow, (0, 0, 0, 120), (radius + 12, radius + 12), radius)
        surface.blit(shadow, (cx - radius - 12, cy - radius - 8))
        outer_fill = (58, 43, 32) if enabled else (34, 34, 40)
        ring = (180, 144, 84) if enabled else (84, 84, 94)
        inner_fill = (104, 76, 54) if enabled else (53, 53, 60)
        pygame.draw.circle(surface, outer_fill, (cx, cy), radius)
        pygame.draw.circle(surface, ring, (cx, cy), radius, 3)
        pygame.draw.circle(surface, inner_fill, (cx, cy), radius - 10)
        pygame.draw.circle(surface, (229, 208, 162, 45), (cx, cy), radius - 17, 2)
        draw_text(surface, "FIM", self.asset_manager.small_font, WHITE if enabled else GRAY, cx, cy - 12, center=True)
        draw_text(surface, "DO TURNO", self.asset_manager.small_font, WHITE if enabled else GRAY, cx, cy + 10, center=True)

    def _draw_cemetery_book(self, surface, enabled=True):
        rect = self.cemetery_button_rect
        if self.asset_manager.get_ui_image("hud_cemetery") is not None:
            art_rect = pygame.Rect(rect.x - 3, rect.y - 15, rect.width + 6, rect.height - 12)
            self.battle_hud.art(surface, "hud_cemetery", art_rect)
            caption = pygame.Rect(rect.x - 7, rect.bottom - 32, rect.width + 14, 40)
            draw_panel(surface, caption, fill=(10, 14, 13, 235),
                       border=(107, 83, 46), radius=4, shadow=False)
            draw_text(surface, "CEMITÉRIO", self.asset_manager.small_font,
                      WHITE if enabled else GRAY, rect.centerx, rect.bottom - 22, center=True)
            draw_text(surface, "DESC 1 E", self.asset_manager.small_font,
                      GOLD if enabled else GRAY, rect.centerx, rect.bottom - 5, center=True)
            badge = pygame.Rect(rect.right - 23, rect.y + 1, 25, 24)
            theme.panel(surface, badge, fill=(15, 17, 16, 245))
            draw_text(surface, str(len(self.engine.discard_pile)), self.asset_manager.small_font,
                      WHITE, badge.centerx, badge.centery, center=True)
            return
        draw_panel(surface, rect, fill=(18, 21, 18, 228), border=(113, 92, 62), radius=12)
        inner = pygame.Rect(rect.x + 8, rect.y + 8, rect.width - 16, rect.height - 28)
        pygame.draw.rect(surface, (20, 18, 24), inner, border_radius=8)
        pygame.draw.rect(surface, (137, 108, 58), inner, 2, border_radius=8)
        line_x = inner.centerx
        pygame.draw.line(surface, (92, 76, 52), (line_x, inner.y + 6), (line_x, inner.bottom - 6), 2)
        draw_text(surface, "CEMITÉRIO", self.asset_manager.small_font, WHITE if enabled else GRAY, rect.centerx, rect.bottom - 28, center=True)
        draw_text(surface, "DESC 1 E",
                  self.asset_manager.small_font,
                  GOLD if not self.engine.cemetery_swap_used else GRAY,
                  rect.centerx, rect.bottom - 12, center=True)
        badge = pygame.Rect(rect.right - 26, rect.y + 10, 18, 18)
        pygame.draw.rect(surface, (56, 44, 34), badge, border_radius=4)
        pygame.draw.rect(surface, (163, 132, 74), badge, 1, border_radius=4)
        draw_text(surface, str(len(self.engine.discard_pile)), self.asset_manager.small_font, WHITE, badge.centerx, badge.centery, center=True)

    def _draw_ultimate_counter(self, surface, hand_rects):
        if hand_rects:
            left = hand_rects[0].x
            right = hand_rects[-1].right
            center_x = (left + right) // 2
        else:
            center_x = WIDTH // 2
        panel = pygame.Rect(center_x - 170, HEIGHT - 26, 340, 18)
        pygame.draw.rect(surface, (8, 10, 18), panel, border_radius=9)
        pygame.draw.rect(surface, (100, 84, 56), panel, 2, border_radius=9)
        fill_width = int((panel.width - 4) * (self.engine.ultimate_charge / max(1, self.engine.ultimate_threshold)))
        if fill_width > 0:
            fill_rect = pygame.Rect(panel.x + 2, panel.y + 2, fill_width, panel.height - 4)
            pygame.draw.rect(surface, self.engine.active_ultimate_color, fill_rect, border_radius=7)
        label = f"Ultimate: {self.engine.ultimate_charge}/{self.engine.ultimate_threshold}"
        if self.engine.ultimate_ready:
            label = f"Ultimate pronta — {self.engine.active_ultimate_name}"
        draw_text(surface, label, self.asset_manager.small_font, WHITE, center_x, panel.centery, center=True)
    def _draw_stat_chip(self, surface, x, y, label, value, color):
        rect = pygame.Rect(x, y, 108, 24)
        draw_panel(surface, rect, fill=(15, 22, 20, 220), border=(62, 68, 84), radius=10, shadow=False)
        draw_text(surface, f"{label}: {value}", self.asset_manager.small_font, color,
                  rect.centerx, rect.centery, center=True)

    def _visible_enemy(self):
        """Mantém vida/escudo visuais anteriores até a onda atingir o alvo."""
        return self._ultimate_enemy_snapshot or self.engine.enemy

    def _visible_player(self):
        return self._boss_player_snapshot or self.engine.player

    def _draw_combatant_panel(self, surface, rect, name, hp, max_hp, bar_color,
                              stats, title_color=WHITE, subtitle=None, align='left'):
        if self.asset_manager.get_ui_image("hud_portrait") is not None:
            self.battle_hud.combatant(surface, rect, name, hp, max_hp, stats,
                                      enemy=align == 'right', boss=bool(subtitle),
                                      combatant=self._visible_enemy() if align == 'right' else self._visible_player(),
                                      mouse=self.window_manager.get_virtual_mouse_pos())
            return
        draw_panel(surface, rect, fill=(10, 17, 17, 228), border=(134, 112, 72), radius=18)
        title_y = rect.y + 10
        title_x = rect.x + 18 if align == 'left' else rect.right - 18
        name_center = rect.x + rect.width // 2
        if subtitle:
            draw_text(surface, subtitle, self.asset_manager.small_font, GOLD, name_center, title_y, center=True)
            title_y += 16
        name_font = self.asset_manager.menu_font
        draw_text(surface, name, name_font, title_color, name_center, title_y + 5, center=True)
        draw_health_bar(surface, rect.x + 14, rect.y + 40, rect.width - 28, 16, hp, max_hp, bar_color)
        draw_text(surface, f"{hp}/{max_hp}", self.asset_manager.small_font, WHITE, rect.centerx, rect.y + 48, center=True)

        chip_y = rect.y + 62
        if stats:
            if align == 'left':
                for index, (label, value, color) in enumerate(stats[:2]):
                    self._draw_stat_chip(surface, rect.x + 10 + index * 110, chip_y, label, value, color)
            else:
                for index, (label, value, color) in enumerate(stats[:2]):
                    self._draw_stat_chip(surface, rect.x + 10 + index * 110, chip_y, label, value, color)

    def _draw_coin_badge(self, surface, x, y):
        badge_rect = pygame.Rect(x, y, 78, 28)
        draw_panel(surface, badge_rect, fill=(14, 16, 22, 210), border=(170, 138, 66), radius=12, shadow=False)
        if self.asset_manager.coin_icon is not None:
            icon = pygame.transform.smoothscale(self.asset_manager.coin_icon, (16, 16))
            surface.blit(icon, (x + 8, y + 6))
        draw_text(surface, str(self.engine.player.coins), self.asset_manager.font, (255, 231, 110), x + 50, y + 14, center=True)

    def _draw_ultimate_card(self, surface):
        card_rect = pygame.Rect(34, HEIGHT - 152, 96, 136)
        card_img = self.asset_manager.get_ultimate_image(self.engine.active_ultimate_id)
        if card_img is not None:
            scaled = pygame.transform.smoothscale(card_img, card_rect.size)
            surface.blit(scaled, card_rect)
        else:
            draw_panel(surface, card_rect, fill=(10, 12, 18, 235), border=self.engine.active_ultimate_color, radius=12, shadow=False)
            draw_text(surface, self.engine.active_ultimate_name, self.asset_manager.small_font, WHITE, card_rect.centerx, card_rect.centery, center=True)

    def _draw_compact_energy(self, surface):
        pass

    def _draw_bottom_hud(self, surface):
        if self.battle_hud.art(surface, "hud_hand_tray", pygame.Rect(8, HEIGHT - 216, WIDTH - 16, 216)):
            return
        frame = self.asset_manager.get_ui_image("battle_hud_frame") or self.asset_manager.get_ui_image("battle_hud_frame_alt")
        base_y = HEIGHT - 162
        base_rect = pygame.Rect(0, base_y + 24, WIDTH, 138)
        base = pygame.Surface(base_rect.size, pygame.SRCALPHA)
        base.fill((10, 14, 14, 206))
        surface.blit(base, base_rect.topleft)
        if frame is not None:
            scaled = pygame.transform.scale(frame, (WIDTH, 142))
            surface.blit(scaled, (0, base_y))
            darken = pygame.Surface((WIDTH, 142), pygame.SRCALPHA)
            darken.fill((0, 0, 0, 18))
            surface.blit(darken, (0, base_y))
        pygame.draw.line(surface, (114, 94, 58), (0, base_y + 30), (WIDTH, base_y + 30), 1)
        pygame.draw.line(surface, (52, 46, 36), (0, base_y + 31), (WIDTH, base_y + 31), 1)
        mid = WIDTH // 2
        pygame.draw.polygon(surface, (156, 127, 78), [(mid, base_y + 24), (mid + 7, base_y + 30), (mid, base_y + 36), (mid - 7, base_y + 30)])

    def _draw_action_button(self, surface, rect, label, fill, border, text_color=WHITE, enabled=True):
        hovered = enabled and rect.collidepoint(self.window_manager.get_virtual_mouse_pos())
        shadow = pygame.Surface((rect.width + 10, rect.height + 10), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 80), (6, 6, rect.width, rect.height), border_radius=12)
        surface.blit(shadow, (rect.x - 6, rect.y - 4))
        button_fill = tuple(min(255, c + 16) for c in fill) if hovered else fill
        pygame.draw.rect(surface, button_fill, rect, border_radius=12)
        pygame.draw.rect(surface, border, rect, 2, border_radius=12)
        inner = pygame.Rect(rect.x + 3, rect.y + 3, rect.width - 6, rect.height - 6)
        pygame.draw.rect(surface, (255, 255, 255, 18), inner, 1, border_radius=10)
        font = self.asset_manager.menu_font if rect.height <= 34 else self.asset_manager.font
        draw_text(surface, label, font, text_color, rect.centerx, rect.centery, center=True)

    def draw(self, surface):
        self._draw_background(surface)

        player = self._visible_player()
        enemy = self._visible_enemy()
        if getattr(player, 'invulnerable', False) and not self.engine.message:
            draw_text(surface, 'LABORATÓRIO · VIDA INFINITA', self.asset_manager.small_font,
                      GOLD, WIDTH // 2, 29, center=True)
        enemy_color = WHITE
        intent_text = "Sem intenção"

        if enemy.intent:
            action_name = enemy.current_action.name if getattr(enemy, "current_action", None) else None
            if enemy.intent == "attack":
                label = action_name or "Atacar"
                preview_value = int(round(enemy.intent_value * 0.75)) if getattr(enemy, "weak_turns", 0) > 0 else enemy.intent_value
                intent_text = f"Intenção: {label} ({preview_value})"
                enemy_color = (200, 90, 90)
            else:
                label = action_name or "Defender"
                intent_text = f"Intenção: {label} ({enemy.intent_value})"
                enemy_color = (90, 130, 200)

        player_stats = []
        if player.block > 0:
            player_stats.append(("Bloqueio", player.block, BLUE))
        if player.strength > 0:
            player_stats.append(("Força", player.strength, RED))
        if not player_stats:
            player_stats.append(("Status", "Estável", GRAY))

        enemy_stats = []
        if enemy.block > 0:
            enemy_stats.append(("Bloqueio", enemy.block, BLUE))
        if getattr(enemy, 'weak_turns', 0) > 0:
            enemy_stats.append(("Fraqueza", enemy.weak_turns, (125, 205, 120)))
        if not enemy_stats:
            enemy_stats.append(("Status", "Pronto", GRAY))

        player_rect = pygame.Rect(22, 20, 390, 92)
        enemy_rect = pygame.Rect(790, 20, 370, 92)
        self._draw_combatant_panel(surface, player_rect, player.name, player.hp, player.max_hp, GREEN, player_stats, align='left')
        self._draw_energy_panel(surface, 36, 156, self.engine.energy, self.engine.energy_max, self.engine.player.MAX_ENERGY_LIMIT, align='left')
        self._draw_coin_badge(surface, 36, 186)

        self._draw_combatant_panel(surface, enemy_rect, enemy.name, enemy.hp, enemy.max_hp, RED, enemy_stats,
                                   title_color=GOLD if enemy.is_miniboss else WHITE,
                                   subtitle="MINIBOSS" if enemy.is_miniboss else None, align='right')
        intent_rect = pygame.Rect(900, 156, 270, 28)
        draw_panel(surface, intent_rect, fill=(12, 19, 17, 210), border=(77, 68, 54), radius=12, shadow=False)
        draw_text(surface, intent_text, self.asset_manager.small_font, GOLD,
                  intent_rect.centerx, intent_rect.centery, center=True)
        if getattr(enemy, "actions_per_turn", 1) > 1:
            until_spin = enemy.special_interval - (enemy.action_counter % enemy.special_interval)
            draw_text(surface, f"2 AÇÕES / RODADA   ·   ESPECIAL EM {until_spin} ATOS",
                      self.asset_manager.small_font, GOLD, 970, 198, center=True)

        self.window_manager.draw_fullscreen_button(self.asset_manager.small_font)
        self._draw_menu_button(surface)

        draw_ultimate_fx(surface, self.entity_view, behind=True)
        draw_boss_ultimate_fx(surface, self.entity_view, behind=True)
        self.entity_view.draw_enemy(surface, enemy, enemy_color)
        self.entity_view.draw_player(surface, self.engine.state)
        self.entity_view.draw_enemy_projectile(surface)
        draw_player_projectile(surface, self.entity_view)
        draw_ultimate_fx(surface, self.entity_view)
        draw_boss_ultimate_fx(surface, self.entity_view)

        self._draw_bottom_hud(surface)
        self._draw_cemetery_button(surface)

        hand_rects = []
        self.ultimate_hand_rect = None
        if self.engine.state in ("player_turn", "enemy_turn", "enemy_resolving"):
            mouse_pos = self.window_manager.get_virtual_mouse_pos()
            hand_rects = self._get_battle_hand_rects()
            normal_count = len(self.engine.hand)
            normal_rects = hand_rects[:normal_count]
            for rect, card in zip(normal_rects, self.engine.hand):
                hovered = rect.collidepoint(mouse_pos) and (self.engine.state == "player_turn")
                CardView.draw_card(surface, rect, card, self.asset_manager, hovered)
            if self._ultimate_in_hand() and hand_rects:
                self.ultimate_hand_rect = hand_rects[-1]
                hovered = self.ultimate_hand_rect.collidepoint(mouse_pos) and (self.engine.state == "player_turn")
                self._draw_ultimate_hand_card(surface, self.ultimate_hand_rect, hovered)
            self._draw_ultimate_counter(surface, hand_rects)

        can_end = self.engine.state == "player_turn" and self.entity_view.player_action is None
        self._draw_end_turn_button(surface, enabled=can_end)

        self.floating_texts.draw(surface, self.asset_manager.font)
        self.coin_hud.draw_particles(surface)

        mouse = self.window_manager.get_virtual_mouse_pos()
        for rect, card in zip(hand_rects, self.engine.hand):
            if rect.collidepoint(mouse):
                CardView.draw_tooltip(surface, card, self.asset_manager, mouse)
                break
        if self.ultimate_hand_rect and self.ultimate_hand_rect.collidepoint(mouse):
            CardView.draw_tooltip(surface, self.engine.ultimate, self.asset_manager, mouse, cost_label='ULT')

        self._draw_top_message(surface)

        if self.engine.state == "game_over" and self.entity_view.enemy_ultimate is None:
            self._draw_game_over(surface)
        if self.engine.state == "victory" and self.entity_view.player_action is None and self.entity_view.attacker is None:
            self._draw_victory(surface)
        if self.engine.state == "phase_complete":
            self._draw_pending_save(surface)

    def _draw_top_message(self, surface):
        """Aviso transitório do topo: ultimate do inimigo ou mensagem do combate."""
        if self.entity_view.enemy_ultimate:
            special = self.entity_view.enemy_ultimate
            self._draw_message_box(surface, special.title.upper(), special.color,
                                   fill=(12, 14, 20, 235), border=special.color, radius=10)
        elif self.engine.message:
            self._draw_message_box(surface, self.engine.message, WHITE,
                                   fill=(36, 14, 18, 235), border=(168, 86, 86), radius=12)

    def _draw_message_box(self, surface, text, color, fill, border, radius):
        """Caixa de aviso no topo: quebra o texto na largura útil e cresce para baixo."""
        font = self.asset_manager.font
        width, min_height, pad_x, pad_y = 460, 40, 18, 6
        lines = wrap_text(text, font, width - pad_x * 2) or [""]
        line_h = font.get_linesize()
        height = max(min_height, len(lines) * line_h + pad_y * 2)
        msg_rect = pygame.Rect(WIDTH // 2 - width // 2, 26, width, height)
        draw_panel(surface, msg_rect, fill=fill, border=border, radius=radius)
        first_center = msg_rect.centery - (len(lines) - 1) * line_h / 2
        for i, line in enumerate(lines):
            draw_text(surface, line, font, color, msg_rect.centerx, first_center + i * line_h, center=True)

    def _draw_cemetery_button(self, surface):
        """Desenha o botão de acesso ao Cemitério durante a partida."""
        is_player_turn = self.engine.state == "player_turn"
        can_use = self.engine.can_use_cemetery() or self.engine.can_swap_cemetery()
        self._draw_cemetery_book(surface, enabled=is_player_turn and can_use)

    def _draw_ultimate_bar(self, surface):
        ready = self.engine.ultimate_ready
        panel_rect = pygame.Rect(20, HEIGHT - 236, 214, 102)
        accent = self.engine.active_ultimate_color
        draw_panel(surface, panel_rect, fill=(16, 17, 28, 226), border=accent, radius=16)
        draw_text(surface, self.engine.active_ultimate_name.upper(), self.asset_manager.small_font,
                  accent, panel_rect.x + 16, panel_rect.y + 12)
        draw_text(surface, self.engine.active_ultimate_description, self.asset_manager.small_font,
                  (167, 174, 187), panel_rect.x + 16, panel_rect.y + 34)
        bar_x, bar_y, bar_w, bar_h = panel_rect.x + 16, panel_rect.y + 58, panel_rect.width - 32, 16
        draw_health_bar(surface, bar_x, bar_y, bar_w, bar_h,
                        self.engine.ultimate_charge, self.engine.ultimate_threshold, accent)
        draw_text(surface,
                  f"Carga {self.engine.ultimate_charge}/{self.engine.ultimate_threshold}",
                  self.asset_manager.small_font, WHITE, panel_rect.centerx, bar_y + 30, center=True)

        can_click = ready and self.engine.state == "player_turn"
        if ready:
            fill = accent if can_click else (71, 71, 71)
            border = GOLD
            label = "ATIVAR ULT"
            text_color = BLACK if can_click else GRAY
        else:
            fill = (48, 49, 57)
            border = (95, 95, 110)
            label = "ULT BLOQUEADA"
            text_color = GRAY
        self._draw_action_button(surface, self.ultimate_button_rect, label, fill, border,
                                 text_color=text_color, enabled=can_click)

    def _draw_menu_button(self, surface):
        hovered = self.menu_button_rect.collidepoint(self.window_manager.get_virtual_mouse_pos())
        theme.button(surface, self.menu_button_rect, "MENU", self.asset_manager.small_font,
                     hover=hovered, prominent=False, enabled=True)

    def _draw_game_over(self, surface):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(210)
        overlay.fill(BLACK)
        surface.blit(overlay, (0, 0))

        draw_text(
            surface, "VOCÊ MORREU", self.asset_manager.big_font, RED, WIDTH // 2, HEIGHT // 2 - 20, center=True
        )
        draw_text(
            surface,
            f"Você chegou até o andar {self.engine.level}",
            self.asset_manager.font,
            WHITE,
            WIDTH // 2,
            HEIGHT // 2 + 20,
            center=True,
        )
        draw_text(
            surface,
            "R para tentar novamente  |  MENU para voltar ao mapa" if self.map_mode else "Pressione R para reiniciar",
            self.asset_manager.font,
            WHITE,
            WIDTH // 2,
            HEIGHT // 2 + 60,
            center=True,
        )

    def _draw_victory(self, surface):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((6, 7, 14, 228))
        surface.blit(overlay, (0, 0))
        title_rect = pygame.Rect(WIDTH // 2 - 250, 46, 500, 76)
        draw_panel(surface, title_rect, fill=(22, 18, 31, 235), border=GOLD, radius=18)
        draw_text(surface, "VITÓRIA! ESCOLHA UMA CARTA", self.asset_manager.big_font,
                  GOLD, title_rect.centerx, title_rect.y + 28, center=True)
        draw_text(surface, "Recompensa da fase concluída", self.asset_manager.small_font,
                  WHITE, title_rect.centerx, title_rect.y + 55, center=True)

        mouse_pos = self.window_manager.get_virtual_mouse_pos()
        reward_rects = CardView.get_reward_rects(len(self.engine.reward_cards))
        for rect, card in zip(reward_rects, self.engine.reward_cards):
            hovered = rect.collidepoint(mouse_pos)
            CardView.draw_card(surface, rect, card, self.asset_manager, hovered)
        for rect, card in zip(reward_rects, self.engine.reward_cards):
            if rect.collidepoint(mouse_pos):
                CardView.draw_tooltip(surface, card, self.asset_manager, mouse_pos)
                break
        self._draw_action_button(surface, self.skip_reward_rect, "Pular",
                                 (55, 57, 63), (148, 148, 148), text_color=WHITE)

    def _draw_pending_save(self, surface):
        """Recuperação caso falhe a gravação do desbloqueio após a vitória."""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((7, 6, 14, 224))
        surface.blit(overlay, (0, 0))
        draw_text(surface, "FASE CONCLUÍDA", self.asset_manager.big_font,
                  GOLD, WIDTH // 2, HEIGHT // 2 - 65, center=True)
        draw_text(surface, "Não foi possível gravar seu progresso.",
                  self.asset_manager.font, WHITE, WIDTH // 2, HEIGHT // 2, center=True)
        draw_text(surface, "Pressione R para tentar salvar novamente.",
                  self.asset_manager.font, WHITE, WIDTH // 2, HEIGHT // 2 + 52, center=True)
        if self.engine.message:
            draw_text(surface, self.engine.message[:90], self.asset_manager.small_font,
                      RED, WIDTH // 2, HEIGHT // 2 + 102, center=True)

    def handle_event(self, event):
        # Trata atalho de tela cheia ou redimensionamento
        if self.window_manager.handle_window_event(event):
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            virt_pos = self.window_manager.map_to_virtual(event.pos)

            # Botão de Tela Cheia
            if self.window_manager.get_fullscreen_button_rect().collidepoint(virt_pos):
                self.window_manager.toggle_fullscreen()
                return

            # Botão de Menu In-game
            if self.menu_button_rect.collidepoint(virt_pos):
                self._open_menu_confirmation()
                return

            # Turno do Jogador: Jogar Carta, Ultimate na mão, Acessar Cemitério ou Encerrar Turno
            if self.engine.state == "player_turn" and self.entity_view.player_action is None:
                if self.cemetery_button_rect.collidepoint(virt_pos):
                    self._open_cemetery_modal()
                    return

                hand_rects = self._get_battle_hand_rects()
                normal_count = len(self.engine.hand)
                if self._ultimate_in_hand() and hand_rects:
                    ultimate_rect = hand_rects[-1]
                    if ultimate_rect.collidepoint(virt_pos):
                        self.engine.activate_ultimate()
                        return
                    hand_rects = hand_rects[:normal_count]

                for index, rect in enumerate(hand_rects[:normal_count]):
                    if rect.collidepoint(virt_pos):
                        self.engine.play_card(index)
                        return

                if self.end_turn_rect.collidepoint(virt_pos):
                    self.engine.end_turn()
                    return

            # Recompensa de Vitória: Escolher Carta ou Pular
            elif self.engine.state == "victory" and self.entity_view.player_action is None and self.entity_view.attacker is None:
                reward_rects = CardView.get_reward_rects(len(self.engine.reward_cards))
                for index, rect in enumerate(reward_rects):
                    if rect.collidepoint(virt_pos):
                        self.engine.choose_reward(index)
                        return

                if self.skip_reward_rect.collidepoint(virt_pos):
                    self.engine.skip_reward()
                    return

        elif event.type == pygame.KEYDOWN:
            # Reiniciar partida em Game Over
            if event.key == pygame.K_r and self.engine.state == "phase_complete":
                self._finalize_map_phase(self.engine.level)
                return
            if event.key == pygame.K_r and self.engine.state == "game_over" and self.entity_view.enemy_ultimate is None:
                self.engine = CombatEngine(
                    on_event_callback=self._handle_combat_event, map_mode=self.map_mode,
                )
                if self.save_manager is not None and self.save_data is not None:
                    try:
                        self.save_data = self.save_manager.load_save(self.save_data["id"])
                        self.engine.resume_from_save(
                            self.save_data, self.save_manager,
                            level=self.selected_level if self.map_mode else None,
                            encounter_kind=self.encounter_kind,
                            encounter_index=self.encounter_index,
                        )
                    except (OSError, SaveError) as exc:
                        # Falha explícita em vez de sobrescrever um save danificado.
                        self.engine.show_message(f"Não foi possível carregar: {exc}")
                self.coin_hud = CoinHUD(self.engine.player, anchor_x=66, anchor_y=102)
                self.energy_hud = EnergyHUD(self.engine.player)
                self.entity_view = EntityView(self.asset_manager)
                self.floating_texts.clear()
                self.enemy_turn_timer = 0

            # Tecla C para atalho rápido do Cemitério durante o turno do jogador
            elif event.key == pygame.K_c and self.engine.state == "player_turn":
                self._open_cemetery_modal()

            # ESC para abrir menu de confirmação
            elif event.key == pygame.K_ESCAPE and self.engine.state in (
                "player_turn",
                "enemy_turn",
                "enemy_resolving",
                "game_over",
                "victory",
            ):
                self._open_menu_confirmation()

    def _open_cemetery_modal(self):
        """Abre a interface interativa do Cemitério como modal."""
        modal = CemeteryModal(
            self.scene_manager,
            self.window_manager,
            self.asset_manager,
            self.engine,
        )
        self.scene_manager.push_modal(modal)

    def _open_menu_confirmation(self):
        if self.engine.state == "phase_complete":
            self._finalize_map_phase(self.engine.level)
            return
        if self.engine.state == "victory":
            message = "Escolha sua recompensa antes de sair para salvar a vitória."
        elif self.engine.state == "game_over":
            message = "Seu último checkpoint continuará disponível."
        else:
            message = "Seu progresso será salvo antes de sair."
        modal = ConfirmationModal(
            self.scene_manager,
            self.window_manager,
            self.asset_manager,
            on_confirm=self._return_to_main_menu,
            message=message,
        )
        self.scene_manager.push_modal(modal)

    def _save_progress(self):
        """Registra um checkpoint do andar atual sem modificar outro slot."""
        if self.save_manager is None or self.save_data is None:
            return True
        # Se o herói morreu ou aguarda recompensa, mantém o último checkpoint:
        # nunca grava HP zero nem concede duas vezes uma vitória ainda pendente.
        if self.engine.state in ("game_over", "victory", "phase_complete"):
            return True
        try:
            self.coin_hud.collect_pending_coins()
            self.save_manager.update_from_game(
                self.save_data, self.engine.player, self.engine.deck_manager,
                level=max(self.engine.level, self.save_data["progresso"]["andar"])
                if self.map_mode else self.engine.level,
            )
            self.save_manager.save(self.save_data)
            return True
        except (OSError, ValueError, SaveError) as exc:
            self.engine.show_message(f"Erro ao salvar progresso: {exc}", duration=3500)
            return False

    def _finalize_map_phase(self, level):
        """Grava vitória, recompensa e desbloqueio antes de trocar de cena."""
        if not self.map_mode or self.save_manager is None or self.save_data is None:
            return
        try:
            recorder = record_road_victory if self.encounter_kind == "road" else record_victory
            recorder(
                self.save_manager, self.save_data, self.engine,
                self.coin_hud.collect_pending_coins,
            )
        except (OSError, ValueError, SaveError) as exc:
            self.engine.show_message(f"Erro ao salvar: {exc}", duration=6000)
            return
        self._return_to_map()

    def _return_to_map(self):
        from src.scenes.map_scene import MapScene
        self.scene_manager.change_scene(MapScene(
            self.scene_manager, self.window_manager, self.asset_manager,
            self.save_manager, self.save_data,
        ))

    def save_on_exit(self):
        """Salva ao fechar a janela, inclusive após um desbloqueio pendente."""
        if self.engine.state == "phase_complete":
            self._finalize_map_phase(self.engine.level)
            return self.scene_manager.current_scene is not self
        return self._save_progress()

    def _return_to_main_menu(self):
        if not self._save_progress():
            return
        if self.map_mode:
            self._return_to_map()
        else:
            from src.scenes.menu_scene import MenuScene
            self.scene_manager.change_scene(
                MenuScene(self.scene_manager, self.window_manager, self.asset_manager)
            )
