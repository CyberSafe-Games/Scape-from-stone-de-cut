"""Distribuição estática, manifesto de integridade e configuração offline versionada."""
import hashlib,json,shutil,tarfile,urllib.request
from pathlib import Path,PurePosixPath
from src.systems.web_resources import context_groups

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def safe_relative(name):
    path=PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not path.parts or "\\" in name or ":" in name:
        raise ValueError("Caminho inválido no manifesto: "+name)
    return path

def verify_pack(root,record):
    relative=safe_relative(record["url"]);path=root/relative
    if path.stat().st_size!=record["bytes"] or sha(path)!=record["sha256"]:
        raise ValueError("Integridade do pacote inválida: "+str(path))
    if len(record["files"])!=len(set(record["files"])):raise ValueError("Inventário duplicado.")
    with tarfile.open(path,"r:gz") as archive:
        members=archive.getmembers()
        if any(not m.isfile() or str(safe_relative(m.name)) not in record["files"] for m in members):
            raise ValueError("Arquivo inesperado no pacote: "+record["url"])
        if [m.name for m in members]!=record["files"]:
            raise ValueError("Inventário divergente: "+record["url"])
    return True

def runtime_resources(root,lock):
    folder=root/"build/runtime-cache";folder.mkdir(parents=True,exist_ok=True)
    for record in lock["resources"]:
        if not record["url"].startswith("https://pygame-web.github.io/cdn/"):
            raise ValueError("Origem de runtime não aprovada.")
        path=folder/record["sha256"]
        if not path.exists():
            with urllib.request.urlopen(record["url"],timeout=90) as response:
                path.write_bytes(response.read())
        if path.stat().st_size!=record["bytes"] or sha(path)!=record["sha256"]:
            raise ValueError("Runtime divergiu do lock: "+record["url"])

def distribution(root,stage,output,destination):
    manifest=json.loads((stage/"web_manifest.json").read_text(encoding="utf-8"))
    lock=json.loads((root/"web/runtime-lock.json").read_text(encoding="utf-8"))
    runtime_resources(root,lock)
    for name in ("manifest.webmanifest","pwa.js","install.html"):
        shutil.copyfile(root/"web"/name,output/name)
    shutil.copytree(root/"web/icons",output/"icons",dirs_exist_ok=True)
    shutil.copyfile(root/"web/icons/pwa-192.png",output/"favicon.png")
    shutil.copyfile(stage/"web_manifest.json",output/"web_manifest.json")
    html_path=output/"index.html"
    html=html_path.read_text(encoding="utf-8").replace('lang="en-us"','lang="pt-BR"')
    html=html.replace("</body>",'<script src="pwa.js"></script></body>')
    html_path.write_text(html,encoding="utf-8")
    (output/".nojekyll").touch()
    (output/"_headers").write_text("/service-worker.js\n  Cache-Control: no-cache\n/index.html\n  Cache-Control: no-cache\n/packs/*\n  Cache-Control: public, max-age=31536000, immutable\n",encoding="utf-8")
    packs=[r for values in manifest["groups"].values() for r in values]
    for record in packs:verify_pack(output,record)
    essential_groups=(context_groups("tutorial",1,["slime","viniurgo"])|
        context_groups("battle",1,["slime","viniurgo"])|context_groups("cutscene:intro")|
        context_groups("cutscene:post"))
    essential=[r for group in sorted(essential_groups) for r in manifest["groups"].get(group,[])]
    # O SW nunca inclui a si mesmo na lista que determina sua versão.
    excludes={"service-worker.js","release.json"}
    shell=[dict(url=p.relative_to(output).as_posix(),sha256=sha(p),bytes=p.stat().st_size)
        for p in sorted(output.rglob("*")) if p.is_file() and p.name not in excludes and "packs" not in p.relative_to(output).parts]
    runtime_version=hashlib.sha256(json.dumps(lock,sort_keys=True).encode()).hexdigest()[:16]
    version=hashlib.sha256(json.dumps(dict(shell=shell,packs=packs,runtime=lock),sort_keys=True).encode()).hexdigest()[:16]
    config=dict(version=version,runtimeVersion=runtime_version,shell=shell,runtime=lock["resources"],packs=packs,essential=essential)
    worker=(root/"web/service-worker.js").read_text(encoding="utf-8").replace("__SCAPE_CONFIG__",json.dumps(config,ensure_ascii=True))
    (output/"service-worker.js").write_text(worker,encoding="utf-8")
    release=dict(version=version,initial_package_bytes=(output/"web-poc.tar.gz").stat().st_size,
        shell_bytes=sum(r["bytes"] for r in shell),runtime_bytes=sum(r["bytes"] for r in lock["resources"]),
        essential_bytes=sum(r["bytes"] for r in essential),essential_packs=len(essential),
        campaign_pack_bytes=sum(r["bytes"] for r in packs),pack_count=len(packs),
        files=[dict(path=p.relative_to(output).as_posix(),sha256=sha(p),bytes=p.stat().st_size)
               for p in sorted(output.rglob("*")) if p.is_file() and p.name!="release.json"])
    (output/"release.json").write_text(json.dumps(release,indent=2)+"\n",encoding="utf-8")
    # Só gerenciar arquivos da distribuição anterior dentro de dist/.
    destination=Path(destination).resolve()
    if not destination.is_relative_to((root/"dist").resolve()) or destination==(root/"dist").resolve():
        raise ValueError("Destino deve ser uma subpasta de dist/.")
    destination.mkdir(parents=True,exist_ok=True)
    current={r["path"] for r in release["files"]}|{"release.json"}
    old=destination/"release.json"
    if old.exists():
        previous=json.loads(old.read_text())
        for record in previous["files"]:
            name=str(safe_relative(record["path"]))
            if name not in current:
                candidate=(destination/name).resolve()
                if not candidate.is_relative_to(destination):raise ValueError("Destino inválido.")
                candidate.unlink(missing_ok=True)
    shutil.copytree(output,destination,dirs_exist_ok=True)
    verify_distribution(destination)
    return release

def verify_distribution(folder):
    folder=Path(folder)
    release=json.loads((folder/"release.json").read_text(encoding="utf-8"))
    expected={r["path"] for r in release["files"]}|{"release.json"}
    actual={p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
    if actual!=expected:raise ValueError("Arquivos estranhos/ausentes na distribuição.")
    for record in release["files"]:
        path=folder/str(safe_relative(record["path"]))
        if path.is_symlink() or path.stat().st_size!=record["bytes"] or sha(path)!=record["sha256"]:
            raise ValueError("Hash inválido: "+record["path"])
    manifest=json.loads((folder/"web_manifest.json").read_text())
    for values in manifest["groups"].values():
        for record in values:verify_pack(folder,record)
    return release

