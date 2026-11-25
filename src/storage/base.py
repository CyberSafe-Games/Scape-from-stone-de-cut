"""Contrato de snapshots JSON; revisão é verificada no ato do commit."""
from abc import ABC, abstractmethod


class StorageError(RuntimeError):
    pass


class RevisionConflict(StorageError):
    pass


def check_revision(current, incoming, expected, create_only=False):
    if create_only and current is not None:
        raise RevisionConflict("Este espaço já existe. Recarregue a lista de jornadas.")
    actual = current.get("revisao", 0) if current else 0
    if actual != expected:
        raise RevisionConflict("Este slot foi alterado em outra aba. Recarregue antes de continuar.")
    if current:
        old_run = current.get("run", current.get("progresso", {}))
        new_run = incoming.get("run", incoming.get("progresso", {}))
        if (old_run.get("run_id") == new_run.get("run_id")
                and old_run.get("estado") in ("morta", "concluida")
                and new_run.get("estado") == "ativa"):
            raise RevisionConflict("Esta run já foi encerrada; inicie uma nova jornada.")
    return actual + 1


class SnapshotStore(ABC):
    @abstractmethod
    async def read(self, key): ...
    @abstractmethod
    async def keys(self): ...
    @abstractmethod
    async def commit(self, key, payload, expected, create_only=False): ...
    @abstractmethod
    async def delete(self, key, expected): ...

