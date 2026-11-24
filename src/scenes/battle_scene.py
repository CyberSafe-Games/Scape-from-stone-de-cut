import pygame
from copy import deepcopy

from src.scenes.base_scene import BaseScene
from src.config.boss_names import boss_display_name
from src.scenes.confirmation_modal import ConfirmationModal
from src.scenes.cemetery_modal import CemeteryModal
from src.scenes.pause_menu_modal import PauseMenuModal
from src.systems.combat_engine import CombatEngine
from src.systems.game_preferences import enemy_windup_ms
from src.config.preferences import ENEMY_SPEED_NORMAL
from src.systems.save_manager import SaveError, is_test_save
from src.systems.campaign_progress import record_victory, record_road_victory
from src.systems.territory_map import TERRITORIES
from src.ui.card_view import CardView
from src.ui.entity_view import EntityView
from src.ui.floating_text import FloatingTextManager
from src.ui.victory_banner import build_outcome_banner, draw_victory_embers
from src.ui.post_combat_reward_view import PostCombatRewardView
from src.ui.coin_hud import CoinHUD
from src.ui.energy_hud import EnergyHUD
from src.ui.battle_hud import BattleHUD
# BEGIN BOSS DIALOGUE INTEGRATION
from src.config.boss_dialogues import dialogue_for
from src.ui.boss_dialogue_overlay import BossDialogueOverlay
# END BOSS DIALOGUE INTEGRATION
from src.ui.enemy_intent_view import EnemyIntentView
from src.ui.card_fx import draw_player_projectile
from src.ui.ultimate_fx import draw_ultimate_fx
from src.ui.boss_ultimate_fx import draw_boss_ultimate_fx
from src.systems.ultimate_animations import ULTIMATE_ANIMATIONS
from src.systems.alvaro_tex_animations import TRANSITION_MS
from src.systems.boss_animation_kits import KITS
from src.systems.common_animation_kits import COMMON_KITS
from src.systems.common_enemy_audio import (
    BASIC_BOSS_ATTACK_SOUNDS, COMMON_ATTACK_SOUNDS, COMMON_SUPPORT_SOUNDS, SOUND_WINDOWS_MS,
    BOSS_ATTACK_SOUNDS, BOSS_SUPPORT_SOUNDS, BOSS_ULTIMATE_SOUNDS,
    SHIELD_BREAK_IMPACT_MS,
)
from src.ui.helpers import (
    draw_text,
    draw_health_bar,
    draw_panel,
    draw_vignette,
    wrap_text,
)
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
    VICTORY_FRAME_MS,
)


