"""Backup JSON validado: não carrega objetos executáveis."""
import asyncio
from pathlib import Path


async def choose_browser_import(store):
    token = store.bridge.chooseImport()
    import json
    from .base import StorageError
    while True:
        result = json.loads(str(store.bridge.poll(token)))
        if result.get("pending"):
            await asyncio.sleep(0)
            continue
        if not result.get("ok"):
            raise StorageError(result.get("error",{}).get("message","Backup inválido."))
        return result.get("value")


def desktop_file(operation):
    # Importação tardia: não inicializa toolkit fora do comando desktop.
    from tkinter import Tk, filedialog
    root = Tk()
    root.withdraw()
    try:
        if operation == "export":
            return filedialog.asksaveasfilename(title="Exportar jornada",defaultextension=".json",
                                                filetypes=[("Backup JSON","*.json")],initialfile="scape-save.json")
        return filedialog.askopenfilename(title="Importar jornada",filetypes=[("Backup JSON","*.json")])
    finally:
        root.destroy()

