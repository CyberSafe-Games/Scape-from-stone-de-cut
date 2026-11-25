"""Carregamento e descarte cooperativos de recursos da campanha."""
import asyncio
import base64
import gc
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile
import shutil
from web.memfs import asset_path, prune_animations
from src.core.asset_manager import AssetManager
from src.systems.web_resources import context_groups,working_set

class CampaignAssets(AssetManager):
    def __init__(self):
        super().__init__(preload=False)
        from web.poc import ProofFont
        self._fonts={key:ProofFont(font) for key,font in self._fonts.items()}
        self.manifest=json.loads(Path("web_manifest.json").read_text())
        self.resident={"menu"}
        self.progress=0
        self.label=""
        self.transfer_bytes=0
        self.active_context="menu"
        self.pruned_groups=set()
        self.memfs_freed_bytes=0
        self.pack_temporary_bytes=0
    async def download(self,pack):
        import platform
        bridge=platform.window.scapeResources
        token=bridge.begin(pack["url"])
        temporary=None
        written=[]
        released=False
        try:
            while True:
                value=json.loads(str(bridge.poll(token)))
                if value.get("error"):raise OSError("Falha ao carregar recursos. "+value["error"])
                self.progress=(self._completed_packs+value["received"]/max(1,value["total"] or pack["bytes"]))/self._total_packs
                if not value["pending"]:break
                await asyncio.sleep(0)
            if value["received"] != pack["bytes"]:
                raise OSError("Pacote incompleto; tente novamente.")
            digest=hashlib.sha256()
            # Uma única cópia comprimida no MEMFS; nunca BytesIO(bytearray inteiro).
            with tempfile.NamedTemporaryFile(prefix="scape-pack-",suffix=".tmp",delete=False) as output:
                temporary=Path(output.name)
                for offset in range(0,value["received"],262144):
                    chunk=base64.b64decode(str(bridge.chunk(token,offset)))
                    digest.update(chunk);output.write(chunk)
                    await asyncio.sleep(0)
            self.pack_temporary_bytes=temporary.stat().st_size
            if digest.hexdigest()!=pack["sha256"]:
                raise OSError("Pacote inválido; recarregue a página.")
            # Soltar os bytes JS antes de expandir os membros do tar no WASM.
            bridge.release(token);released=True
            expected=set(pack["files"]);seen=set()
            if len(expected)!=len(pack["files"]):raise OSError("Inventário duplicado.")
            with tarfile.open(temporary,mode="r:gz") as archive:
                for index,member in enumerate(archive):
                    if not member.isfile() or member.name not in expected or member.name in seen:
                        raise OSError("Caminho de recurso inválido.")
                    path=asset_path(member.name);seen.add(member.name)
                    path.parent.mkdir(parents=True,exist_ok=True)
                    written.append(path)
                    with archive.extractfile(member) as source,path.open("wb") as output:
                        shutil.copyfileobj(source,output,length=262144)
                    if index%8==0:await asyncio.sleep(0)
            if seen!=expected:raise OSError("Inventário de recursos incompleto.")
            self.transfer_bytes+=value["received"]
        except BaseException:
            for path in written:path.unlink(missing_ok=True)
            raise
        finally:
            if not released:bridge.release(token)
            if temporary is not None:temporary.unlink(missing_ok=True)
            self.pack_temporary_bytes=0
    def release_surfaces(self):
        for key in ("_enemy_sprites","_enemy_projectiles","_boss_ultimate_sprites","_boss_ultimate_effects",
                    "_boss_original_groups","_boss_original_ultimates","_player_sprites","_card_action_sprites",
                    "_ultimate_effect_sprites","_territory_backgrounds","_character_portraits",
                    "_projectile_images","_intent_art"):
            value=getattr(self,key,None)
            if isinstance(value,dict):value.clear()
        self._background_tutorial=None
        from src.ui.render_cache import clear_context_caches
        clear_context_caches()
        gc.collect()
    async def prepare(self,kind,level=1,names=(),cards=()):
        from src.systems.boss_animation_kits import KITS
        from src.systems.common_animation_kits import COMMON_KITS
        from src.systems.boss_ultimate_animations import BOSS_ULTIMATE_ANIMATIONS
        slugs=set()
        names={name.lower() for name in names}
        for name in names:
            item=(KITS|COMMON_KITS).get(name)
            if item:slugs.add(item[0].split("_phase")[0])
        if any(n.startswith("álvaro") for n in names):
            names.update(("álvaro e tex","álvaro e tex · pequeno"));slugs.add("alvaro_tex")
        wanted=working_set(kind,context_groups(kind,level,slugs),self.resident)
        self.release_surfaces()
        if "management" not in wanted:
            for key in ("_ui_images","_card_images","_ultimate_images","_ultimate_sources",
                        "_ultimate_layouts","_map_icons","_status_icons"):
                getattr(self,key).clear()
        for old in self.resident-wanted:
            for pack in self.manifest["groups"].get(old,[]):
                for name in pack["files"]:
                    path=Path(name)
                    if path.is_file():path.unlink()
        self.resident.intersection_update(wanted)
        # Os objetos SDL antigos já foram soltos; repor arquivos consumidos antes dos loaders.
        if kind in ("battle","tutorial"):
            self.resident.difference_update(self.pruned_groups)
        self.pruned_groups.intersection_update(wanted)
        total=sum(len(self.manifest["groups"].get(group,[])) for group in wanted-self.resident)
        self._completed_packs=0
        self._total_packs=max(1,total)
        for group in sorted(wanted-self.resident):
            labels={"management":"Mapa e acampamento","player":"Magias e equipamentos",
                    "audio":"Sons da floresta","combat_shared":"Preparando o combate","tutorial":"Primeiros passos"}
            self.label=labels.get(group, "Memórias da tribo" if group.startswith("cutscene:") else
                "Preparando o adversário" if group.startswith("enemy:") else
                "Trilha da jornada" if group.startswith("music:") else "Explorando o território")
            for pack in self.manifest["groups"].get(group,[]):
                await self.download(pack)
                self._completed_packs+=1
            self.resident.add(group)
            self.pruned_groups.discard(group)
        self.label="Preparando imagens"
        if "management" in wanted:
            self._load_ui_images();self._load_ultimate_images();self._load_coin_icon()
        if kind in ("battle","tutorial"):
            self.CARD_ACTION_FILES={key:value for key,value in AssetManager.CARD_ACTION_FILES.items() if key in cards}
            for work in (self._load_player_sprites,self._load_card_action_sprites,
                         self._load_player_eight_frames,self._load_enemy_sprites):
                work();await asyncio.sleep(0)
            self._load_common_eight_frames(names)
            await asyncio.sleep(0)
            self._load_boss_ultimate_sprites(names)
            await asyncio.sleep(0)
            self._load_boss_eight_frame_sprites(names)
            self._load_defeat_poses()
            self._load_territory_backgrounds()
            if kind=="tutorial":self._load_tutorial_background()
        if kind in ("battle","tutorial"):
            removed,freed=prune_animations(self.manifest,self.resident)
            self.pruned_groups.update(removed)
            self.memfs_freed_bytes+=freed
        self.active_context=kind
        self.progress=1
        gc.collect()

