import unittest
from tests import test_audio_enemies
from src.systems.enemy_factory import create_zanzara

class TestZanzaraAudio(unittest.TestCase):
    def scene(self, action, ultimate=False):
        scene = test_audio_enemies.TestCommonEnemyAudio().make_scene('Zanzara')
        scene.engine.enemy = create_zanzara()
        scene._handle_combat_event('attack', attacker='enemy', action=action, ultimate=ultimate)
        scene._handle_combat_event('flash', target='player')
        return scene

    def test_four_attacks_schedule_distinct_stages(self):
        expected = [('atk1',False,['swing','flesh']),('atk2',False,['smoke','swing','flesh','smoke']),('atk3',False,['aura','portal','souls']),('atk3',True,['aura','laugh','summon','ferry'])]
        for action, ultimate, stages in expected:
            with self.subTest(action=action,ultimate=ultimate):
                scene=self.scene(action,ultimate)
                queue=scene._pending_enemy_audio
                self.assertEqual([q[4] for q in queue],['gameplay.boss.zanzara.'+s for s in stages])
                audio=scene.scene_manager.audio_manager.play_sfx
                first=queue[0][3]
                scene.update(first-1)
                audio.assert_not_called()
                scene.update(1)
                self.assertEqual(audio.call_args.args[0],queue[0][4])
                for _ in range(220): scene.update(16)
                self.assertEqual([c.args[0] for c in audio.call_args_list],['gameplay.boss.zanzara.'+s for s in stages])

    def test_cancelled_action_does_not_play(self):
        scene=self.scene('atk3',True)
        scene.entity_view.attacker=None
        scene.entity_view.enemy_action=None
        scene.update(16)
        scene.scene_manager.audio_manager.play_sfx.assert_not_called()
        self.assertEqual(scene._pending_enemy_audio,[])