class BattleScene(BaseScene):
    """Cena principal de batalha onde o combate por turnos acontece."""

    boss_dialogue = None
    preferences = None
    _outcome_elapsed = None
    _reward_gold = 0
    _fall_elapsed = None
    _status_audio = ()
    BLEED_FEEDBACK_DELAY_MS = 400
    _ultimate_enemy_snapshot = None
    victory_sound = "gameplay.victory"
    VICTORY_POSE_MS = 12 * VICTORY_FRAME_MS
    VICTORY_BANNER_MS = 6 * VICTORY_FRAME_MS
    ENEMY_FALL_MS = 420

    @property
    def _victory_ready(self):
        return (self.engine.state == "victory" and self._outcome_elapsed is not None
                and self._outcome_elapsed >= self.VICTORY_POSE_MS)

    @property
    def _game_over_ready(self):
        return self.engine.state == "game_over" and self._outcome_elapsed is not None


    @property
    def music_context(self):
        state = self.engine.state
        if state == 'game_over' and self._outcome_elapsed is not None:
            return None
        enemy = self.engine.enemy
        if getattr(enemy, 'is_final_boss', False) or enemy.name.lower() == 'zanzara':
            return 'final_boss'
        if state == 'phase_complete' or (state == 'victory' and self._outcome_elapsed is not None):
            return None
        if getattr(enemy, 'is_miniboss', False) or getattr(enemy, 'boss_id', None):
            return 'boss'
        return 'battle'

    def __init__(
        self,
        scene_manager,
        window_manager,
        asset_manager,
        save_manager=None,
        save_data=None,
        map_mode=False,
        selected_level=None,
        encounter_kind="point",
        encounter_index=None,
    ):

        super().__init__(scene_manager, window_manager, asset_manager)

        self.save_manager = save_manager
        self.save_data = save_data
        self.map_mode = map_mode
        self.selected_level = selected_level
        self.encounter_kind = encounter_kind
        self.encounter_index = encounter_index
        self.preferences = getattr(scene_manager, "audio_preferences", None)
        self.floating_texts = FloatingTextManager(
            enabled=self._damage_numbers_enabled()
        )
        self.entity_view = EntityView(asset_manager)
        self.battle_hud = BattleHUD(asset_manager)
        self.intent_view = EnemyIntentView(asset_manager)
        self._ultimate_events = []
        self._ultimate_clock = 0
        self._ultimate_enemy_snapshot = None
        self._boss_events = []
        self._boss_clock = 0
        self._boss_player_snapshot = None
        self._phase_transition_pending = False
        self._pending_attack_sound = None
        self._pending_enemy_audio = []

        # Inicializa o motor puro de combate com callbacks para efeitos visuais
        self.engine = CombatEngine(
            on_event_callback=self._handle_combat_event,
            map_mode=self.map_mode,
        )
        if self.save_manager is not None and self.save_data is not None:
            self.engine.resume_from_save(
                self.save_data,
                self.save_manager,
                level=self.selected_level if self.map_mode else None,
                encounter_kind=self.encounter_kind,
                encounter_index=self.encounter_index,
            )

        # Diálogos só aparecem quando há falas configuradas para este chefe.
        boss_lines = dialogue_for(self.engine.enemy)
        self.boss_dialogue = (
            BossDialogueOverlay(
                self.asset_manager, self.engine.enemy.name, boss_lines,
                self.selected_level or self.engine.level,
            ) if boss_lines else None
        )
        # Sistema de moedas (instanciado apos o engine para ter acesso ao player)
        self.coin_hud = CoinHUD(self.engine.player, anchor_x=99, anchor_y=153)
        self.energy_hud = EnergyHUD(self.engine.player)

        self.enemy_turn_timer = 0
        self.menu_button_rect = pygame.Rect(WIDTH - 162, 27, 129, 42)
        self.end_turn_rect = pygame.Rect(WIDTH - 180, HEIGHT - 198, 150, 150)
        self.cemetery_button_rect = pygame.Rect(42, HEIGHT - 231, 138, 186)
        self.ultimate_button_rect = pygame.Rect(0, 0, 0, 0)
        self.ultimate_hand_rect = None
        self._hovered_hand_card = None
        self._last_card_hover_sound_at = -120
        self.reward_view = PostCombatRewardView(asset_manager)
        self._logical_saved = None
        self._save_failed = False
        self.new_run_rect = pygame.Rect(WIDTH // 2 - 220, HEIGHT // 2 + 145, 440, 66)
        if self.map_mode:
            if self.engine.state == 'boss_transition':
                self._phase_transition_pending = True
            if self.engine.state == 'victory':
                self._reward_gold = self.engine.victory_gold()
            self._persist_logical_state()

    def _handle_combat_event(self, event_name, **kwargs):
        """Reage a eventos emitidos pelo motor de combate."""
        ultimate = ULTIMATE_ANIMATIONS.get(self.entity_view.player_action)
        if ultimate and event_name == "floating_text":
            self._ultimate_events.append(
                (ultimate.duration * ultimate.impact, event_name, kwargs)
            )
            return
        boss_attack = self.entity_view.attacker == "enemy" and (
            self.entity_view.enemy_attack_name in KITS
            or self.entity_view.enemy_attack_name in COMMON_KITS
        )
        if boss_attack and event_name == "floating_text":
            impact = (
                self.entity_view.enemy_attack_duration
                * self.entity_view.enemy_impact_fraction
            )
            self._boss_events.append((impact, kwargs))
            return
        if event_name == "game_over":
            if getattr(self, 'map_mode', False) and self.save_manager and not self.engine.is_replay:
                ok, message = self.save_manager.end_run(self.save_data, self.engine.level)
                self._save_failed = not ok
                if not ok:
                    self.engine.show_message(message, 6000)
        elif event_name == "status_trigger":
            self._status_audio = (*self._status_audio, (kwargs["status"], kwargs["target"],
                                                        kwargs.get("damage"), None))
        elif event_name == "boss_phase_transition":
            self._phase_transition_pending = True
        elif event_name == "boss_phase_started":
            self.entity_view.phase_transition_timer = None
            self.entity_view.enemy_flash = 0
            self.entity_view.pending_enemy_hit_at = None
            self._ultimate_enemy_snapshot = None
        elif event_name == "attack":
            if kwargs.get("attacker") == "enemy" and (
                self.engine.enemy.name.lower() in KITS
                or self.engine.enemy.name.lower() in COMMON_KITS
            ):
                self._boss_clock = 0
                self._boss_player_snapshot = deepcopy(self.engine.player)
            self.entity_view.trigger_attack(
                kwargs.get("attacker"),
                kwargs.get("action"),
                enemy_name=getattr(self.engine.enemy, "name", None),
                ultimate=kwargs.get("ultimate", False),
            )
            if kwargs.get("attacker") == "enemy":
                self._queue_common_enemy_audio(
                    kwargs.get("action"), is_attack=True,
                    is_ultimate=kwargs.get("ultimate", False),
                )
            if kwargs.get("attacker") == "player":
                sound_cue = {
                    "Soco Simples": ("gameplay.attack.punch", 0.24),
                    "Adaga Sangrenta": ("gameplay.attack.dagger", 0.24),
                    "Zarabatana Venenosa": ("gameplay.attack.blowgun", 0.64),
                    "Investida": ("gameplay.attack.charge", 0.24),
                    "Lança Perfurante": ("gameplay.attack.spear", 0.24),
                    "Machados Gêmeos": ("gameplay.attack.twin_axes", 0.24),
                    "Machado Quebra-Escudo": ("gameplay.attack.shield_break", 0.24),
                    "Bola de Fogo": ("gameplay.attack.fireball", 0.64),
                }.get(kwargs.get("action"))
                self._pending_attack_sound = (
                    (
                        kwargs.get("action"),
                        self.entity_view.player_attack_duration * sound_cue[1],
                        sound_cue[0],
                        self.entity_view.player_attack_duration
                        * (0.90 if sound_cue[1] == 0.64 else 0.52),
                    )
                    if sound_cue is not None
                    else None
                )
                revised = {
                    "Disparo de Arco": (768, "gameplay.attack.arrow_launch", 1368),
                    "Adaga Sangrenta": (216, "gameplay.attack.dagger", 1982),
                    "Investida": (0, "gameplay.attack.charge", 1500),
                    "Lança Perfurante": (308, "gameplay.attack.spear", 900),
                    "Machados Gêmeos": (368, "gameplay.attack.twin_axes", 900),
                    "Machado Quebra-Escudo": (216, "gameplay.attack.shield_break", 2416),
                    "Bola de Fogo": (768, "gameplay.attack.fireball", 2868),
                    "Poção Venenosa": (768, "gameplay.potion.poison", 3175),
                    "Poção Fragilizante": (768, "gameplay.potion.weaken", 2460),
                    "Amuleto Dissipador": (768, "gameplay.skill.dispel", 1488),
                }.get(kwargs.get("action"))
                if revised is not None:
                    start, sound_id, end = revised
                    reference_duration = (
                        1200 if kwargs.get("action") in (
                            "Bola de Fogo", "Poção Venenosa", "Poção Fragilizante", "Amuleto Dissipador",
                            "Disparo de Arco"
                        )
                        else 900
                    )
                    scale = self.entity_view.player_attack_duration / reference_duration
                    self._pending_attack_sound = (
                        kwargs.get("action"), start * scale, sound_id, end * scale,
                    )
                self._pending_contact_sound = (
                    (
                        kwargs.get("action"),
                        self.entity_view.player_attack_duration
                        * (0.90 if kwargs.get("action") == "Disparo de Arco" else 0.52),
                    )
                    if kwargs.get("action") in (
                        "Lança Perfurante", "Machados Gêmeos", "Investida", "Disparo de Arco"
                    )
                    else None
                )
                self._attack_latest_start_ms = self.entity_view.player_attack_duration * (
                    0.90 if kwargs.get("action") in (
                        "Zarabatana Venenosa", "Disparo de Arco", "Bola de Fogo", "Poção Venenosa",
                        "Poção Fragilizante", "Amuleto Dissipador"
                    ) else 0.52
                )
                if kwargs.get("action") == "Amuleto Dissipador":
                    self._attack_latest_start_ms = self.entity_view.player_attack_duration
        elif event_name == "flash":
            self.entity_view.trigger_flash(kwargs.get("target"), getattr(self.engine.enemy, "name", None))
        elif event_name == "player_action":
            self._attack_latest_start_ms = None
            self.entity_view.trigger_player_action(kwargs.get("action"))
            sound_id = {
                "Aura Rubra": "gameplay.skill.aura",
                "Esfera Protetora": "gameplay.skill.shield_light",
                "Esfera Escudo": "gameplay.skill.shield_heavy",
                "Totem Protetor": "gameplay.skill.totem",
                "Poção de Cura": "gameplay.potion.heal",
                "Poção Purificadora": "gameplay.potion.cleanse",
                "Máscara Ancestral": "gameplay.skill.mask",
                "Surto de Energia": "gameplay.skill.energy",
            }.get(kwargs.get("action"))
            if sound_id is not None:
                self._pending_attack_sound = (
                    kwargs.get("action"),
                    self.entity_view.player_action_duration * 0.52,
                    sound_id,
                    None,
                )
                if kwargs.get("action") in (
                    "Aura Rubra", "Totem Protetor", "Máscara Ancestral", "Surto de Energia"
                ):
                    self._pending_attack_sound = (
                        kwargs.get("action"), 0, sound_id,
                        self.entity_view.player_action_duration,
                    )
                elif kwargs.get("action") == "Esfera Escudo":
                    self._pending_attack_sound = (
                        kwargs.get("action"), self.entity_view.player_action_duration * 0.52,
                        sound_id, self.entity_view.player_action_duration + 1200,
                    )
                if kwargs.get("action") == "Surto de Energia":
                    self._pending_attack_sound = (
                        kwargs.get("action"), 0, sound_id,
                        self.entity_view.player_action_duration + 800,
                    )
                elif kwargs.get("action") == "Máscara Ancestral":
                    self._pending_attack_sound = (
                        kwargs.get("action"), 0, sound_id,
                        self.entity_view.player_action_duration + 600,
                    )
            self._ultimate_clock = 0
            self._ultimate_enemy_snapshot = None
            if kwargs.get("action") == "Rugido da Floresta":
                rugido = ULTIMATE_ANIMATIONS["Rugido da Floresta"]
                self._ultimate_enemy_snapshot = deepcopy(self.engine.enemy)
                self._pending_attack_sound = (
                    "Rugido da Floresta", rugido.duration * rugido.release,
                    "gameplay.attack.fireball", None,
                )
                self._attack_latest_start_ms = rugido.duration * rugido.impact
        elif event_name == "enemy_action":
            self.entity_view.trigger_enemy_action(
                kwargs.get("action"),
                enemy_name=getattr(self.engine.enemy, "name", None),
            )
            self._queue_common_enemy_audio(kwargs.get("action"), is_attack=False)
        elif event_name == "floating_text":
            self.floating_texts.spawn(
                kwargs["x"], kwargs["y"], kwargs["text"], kwargs["color"]
            )
        elif event_name == "coin_drop":
            self._reward_gold = kwargs["amount"]
        elif event_name == "checkpoint":
            self._reset_outcome()
            # Modo legado sem mapa: o motor ainda avança de andar sozinho.
            self._save_progress()
        elif event_name == "phase_complete":
            # Uma fase só é concluída após a escolha (ou pulo) da recompensa.
            self._finalize_map_phase(kwargs["level"])
        elif event_name == "cemetery_swap":
            card = kwargs.get("new_card")
            if card is not None:
                self.floating_texts.spawn(
                    PLAYER_X,
                    HEIGHT - 330,
                    f"Carta trocada: {card.name}",
                    (176, 184, 146),
                )
        elif event_name == "cemetery_discard":
            card = kwargs.get("card")
            card_name = card.name if card else "Carta"
            self.floating_texts.spawn(
                PLAYER_X,
                HEIGHT - 330,
                f"{card_name} Descartada",
                (176, 153, 117),
            )

    def _queue_common_enemy_audio(self, action, is_attack, is_ultimate=False):
        self._pending_enemy_audio = []
        enemy = self.engine.enemy
        name = enemy.name.lower()
        is_boss = (
            getattr(enemy, "is_miniboss", False)
            or getattr(enemy, "is_final_boss", False)
            or getattr(enemy, "boss_id", None) is not None
            or name in KITS
        )
        if is_ultimate:
            if not is_boss or not is_attack:
                return
            mapping = BOSS_ULTIMATE_SOUNDS
        elif is_boss:
            mapping = (
                {name: {**BASIC_BOSS_ATTACK_SOUNDS.get(name, {}), **BOSS_ATTACK_SOUNDS.get(name, {})}}
                if is_attack else BOSS_SUPPORT_SOUNDS
            )
        else:
            mapping = COMMON_ATTACK_SOUNDS if is_attack else COMMON_SUPPORT_SOUNDS
        sound_id = mapping.get(name, {}).get(action)
        if sound_id is None:
            return
        view = self.entity_view
        duration = view.enemy_attack_duration if is_attack else view.enemy_action_duration
        fraction = view.enemy_impact_fraction if is_attack else 0.52
        if name == "zanzara" and is_attack:
            prefix = "gameplay.boss.zanzara."
            if is_ultimate:
                spec = view.enemy_ultimate
                if spec is None:
                    return
                cues = ((.08, "aura"), (.12, "laugh"), (spec.release, "summon"), (spec.impact, "ferry"), (spec.impact, "ferry_hit"))
            elif action == "atk1":
                cues = ((max(0, fraction-400/duration), "swing"), (fraction, "flesh"))
            elif action == "atk2":
                cues = ((.24, "smoke"), (max(.24, fraction-400/duration), "swing"), (fraction, "flesh"), (.91, "smoke"))
            else:
                cues = ((.08, "aura"), (.12, "portal"), (.42, "souls"))
            self._pending_enemy_audio.extend(
                (name, action, is_attack, duration * at, prefix + cue) for at, cue in cues
            )
            return
        if name == "carrasco da vigília" and is_attack:
            launch = view.enemy_ultimate.release if is_ultimate and view.enemy_ultimate else 0.24
            impact_sound = "gameplay.boss.carrasco.execution_hit" if is_ultimate else "gameplay.boss.duo.heavy_hit"
            self._pending_enemy_audio.extend((
                (name, action, is_attack, duration * launch, sound_id),
                (name, action, is_attack, duration * fraction, impact_sound),
            ))
            return
        if name == "corpo seco" and is_attack:
            launch = view.enemy_ultimate.release if is_ultimate and view.enemy_ultimate else 0.24
            self._pending_enemy_audio.extend((
                (name, action, is_attack, duration * launch, sound_id),
                (name, action, is_attack, duration * fraction, "gameplay.boss.duo.flesh_hit"),
            ))
            return
        if name == "gordofera" and is_attack:
            if is_ultimate:
                self._pending_enemy_audio.extend((
                    (name, action, is_attack, duration * 0.25, sound_id),
                    (name, action, is_attack, duration * fraction, "gameplay.boss.gordofera.tremor"),
                ))
                return
            if action == "atk1":
                self._pending_enemy_audio.extend((
                    (name, action, is_attack, duration * 0.24, sound_id),
                    (name, action, is_attack, duration * fraction, "gameplay.boss.guardian.claw_hit"),
                ))
                return
            if action == "atk2":
                fraction = 0.35
        if name == "goblin nerd" and is_attack:
            if is_ultimate:
                spec = view.enemy_ultimate
                if spec is None:
                    return
                cues = (
                    (duration * 0.10, "gameplay.boss.goblin.charge"),
                    (duration * spec.release, sound_id),
                    (duration * spec.impact, "gameplay.boss.goblin.energy_hit"),
                )
            elif view.enemy_ranged_attack:
                cues = (
                    (duration * view.enemy_ranged_attack[1], sound_id),
                    (duration * fraction, "gameplay.boss.small.body_hit" if action == "atk1"
                     else "gameplay.boss.goblin.energy_hit"),
                )
            else:
                # Preparação e primeiro quadro com jato são momentos distintos.
                cues = (
                    (duration * 0.18, "gameplay.boss.goblin.retch"),
                    (duration * 0.43, sound_id),
                )
            self._pending_enemy_audio.extend(
                (name, action, is_attack, when, cue) for when, cue in cues
            )
            return
        if name == "álvaro e tex" and not is_attack and action == "healer2":
            # A fumaça visual surge aos 20%, antes da ativação do buff.
            fraction = 0.20
        if name == "álvaro e tex · pequeno" and is_attack and action != "atk1":
            launch = view.enemy_ranged_attack[1] if view.enemy_ranged_attack else 0.24
            impact_sound = (
                "gameplay.boss.duo.flesh_hit" if action == "atk4"
                else "gameplay.boss.small.fury_hit" if is_ultimate
                else "gameplay.boss.small.body_hit"
            )
            self._pending_enemy_audio.extend((
                (name, action, is_attack, duration * launch, sound_id),
                (name, action, is_attack, duration * fraction, impact_sound),
            ))
            return
        if name == "álvaro e tex" and is_attack:
            launch = view.enemy_ranged_attack[1] if view.enemy_ranged_attack else 0.24
            impact_sound = (
                "gameplay.boss.duo.flesh_hit" if action == "atk2"
                else "gameplay.boss.duo.heavy_hit"
            )
            self._pending_enemy_audio.extend((
                (name, action, is_attack, duration * launch, sound_id),
                (name, action, is_attack, duration * fraction, impact_sound),
            ))
            return
        if is_ultimate:
            if view.enemy_ultimate is None:
                return
            fraction = view.enemy_ultimate.release
        if name == "guardião da pedra" and is_attack and not is_ultimate and action == "atk1":
            self._pending_enemy_audio.append((
                name, action, is_attack, duration * 0.24,
                "gameplay.boss.guardian.claw",
            ))
            sound_id = "gameplay.boss.guardian.claw_hit"
        if is_attack and name == "centauro vigia" and action == "atk1":
            self._pending_enemy_audio.append((
                name, action, is_attack, duration * view.enemy_ranged_attack[1],
                "gameplay.attack.arrow_launch",
            ))
        if is_attack and name == "golem das ruínas" and action == "atk1":
            self._pending_enemy_audio.append((
                name, action, is_attack, duration * view.enemy_ranged_attack[1],
                "gameplay.boss.goblin.beam",
            ))
        start = duration * fraction
        if sound_id == "gameplay.attack.shield_break":
            start = max(0, start - SHIELD_BREAK_IMPACT_MS)
        self._pending_enemy_audio.append((name, action, is_attack, start, sound_id))

    def update(self, dt):
        if getattr(self, 'map_mode', False) and not self._persist_logical_state():
            return
        if self.boss_dialogue is not None:
            self.boss_dialogue.update(dt)
            if self.boss_dialogue.finished:
                self.boss_dialogue = None
            return
        reward_view = getattr(self, "reward_view", None)
        if self._victory_ready and reward_view is not None:
            choice = reward_view.update(dt)
            if choice:
                self._commit_reward(choice)
                return
        self.floating_texts.set_enabled(self._damage_numbers_enabled())
        pending_attack = getattr(self, "_pending_attack_sound", None)
        if pending_attack is not None:
            action, start_ms, sound_id, collision_ms = pending_attack
            animation_ms = self.entity_view.player_action_timer + dt
            if self.entity_view.player_action != action:
                self._pending_attack_sound = None
            elif animation_ms >= start_ms:
                self._pending_attack_sound = None
                latest_start = getattr(self, "_attack_latest_start_ms", None)
                if latest_start is not None and animation_ms > latest_start:
                    pass
                elif collision_ms is None:
                    self.play_ui_sound(sound_id)
                elif collision_ms > animation_ms:
                    self.play_ui_sound(sound_id, maxtime=collision_ms - animation_ms)
        arrow_impact_duration = None
        pending_contact = getattr(self, "_pending_contact_sound", None)
        if pending_contact is not None:
            action, contact_ms = pending_contact
            is_arrow = action == "Disparo de Arco"
            animation_ms = (
                self.entity_view.attack_timer if is_arrow
                else self.entity_view.player_action_timer
            ) + dt
            if is_arrow and self.entity_view.pending_enemy_hit_at is not None:
                contact_ms = self.entity_view.pending_enemy_hit_at
            if self.entity_view.player_action != action:
                self._pending_contact_sound = None
            elif animation_ms >= contact_ms:
                self._pending_contact_sound = None
                is_charge = action == "Investida"
                remaining = contact_ms + (350 if is_arrow else 450 if is_charge else 160) - animation_ms
                if remaining > 0:
                    if is_arrow:
                        arrow_impact_duration = remaining
                    else:
                        self.play_ui_sound(
                            "gameplay.attack.charge_impact" if is_charge else "gameplay.attack.punch",
                            volume=1.0 if is_charge else 0.6, maxtime=remaining,
                        )
        ready_enemy_audio = []
        pending_enemy_audio = []
        for name, action, is_attack, when, sound_id in getattr(self, "_pending_enemy_audio", []):
            view = self.entity_view
            active = (
                self.engine.enemy.name.lower() == name
                and view.enemy_attack_name == name
                and view.enemy_action == action
                and (view.attacker == "enemy" if is_attack else view.attacker != "enemy")
            )
            if not active:
                continue
            elapsed = (view.attack_timer if is_attack else view.enemy_action_timer) + dt
            duration = view.enemy_attack_duration if is_attack else view.enemy_action_duration
            if elapsed < when:
                pending_enemy_audio.append((name, action, is_attack, when, sound_id))
            else:
                remaining = when + SOUND_WINDOWS_MS.get(sound_id, 450) - elapsed
                if remaining > 0 and elapsed <= duration:
                    ready_enemy_audio.append((sound_id, remaining))
        self._pending_enemy_audio = pending_enemy_audio
        self.engine.update_message(dt)
        self.entity_view.update(dt)
        for sound_id, remaining in ready_enemy_audio:
            self.play_ui_sound(sound_id, volume=0.85, maxtime=remaining)
        if arrow_impact_duration is not None:
            self.play_ui_sound("gameplay.attack.arrow_impact", maxtime=arrow_impact_duration)
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
                self.floating_texts.spawn(
                    kwargs["x"], kwargs["y"], kwargs["text"], kwargs["color"]
                )
        self._boss_events = pending_boss
        impact = (
            self.entity_view.enemy_attack_duration
            * self.entity_view.enemy_impact_fraction
        )
        if self.entity_view.attacker != "enemy" or self._boss_clock >= impact:
            self._boss_player_snapshot = None
        pending = []
        text_offsets = {}
        for when, event_name, kwargs in self._ultimate_events:
            if self._ultimate_clock < when:
                pending.append((when, event_name, kwargs))
            elif event_name == "floating_text":
                key = (kwargs["x"], kwargs["y"])
                offset = text_offsets.get(key, 0)
                self.floating_texts.spawn(
                    kwargs["x"], kwargs["y"] - offset, kwargs["text"], kwargs["color"]
                )
                text_offsets[key] = offset + 35
        self._ultimate_events = pending
        spec = ULTIMATE_ANIMATIONS.get(self.entity_view.player_action)
        if spec is None or self._ultimate_clock >= spec.duration * spec.impact:
            self._ultimate_enemy_snapshot = None
        self._update_status_audio(dt)
        self._update_outcome(dt)

        # The finishing card/ultimate completes before the supplied eight-frame fall.
        if self.engine.state == "boss_transition":
            if (
                self._phase_transition_pending
                and self.entity_view.player_action is None
                and self.entity_view.attacker is None
            ):
                self._phase_transition_pending = False
                self.entity_view.enemy_action = None
                self.entity_view.enemy_flash = 0
                self.entity_view.pending_enemy_hit_at = None
                self.entity_view.phase_transition_timer = 0
                self.play_ui_sound("gameplay.attack.charge_impact", volume=0.45)
            if (
                self.entity_view.phase_transition_timer is not None
                and self.entity_view.phase_transition_timer >= TRANSITION_MS
            ):
                self.engine.finish_boss_transition()

        # ----------------------------------------------------
        # Turno do Inimigo
        # ----------------------------------------------------
        if self.engine.state == "enemy_turn":
            self.enemy_turn_timer += dt
            enemy = self.engine.enemy
            # No combo do Corpo Seco, a segunda ação começa pouco após
            # a primeira animação terminar, sem outra pausa longa.
            combo_followup = getattr(enemy, "actions_per_turn", 1) > 1 and getattr(
                self.engine, "enemy_actions_remaining", 0
            ) < getattr(enemy, "actions_per_turn", 1)
            windup_ms = self._enemy_windup_ms(combo_followup)
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
        if getattr(self, 'map_mode', False):
            self._persist_logical_state()

    def _reset_outcome(self):
        self._outcome_elapsed = None
        self._fall_elapsed = None
        self._reward_gold = 0
        self._status_audio = ()
        self.entity_view.reset_enemy_defeat()
        if hasattr(self, "reward_view"):
            self.reward_view = PostCombatRewardView(self.asset_manager)

    def _update_status_audio(self, dt):
        view = self.entity_view
        sounds = {
            "poison": ("gameplay.status.poison_tick", 0.60),
            "bleed": ("gameplay.status.bleed_tick", 1.0),
            "shock": ("gameplay.status.shock_tick", 1.0),
            "burn": ("gameplay.status.burn_tick", 1.0),
        }
        waiting = []
        for status, target, damage, remaining in self._status_audio:
            if status == "bleed" and (
                (target == "player" and view.pending_enemy_hit_at is not None)
                or (target == "enemy" and view.pending_player_hit_at is not None)
            ):
                waiting.append((status, target, damage, remaining))
                continue
            if status == "bleed":
                remaining = self.BLEED_FEEDBACK_DELAY_MS if remaining is None else remaining - dt
                if remaining > 0:
                    waiting.append((status, target, damage, remaining))
                    continue
                if damage is not None:
                    if target == "player":
                        self.engine.spawn_player_text(f"Sangramento -{damage}", RED)
                    else:
                        self.engine.spawn_enemy_text(f"Sangramento -{damage}", RED)
            if status == "poison":
                view.trigger_flash(target)
            sound_id, volume = sounds[status]
            self.play_ui_sound(sound_id, volume=volume)
        self._status_audio = tuple(waiting)

    def _update_outcome(self, dt):
        state = self.engine.state
        if state not in ("victory", "game_over"):
            return
        if self._outcome_elapsed is not None:
            previous = self._outcome_elapsed
            self._outcome_elapsed += dt
            if (state == "victory" and self._reward_gold
                    and previous < self.VICTORY_POSE_MS <= self._outcome_elapsed):
                self.play_ui_sound("gameplay.reward_gold", volume=0.45)
            return
        view = self.entity_view
        if view.player_action is not None or view.attacker is not None:
            return
        if state == "game_over":
            self._outcome_elapsed = 0
            self.play_ui_sound("gameplay.game_over")
            return
        if view.pending_enemy_hit_at is not None or view.enemy_flash > 0:
            return
        bat = self.engine.enemy.name.lower() == "morcego sombrio"
        fall_progress = view.enemy_fall_progress or 0
        if self._fall_elapsed is None:
            self._fall_elapsed = 0
            if not bat:
                self.play_ui_sound("gameplay.attack.charge_impact", volume=0.45)
        else:
            self._fall_elapsed += dt
        done = view.advance_enemy_defeat(self.engine.enemy, self._fall_elapsed, self.ENEMY_FALL_MS)
        if bat and fall_progress < view.BAT_LANDING_FRACTION <= view.enemy_fall_progress:
            self.play_ui_sound("gameplay.attack.charge_impact", volume=0.45)
        if not done:
            return
        self._outcome_elapsed = 0
        if self.victory_sound:
            self.play_ui_sound(self.victory_sound)

    def _persist_logical_state(self):
        """Salva só quando a consequência lógica mudou, nunca por quadro visual."""
        if not self.save_manager or not self.save_data or self.engine.is_replay:
            return True
        if self.engine.state == 'phase_complete':
            return True
        if self.engine.state == 'game_over':
            if self.save_data['progresso'].get('estado') == 'morta':
                self._save_failed = False
                return True
            ok, message = self.save_manager.end_run(self.save_data, self.engine.level)
            self._save_failed = not ok
            if not ok:
                self.engine.show_message(message, 6000)
            return ok
        from src.systems.combat_snapshot import capture
        from src.systems.roguelite import transact
        signature = capture(self.engine, include_random=False)
        if signature == self._logical_saved:
            return True
        def mutate():
            self.save_manager.update_from_game(self.save_data, self.engine.player,
                                               self.engine.deck_manager)
            p = self.save_data['progresso']
            if self.engine.state == 'victory':
                from src.systems.campaign_progress import confirm_victory
                confirm_victory(self.save_data, self.engine)
            p['combat_snapshot'] = capture(self.engine)
            p['retomada_legada'] = False
            return 'Combate salvo.'
        ok, message = transact(self.save_manager, self.save_data, mutate)
        self.engine.run_progress = self.save_data['progresso']
        self._save_failed = not ok
        if ok:
            self._logical_saved = signature
        else:
            self.engine.show_message(f'Falha ao salvar; tente novamente: {message}', 6000)
        return ok

    def _draw_background(self, surface):
        bg = self.asset_manager.get_battle_background(
            self.selected_level or self.engine.level
        )
        if bg is not None:
            surface.blit(bg, (0, 0))
        else:
            surface.fill(BG)

        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((5, 11, 10, 35 if (self.selected_level or self.engine.level) == 7 else 135))
        surface.blit(shade, (0, 0))
        draw_vignette(surface, WIDTH, HEIGHT, alpha=88)

        ground = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.ellipse(
            ground, (0, 0, 0, 72), pygame.Rect(PLAYER_X - 138, 633, 270, 54)
        )
        pygame.draw.ellipse(
            ground, (0, 0, 0, 72), pygame.Rect(ENEMY_X - 129, 633, 255, 51)
        )
        surface.blit(ground, (0, 0))

    def _draw_energy_gems(
        self, surface, x, y, current, maximum, accent=(212, 170, 75), left_to_right=True
    ):
        step = 30
        for i in range(maximum):
            draw_x = x + i * step if left_to_right else x - i * step
            points = [
                (draw_x, y - 12),
                (draw_x + 11, y),
                (draw_x, y + 12),
                (draw_x - 11, y),
            ]
            active = i < current
            fill = accent if active else (39, 42, 51)
            border = (245, 222, 152) if active else (92, 94, 106)
            pygame.draw.polygon(surface, fill, points)
            pygame.draw.polygon(surface, border, points, 3)
            if active:
                pygame.draw.polygon(
                    surface,
                    (255, 241, 193),
                    [
                        (draw_x, y - 8),
                        (draw_x + 6, y - 2),
                        (draw_x, y + 5),
                        (draw_x - 6, y - 2),
                    ],
                )

    def _draw_energy_panel(self, surface, x, y, current, maximum, limit, align="left"):
        rect = pygame.Rect(x, y, 255, 36)
        draw_panel(
            surface,
            rect,
            fill=(13, 19, 18, 190),
            border=(126, 102, 58),
            radius=18,
            shadow=False,
        )
        if align == "left":
            self._draw_energy_gems(
                surface,
                rect.x + 24,
                rect.y + 18,
                current,
                limit,
                accent=(212, 170, 75),
                left_to_right=True,
            )
        else:
            self._draw_energy_gems(
                surface,
                rect.right - 24,
                rect.y + 18,
                current,
                limit,
                accent=(212, 170, 75),
                left_to_right=False,
            )

    def _ultimate_in_hand(self):
        return self.engine.ultimate_ready and self.engine.state in (
            "player_turn",
            "enemy_turn",
            "enemy_resolving",
        )

    def _get_battle_hand_rects(self):
        total = len(self.engine.hand) + (1 if self._ultimate_in_hand() else 0)
        return CardView.get_hand_rects(total)

    def _hand_card_at(self, position):
        if self.engine.state != "player_turn":
            return None
        rects = self._get_battle_hand_rects()
        for card, rect in zip(self.engine.hand, rects):
            if rect.collidepoint(position):
                return card
        if len(rects) > len(self.engine.hand) and rects[-1].collidepoint(position):
            return self.engine.ultimate
        return None

    def _draw_ultimate_hand_card(self, surface, rect, hovered=False):
        shadow = pygame.Surface((rect.width + 21, rect.height + 21), pygame.SRCALPHA)
        pygame.draw.rect(
            shadow, (0, 0, 0, 120), (11, 11, rect.width, rect.height), border_radius=21
        )
        surface.blit(shadow, (rect.x - 11, rect.y - 8))
        image = self.asset_manager.get_ultimate_image(
            self.engine.active_ultimate_id, energy_cost=self.engine.ultimate.energy_cost)
        draw_rect = rect.move(0, -18 if hovered else 0)
        if image is not None:
            fitted = image.get_rect().fit(draw_rect)
            scaled = pygame.transform.smoothscale(image, fitted.size)
            surface.blit(scaled, fitted)
        else:
            draw_panel(
                surface,
                draw_rect,
                fill=(16, 18, 28, 232),
                border=self.engine.active_ultimate_color,
                radius=18,
                shadow=False,
            )
            draw_text(
                surface,
                self.engine.active_ultimate_name.upper(),
                self.asset_manager.small_font,
                self.engine.active_ultimate_color,
                draw_rect.centerx,
                draw_rect.centery - 15,
                center=True,
            )
            for i, line in enumerate(
                wrap_text(
                    self.engine.active_ultimate_description,
                    self.asset_manager.small_font,
                    draw_rect.width - 24,
                )[:3]
            ):
                draw_text(
                    surface,
                    line,
                    self.asset_manager.small_font,
                    WHITE,
                    draw_rect.centerx,
                    draw_rect.centery + 15 + i * 21,
                    center=True,
                )
        glow = pygame.Surface(
            (draw_rect.width + 27, draw_rect.height + 27), pygame.SRCALPHA
        )
        pygame.draw.rect(
            glow,
            (*self.engine.active_ultimate_color, 70),
            (14, 14, draw_rect.width, draw_rect.height),
            border_radius=24,
            width=6,
        )
        surface.blit(glow, (draw_rect.x - 14, draw_rect.y - 14))

    def _draw_end_turn_button(self, surface, enabled=True):
        cx, cy = self.end_turn_rect.center
        radius = self.end_turn_rect.width // 2
        shadow = pygame.Surface((radius * 2 + 36, radius * 2 + 36), pygame.SRCALPHA)
        pygame.draw.circle(shadow, (0, 0, 0, 120), (radius + 18, radius + 18), radius)
        surface.blit(shadow, (cx - radius - 18, cy - radius - 12))
        outer_fill = (58, 43, 32) if enabled else (34, 34, 40)
        ring = (180, 144, 84) if enabled else (84, 84, 94)
        inner_fill = (104, 76, 54) if enabled else (53, 53, 60)
        pygame.draw.circle(surface, outer_fill, (cx, cy), radius)
        pygame.draw.circle(surface, ring, (cx, cy), radius, 5)
        pygame.draw.circle(surface, inner_fill, (cx, cy), radius - 15)
        pygame.draw.circle(surface, (229, 208, 162, 45), (cx, cy), radius - 26, 3)
        draw_text(
            surface,
            "FIM",
            self.asset_manager.small_font,
            WHITE if enabled else GRAY,
            cx,
            cy - 18,
            center=True,
        )
        draw_text(
            surface,
            "DO TURNO",
            self.asset_manager.small_font,
            WHITE if enabled else GRAY,
            cx,
            cy + 15,
            center=True,
        )

    def _draw_cemetery_book(self, surface, enabled=True):
        rect = self.cemetery_button_rect
        if self.asset_manager.get_ui_image("hud_cemetery") is not None:
            art_rect = pygame.Rect(
                rect.x - 5, rect.y - 23, rect.width + 9, rect.height - 18
            )
            self.battle_hud.art(surface, "hud_cemetery", art_rect)
            caption = pygame.Rect(rect.x - 11, rect.bottom - 48, rect.width + 21, 60)
            draw_panel(
                surface,
                caption,
                fill=(10, 14, 13, 235),
                border=(107, 83, 46),
                radius=6,
                shadow=False,
            )
            draw_text(
                surface,
                "CEMITÉRIO",
                self.asset_manager.small_font,
                WHITE if enabled else GRAY,
                rect.centerx,
                rect.bottom - 33,
                center=True,
            )
            draw_text(
                surface,
                "DESC 1 E",
                self.asset_manager.small_font,
                GOLD if enabled else GRAY,
                rect.centerx,
                rect.bottom - 8,
                center=True,
            )
            badge = pygame.Rect(rect.right - 35, rect.y + 2, 38, 36)
            theme.panel(surface, badge, fill=(15, 17, 16, 245))
            draw_text(
                surface,
                str(len(self.engine.discard_pile)),
                self.asset_manager.small_font,
                WHITE,
                badge.centerx,
                badge.centery,
                center=True,
            )
            return
        draw_panel(
            surface, rect, fill=(18, 21, 18, 228), border=(113, 92, 62), radius=18
        )
        inner = pygame.Rect(rect.x + 12, rect.y + 12, rect.width - 24, rect.height - 42)
        pygame.draw.rect(surface, (20, 18, 24), inner, border_radius=12)
        pygame.draw.rect(surface, (137, 108, 58), inner, 3, border_radius=12)
        line_x = inner.centerx
        pygame.draw.line(
            surface, (92, 76, 52), (line_x, inner.y + 9), (line_x, inner.bottom - 9), 3
        )
        draw_text(
            surface,
            "CEMITÉRIO",
            self.asset_manager.small_font,
            WHITE if enabled else GRAY,
            rect.centerx,
            rect.bottom - 42,
            center=True,
        )
        draw_text(
            surface,
            "DESC 1 E",
            self.asset_manager.small_font,
            GOLD if not self.engine.cemetery_swap_used else GRAY,
            rect.centerx,
            rect.bottom - 18,
            center=True,
        )
        badge = pygame.Rect(rect.right - 39, rect.y + 15, 27, 27)
        pygame.draw.rect(surface, (56, 44, 34), badge, border_radius=6)
        pygame.draw.rect(surface, (163, 132, 74), badge, 2, border_radius=6)
        draw_text(
            surface,
            str(len(self.engine.discard_pile)),
            self.asset_manager.small_font,
            WHITE,
            badge.centerx,
            badge.centery,
            center=True,
        )

    def _draw_ultimate_counter(self, surface, hand_rects):
        if hand_rects:
            left = hand_rects[0].x
            right = hand_rects[-1].right
            center_x = (left + right) // 2
        else:
            center_x = WIDTH // 2
        panel = pygame.Rect(center_x - 255, HEIGHT - 39, 510, 27)
        pygame.draw.rect(surface, (8, 10, 18), panel, border_radius=14)
        pygame.draw.rect(surface, (100, 84, 56), panel, 3, border_radius=14)
        fill_width = int(
            (panel.width - 6)
            * (self.engine.ultimate_charge / max(1, self.engine.ultimate_threshold))
        )
        if fill_width > 0:
            fill_rect = pygame.Rect(
                panel.x + 3, panel.y + 3, fill_width, panel.height - 6
            )
            pygame.draw.rect(
                surface, self.engine.active_ultimate_color, fill_rect, border_radius=11
            )
        label = (
            f"Ultimate: {self.engine.ultimate_charge}/{self.engine.ultimate_threshold}"
        )
        if self.engine.ultimate_ready:
            label = f"Ultimate pronta — custo {self.engine.ultimate.energy_cost} energia"
        draw_text(
            surface,
            label,
            self.asset_manager.small_font,
            WHITE,
            center_x,
            panel.centery,
            center=True,
        )

    def _draw_stat_chip(self, surface, x, y, label, value, color):
        rect = pygame.Rect(x, y, 162, 36)
        draw_panel(
            surface,
            rect,
            fill=(15, 22, 20, 220),
            border=(62, 68, 84),
            radius=15,
            shadow=False,
        )
        draw_text(
            surface,
            f"{label}: {value}",
            self.asset_manager.small_font,
            color,
            rect.centerx,
            rect.centery,
            center=True,
        )

    def _visible_enemy(self):
        """Mantém vida/escudo visuais anteriores até a onda atingir o alvo."""
        return self._ultimate_enemy_snapshot or self.engine.enemy

    def _visible_player(self):
        return self._boss_player_snapshot or self.engine.player

    def _draw_combatant_panel(
        self,
        surface,
        rect,
        name,
        hp,
        max_hp,
        bar_color,
        stats,
        title_color=WHITE,
        subtitle=None,
        align="left",
    ):
        if self.asset_manager.get_ui_image("hud_portrait") is not None:
            self.battle_hud.combatant(
                surface,
                rect,
                name,
                hp,
                max_hp,
                stats,
                enemy=align == "right",
                boss=bool(subtitle),
                combatant=self._visible_enemy()
                if align == "right"
                else self._visible_player(),
                mouse=self.window_manager.get_virtual_mouse_pos(),
            )
            return
        draw_panel(
            surface, rect, fill=(10, 17, 17, 228), border=(134, 112, 72), radius=27
        )
        title_y = rect.y + 15
        title_x = rect.x + 27 if align == "left" else rect.right - 27
        name_center = rect.x + rect.width // 2
        if subtitle:
            draw_text(
                surface,
                subtitle,
                self.asset_manager.small_font,
                GOLD,
                name_center,
                title_y,
                center=True,
            )
            title_y += 24
        name_font = self.asset_manager.menu_font
        label = boss_display_name(name) if align == "right" else name
        if name_font.size(label)[0] > rect.width - 42:
            name_font = self.asset_manager.small_font
        draw_text(
            surface, label, name_font, title_color, name_center, title_y + 8, center=True
        )
        draw_health_bar(
            surface,
            rect.x + 21,
            rect.y + 60,
            rect.width - 42,
            24,
            hp,
            max_hp,
            bar_color,
        )
        draw_text(
            surface,
            f"{hp}/{max_hp}",
            self.asset_manager.small_font,
            WHITE,
            rect.centerx,
            rect.y + 72,
            center=True,
        )

        chip_y = rect.y + 93
        if stats:
            if align == "left":
                for index, (label, value, color) in enumerate(stats[:2]):
                    self._draw_stat_chip(
                        surface, rect.x + 15 + index * 165, chip_y, label, value, color
                    )
            else:
                for index, (label, value, color) in enumerate(stats[:2]):
                    self._draw_stat_chip(
                        surface, rect.x + 15 + index * 165, chip_y, label, value, color
                    )

    def _draw_coin_badge(self, surface, x, y):
        badge_rect = pygame.Rect(x, y, 117, 42)
        draw_panel(
            surface,
            badge_rect,
            fill=(14, 16, 22, 210),
            border=(170, 138, 66),
            radius=18,
            shadow=False,
        )
        if self.asset_manager.coin_icon is not None:
            icon = pygame.transform.smoothscale(self.asset_manager.coin_icon, (24, 24))
            surface.blit(icon, (x + 12, y + 9))
        draw_text(
            surface,
            str(self.engine.player.coins - self._reward_gold),
            self.asset_manager.font,
            (255, 231, 110),
            x + 75,
            y + 21,
            center=True,
        )

    def _draw_ultimate_card(self, surface):
        card_rect = pygame.Rect(51, HEIGHT - 228, 144, 204)
        card_img = self.asset_manager.get_ultimate_image(
            self.engine.active_ultimate_id, energy_cost=self.engine.ultimate.energy_cost)
        if card_img is not None:
            fitted = card_img.get_rect().fit(card_rect)
            scaled = pygame.transform.smoothscale(card_img, fitted.size)
            surface.blit(scaled, fitted)
        else:
            draw_panel(
                surface,
                card_rect,
                fill=(10, 12, 18, 235),
                border=self.engine.active_ultimate_color,
                radius=18,
                shadow=False,
            )
            draw_text(
                surface,
                self.engine.active_ultimate_name,
                self.asset_manager.small_font,
                WHITE,
                card_rect.centerx,
                card_rect.centery,
                center=True,
            )

    def _draw_compact_energy(self, surface):
        pass

    def _draw_bottom_hud(self, surface):
        if self.battle_hud.art(
            surface, "hud_hand_tray", pygame.Rect(12, HEIGHT - 324, WIDTH - 24, 324)
        ):
            return
        frame = self.asset_manager.get_ui_image(
            "battle_hud_frame"
        ) or self.asset_manager.get_ui_image("battle_hud_frame_alt")
        base_y = HEIGHT - 243
        base_rect = pygame.Rect(0, base_y + 36, WIDTH, 207)
        base = pygame.Surface(base_rect.size, pygame.SRCALPHA)
        base.fill((10, 14, 14, 206))
        surface.blit(base, base_rect.topleft)
        if frame is not None:
            scaled = pygame.transform.scale(frame, (WIDTH, 213))
            surface.blit(scaled, (0, base_y))
            darken = pygame.Surface((WIDTH, 213), pygame.SRCALPHA)
            darken.fill((0, 0, 0, 18))
            surface.blit(darken, (0, base_y))
        pygame.draw.line(
            surface, (114, 94, 58), (0, base_y + 45), (WIDTH, base_y + 45), 2
        )
        pygame.draw.line(
            surface, (52, 46, 36), (0, base_y + 47), (WIDTH, base_y + 47), 2
        )
        mid = WIDTH // 2
        pygame.draw.polygon(
            surface,
            (156, 127, 78),
            [
                (mid, base_y + 36),
                (mid + 11, base_y + 45),
                (mid, base_y + 54),
                (mid - 11, base_y + 45),
            ],
        )

    def _draw_action_button(
        self, surface, rect, label, fill, border, text_color=WHITE, enabled=True
    ):
        hovered = enabled and rect.collidepoint(
            self.window_manager.get_virtual_mouse_pos()
        )
        shadow = pygame.Surface((rect.width + 15, rect.height + 15), pygame.SRCALPHA)
        pygame.draw.rect(
            shadow, (0, 0, 0, 80), (9, 9, rect.width, rect.height), border_radius=18
        )
        surface.blit(shadow, (rect.x - 9, rect.y - 6))
        button_fill = tuple(min(255, c + 16) for c in fill) if hovered else fill
        pygame.draw.rect(surface, button_fill, rect, border_radius=18)
        pygame.draw.rect(surface, border, rect, 3, border_radius=18)
        inner = pygame.Rect(rect.x + 5, rect.y + 5, rect.width - 9, rect.height - 9)
        pygame.draw.rect(surface, (255, 255, 255, 18), inner, 2, border_radius=15)
        font = (
            self.asset_manager.menu_font
            if rect.height <= 51
            else self.asset_manager.font
        )
        draw_text(
            surface, label, font, text_color, rect.centerx, rect.centery, center=True
        )

    def draw(self, surface):
        if self.boss_dialogue is not None:
            self.boss_dialogue.draw(surface)
            return
        self._draw_background(surface)

        player = self._visible_player()
        enemy = self._visible_enemy()
        if getattr(player, "invulnerable", False) and not self.engine.message:
            draw_text(
                surface,
                "LABORATÓRIO · VIDA INFINITA",
                self.asset_manager.small_font,
                GOLD,
                WIDTH // 2,
                44,
                center=True,
            )
        enemy_color = WHITE
        if enemy.intent:
            if enemy.intent == "attack":
                enemy_color = (200, 90, 90)
            else:
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
        if getattr(enemy, "weak_turns", 0) > 0:
            enemy_stats.append(("Fraqueza", enemy.weak_turns, (125, 205, 120)))
        if not enemy_stats:
            enemy_stats.append(("Status", "Pronto", GRAY))

        player_rect = pygame.Rect(33, 30, 585, 138)
        enemy_rect = pygame.Rect(1185, 30, 555, 138)
        self._draw_combatant_panel(
            surface,
            player_rect,
            player.name,
            player.hp,
            player.max_hp,
            GREEN,
            player_stats,
            align="left",
        )
        self._draw_energy_panel(
            surface,
            54,
            234,
            self.engine.energy,
            self.engine.energy_max,
            self.engine.player.MAX_ENERGY_LIMIT,
            align="left",
        )
        self._draw_coin_badge(surface, 54, 279)

        self._draw_combatant_panel(
            surface,
            enemy_rect,
            enemy.name,
            enemy.hp,
            enemy.max_hp,
            RED,
            enemy_stats,
            title_color=GOLD if enemy.is_miniboss else WHITE,
            subtitle="BOSS FINAL"
            if getattr(enemy, "is_final_boss", False)
            else "MINIBOSS"
            if enemy.is_miniboss
            else None,
            align="right",
        )

        self.window_manager.draw_fullscreen_button(self.asset_manager.small_font)
        self._draw_menu_button(surface)

        draw_ultimate_fx(surface, self.entity_view, behind=True)
        draw_boss_ultimate_fx(surface, self.entity_view, behind=True)
        self.entity_view.draw_enemy(surface, enemy, enemy_color)
        player_pose = self.engine.state
        if player_pose == "victory" and self._outcome_elapsed is None:
            player_pose = "player_turn"
        self.entity_view.draw_player(surface, player_pose)
        self.entity_view.draw_enemy_projectile(surface)
        draw_player_projectile(surface, self.entity_view)
        draw_ultimate_fx(surface, self.entity_view)
        draw_boss_ultimate_fx(surface, self.entity_view)
        self.intent_view.draw(
            surface, self.engine, self.window_manager.get_virtual_mouse_pos()
        )

        self._draw_bottom_hud(surface)
        self._draw_cemetery_button(surface)

        hand_rects = []
        self.ultimate_hand_rect = None
        if self.engine.state in (
            "player_turn",
            "enemy_turn",
            "enemy_resolving",
            "boss_transition",
        ):
            mouse_pos = self.window_manager.get_virtual_mouse_pos()
            hand_rects = self._get_battle_hand_rects()
            normal_count = len(self.engine.hand)
            normal_rects = hand_rects[:normal_count]
            for rect, card in zip(normal_rects, self.engine.hand):
                hovered = rect.collidepoint(mouse_pos) and (
                    self.engine.state == "player_turn"
                )
                CardView.draw_card(surface, rect, card, self.asset_manager, hovered)
                if card.name == 'Surto de Energia' and self.engine.state == 'player_turn':
                    from src.models.effects.tactical_card_effect import next_turn_energy_gain
                    gain = next_turn_energy_gain(self.engine.player, card.value)
                    badge = pygame.Rect(rect.x + 3, rect.y + 35, rect.width - 6, 28)
                    pygame.draw.rect(surface, (20, 22, 30), badge, border_radius=5)
                    draw_text(surface, 'SEM GANHO' if gain == 0 else f'+{gain} PRÓX.',
                              self.asset_manager.small_font, RED if gain == 0 else GOLD,
                              badge.centerx, badge.centery, center=True)
            if self._ultimate_in_hand() and hand_rects:
                self.ultimate_hand_rect = hand_rects[-1]
                hovered = self.ultimate_hand_rect.collidepoint(mouse_pos) and (
                    self.engine.state == "player_turn"
                )
                self._draw_ultimate_hand_card(surface, self.ultimate_hand_rect, hovered)
            self._draw_ultimate_counter(surface, hand_rects)

        can_end = (
            self.engine.state == "player_turn"
            and self.entity_view.player_action is None
        )
        self._draw_end_turn_button(surface, enabled=can_end)

        self.floating_texts.draw(surface, self.asset_manager.font)
        self.coin_hud.draw_particles(surface)

        mouse = self.window_manager.get_virtual_mouse_pos()
        for rect, card in zip(hand_rects, self.engine.hand):
            if rect.collidepoint(mouse):
                CardView.draw_tooltip(surface, card, self.asset_manager, mouse)
                break
        if self.ultimate_hand_rect and self.ultimate_hand_rect.collidepoint(mouse):
            CardView.draw_tooltip(
                surface,
                self.engine.ultimate,
                self.asset_manager,
                mouse,
                cost_label=f"{self.engine.ultimate.energy_cost} E",
            )

        self._draw_top_message(surface)
        self.intent_view.draw_tooltip(
            surface, self.window_manager.get_virtual_mouse_pos()
        )

        if self._game_over_ready:
            self._draw_game_over(surface)
        if self._victory_ready:
            self._draw_victory(surface)
        elif (self.engine.state == "victory" and self.victory_sound
              and self._outcome_elapsed is not None
              and self._outcome_elapsed >= self.VICTORY_BANNER_MS):
            self._draw_victory_banner(surface)
        if self.engine.state == "phase_complete":
            self._draw_pending_save(surface)

    def _draw_top_message(self, surface):
        """Aviso transitório do topo: ultimate do inimigo ou mensagem do combate."""
        enemy = self.engine.enemy
        if (
            getattr(enemy, "boss_id", None) == "alvaro_tex"
            and self.entity_view.attacker == "enemy"
            and self.entity_view.enemy_action == enemy.special_action.visual_effect
        ):
            self._draw_message_box(
                surface,
                enemy.special_action.name.upper(),
                GOLD,
                fill=(18, 29, 15, 235),
                border=(154, 172, 66),
                radius=15,
                top=177,
            )
        elif self.entity_view.enemy_ultimate:
            special = self.entity_view.enemy_ultimate
            self._draw_message_box(
                surface,
                special.title.upper(),
                special.color,
                fill=(12, 14, 20, 235),
                border=special.color,
                radius=15,
            )
        elif self.engine.message:
            self._draw_message_box(
                surface,
                self.engine.message,
                WHITE,
                fill=(36, 14, 18, 235),
                border=(168, 86, 86),
                radius=18,
                top=177 if getattr(enemy, "boss_id", None) == "alvaro_tex" else 39,
            )

    def _draw_message_box(self, surface, text, color, fill, border, radius, top=39):
        """Caixa de aviso no topo: quebra o texto na largura útil e cresce para baixo."""
        font = self.asset_manager.font
        width, min_height, pad_x, pad_y = 690, 60, 27, 9
        lines = wrap_text(text, font, width - pad_x * 2) or [""]
        line_h = font.get_linesize()
        height = max(min_height, len(lines) * line_h + pad_y * 2)
        msg_rect = pygame.Rect(WIDTH // 2 - width // 2, top, width, height)
        draw_panel(surface, msg_rect, fill=fill, border=border, radius=radius)
        first_center = msg_rect.centery - (len(lines) - 1) * line_h / 2
        for i, line in enumerate(lines):
            draw_text(
                surface,
                line,
                font,
                color,
                msg_rect.centerx,
                first_center + i * line_h,
                center=True,
            )

    def _draw_cemetery_button(self, surface):
        """Desenha o botão de acesso ao Cemitério durante a partida."""
        is_player_turn = self.engine.state == "player_turn"
        can_use = self.engine.can_use_cemetery() or self.engine.can_swap_cemetery()
        self._draw_cemetery_book(surface, enabled=is_player_turn and can_use)

    def _draw_ultimate_bar(self, surface):
        ready = self.engine.ultimate_ready
        panel_rect = pygame.Rect(30, HEIGHT - 354, 321, 153)
        accent = self.engine.active_ultimate_color
        draw_panel(
            surface, panel_rect, fill=(16, 17, 28, 226), border=accent, radius=24
        )
        draw_text(
            surface,
            self.engine.active_ultimate_name.upper(),
            self.asset_manager.small_font,
            accent,
            panel_rect.x + 24,
            panel_rect.y + 18,
        )
        draw_text(
            surface,
            self.engine.active_ultimate_description,
            self.asset_manager.small_font,
            (167, 174, 187),
            panel_rect.x + 24,
            panel_rect.y + 51,
        )
        bar_x, bar_y, bar_w, bar_h = (
            panel_rect.x + 24,
            panel_rect.y + 87,
            panel_rect.width - 48,
            24,
        )
        draw_health_bar(
            surface,
            bar_x,
            bar_y,
            bar_w,
            bar_h,
            self.engine.ultimate_charge,
            self.engine.ultimate_threshold,
            accent,
        )
        draw_text(
            surface,
            f"Carga {self.engine.ultimate_charge}/{self.engine.ultimate_threshold}",
            self.asset_manager.small_font,
            WHITE,
            panel_rect.centerx,
            bar_y + 45,
            center=True,
        )

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
        self._draw_action_button(
            surface,
            self.ultimate_button_rect,
            label,
            fill,
            border,
            text_color=text_color,
            enabled=can_click,
        )

    def _draw_menu_button(self, surface):
        hovered = self.menu_button_rect.collidepoint(
            self.window_manager.get_virtual_mouse_pos()
        )
        theme.button(
            surface,
            self.menu_button_rect,
            "MENU",
            self.asset_manager.small_font,
            hover=hovered,
            prominent=False,
            enabled=True,
        )

    def _draw_game_over(self, surface):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(210)
        overlay.fill(BLACK)
        surface.blit(overlay, (0, 0))

        if not hasattr(self, "_defeat_banner"):
            crest = self.asset_manager.get_service_image("rewards/victory_crest")
            self._defeat_banner = build_outcome_banner(self.asset_manager.title_font, crest, defeat=True)
        rise = min(1.0, self._outcome_elapsed / 220)
        self._defeat_banner.set_alpha(round(255 * rise))
        center = (WIDTH // 2, HEIGHT // 2 - 180 + round(23 * (1 - rise) ** 2))
        surface.blit(self._defeat_banner, self._defeat_banner.get_rect(center=center))

        draw_text(
            surface,
            "VOCÊ PERDEU",
            self.asset_manager.big_font,
            RED,
            WIDTH // 2,
            HEIGHT // 2 - 30,
            center=True,
        )
        draw_text(
            surface,
            f"Você chegou até o andar {self.engine.level}",
            self.asset_manager.font,
            WHITE,
            WIDTH // 2,
            HEIGHT // 2 + 30,
            center=True,
        )
        draw_text(
            surface,
            "A run terminou. Fragmentos e melhorias permanentes foram preservados."
            if self.map_mode
            else "Pressione R para reiniciar",
            self.asset_manager.font,
            WHITE,
            WIDTH // 2,
            HEIGHT // 2 + 90,
            center=True,
        )
        if self.map_mode:
            self._draw_action_button(surface, self.new_run_rect, 'PREPARAR NOVA RUN',
                                     (55, 57, 63), GOLD, text_color=WHITE)

    def _draw_victory_banner(self, surface):
        elapsed = self._outcome_elapsed - self.VICTORY_BANNER_MS
        rise = min(1.0, elapsed / 220)
        center_y = 250 + round(24 * (1 - rise) ** 2)
        if not hasattr(self, "_victory_banner"):
            crest = self.asset_manager.get_service_image("rewards/victory_crest")
            self._victory_banner = build_outcome_banner(self.asset_manager.title_font, crest)
        banner = self._victory_banner
        banner.set_alpha(round(255 * rise))
        center = (WIDTH // 2, center_y)
        draw_victory_embers(surface, center, elapsed, rise)
        surface.blit(banner, banner.get_rect(center=center))

    def _reward_progress(self):
        if self.map_mode and self.save_data:
            return self.save_data["progresso"]
        return None

    def _draw_victory(self, surface):
        self.reward_view.draw(surface, self.engine, self._reward_progress(), self._reward_gold,
                              self.window_manager.get_virtual_mouse_pos())

    def _commit_reward(self, choice):
        kind, value = choice
        if kind == "card":
            self.engine.choose_reward(value)
        elif kind == "material":
            self.engine.choose_material(value)
        else:
            self.engine.skip_reward()

    def _draw_pending_save(self, surface):
        """Recuperação caso falhe a gravação do desbloqueio após a vitória."""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((7, 6, 14, 224))
        surface.blit(overlay, (0, 0))
        draw_text(
            surface,
            "FASE CONCLUÍDA",
            self.asset_manager.big_font,
            GOLD,
            WIDTH // 2,
            HEIGHT // 2 - 98,
            center=True,
        )
        draw_text(
            surface,
            "Não foi possível gravar seu progresso.",
            self.asset_manager.font,
            WHITE,
            WIDTH // 2,
            HEIGHT // 2,
            center=True,
        )
        draw_text(
            surface,
            "Pressione R para tentar salvar novamente.",
            self.asset_manager.font,
            WHITE,
            WIDTH // 2,
            HEIGHT // 2 + 78,
            center=True,
        )
        if self.engine.message:
            draw_text(
                surface,
                self.engine.message[:90],
                self.asset_manager.small_font,
                RED,
                WIDTH // 2,
                HEIGHT // 2 + 153,
                center=True,
            )

    def handle_event(self, event):
        if getattr(self, 'map_mode', False) and self._game_over_ready:
            restart = (event.type == pygame.KEYDOWN and event.key == pygame.K_r)
            restart = restart or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.new_run_rect.collidepoint(self.window_manager.map_to_virtual(event.pos)))
            if restart:
                if self._persist_logical_state():
                    self._return_to_map()
                return
        if getattr(self, 'map_mode', False) and getattr(self, '_save_failed', False):
            self._persist_logical_state()
            return
        # Trata atalho de tela cheia ou redimensionamento
        if self.window_manager.handle_window_event(event):
            return
        if self._victory_ready:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                position = self.window_manager.map_to_virtual(event.pos)
                choice = self.reward_view.click(position, self.engine, self._reward_progress())
                if choice:
                    self.reward_view.confirm(choice)
                    self.play_ui_sound("ui.confirm")
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and not self.reward_view.pending:
                self._open_menu_confirmation()
            return
        if self.boss_dialogue is not None:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._open_menu_confirmation()
                return
            self.boss_dialogue.handle_event(event)
            if self.boss_dialogue.finished:
                self.boss_dialogue = None
            return
        if event.type == pygame.MOUSEMOTION:
            hovered_card = self._hand_card_at(self.window_manager.map_to_virtual(event.pos))
            if (
                hovered_card is not None
                and hovered_card is not getattr(self, "_hovered_hand_card", None)
            ):
                now = pygame.time.get_ticks()
                if now - getattr(self, "_last_card_hover_sound_at", -120) >= 120:
                    self.play_ui_sound("gameplay.card_hover")
                    self._last_card_hover_sound_at = now
            self._hovered_hand_card = hovered_card

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
            if (
                self.engine.state == "player_turn"
                and self.entity_view.player_action is None
            ):
                if self.cemetery_button_rect.collidepoint(virt_pos):
                    self.play_ui_sound("ui.click")
                    self._open_cemetery_modal()
                    return

                hand_rects = self._get_battle_hand_rects()
                normal_count = len(self.engine.hand)
                if self._ultimate_in_hand() and hand_rects:
                    ultimate_rect = hand_rects[-1]
                    if ultimate_rect.collidepoint(virt_pos):
                        if self.engine.activate_ultimate():
                            self.play_ui_sound("gameplay.ultimate_activate")
                            self._hovered_hand_card = self._hand_card_at(virt_pos)
                        return
                    hand_rects = hand_rects[:normal_count]

                for index, rect in enumerate(hand_rects[:normal_count]):
                    if rect.collidepoint(virt_pos):
                        self.engine.play_card(index)
                        self._hovered_hand_card = self._hand_card_at(virt_pos)
                        return

                if self.end_turn_rect.collidepoint(virt_pos):
                    self.engine.end_turn()
                    self.play_ui_sound("gameplay.turn_end")
                    return

        elif event.type == pygame.KEYDOWN:
            # Reiniciar partida em Game Over
            if event.key == pygame.K_r and self.engine.state == "phase_complete":
                self._finalize_map_phase(self.engine.level)
                return
            if (
                event.key == pygame.K_r
                and self._game_over_ready
            ):
                self.engine = CombatEngine(
                    on_event_callback=self._handle_combat_event,
                    map_mode=self.map_mode,
                )
                if self.save_manager is not None and self.save_data is not None:
                    try:
                        self.save_data = self.save_manager.load_save(
                            self.save_data["id"]
                        )
                        self.engine.resume_from_save(
                            self.save_data,
                            self.save_manager,
                            level=self.selected_level if self.map_mode else None,
                            encounter_kind=self.encounter_kind,
                            encounter_index=self.encounter_index,
                        )
                    except (OSError, SaveError) as exc:
                        # Falha explícita em vez de sobrescrever um save danificado.
                        self.engine.show_message(f"Não foi possível carregar: {exc}")
                self.coin_hud = CoinHUD(self.engine.player, anchor_x=99, anchor_y=153)
                self.energy_hud = EnergyHUD(self.engine.player)
                self.entity_view = EntityView(self.asset_manager)
                self._reset_outcome()
                self.floating_texts.clear()
                self.enemy_turn_timer = 0

            # Tecla C para atalho rápido do Cemitério durante o turno do jogador
            elif event.key == pygame.K_c and self.engine.state == "player_turn":
                self.play_ui_sound("ui.click")
                self._open_cemetery_modal()

            # ESC para abrir menu de confirmação
            elif event.key == pygame.K_ESCAPE and self.engine.state in (
                "player_turn",
                "enemy_turn",
                "enemy_resolving",
                "boss_transition",
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
        """Abre o menu de pausa da batalha (mesmo atalho do botão MENU e do Esc)."""
        if self.engine.state == "phase_complete":
            self._finalize_map_phase(self.engine.level)
            return
        pause = PauseMenuModal(
            self.scene_manager,
            self.window_manager,
            self.asset_manager,
            on_options=self._open_options_modal,
            on_exit=self._open_leave_confirmation,
            exit_label=(
                "VOLTAR AO MAPA"
                if getattr(self, "map_mode", False)
                else "MENU PRINCIPAL"
            ),
        )
        self.play_ui_sound("ui.click")
        self.scene_manager.push_modal(pause)

    def _open_options_modal(self):
        from src.scenes.options_scene import OptionsScene

        self.scene_manager.push_modal(
            OptionsScene(
                self.scene_manager,
                self.window_manager,
                self.asset_manager,
                modal=True,
            )
        )

    def _open_leave_confirmation(self):
        if self.engine.state == "victory":
            message = "Escolha sua recompensa antes de sair para salvar a vitória."
        elif self.engine.state == "game_over":
            message = "Seu último checkpoint continuará disponível."
        else:
            message = "Seu progresso será salvo antes de sair."
        leaving_to_map = getattr(self, "map_mode", False)
        modal = ConfirmationModal(
            self.scene_manager,
            self.window_manager,
            self.asset_manager,
            on_confirm=self._return_to_main_menu,
            title="VOLTAR AO MAPA?" if leaving_to_map else "VOLTAR AO MENU?",
            message=message,
            confirm_label="SIM, VOLTAR",
        )
        self.play_ui_sound("ui.click")
        self.scene_manager.push_modal(modal)

    def _enemy_speed(self):
        if self.preferences is None:
            return ENEMY_SPEED_NORMAL
        return self.preferences.get("enemy_speed")

    def _enemy_windup_ms(self, combo_followup=False):
        return enemy_windup_ms(self._enemy_speed(), combo_followup)

    def _damage_numbers_enabled(self):
        if self.preferences is None:
            return True
        return bool(self.preferences.get("damage_numbers"))

    def _save_progress(self):
        """Registra um checkpoint do andar atual sem modificar outro slot."""
        if self.save_manager is None or self.save_data is None:
            return True
        if self.map_mode:
            return self._persist_logical_state()
        # Se o herói morreu, mantém o último checkpoint: nunca grava HP zero.
        # Em phase_complete, "_finalize_map_phase"/"record_*" gravam a vitória;
        # regravar aqui causaria desbloqueio duplicado. No estado de vitória,
        # grava apenas a vida do fim do combate — nunca a recompensa nem o
        # avanço de território (ainda pendente de escolha do jogador).
        if self.engine.state in ("game_over", "phase_complete"):
            return True
        try:
            self.coin_hud.collect_pending_coins()
            self.save_manager.update_from_game(
                self.save_data,
                self.engine.player,
                self.engine.deck_manager,
                level=max(self.engine.level, self.save_data["progresso"]["andar"])
                if self.map_mode
                else self.engine.level,
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
        final_boss = self.encounter_kind == "point" and level == TERRITORIES[-1].level
        if self.engine.is_replay:
            if final_boss and is_test_save(self.save_data):
                self._show_final_cutscene()
            else:
                self._return_to_map()
            return
        try:
            recorder = (
                record_road_victory if self.encounter_kind == "road" else record_victory
            )
            recorder(
                self.save_manager,
                self.save_data,
                self.engine,
                self.coin_hud.collect_pending_coins,
            )
        except (OSError, ValueError, SaveError) as exc:
            self.engine.show_message(f"Erro ao salvar: {exc}", duration=6000)
            return
        if final_boss:
            self._show_final_cutscene()
        else:
            self._return_to_map()

    def _show_final_cutscene(self):
        from src.config.cutscenes import FINAL_CUTSCENE
        from src.scenes.cutscene_scene import CutsceneScene

        self.scene_manager.change_scene(
            CutsceneScene(
                self.scene_manager,
                self.window_manager,
                self.asset_manager,
                scenes=FINAL_CUTSCENE,
                next_scene_factory=self._make_map_scene,
            )
        )

    def _make_map_scene(self):
        from src.scenes.map_scene import MapScene

        return MapScene(
            self.scene_manager,
            self.window_manager,
            self.asset_manager,
            self.save_manager,
            self.save_data,
        )

    def _return_to_map(self):
        self.scene_manager.change_scene(self._make_map_scene())

    def save_on_exit(self):
        """Salva ao fechar a janela, inclusive após um desbloqueio pendente."""
        if self.engine.state == "victory" and self.reward_view.pending:
            self._commit_reward(self.reward_view.take_confirmation())
            if self.scene_manager.current_scene is not self:
                return True
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
            self.play_ui_sound("ui.confirm")
            from src.scenes.menu_scene import MenuScene

            self.scene_manager.change_scene(
                MenuScene(self.scene_manager, self.window_manager, self.asset_manager)
            )
