import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
from src.systems.enemy_factory import create_zanzara
from src.systems.combat_engine import CombatEngine
from src.systems.enemy_intents import preview_intents, icon_family
from src.ui.entity_view import EntityView
from src.core.asset_manager import AssetManager

class FinalKitTests(unittest.TestCase):
    def test_final_kit_names_and_no_old_healing_buff(self):
        boss = create_zanzara()
        self.assertEqual([a.name for a in boss.actions],['Foice Sombria','Passo do Barqueiro','Grilhões das Almas'])
        self.assertEqual([a.damage for a in boss.actions],[20,24,20])
        self.assertEqual(boss.special_action.name,'Travessia Final')
        self.assertEqual(boss.special_action.damage,45)
        self.assertFalse(any(a.action_type in ('buff','heal') for a in boss.actions))

    def test_chains_damage_vulnerability_and_totem_protection(self):
        for protected in (False,True):
            engine = CombatEngine()
            engine.enemy = create_zanzara()
            action = engine.enemy.actions[2]
            engine.enemy.set_intent('attack',20,action)
            engine.enemy_actions_remaining = 1
            engine.state = 'enemy_turn'
            if protected: engine.player.apply_status('totem',2,1)
            hp = engine.player.hp
            engine.enemy_turn()
            self.assertEqual(engine.player.hp,hp if protected else hp-20)
            if protected:
                self.assertNotIn('vulnerable',engine.player.statuses)
            else:
                self.assertEqual(engine.player.statuses['vulnerable'],{'turns':2,'potency':25})
                self.assertEqual(engine.player.receive_attack(15),19)
                engine.player.end_turn_statuses()
                self.assertEqual(engine.player.statuses['vulnerable']['turns'],1)
                engine.player.end_turn_statuses()
                self.assertNotIn('vulnerable',engine.player.statuses)

    def test_second_intent_accounts_for_chains_but_not_if_totem_protects(self):
        for protected in (False,True):
            engine=CombatEngine();engine.enemy=create_zanzara()
            chains,attack=engine.enemy.actions[2],engine.enemy.actions[0]
            engine.enemy.action_plan=[chains,attack]
            engine.enemy.set_intent('attack',20,chains)
            if protected:engine.player.apply_status('totem',2,1)
            intents=preview_intents(engine)
            self.assertEqual([i.value for i in intents],[20,20 if protected else 25])

    def test_intent_describes_chains_and_new_skill_icons(self):
        engine = CombatEngine();engine.enemy = create_zanzara()
        engine.enemy.action_plan = [engine.enemy.actions[2]]
        text = preview_intents(engine)[0].description
        self.assertIn('Vulnerável',text)
        self.assertIn('25%',text)
        self.assertIn('2 turnos',text)
        self.assertEqual([icon_family(a) for a in engine.enemy.actions],['scythe','scythe','chains'])
        self.assertEqual(icon_family(engine.enemy.special_action),'ferry')

class FinalVisualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init();pygame.display.set_mode((1,1));cls.assets=AssetManager()

    def test_final_dungeon_is_specific_to_level_seven(self):
        bg = self.assets.get_battle_background(7)
        self.assertIsNot(bg,self.assets.background)
        self.assertEqual(bg.get_size(),(1920,1080))
        self.assertIsNot(bg,self.assets.get_battle_background(6))

    def test_damage_and_defeat_strips_have_eight_complete_frames(self):
        from src.ui.zanzara_necromancer import state_frames
        for name in ('dano','derrota'):
            frames=state_frames(name)
            self.assertEqual(len(frames),8)
            self.assertTrue(all(f.get_size()==(384,280) for f in frames))
        self.assertEqual(state_frames('derrota')[-1].get_bounding_rect().width,0)

    def test_hit_reaction_and_defeat_are_different_from_idle(self):
        view = EntityView(self.assets);enemy = create_zanzara()
        idle = pygame.Surface((1920,1080),pygame.SRCALPHA);view.draw_enemy(idle,enemy)
        view.enemy_flash=140
        hurt = pygame.Surface((1920,1080),pygame.SRCALPHA);view.draw_enemy(hurt,enemy)
        self.assertTrue(pygame.image.tobytes(idle,'RGBA') != pygame.image.tobytes(hurt,'RGBA'),'reação de dano igual ao repouso')
        enemy.hp=0
        view.draw_enemy(pygame.Surface((1920,1080)),enemy)
        self.assertFalse(view.is_enemy_defeat_done(enemy))
        view.update(700)
        fallen=pygame.Surface((1920,1080),pygame.SRCALPHA);view.draw_enemy(fallen,enemy)
        self.assertGreater(fallen.get_bounding_rect().width,0)
        self.assertTrue(pygame.image.tobytes(idle,'RGBA') != pygame.image.tobytes(fallen,'RGBA'),'derrota igual ao repouso')
        view.update(1500)
        self.assertTrue(view.is_enemy_defeat_done(enemy))

    def test_defeat_starts_only_when_player_attack_reaches_contact(self):
        enemy=create_zanzara();enemy.hp=0
        view=EntityView(self.assets)
        view.trigger_attack('player')
        view.pending_enemy_hit_at=300
        canvas=pygame.Surface((1920,1080))
        view.draw_enemy(canvas,enemy)
        self.assertIsNone(view._zanzara_defeat_timer)
        view.update(299);view.draw_enemy(canvas,enemy)
        self.assertIsNone(view._zanzara_defeat_timer)
        view.update(1);view.draw_enemy(canvas,enemy)
        self.assertEqual(view._zanzara_defeat_timer,0)

    def test_victory_waits_for_the_defeat_animation(self):
        from src.scenes.battle_scene import BattleScene
        window=SimpleNamespace(get_virtual_mouse_pos=lambda:(-1,-1),draw_fullscreen_button=lambda *_:None)
        scene=BattleScene(None,window,self.assets,selected_level=7)
        scene.engine.enemy=create_zanzara();scene.engine.enemy.hp=0;scene.engine.state='victory'
        scene._draw_victory=MagicMock()
        scene.draw(pygame.Surface((1920,1080)))
        scene._draw_victory.assert_not_called()
        scene.entity_view.update(2200)
        scene.draw(pygame.Surface((1920,1080)))
        scene._draw_victory.assert_called_once()

if __name__ == '__main__':unittest.main()
