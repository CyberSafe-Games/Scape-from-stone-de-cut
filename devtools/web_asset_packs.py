"""Produz manifesto completo e pacotes independentes do arquivo inicial Pygbag."""
import gzip
import hashlib
import json
from pathlib import Path
import re
import tarfile
from src.systems.web_resources import owner

PACK_LIMIT = 8*1024*1024

def build_packs(root,stage):
    resources=sorted(p for p in (root/"assets").rglob("*")
                     if p.is_file() and p.suffix.lower() in (".png",".jpg",".jpeg",".ogg",".wav",".ttf",".json"))
    groups={}
    for path in resources:
        groups.setdefault(owner(path.relative_to(root).as_posix()),[]).append(path)
    output=stage/"build/web/packs"
    output.mkdir(parents=True,exist_ok=True)
    manifest={"version":1,"groups":{},"files":{}}
    initial=[]
    for group,paths in sorted(groups.items()):
        if group=="menu":
            initial.extend(paths)
            for path in paths:manifest["files"][path.relative_to(root).as_posix()]="menu"
            continue
        chunks=[];current=[];size=0
        for path in paths:
            if current and size+path.stat().st_size>PACK_LIMIT:
                chunks.append(current);current=[];size=0
            current.append(path);size+=path.stat().st_size
        if current:chunks.append(current)
        packs=[]
        for index,chunk in enumerate(chunks):
            prefix=re.sub(r"[^a-zA-Z0-9_-]","_",group)+f"-{index}"
            target=output/(prefix+".tar.gz")
            with target.open("wb") as raw:
                with gzip.GzipFile(fileobj=raw,mode="wb",filename="",mtime=0,compresslevel=1) as compressed:
                    with tarfile.open(fileobj=compressed,mode="w") as archive:
                        for path in chunk:
                            info=archive.gettarinfo(str(path),arcname=path.relative_to(root).as_posix())
                            info.mtime=0
                            info.uid=info.gid=0
                            info.uname=info.gname=""
                            info.mode=0o644
                            with path.open("rb") as source:archive.addfile(info,source)
            digest=hashlib.sha256(target.read_bytes()).hexdigest()
            final=target.with_name(prefix+"-"+digest[:12]+".tar.gz")
            target.replace(final)
            files=[p.relative_to(root).as_posix() for p in chunk]
            for name in files:manifest["files"][name]=group
            packs.append({"url":"packs/"+final.name,"bytes":final.stat().st_size,
                          "sha256":digest,"files":files})
        manifest["groups"][group]=packs
    keep={Path(pack["url"]).name for packs in manifest["groups"].values() for pack in packs}
    for old in output.glob("*.tar.gz"):
        if old.name not in keep:old.unlink()
    manifest["source_bytes"]=sum(p.stat().st_size for p in resources)
    manifest["initial_asset_bytes"]=sum(p.stat().st_size for p in initial)
    (stage/"web_manifest.json").write_text(json.dumps(manifest,ensure_ascii=True),encoding="utf-8")
    keep={p.relative_to(root).as_posix() for p in initial}
    keep.update(("assets/fonts/NotoSansSymbols2-Regular.ttf","assets/fonts/OFL.txt"))
    active=stage/"assets"
    for path in active.rglob("*"):
        if path.is_file() and path.relative_to(stage).as_posix() not in keep:path.unlink()
    import shutil
    for path in initial:
        dest=stage/path.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
    return manifest

