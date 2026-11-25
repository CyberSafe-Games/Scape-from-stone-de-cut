"""Bridge assíncrona; nunca simula sucesso antes de IDBTransaction.oncomplete."""
import asyncio
from copy import deepcopy
import json
from .base import SnapshotStore, StorageError, RevisionConflict, check_revision


class BrowserStore(SnapshotStore):
    def __init__(self, bridge=None):
        self._bridge = bridge
        self.cache = {}
        self.preference_error = ""

    @property
    def bridge(self):
        if self._bridge is None:
            import platform
            self._bridge = platform.window.scapeStorage
        return self._bridge

    async def request(self, operation, arguments=None):
        token = self.bridge.begin(operation, json.dumps(arguments or {}, ensure_ascii=True))
        while True:
            result = json.loads(str(self.bridge.poll(token)))
            if result.get("pending"):
                await asyncio.sleep(0)
                continue
            if not result.get("ok"):
                error = result.get("error", {})
                kind = RevisionConflict if error.get("name") == "RevisionConflict" else StorageError
                raise kind(error.get("message", "Não foi possível gravar no navegador."))
            return result.get("value")

    async def open(self):
        rows = await self.request("open")
        self.cache = {row["id"]: row for row in rows}
        return self

    async def read(self, key):
        value = await self.request("read", {"key": key})
        if value is None:
            self.cache.pop(key, None)
        else:
            self.cache[key] = value
        return deepcopy(value)

    async def keys(self):
        await self.open()
        return list(self.cache)

    async def commit(self, key, payload, expected, create_only=False):
        results = await self.commit_batch([dict(key=key, payload=payload, expected=expected, create_only=create_only)])
        return results[key]

    async def commit_batch(self, changes):
        revisions = await self.request("commit", {"changes": changes})
        for change in changes:
            key = change["key"]
            if change.get("delete"):
                self.cache.pop(key, None)
            else:
                value = deepcopy(change["payload"])
                value["revisao"] = revisions[key]
                self.cache[key] = value
        return revisions

    async def delete(self, key, expected):
        await self.commit_batch([dict(key=key, delete=True, expected=expected)])

    def load_preferences(self):
        try:
            return json.loads(str(self.bridge.preferencesGet()))
        except Exception as exc:
            self.preference_error = "Preferências indisponíveis; os ajustes valerão apenas nesta sessão."
            return {}

    def save_preferences(self, values):
        response = json.loads(str(self.bridge.preferencesSet(json.dumps(values))))
        if not response.get("ok"):
            raise OSError(response.get("message", "Não foi possível salvar as preferências."))


class StagedStore:
    """Cópia isolada do último estado confirmado; não acessa disco nem IndexedDB."""
    def __init__(self, cache):
        self.original = deepcopy(cache)
        self.cache = deepcopy(cache)
        self.dirty = set()
        self.deleted = set()

    def exists_sync(self, key):
        return key in self.cache

    def keys_sync(self):
        return list(self.cache)

    def read_sync(self, key):
        return deepcopy(self.cache[key])

    def commit_sync(self, key, payload, expected, create_only=False):
        revision = check_revision(self.cache.get(key), payload, expected, create_only)
        self.cache[key] = deepcopy(payload)
        self.cache[key]["revisao"] = revision
        self.dirty.add(key)
        return revision

    def delete_sync(self, key, expected=None):
        self.cache.pop(key, None)
        self.deleted.add(key)

    def changes(self):
        result = []
        for key in self.dirty | self.deleted:
            old = self.original.get(key)
            result.append(dict(key=key, payload=self.cache.get(key),
                               expected=old.get("revisao", 0) if old else 0,
                               expected_run_id=(old.get("run") or old.get("progresso") or {}).get("run_id") if old else None,
                               create_only=old is None,
                               delete=key in self.deleted))
        return result

