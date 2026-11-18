"""Ciclo de run, inventário individual e retomada sem saves reais."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.systems.save_manager import SaveManager, SaveError, SaveCorruptedError
from src.systems.roguelite import upgrade_copy, purchase_material, purchase_permanent, instance_card
from src.systems.combat_engine import CombatEngine
from src.systems.combat_snapshot import capture, restore
from src.systems.enemy_factory import create_zanzara, choose_next_action
from src.systems.campaign_progress import confirm_victory, record_road_victory


class RogueliteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.manager = SaveManager(self.tmp.name)
        self.data = self.manager.create_save('slot_1')
        self.p = self.data['progresso']
        self.p['moedas'] = 1000
        self.p['materials']['Soco Simples'] = 9
        self.manager.save(self.data)

    def punches(self):
        return [c for c in self.data['progresso']['copies'] if c['name'] == 'Soco Simples']

    def test_exact_three_materials_upgrade_one_equipped_copy(self):
        cid = self.punches()[0]['id']
        self.assertTrue(upgrade_copy(self.manager, self.data, cid)[0])
        loaded = self.manager.load_save('slot_1')['progresso']
        self.assertEqual([c['level'] for c in loaded['copies'][:3]], [2, 1, 1])
        self.assertEqual(loaded['moedas'], 960)
        self.assertEqual(loaded['materials']['Soco Simples'], 6)
        self.assertEqual(loaded['copy_slots'].count(cid), 1)
        self.assertEqual(len([c for c in loaded['copy_slots'] if c]), 6)

    def test_duplicate_upgrade_and_short_materials_never_charge(self):
        cid = self.punches()[0]['id']
        self.assertTrue(upgrade_copy(self.manager, self.data, cid)[0])
        before = deepcopy(self.data)
        self.assertFalse(upgrade_copy(self.manager, self.data, cid)[0])
        self.assertEqual(self.data, before)
        self.data['progresso']['materials']['Soco Simples'] = 2
        before = deepcopy(self.data)
        self.assertFalse(upgrade_copy(self.manager, self.data, self.punches()[1]['id'])[0])
        self.assertEqual(self.data, before)

    def test_io_failure_rolls_back_level_material_gold_and_counter(self):
        before = deepcopy(self.data)
        with patch.object(self.manager, 'save', side_effect=OSError('disco')):
            self.assertFalse(upgrade_copy(self.manager, self.data, self.punches()[0]['id'])[0])
        self.assertEqual(self.data, before)

    def test_limit_survives_unequip_and_reload(self):
        for c in list(self.punches()):
            self.assertTrue(upgrade_copy(self.manager, self.data, c['id'])[0])
        self.data = self.manager.load_save('slot_1')
        self.data['progresso']['deck_slots'][0] = None
        self.manager.save(self.data)
        shield = next(c for c in self.data['progresso']['copies'] if c['name'] == 'Esfera Protetora')
        self.data['progresso']['materials']['Esfera Protetora'] = 3
        self.assertFalse(upgrade_copy(self.manager, self.data, shield['id'])[0])
        self.assertEqual(self.data['progresso']['upgrades_purchased'], 3)

    def test_material_purchase_repeated_and_cap(self):
        self.p['materials']['Soco Simples'] = 7
        self.assertTrue(purchase_material(self.manager, self.data, 'Soco Simples')[0])
        self.assertTrue(purchase_material(self.manager, self.data, 'Soco Simples')[0])
        self.assertFalse(purchase_material(self.manager, self.data, 'Soco Simples')[0])
        self.assertEqual(self.data['progresso']['moedas'], 970)
        self.assertEqual(len(self.data['progresso']['copies']), 6)

    def test_death_new_run_preserves_profile_and_resets_temporaries(self):
        self.data['perfil']['fragmentos'] = 10
        self.assertTrue(upgrade_copy(self.manager, self.data, self.punches()[0]['id'])[0])
        old_id = self.p['run_id']
        self.assertTrue(self.manager.end_run(self.data, 5)[0])
        self.assertTrue(purchase_permanent(self.manager, self.data, 'vida')[0])
        self.assertTrue(self.manager.new_run(self.data)[0])
        loaded = self.manager.load_save('slot_1')
        p = loaded['progresso']
        self.assertNotEqual(p['run_id'], old_id)
        self.assertEqual((p['vida'], p['moedas'], p['upgrades_purchased']), (65, 30, 0))
        self.assertEqual(p['materials'], {})
        self.assertEqual(loaded['perfil']['fragmentos'], 7)
        self.assertEqual(p['territorios_concluidos'], [])
        self.assertTrue(all(c['level'] == 1 for c in p['copies']))

    def test_stale_checkpoint_cannot_resurrect_confirmed_death(self):
        stale = deepcopy(self.data)
        self.assertTrue(self.manager.end_run(self.data, 3)[0])
        with self.assertRaises(SaveError):
            self.manager.save(stale)
        engine = CombatEngine()
        with self.assertRaises(SaveError):
            engine.resume_from_save(self.manager.load_save('slot_1'), self.manager)

    def test_permanent_is_between_runs_and_slot_isolation(self):
        self.data['perfil']['fragmentos'] = 20
        self.assertFalse(purchase_permanent(self.manager, self.data, 'energia')[0])
        self.manager.end_run(self.data, 1)
        self.assertTrue(purchase_permanent(self.manager, self.data, 'energia')[0])
        self.manager.new_run(self.data)
        engine = CombatEngine()
        engine.resume_from_save(self.data, self.manager)
        self.assertEqual(engine.energy, 3)
        other = self.manager.create_save('slot_2')
        self.assertEqual(other['perfil']['fragmentos'], 0)
        self.assertEqual(other['perfil']['energia'], 0)

    def test_snapshot_json_preserves_hand_and_two_action_plan(self):
        engine = CombatEngine(map_mode=True)
        engine.resume_from_save(self.data, self.manager, encounter_kind='road', encounter_index=0)
        engine.enemy = create_zanzara()
        engine.enemy.action_counter = 6
        choose_next_action(engine.enemy)
        engine.player.add_stacks('bleed', 2)
        engine.player.add_block(7)
        engine.play_card(0)
        snapshot = json.loads(json.dumps(capture(engine)))
        resumed = CombatEngine(map_mode=True)
        restore(resumed, snapshot)
        self.assertEqual([c.name for c in resumed.hand], [c.name for c in engine.hand])
        self.assertEqual(resumed.enemy.action_counter, 6)
        self.assertEqual(resumed.enemy.action_plan[1].name, 'Travessia Final')
        self.assertIs(resumed.enemy.action_plan[1], resumed.enemy.special_action)
        self.assertEqual(resumed.player.hp, engine.player.hp)
        self.assertEqual(resumed.player.bleed_stacks, 2)

    def test_level_two_observable_damage(self):
        card = instance_card(dict(self.punches()[0], level=2))
        engine = CombatEngine()
        engine.enemy.hp = engine.enemy.max_hp = 100
        engine.deck_manager.hand = [card]
        self.assertTrue(engine.play_card(0))
        self.assertEqual(engine.enemy.hp, 91)

    def test_v12_migrates_without_inventing_materials_and_keeps_backup(self):
        legacy = self.manager._new_data('legado', 'old')
        legacy['versao'] = 12
        path = Path(self.tmp.name) / 'old.json'
        path.write_text(json.dumps(legacy), encoding='utf-8')
        loaded = self.manager.load_save('old')
        self.assertEqual(len(loaded['progresso']['copies']), 6)
        self.assertEqual(loaded['progresso']['materials'], {})
        self.assertEqual(loaded['perfil']['fragmentos'], 0)
        self.assertTrue(path.with_suffix('.json.v12.bak').exists())

    def test_future_save_rejected_without_overwrite(self):
        data = deepcopy(self.data)
        data['versao'] = 99
        with self.assertRaises(SaveCorruptedError):
            self.manager.save(data)

    def test_material_reward_and_gold_are_applied_once_after_reload(self):
        engine = CombatEngine(map_mode=True)
        engine.resume_from_save(self.data, self.manager, level=1, encounter_kind='road', encounter_index=0)
        engine.enemy.hp = 0
        engine._on_enemy_defeated()
        self.p['materials']['Soco Simples'] = 0
        self.assertTrue(engine.choose_material('Soco Simples'))
        record_road_victory(self.manager, self.data, engine, lambda: None)
        self.data = self.manager.load_save('slot_1')
        record_road_victory(self.manager, self.data, engine, lambda: None)
        self.assertEqual(self.data['progresso']['materials']['Soco Simples'], 1)
        self.assertEqual(self.data['progresso']['moedas'], 1035)
        self.assertEqual(self.data['perfil']['fragmentos'], 0)

    def test_boss_fragments_persist_before_choice_and_do_not_repeat(self):
        engine = CombatEngine(map_mode=True)
        engine.resume_from_save(self.data, self.manager, level=1, encounter_kind='point')
        engine.enemy.hp = 0
        engine._on_enemy_defeated()
        confirm_victory(self.data, engine)
        self.manager.save(self.data)
        self.data = self.manager.load_save('slot_1')
        confirm_victory(self.data, engine)
        self.assertEqual(self.data['perfil']['fragmentos'], 1)

    def test_old_document_cannot_replace_a_new_run(self):
        stale = deepcopy(self.data)
        self.manager.end_run(self.data, 1)
        self.manager.new_run(self.data)
        with self.assertRaises(SaveError):
            self.manager.save(stale)

    def test_snapshot_roundtrip_keeps_phase_transition_player_state(self):
        from src.systems.enemy_factory import create_alvaro_tex
        engine = CombatEngine(map_mode=True)
        engine.enemy = create_alvaro_tex()
        engine.player.energy = 1
        engine.player.ultimate_charge = 17
        engine.enemy.hp = 0
        engine._on_enemy_defeated()
        restored = CombatEngine(map_mode=True)
        restore(restored, json.loads(json.dumps(capture(engine))))
        self.assertEqual(restored.state, 'boss_transition')
        restored.finish_boss_transition()
        self.assertEqual(restored.enemy.phase, 2)
        self.assertEqual((restored.player.energy, restored.player.ultimate_charge), (1, 17))

    def test_level_two_hybrids_keep_status_limits_and_individual_benefits(self):
        for name, expected_block, expected_hp in (
                ('Poção Purificadora', 0, 26), ('Poção Venenosa', 6, 20),
                ('Poção Fragilizante', 5, 20), ('Totem Protetor', 8, 20),
                ('Máscara Ancestral', 28, 38)):
            with self.subTest(name=name):
                engine = CombatEngine()
                engine.player.hp = 20
                engine.player.energy_max = engine.player.energy = 8
                engine.player.add_stacks('poison', 1)
                engine.deck_manager.hand = [instance_card({'id': 'test', 'name': name, 'level': 2})]
                self.assertTrue(engine.play_card(0))
                self.assertEqual(engine.player.block, expected_block)
                self.assertEqual(engine.player.hp, expected_hp)
                if name == 'Poção Venenosa':
                    self.assertEqual(engine.enemy.poison_stacks, 2)
                if name == 'Poção Purificadora':
                    self.assertEqual(engine.player.poison_stacks, 0)

    def test_snapshot_blocks_shop_and_deck_changes(self):
        from src.systems.shop_system import purchase_heal, purchase_card
        from src.systems.deck_loadout import commit_deck
        self.p['combat_snapshot'] = {'locked': True}
        self.assertFalse(purchase_heal(self.manager, self.data).success)
        self.assertFalse(purchase_card(self.manager, self.data, 'Investida').success)
        self.assertFalse(purchase_material(self.manager, self.data, 'Soco Simples')[0])
        self.assertFalse(commit_deck(self.manager, self.data, self.p['deck_slots'])[0])
