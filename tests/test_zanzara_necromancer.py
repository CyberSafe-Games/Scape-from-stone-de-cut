import os
import unittest
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame
from src.ui.zanzara_necromancer import load_kit, frame_index, actor_x, action_frame, ferry_pose, windup_sprite, ultimate_cast_index, portal_pose, pose_aura, passo_strike_phase
from src.config.layout import ENEMY_X, PLAYER_X, APPROACH_GAP

class NecromancerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def test_dense_aura_is_drawn_behind_character(self):
        from unittest.mock import MagicMock, patch
        from src.ui.entity_view import EntityView
        import src.ui.zanzara_necromancer as module
        view = EntityView(MagicMock())
        for special in (False,True):
            view.trigger_attack('enemy','atk3','zanzara',ultimate=special)
            view.attack_timer = view.enemy_attack_duration*.6
            with patch.object(module,'_blit') as draw:
                module.draw(pygame.Surface((1920,1080)),view)
            calls = draw.call_args_list
            aura = [i for i,c in enumerate(calls) if any(c.args[1] is f for f in module.rubra_aura_frames())]
            body = module.load_kit()['atk1'][module.ultimate_cast_index(.6)] if special else module.conjure_sprite(2)
            body_index = next(i for i,c in enumerate(calls) if c.args[1] is body)
            self.assertTrue(aura)
            self.assertLess(max(aura),body_index)

    def test_spectral_flames_cover_both_sides_from_feet_to_shoulders(self):
        from src.ui.zanzara_necromancer import rubra_aura_frames
        frame = rubra_aura_frames()[3]
        for x in (0,264):
            bands = sum(pygame.mask.from_surface(frame.subsurface((x,y,176,50)),20).count() > 30 for y in range(40,440,50))
            self.assertGreaterEqual(bands,6)

    def test_rubra_style_aura_leaves_character_center_clear(self):
        from src.ui.zanzara_necromancer import rubra_aura_frames
        frames = rubra_aura_frames()
        self.assertEqual(len(frames),8)
        self.assertGreater(sum(pygame.mask.from_surface(f,15).count() for f in frames),100)
        for frame in frames:
            self.assertEqual(frame.get_size(),(440,480))
            self.assertEqual(pygame.mask.from_surface(frame.subsurface((204,150,20,140)),1).count(),0)
        colors = {frames[3].get_at((x,y))[:3] for x in range(0,440,3) for y in range(0,480,3) if frames[3].get_at((x,y)).a > 30}
        self.assertGreater(len(colors),64)

    def test_aura_tracks_current_silhouette_and_has_no_body_inside(self):
        left = pygame.Surface((32,32),pygame.SRCALPHA)
        right = pygame.Surface((32,32),pygame.SRCALPHA)
        pygame.draw.rect(left,(255,255,255,255),(3,3,5,5))
        pygame.draw.rect(right,(255,255,255,255),(19,19,5,5))
        a,b = pose_aura(left),pose_aura(right)
        self.assertEqual(b.get_bounding_rect().centerx-a.get_bounding_rect().centerx,16)
        self.assertEqual(a.get_at((17,17)).a,0)
        self.assertGreater(a.get_at((14,17)).a,0)

    def test_passo_has_backswing_release_and_contact(self):
        self.assertEqual(passo_strike_phase(.69,.78),'windup')
        self.assertEqual(passo_strike_phase(.76,.78),'release')
        self.assertEqual(passo_strike_phase(.78,.78),'hit')

    def test_ultimate_uses_normal_pose_indices_not_a_larger_body(self):
        self.assertEqual([ultimate_cast_index(p) for p in (0,.25,.38,.48,.7,.99)], [0,3,4,5,6,0])

    def test_ultimate_renderer_keeps_normal_character_scale(self):
        from unittest.mock import MagicMock, patch
        from types import SimpleNamespace
        from src.ui.entity_view import EntityView
        import src.ui.zanzara_necromancer as kit_module
        view = EntityView(MagicMock())
        view.trigger_attack('enemy', 'atk3', 'zanzara', ultimate=True)
        for progress in (.1,.25,.38,.48,.7,.9):
            view.attack_timer = view.enemy_attack_duration*progress
            with patch.object(kit_module, '_blit') as draw:
                kit_module.draw(pygame.Surface((1920,1080)), view)
            body = [call for call in draw.call_args_list if any(call.args[1] is f for f in load_kit()['atk1'])]
            self.assertEqual(len(body),1)
            self.assertEqual(body[0].args[3:6],(4,38,62))

    def test_player_anchor_ignores_transparent_canvas_padding(self):
        from unittest.mock import MagicMock
        from src.ui.entity_view import EntityView
        view = EntityView(MagicMock())
        image = pygame.Surface((320,260),pygame.SRCALPHA)
        pygame.draw.rect(image,(255,255,255,255),(132,129,46,129))
        view.get_player_frame = MagicMock(return_value=(390,image))
        view.draw_player(pygame.Surface((1920,1080)), 'player_turn')
        self.assertEqual(view.player_ground_anchor,(382,627))

    def test_portal_is_centered_on_actual_opponent_feet(self):
        rect, alpha = portal_pose(.8, (382, 627))
        self.assertEqual(rect.centerx, 382)
        self.assertEqual(rect.top+rect.height*.75, 627)
        self.assertEqual(alpha, 255)
        self.assertEqual(portal_pose(0, (382, 627))[1], 0)

    def test_eight_native_frames_and_transparency(self):
        kit = load_kit()
        self.assertEqual(set(kit), {"atk1", "atk2", "atk3", "ultimate"})
        for name, frames in kit.items():
            self.assertEqual(len(frames), 8)
            expected = (768, 512) if name == "ultimate" else (256, 256)
            for frame in frames:
                self.assertEqual(frame.get_size(), expected)
                self.assertTrue(frame.get_flags() & pygame.SRCALPHA)
            self.assertEqual(pygame.image.tobytes(frames[0], "RGBA"), pygame.image.tobytes(frames[7], "RGBA"))

    def test_entity_renderer_draws_all_actions_and_suppresses_legacy_projectiles(self):
        from unittest.mock import MagicMock
        from types import SimpleNamespace
        from src.ui.entity_view import EntityView
        from src.ui.boss_ultimate_fx import draw_boss_ultimate_fx
        view = EntityView(MagicMock())
        enemy = SimpleNamespace(name='Zanzara')
        for action, special in (("atk1", False), ("atk2", False), ("atk3", False), ("atk3", True)):
            view.trigger_attack('enemy', action, 'zanzara', ultimate=special)
            for index in range(21):
                view.attack_timer = view.enemy_attack_duration * index / 20
                canvas = pygame.Surface((1920, 1080), pygame.SRCALPHA)
                view.draw_enemy(canvas, enemy)
                self.assertGreater(canvas.get_bounding_rect().width, 0)
                effects = pygame.Surface((1920, 1080), pygame.SRCALPHA)
                view.draw_enemy_projectile(effects)
                draw_boss_ultimate_fx(effects, view)
                if action == 'atk3' and not special and .12 < index/20 < .97:
                    self.assertGreater(effects.get_bounding_rect().width, 0)
                    self.assertLess(abs(effects.get_bounding_rect().centerx-PLAYER_X), 45)
                else:
                    self.assertEqual(effects.get_bounding_rect().width, 0)

    def test_new_windup_has_blade_behind_the_character(self):
        frame = windup_sprite()
        self.assertEqual(frame.get_size(), (280, 280))
        # A lâmina levantada ocupa a direita acima da cabeça, não a frente esquerda.
        blade = frame.subsurface((0, 0, 280, 54)).get_bounding_rect(min_alpha=60)
        self.assertGreater(blade.left, 150)
        self.assertGreater(blade.right, 240)

    def test_scythe_prepares_before_approaching_and_hits_at_contact(self):
        self.assertEqual(action_frame('atk1', .15, .52), 3)
        self.assertEqual(actor_x('atk1', .15, 3), ENEMY_X)
        self.assertEqual(action_frame('atk1', .40, .52), 3)
        self.assertEqual(actor_x('atk1', .48, 4), PLAYER_X + APPROACH_GAP)
        self.assertEqual(action_frame('atk1', .52, .52), 5)

    def test_ferry_moves_continuously_from_summon_to_impact(self):
        before = ferry_pose(.699)
        after = ferry_pose(.701)
        self.assertLess(abs(before[0]-after[0]), 10)
        self.assertEqual(ferry_pose(.8)[0], PLAYER_X)
        self.assertEqual(ferry_pose(.44)[1], 0)
        self.assertEqual(ferry_pose(1)[1], 0)

    def test_contact_frame_and_return_home(self):
        for impact in (.52, .78, .80):
            self.assertEqual(frame_index(impact, impact), 5)
        for action in ("atk1", "atk2", "atk3", "ultimate"):
            self.assertEqual(actor_x(action, 0, 0), ENEMY_X)
            self.assertEqual(actor_x(action, 1, 7), ENEMY_X)
        self.assertEqual(actor_x("atk2", .78, 5), PLAYER_X + APPROACH_GAP)
        self.assertEqual(actor_x("atk3", .8, 5), ENEMY_X)

if __name__ == "__main__":
    unittest.main()
