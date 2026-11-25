"""Contratos de disco/IndexedDB, migrações v15 e publicação após confirmação."""
import asyncio
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, IsolatedAsyncioTestCase
from unittest.mock import patch
from src.storage.base import check_revision, RevisionConflict, StorageError
from src.storage.disk_store import DiskStore
from src.storage.browser_store import BrowserStore
from src.storage.manager import BrowserSaveManager
from src.systems.save_manager import SaveManager, SaveError, SaveCorruptedError
from src.systems.shop_system import purchase_card
from src.systems.roguelite import upgrade_copy, transact
from src.systems.management_tutorials import complete_guide


class ControlledBrowser(BrowserStore):
    def __init__(self, cache):
        super().__init__()
        self.cache=deepcopy(cache)
        self.fail=False
        self.gate=None
        self.commits=0
    async def commit_batch(self,changes):
        if self.gate is not None:
            await self.gate.wait()
        if self.fail:raise StorageError("Sem espaço. A operação foi desfeita.")
        candidate=deepcopy(self.cache)
        revisions={}
        for change in changes:
            key=change["key"]
            revision=check_revision(candidate.get(key),change.get("payload") or {},change["expected"],change.get("create_only",False))
            if change.get("delete"):candidate.pop(key,None)
            else:
                candidate[key]=deepcopy(change["payload"])
                candidate[key]["revisao"]=revision
                revisions[key]=revision
        self.cache=candidate
        self.commits+=1
        return revisions


def fixture():
    with TemporaryDirectory() as folder:
        manager=SaveManager(folder)
        data=manager.create_save("slot_1")
        data["progresso"]["moedas"]=1000
        data["progresso"]["materials"]["Soco Simples"]=3
        manager.save(data)
        return manager.payload(data)


class DiskContractTests(TestCase):
    def test_atomic_replace_and_fsync_are_used(self):
        with TemporaryDirectory() as folder:
            manager=SaveManager(folder)
            with patch("os.fsync",wraps=__import__("os").fsync) as flush,patch("os.replace",wraps=__import__("os").replace) as replace:
                data=manager.create_save("slot_1")
            flush.assert_called_once()
            replace.assert_called_once()
            self.assertEqual(manager.load_save("slot_1")["revisao"],1)
            self.assertFalse((Path(folder)/"slot_1.json.tmp").exists())
            self.assertEqual(data["versao"],15)

    def test_failed_replace_preserves_previous_document_and_transact_rolls_back(self):
        with TemporaryDirectory() as folder:
            manager=SaveManager(folder);data=manager.create_save("slot_1")
            before=deepcopy(data)
            with patch("os.replace",side_effect=OSError("disco cheio")):
                result=transact(manager,data,lambda:data["progresso"].update(moedas=999))
            self.assertFalse(result[0])
            self.assertEqual(data,before)
            self.assertEqual(manager.load_save("slot_1")["progresso"]["moedas"],0)

    def test_export_import_v15_moves_profile_and_run_between_slots(self):
        with TemporaryDirectory() as folder:
            manager=SaveManager(folder);data=manager.create_save("slot_1")
            data["progresso"]["moedas"]=123
            data["perfil"]["fragmentos"]=7
            manager.save(data)
            imported=manager.import_json(manager.export_json("slot_1"),2)
            self.assertEqual(imported["versao"],15)
            self.assertEqual(imported["perfil"]["fragmentos"],7)
            self.assertEqual(imported["progresso"]["moedas"],123)
            self.assertEqual(imported["id"],"slot_2")
            self.assertEqual(imported["revisao"],1)

    def test_invalid_future_import_does_not_replace_slot(self):
        with TemporaryDirectory() as folder:
            manager=SaveManager(folder);data=manager.create_save("slot_1")
            before=manager.export_json("slot_1")
            payload=json.loads(before);payload["versao"]=999
            with self.assertRaises(SaveCorruptedError):
                manager.import_json(json.dumps(payload),1,True)
            self.assertEqual(manager.export_json("slot_1"),before)

    def test_legacy_read_keeps_backup_and_migrates(self):
        with TemporaryDirectory() as folder:
            payload=fixture();payload["versao"]=14
            Path(folder,"slot_1.json").write_text(json.dumps(payload),encoding="utf-8")
            manager=SaveManager(folder)
            self.assertEqual(manager.load_save("slot_1")["versao"],15)
            self.assertTrue(Path(folder,"slot_1.json.v14.bak").exists())


class BrowserTransactionTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.store=ControlledBrowser({"slot_1":fixture()})
        self.manager=BrowserSaveManager(self.store)
        self.data=self.manager.load_save("slot_1")

    async def test_purchase_is_not_published_until_commit_completes(self):
        self.store.gate=asyncio.Event()
        before=deepcopy(self.data)
        task=asyncio.create_task(self.manager.run(self.data,lambda m,d:purchase_card(m,d,"Investida")))
        await asyncio.sleep(0)
        self.assertEqual(self.data,before)
        self.assertTrue(self.manager.busy)
        self.store.gate.set()
        result=await task
        self.assertTrue(result.success)
        self.assertIn("Investida",self.data["progresso"]["cartas_colecao"])

    async def test_write_failure_rolls_back_entire_document(self):
        self.store.fail=True
        before=deepcopy(self.data)
        with self.assertRaises(SaveError):
            await self.manager.run(self.data,lambda m,d:purchase_card(m,d,"Investida"))
        self.assertEqual(self.data,before)
        self.assertEqual(self.store.cache["slot_1"]["run"]["moedas"],1000)

    async def test_double_command_is_rejected_while_pending(self):
        self.store.gate=asyncio.Event()
        first=asyncio.create_task(self.manager.run(self.data,lambda m,d:purchase_card(m,d,"Investida")))
        await asyncio.sleep(0)
        with self.assertRaises(SaveError):
            await self.manager.run(self.data,lambda m,d:purchase_card(m,d,"Aura Rubra"))
        self.store.gate.set()
        await first
        self.assertEqual(self.store.commits,1)

    async def test_stale_tab_cannot_overwrite_newer_revision(self):
        second=BrowserSaveManager(self.store)
        stale=second.load_save("slot_1")
        await self.manager.run(self.data,lambda m,d:purchase_card(m,d,"Investida"))
        before=deepcopy(stale)
        with self.assertRaises(SaveError):
            await second.run(stale,lambda m,d:purchase_card(m,d,"Aura Rubra"))
        self.assertEqual(stale,before)
        self.assertIn("Investida",self.store.cache["slot_1"]["run"]["cartas_colecao"])
        self.assertNotIn("Aura Rubra",self.store.cache["slot_1"]["run"]["cartas_colecao"])

    async def test_upgrade_and_guide_use_shared_rules(self):
        copy_id=next(c["id"] for c in self.data["progresso"]["copies"] if c["name"]=="Soco Simples")
        result=await self.manager.run(self.data,lambda m,d:upgrade_copy(m,d,copy_id))
        self.assertTrue(result[0])
        self.assertEqual(next(c for c in self.data["progresso"]["copies"] if c["id"]==copy_id)["level"],2)
        await self.manager.run(self.data,lambda m,d:complete_guide(m,d,"shop"))
        loaded=SaveManager(store=__import__("src.storage.browser_store",fromlist=["StagedStore"]).StagedStore(self.store.cache)).load_save("slot_1")
        self.assertTrue(loaded["perfil"]["tutoriais_gerenciamento"]["shop"])

    async def test_new_slot_is_created_only_after_durable_commit(self):
        document=await self.manager.run(None,lambda m,d:m.create_save("slot_2"))
        self.assertEqual(document["revisao"],1)
        self.assertEqual(self.store.cache["slot_2"]["versao"],15)

    async def test_sync_save_cannot_fake_acknowledgment(self):
        with self.assertRaises(SaveError):
            self.manager.save(self.data)



