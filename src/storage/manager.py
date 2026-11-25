"""Coordenador de comandos: candidata isolada, commit real, publicação após confirmação."""
from copy import deepcopy
from src.systems.save_manager import SaveManager, SaveError
from .browser_store import BrowserStore, StagedStore
from .base import StorageError


def succeeded(result):
    if hasattr(result, "success"):
        return result.success
    if isinstance(result, tuple) and result and isinstance(result[0], bool):
        return result[0]
    return result is not False


class BrowserSaveManager(SaveManager):
    async_commands = True

    def __init__(self, store):
        # Leituras síncronas consultam somente o espelho hidratado; escritas exigem run().
        super().__init__(saves_dir="/tmp/scape-from-stone-session/saves", store=StagedStore(store.cache))
        self.browser_store = store
        self.busy = False

    async def refresh(self):
        await self.browser_store.open()
        self.store = StagedStore(self.browser_store.cache)

    def save(self, data):
        raise SaveError("Aguarde a confirmação assíncrona da gravação.")

    def delete_save(self, name):
        raise SaveError("A exclusão precisa de confirmação assíncrona.")

    async def run(self, data, command):
        if self.busy:
            raise SaveError("Já existe uma gravação em andamento.")
        self.busy = True
        try:
            if data is not None:
                current = self.browser_store.cache.get(data.get("id"))
                if current is None or current.get("revisao",0) != data.get("revisao",0):
                    raise SaveError("Este slot foi alterado em outra aba. Recarregue antes de continuar.")
            candidate = deepcopy(data) if data is not None else None
            stage = StagedStore(self.browser_store.cache)
            manager = SaveManager(saves_dir=self.saves_dir, store=stage)
            result = command(manager, candidate)
            if not succeeded(result):
                return result
            changes = stage.changes()
            if candidate != data and not changes:
                raise SaveError("A operação não solicitou uma gravação.")
            revisions = await self.browser_store.commit_batch(changes) if changes else {}
            for document in (candidate, result):
                if isinstance(document,dict) and document.get("id") in revisions:
                    document["revisao"] = revisions[document["id"]]
            if data is not None:
                data.clear()
                data.update(candidate)
                data["run"] = data["progresso"]
            self.store = StagedStore(self.browser_store.cache)
            return result
        except StorageError as exc:
            raise SaveError(str(exc)) from exc
        finally:
            self.busy = False


def persist_command(scene, command, complete):
    """Mesmo comando de negócio no desktop e na candidata web."""
    manager, data = scene.save_manager, scene.save_data
    if getattr(manager, "async_commands", False) is True:
        from src.systems.roguelite import transact_async
        return scene.scene_manager.submit(
            lambda: transact_async(manager, data, command), complete,
            lambda error: storage_failure(scene, error))
    return complete(command(manager, data))


def storage_failure(scene, error):
    message = str(error)
    if hasattr(scene,"message"):
        scene.message = message
        if hasattr(scene,"message_timer"):scene.message_timer = 6000
        if hasattr(scene,"message_positive"):scene.message_positive = False
    if hasattr(scene,"notice"):
        scene.notice = message
    if hasattr(scene,"error"):
        scene.error = message
    scene.scene_manager.storage_error = message

