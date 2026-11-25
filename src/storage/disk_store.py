"""Backend desktop: mesmos JSONs, temporário, fsync e substituição atômica."""
from copy import deepcopy
import json
import os
from .base import SnapshotStore, check_revision


class DiskStore(SnapshotStore):
    def __init__(self, directory):
        self.directory = os.fspath(directory)

    def path(self, key):
        return os.path.join(self.directory, key + ".json")

    def exists_sync(self, key):
        return os.path.exists(self.path(key))

    def keys_sync(self):
        if not os.path.isdir(self.directory):
            return []
        return [name[:-5] for name in os.listdir(self.directory) if name.endswith(".json")]

    def read_sync(self, key):
        with open(self.path(key), encoding="utf-8") as source:
            return json.load(source)

    def commit_sync(self, key, payload, expected, create_only=False):
        os.makedirs(self.directory, exist_ok=True)
        current = self.read_sync(key) if self.exists_sync(key) else None
        revision = check_revision(current, payload, expected, create_only)
        document = deepcopy(payload)
        document["revisao"] = revision
        path = self.path(key)
        with open(path + ".tmp", "w", encoding="utf-8") as target:
            json.dump(document, target, indent=4, ensure_ascii=False)
            target.flush()
            os.fsync(target.fileno())
        os.replace(path + ".tmp", path)
        return revision

    def delete_sync(self, key, expected=None):
        if self.exists_sync(key):
            if expected is not None:
                current = self.read_sync(key)
                check_revision(current, current, expected)
            os.remove(self.path(key))

    async def read(self, key):
        return self.read_sync(key)

    async def keys(self):
        return self.keys_sync()

    async def commit(self, key, payload, expected, create_only=False):
        return self.commit_sync(key, payload, expected, create_only)

    async def delete(self, key, expected):
        return self.delete_sync(key, expected)

