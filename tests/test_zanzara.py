"""Boss final, amuleto restaurador, projéteis e conclusão do Santuário."""
import os
import unittest
from unittest.mock import MagicMock
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
from src.systems.enemy_factory import create_zanzara, create_point_enemy, create_road_enemy, choose_next_action
from src.systems.combat_engine import CombatEngine
from src.core.asset_manager import AssetManager
from src.ui.entity_view import EntityView
from src.config.layout import ENEMY_X, PLAYER_X
from src.systems.boss_ultimate_animations import BOSS_ULTIMATE_ANIMATIONS


class ZanzaraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.assets = AssetManager()

    def test_final_boss_occupies_only_the_final_point(self):
        boss = create_point_enemy(7)
        self.assertEqual(boss.name, 'Zanzara')
        self.assertEqual(boss.boss_id, 'zanzara')
        self.assertTrue(boss.is_final_boss)
        self.assertTrue(boss.is_miniboss)
        self.assertEqual(boss.max_hp, 190)
        self.assertEqual(boss.actions_per_turn, 2)
        for level in range(1, 7):
            self.assertNotEqual(create_point_enemy(level).name, 'Zanzara')
        self.assertNotEqual(create_road_enemy(7).name, 'Zanzara')

    def test_no_old_amulet_and_current_skill_names(self):
        boss = create_zanzara()
        self.assertEqual(len(boss.actions),3)
        self.assertEqual(boss.actions[2].status_effect,('vulnerable',2,25))
        self.assertFalse(any(a.action_type == 'buff' for a in boss.actions))

    def test_passo_teleports_and_chains_use_target_effect(self):
        from unittest.mock import patch
        from src.config.layout import APPROACH_GAP
        from src.ui.zanzara_necromancer import actor_x
        for action in ('atk2','atk3'):
            view = EntityView(self.assets)
            view.trigger_attack('enemy',action,'Zanzara')
            view.attack_timer=view.enemy_attack_duration*view.enemy_impact_fraction
            target = PLAYER_X+APPROACH_GAP if action == 'atk2' else ENEMY_X
            self.assertEqual(actor_x(action,view.enemy_impact_fraction,5),target)
            screen=pygame.Surface((1920,1080),pygame.SRCALPHA)
            with patch.object(self.assets,'get_enemy_projectile',side_effect=AssertionError('efeito antigo')):
                view.draw_enemy(screen,create_zanzara())
                view.draw_enemy_projectile(screen)
            self.assertGreater(screen.get_bounding_rect().width,20)

    def test_special_uses_dedicated_poses_and_ends_with_final_victory(self):
        boss = create_zanzara()
        boss.action_counter = 7
        choose_next_action(boss)
        self.assertIs(boss.current_action, boss.special_action)
        view = EntityView(self.assets)
        view.trigger_attack('enemy', 'atk3', boss.name, ultimate=True)
        self.assertIs(view.enemy_ultimate, BOSS_ULTIMATE_ANIMATIONS['zanzara'])
        from src.ui.zanzara_necromancer import load_kit
        self.assertEqual(len(load_kit()['ultimate']),8)
        self.assertEqual(view.enemy_ultimate.title,'Travessia Final')
        engine = CombatEngine()
        engine.enemy = boss
        boss.hp = 0
        engine._on_enemy_defeated()
        self.assertEqual(engine.state, 'victory')

    def test_map_resume_starts_zanzara_and_finishes_level_seven(self):
        from src.systems.save_manager import SaveManager
        saves = SaveManager()
        data = saves._new_data('Teste', 'test')
        events = []
        engine = CombatEngine(map_mode=True, on_event_callback=lambda event, **payload: events.append((event, payload)))
        engine.resume_from_save(data, saves, level=7, encounter_kind='point')
        self.assertEqual(engine.enemy.name, 'Zanzara')
        self.assertEqual(engine.level, 7)
        engine.enemy.hp = 0
        engine._on_enemy_defeated()
        engine.finish_map_phase()
        self.assertEqual(engine.state, 'phase_complete')
        self.assertIn(('phase_complete', {'level': 7}), events)
