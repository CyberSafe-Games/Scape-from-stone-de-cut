"""Gera campanha web estática, recursos por contexto e PWA; --poc mantém a prova anterior."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
STAGE = ROOT / "build" / "web-poc"


def selected_assets():
    patterns = [
        "background.png", "fonts/IgarapePixel-*.ttf",
        "cards/*.png", "cards/lv2/*.png",
        "ui/shop/*.png", "ui/workshop/*.png", "ui/backpack/*.png", "ui/options/*.png",
        "cards/art_manifest.json", "cards/soco_simples.png", "cards/esfera_protetora.png",
        "ultimates/*.png", "ultimates/art_manifest.json",
        "ui/hud_hand_tray.png", "ui/hud_health.png", "ui/hud_cemetery.png",
        "ui/battle_hud_frame_top.png", "ui/battle_hud_frame_bottom.png",
        "portraits/source/framed/manel.png", "portraits/source/dedicated/slime.png",
        "enemies/eight_frames/slime/*.png", "enemies/defeat/slime.png",
        "icons/moeda.png", "status/*.png", "intent_art/slime/*.png",
        "projectiles/slime*.png",
        "player/eight_frames/idle_*.png", "player/eight_frames/dano_*.png",
        "player/twelve_frames/soco_*.png", "player/twelve_frames/vitoria_*.png",
        "player/twelve_frames/soco_simples_*.png", "player/twelve_frames/esfera_protetora_*.png",
        "player/twelve_frames/mana_ancestral_*.png",
        "audio/music/menu_floresta_v1.ogg", "audio/music/combate_tambores_v1.ogg",
        "audio/ui/*.ogg", "audio/card-place-2.ogg", "audio/chip-lay-1.ogg",
        "audio/victory_fanfare_2_curta.ogg", "audio/game_over_risada_apos_fala_v4.ogg",
        "audio/soco_impacto_suave_v2.ogg", "audio/esfera_protetora_leve_curta.ogg",
        "audio/slime_corpo_fragilizante.ogg", "audio/inimigo_acido.ogg",
        "audio/veneno_dano_corrosivo_v1.ogg", "audio/ultimate_xamanico_opcao_2.ogg",
        "ui/rewards/*.png",
    ]
    return sorted({p for pattern in patterns for p in (ROOT/"assets").glob(pattern) if p.is_file() and p.name != "reference.png"})


def prepare():
    STAGE.mkdir(parents=True, exist_ok=True)
    allowed={"assets","src","web","build","main.py","desktop_entry.py","proof_manifest.json","web_manifest.json"}
    unexpected={p.name for p in STAGE.iterdir()}-allowed
    if unexpected:
        raise ValueError("Arquivos estranhos na área de empacotamento: "+str(sorted(unexpected)))
    # Copiar somente fontes .py evita incluir caches, relatórios e ambientes.
    for source in (ROOT/"src").rglob("*.py"):
        dest = STAGE/source.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
    for source in (ROOT/"web").glob("*.py"):
        dest = STAGE/"web"/source.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
    shutil.copyfile(ROOT/"web/main.py", STAGE/"main.py")
    shutil.copyfile(ROOT/"main.py", STAGE/"desktop_entry.py")
    resources = selected_assets()
    allowed_assets={p.relative_to(ROOT).as_posix() for p in resources}
    allowed_assets.update({"assets/fonts/NotoSansSymbols2-Regular.ttf","assets/fonts/OFL.txt"})
    staged_assets=STAGE/"assets"
    if staged_assets.exists():
        if staged_assets.resolve().parent != STAGE.resolve():
            raise ValueError("Área de assets fora do diretório de build")
        for previous in staged_assets.rglob("*"):
            if previous.is_file() and previous.relative_to(STAGE).as_posix() not in allowed_assets:
                previous.unlink()
    for source in resources:
        dest = STAGE/source.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
    fonts = STAGE/"assets/fonts"
    sources = {
        "NotoSansSymbols2-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssymbols2/NotoSansSymbols2-Regular.ttf",
        "OFL.txt": "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssymbols2/OFL.txt",
    }
    expected = {
        "NotoSansSymbols2-Regular.ttf": "7d5fb73b7ca67a6798101741f5d280a3d016a56a197afcd4199dbb57b4b82a21",
        "OFL.txt": "b118dd41337806a5d4797052c77caf3bd096aed783e5eb21b4d11154351e1ac0",
    }
    for filename, url in sources.items():
        target = fonts/filename
        if not target.exists():
            with urllib.request.urlopen(url, timeout=60) as response:
                target.write_bytes(response.read())
        if hashlib.sha256(target.read_bytes()).hexdigest() != expected[filename]:
            raise ValueError("Fonte/licença divergente da versão auditada: " + filename)
    files = [*resources, *(fonts/name for name in sources)]
    manifest = {
        "scope": "Etapas 1–3: Slime e gerenciamento com IndexedDB",
        "assets_count": len(files),
        "assets_bytes": sum(p.stat().st_size for p in files),
        "assets": [p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT/"assets") else
                   "assets/fonts/"+p.name for p in files],
        "font_sources": {name: {"url":url, "sha256":hashlib.sha256((fonts/name).read_bytes()).hexdigest()}
                         for name,url in sources.items()},
    }
    (STAGE/"proof_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in manifest.items() if k not in ("assets","font_sources")},ensure_ascii=False))
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-only",action="store_true")
    parser.add_argument("--serve",action="store_true")
    parser.add_argument("--poc",action="store_true",help="Preserva o piloto das Etapas 1–3.")
    parser.add_argument("--dist-dir",default="dist/web",help="Subpasta de dist/ para hospedagem estática.")
    args=parser.parse_args()
    prepare()
    if args.poc:
        (STAGE/"web_manifest.json").unlink(missing_ok=True)
    if not args.poc:
        from devtools.web_asset_packs import build_packs
        manifest=build_packs(ROOT,STAGE)
        print(json.dumps({"full_assets":len(manifest["files"]),"groups":len(manifest["groups"]),
                          "initial_asset_bytes":manifest["initial_asset_bytes"]}))
    if not args.prepare_only:
        command=[sys.executable,"-m","pygbag","--no_opt","--ume_block","0","--width","1280","--height","720","--title","Scape From Stone"]
        command.append("--build")
        subprocess.run([*command,str(STAGE)],cwd=ROOT,check=True)
        output=STAGE/"build/web"
        with tarfile.open(output/"web-poc.tar.gz","r:gz") as archive:
            names=archive.getnames()
        allowed_prefixes=("assets/assets/","assets/src/","assets/web/")
        allowed_files={"assets/main.py","assets/desktop_entry.py","assets/proof_manifest.json","assets/web_manifest.json"}
        unexpected=[name for name in names if name not in allowed_files and not name.startswith(allowed_prefixes)]
        if unexpected:
            raise ValueError("Pacote contém arquivos fora da prova: "+str(unexpected[:5]))
        shutil.copyfile(ROOT/"web/styles.css",output/"styles.css")
        shutil.copyfile(ROOT/"web/bridge.js",output/"bridge.js")
        shutil.copyfile(ROOT/"web/storage.js",output/"storage.js")
        shutil.copyfile(ROOT/"web/resources.js",output/"resources.js")
        shutil.copyfile(ROOT/"web/mobile.js",output/"mobile.js")
        index=output/"index.html"
        html=index.read_text(encoding="utf-8")
        html=html.replace("</head>",'<link rel="stylesheet" href="styles.css"></head>')
        html=html.replace("</body>",'<script src="bridge.js"></script><script src="storage.js"></script><script src="resources.js"></script></body>')
        import re
        fragment=(ROOT/"web/index.html").read_text(encoding="utf-8")
        pwa_head=re.search(r"<!-- PWA_HEAD -->(.*?)<!-- /PWA_HEAD -->",fragment,re.DOTALL)
        if pwa_head:
            if not args.poc:html=html.replace("</head>",pwa_head.group(1)+"</head>")
            fragment=fragment.replace(pwa_head.group(0),"")
        viewport=re.search(r'<meta name="viewport"[^>]*>',fragment).group()
        html=re.sub(r'<meta\s+name="viewport"[^>]*>',"",html,flags=re.IGNORECASE)
        html=html.replace("</head>",viewport+"</head>")
        html=html.replace("</body>",fragment.replace(viewport,"")+"</body>")
        index.write_text(html,encoding="utf-8")
        destination=output
        if not args.poc:
            from devtools.web_distribution import distribution
            release=distribution(ROOT,STAGE,output,ROOT/args.dist_dir)
            destination=ROOT/args.dist_dir
            print(json.dumps({"distribution":str(destination),"release":release["version"],
                              "essential_bytes":release["essential_bytes"],"runtime_bytes":release["runtime_bytes"]}))
        if args.serve:
            subprocess.run([sys.executable,"-m","http.server","8765","--bind","127.0.0.1",
                            "--directory",str(destination)],cwd=ROOT,check=True)


if __name__=="__main__":
    main()

