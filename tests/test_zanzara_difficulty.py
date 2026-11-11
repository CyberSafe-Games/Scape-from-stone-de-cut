import unittest
from src.systems.combat_engine import CombatEngine
from src.systems.enemy_factory import create_zanzara
from src.systems.enemy_intents import preview_intents
from src.models.action import Action

class ZanzaraDifficultyTests(unittest.TestCase):
    def execute(self,index,protected=False,engine=None):
        engine=engine or CombatEngine()
        if engine.enemy.name != 'Zanzara':engine.enemy=create_zanzara()
        engine.player.hp=engine.player.max_hp=999
        action=engine.enemy.special_action if index==3 else engine.enemy.actions[index]
        engine.enemy.energy=4
        engine.enemy.set_intent('attack',action.damage,action)
        engine.enemy_actions_remaining=1
        engine.state='enemy_turn'
        if protected:engine.player.apply_status('totem',2,1)
        before=engine.player.hp
        engine.enemy_turn()
        return engine,before-engine.player.hp

    def test_both_scythe_attacks_apply_bleed_and_poison(self):
        for index,damage in ((0,20),(1,24)):
            engine,dealt=self.execute(index)
            self.assertEqual(dealt,damage)
            self.assertEqual(engine.player.statuses['bleed'],{'turns':2,'potency':5})
            self.assertEqual(engine.player.statuses['poison'],{'turns':2,'potency':3})
            self.assertEqual(engine.player.on_attack(),5)
            self.assertEqual(engine.player.on_attack(),0)
            self.assertIn(('poison',3),engine.player.end_turn_statuses())

    def test_ultimate_is_massive_and_applies_longer_stronger_poison(self):
        engine,dealt=self.execute(3)
        self.assertEqual(dealt,45)
        self.assertEqual(engine.player.statuses['poison'],{'turns':3,'potency':6})
        self.assertNotIn('bleed',engine.player.statuses)

    def test_totem_blocks_damage_and_every_attached_debuff(self):
        for index in range(4):
            engine,dealt=self.execute(index,protected=True)
            self.assertEqual(dealt,0)
            self.assertFalse(engine.player.statuses)

    def test_refresh_does_not_stack_or_downgrade_stronger_poison(self):
        engine,_=self.execute(3)
        engine,_=self.execute(0,engine=engine)
        self.assertEqual(engine.player.statuses['poison'],{'turns':3,'potency':6})
        engine,_=self.execute(0,engine=engine)
        self.assertEqual(engine.player.statuses['bleed'],{'turns':2,'potency':5})

    def test_intents_show_both_scythe_debuffs(self):
        engine=CombatEngine();engine.enemy=create_zanzara()
        engine.enemy.action_plan=[engine.enemy.actions[0],engine.enemy.special_action]
        texts=[p.description for p in preview_intents(engine)]
        self.assertIn('Sangramento',texts[0])
        self.assertIn('Veneno',texts[0])
        self.assertIn('6 de dano',texts[1])

    def test_legacy_single_status_actions_still_work(self):
        engine=CombatEngine();engine.enemy=create_zanzara()
        action=Action('Legado',damage=8,status_effect=('poison',2,4))
        engine.enemy.set_intent('attack',8,action);engine.state='enemy_turn';engine.enemy_actions_remaining=1
        engine.enemy_turn()
        self.assertEqual(engine.player.statuses['poison'],{'turns':2,'potency':4})

if __name__=='__main__':unittest.main()