class BridgeContractTests(IsolatedAsyncioTestCase):
    async def test_bridge_yields_while_pending_and_waits_for_confirmation(self):
        class Bridge:
            def begin(self, operation, text):
                self.arguments = json.loads(text)
                return 4
            def poll(self, token):
                self.calls = getattr(self, "calls", 0) + 1
                return json.dumps({"pending":True} if self.calls == 1 else {"ok":True,"value":7})
        bridge = Bridge()
        store = BrowserStore(bridge)
        self.assertEqual(await store.request("read", {"key":"slot_1"}), 7)
        self.assertEqual(bridge.calls, 2)
        self.assertEqual(bridge.arguments, {"key":"slot_1"})

    async def test_bridge_reports_revision_conflict_and_preserves_cache(self):
        class Bridge:
            def begin(self, *args): return 1
            def poll(self, token):
                return json.dumps({"ok":False,"error":{"name":"RevisionConflict","message":"Outra aba."}})
        store = BrowserStore(Bridge())
        store.cache = {"slot_1":fixture()}
        before = deepcopy(store.cache)
        with self.assertRaises(RevisionConflict):
            await store.commit("slot_1", {}, 1)
        self.assertEqual(store.cache, before)

    async def test_successful_commit_updates_cache_only_with_confirmed_revision(self):
        class Bridge:
            def begin(self, *args): return 1
            def poll(self, token): return json.dumps({"ok":True,"value":{"slot_1":8}})
        store = BrowserStore(Bridge())
        payload = fixture()
        self.assertEqual(await store.commit("slot_1", payload, 7), 8)
        self.assertEqual(store.cache["slot_1"]["revisao"], 8)
        self.assertNotEqual(payload["revisao"], 8)

    async def test_browser_v14_migration_is_normalized_then_written_as_v15(self):
        payload = fixture()
        payload["versao"] = 14
        store = ControlledBrowser({"slot_1":payload})
        manager = BrowserSaveManager(store)
        data = manager.load_save("slot_1")
        self.assertEqual(data["versao"], 15)
        await manager.run(data, lambda m,d:complete_guide(m,d,"shop"))
        self.assertEqual(store.cache["slot_1"]["versao"], 15)
        self.assertIn("perfil", store.cache["slot_1"])
        self.assertIn("run", store.cache["slot_1"])

    async def test_failed_upgrade_preserves_materials_gold_and_levels(self):
        store = ControlledBrowser({"slot_1":fixture()})
        manager = BrowserSaveManager(store)
        data = manager.load_save("slot_1")
        before = deepcopy(data)
        copy_id = next(c["id"] for c in data["run"]["copies"] if c["name"]=="Soco Simples")
        store.fail = True
        with self.assertRaises(SaveError):
            await manager.run(data, lambda m,d:upgrade_copy(m,d,copy_id))
        self.assertEqual(data, before)

    async def test_failed_death_commit_preserves_active_run(self):
        store = ControlledBrowser({"slot_1":fixture()})
        manager = BrowserSaveManager(store)
        data = manager.load_save("slot_1")
        store.fail = True
        with self.assertRaises(SaveError):
            await manager.run(data, lambda m,d:m.end_run(d,1))
        self.assertEqual(data["run"]["estado"], "ativa")
        store.fail = False
        await manager.run(data, lambda m,d:m.end_run(d,1))
        self.assertEqual(data["run"]["estado"], "morta")
        self.assertEqual(data["run"]["vida"], 0)
        self.assertIsNone(data["run"]["combat_snapshot"])

    async def test_import_replaces_only_after_confirmation_and_creates_new_revision(self):
        store = ControlledBrowser({"slot_1":fixture()})
        manager = BrowserSaveManager(store)
        text = json.dumps(fixture())
        with self.assertRaises(SaveError):
            await manager.run(None, lambda m,d:m.import_json(text,1))
        original = store.cache["slot_1"]["revisao"]
        result = await manager.run(None, lambda m,d:m.import_json(text,1,True))
        self.assertEqual(result["revisao"], original+1)


class BrowserPreferencesTests(TestCase):
    def test_local_preferences_sanitized_and_survive_new_preferences_instance(self):
        from src.systems.game_preferences import GamePreferences
        class Bridge:
            text = "{}"
            def preferencesGet(self): return self.text
            def preferencesSet(self, text):
                self.text = text
                return '{"ok":true}'
        bridge = Bridge()
        store = BrowserStore(bridge)
        preferences = GamePreferences(store=store)
        preferences.set("master_volume", 0.3)
        preferences.save()
        self.assertEqual(GamePreferences(store=BrowserStore(bridge)).get("master_volume"), 0.3)
        self.assertNotIn("run", json.loads(bridge.text))

    def test_restricted_local_storage_uses_defaults_and_reports_failure(self):
        from src.systems.game_preferences import GamePreferences
        class Bridge:
            def preferencesGet(self): raise RuntimeError("blocked")
            def preferencesSet(self, text): return '{"ok":false,"message":"blocked"}'
        store = BrowserStore(Bridge())
        preferences = GamePreferences(store=store)
        self.assertTrue(store.preference_error)
        with self.assertRaises(OSError):
            preferences.save()



class UnicodeWireTests(IsolatedAsyncioTestCase):
    async def test_python_to_javascript_uses_ascii_json_without_changing_names(self):
        class Bridge:
            def begin(self, operation, text):
                self.text = text
                self.payload = json.loads(text)
                return 1
            def poll(self, token):
                return '{"ok":true,"value":null}'
        bridge = Bridge()
        store = BrowserStore(bridge)
        name = "Poção de Cura — João"
        await store.request("commit", {"name":name})
        self.assertTrue(bridge.text.isascii())
        self.assertEqual(bridge.payload["name"], name)

    async def test_javascript_ascii_json_decodes_portuguese_names_and_errors(self):
        class Bridge:
            def begin(self, *args): return 1
            def poll(self, token):
                return json.dumps({"ok":True,"value":{"name":"Poção Venenosa"}},ensure_ascii=True)
        store = BrowserStore(Bridge())
        self.assertEqual((await store.request("read"))["name"], "Poção Venenosa")

