"""Carregamento e descarte cooperativos de recursos da campanha."""
import asyncio
import base64
import gc
import hashlib
import io
import json
from pathlib import Path
import tarfile
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
    async def download(self,pack):
        import platform
        bridge=platform.window.scapeResources
        token=bridge.begin(pack["url"])
        try:
            while True:
                value=json.loads(str(bridge.poll(token)))
                if value.get("error"):raise OSError("Falha ao carregar recursos. "+value["error"])
                self.progress=(self._completed_packs+value["received"]/max(1,value["total"] or pack["bytes"]))/self._total_packs
                if not value["pending"]:break
                await asyncio.sleep(0)
            data=bytearray()
            for offset in range(0,value["received"],262144):
                data.extend(base64.b64decode(str(bridge.chunk(token,offset))))
                await asyncio.sleep(0)
            if hashlib.sha256(data).hexdigest()!=pack["sha256"]:
                raise OSError("Pacote inválido; recarregue a página.")
            expected=set(pack["files"])
            with tarfile.open(fileobj=io.BytesIO(data),mode="r:gz") as archive:
                for index,member in enumerate(archive):
                    if not member.isfile() or member.name not in expected or ".." in Path(member.name).parts:
                        raise OSError("Caminho de recurso inválido.")
                    path=Path(member.name)
                    path.parent.mkdir(parents=True,exist_ok=True)
                    path.write_bytes(archive.extractfile(member).read())
                    if index%8==0:await asyncio.sleep(0)
            self.transfer_bytes+=len(data)
        finally:bridge.release(token)
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
        self.active_context=kind
        self.progress=1
        gc.collect()

