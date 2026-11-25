"""Gera e exercita o executável/instalador em diretórios de QA, sem slots pessoais."""
import argparse,hashlib,json,os,re,subprocess,sys,tempfile,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP_KEY=r"Software\Microsoft\Windows\CurrentVersion\Uninstall\{C92D740B-47E8-460D-B4E5-2CA152886C3A}_is1"

def installed():
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,APP_KEY):return True
    except FileNotFoundError:return False

def run_command(args,log,*,env=None,timeout=240):
    with Path(log).open("w",encoding="utf-8") as output:
        startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
        result=subprocess.run(args,cwd=ROOT,env=env,stdout=output,stderr=subprocess.STDOUT,
            timeout=timeout,startupinfo=startup)
    if result.returncode:raise RuntimeError("Comando falhou: "+str(args[0])+"; veja "+str(log))

def user_data_fingerprint(folder):
    if not folder.exists():return None
    return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in folder.rglob("*.json") if p.is_file()}

def smoke(executable,target,env):
    run_command([str(executable),"--smoke-report",str(target)],target.with_suffix(".log"),env=env,timeout=60)
    report=json.loads(target.read_text(encoding="utf-8"))
    if not report["passed"] or not report["frozen"] or report["web_dependencies_loaded"]:
        raise RuntimeError("Verificação nativa falhou: "+str(report))
    return report

def verify_bundled_assets():
    source=ROOT/"assets"
    bundled=ROOT/"dist/ScapeFromStoneDeCut/_internal/assets"
    originals={p.relative_to(source).as_posix():p for p in source.rglob("*") if p.is_file()}
    copies={p.relative_to(bundled).as_posix():p for p in bundled.rglob("*") if p.is_file()}
    if set(originals)!=set(copies):raise RuntimeError("Inventário de assets do executável divergiu.")
    for name,path in originals.items():
        if hashlib.sha256(path.read_bytes()).digest()!=hashlib.sha256(copies[name].read_bytes()).digest():
            raise RuntimeError("Asset divergiu no executável: "+name)
    return dict(files=len(originals),bytes=sum(p.stat().st_size for p in originals.values()),sha256_match=True)

def main():
    if os.name!="nt":raise SystemExit("Esta validação requer Windows.")
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iscc",type=Path,required=True)
    parser.add_argument("--skip-install",action="store_true")
    args=parser.parse_args()
    out=ROOT/"build/web-stage7";out.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy();env["PATH"]=str(args.iscc.resolve().parent)+os.pathsep+env["PATH"]
    env["SDL_VIDEODRIVER"]=env["SDL_AUDIODRIVER"]="dummy"
    build_python=ROOT/".venv-build/Scripts/python.exe"
    libraries=json.loads(subprocess.check_output([str(build_python),"-c",
        "import importlib.util,json;print(json.dumps({m:importlib.util.find_spec(m) is not None for m in ('pygbag','playwright')}))"],text=True))
    if any(libraries.values()):raise RuntimeError("Ambiente nativo contém dependências exclusivas da web.")
    print("Gerando executável e instalador com o batch oficial…",flush=True)
    run_command(["cmd.exe","/d","/c","installer\\build_installer.bat"],out/"windows-build.log",env=env,timeout=600)
    version=(ROOT/"VERSION").read_text().strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+",version):raise RuntimeError("Versão inválida")
    setup=ROOT/f"ScapeFromStoneDeCut-Setup-{version}.exe"
    executable=ROOT/"dist/ScapeFromStoneDeCut/ScapeFromStoneDeCut.exe"
    report=dict(passed=False,python=subprocess.check_output([str(build_python),"--version"],text=True).strip(),
        no_web_libraries=libraries,installer=dict(path=setup.name,bytes=setup.stat().st_size,sha256=hashlib.sha256(setup.read_bytes()).hexdigest()),
        executable=dict(path=executable.relative_to(ROOT).as_posix(),bytes=executable.stat().st_size))
    report["assets"]=verify_bundled_assets()
    print("Verificando o executável portátil…",flush=True)
    sandbox=out/"localappdata";sandbox.mkdir(exist_ok=True)
    smoke_env=dict(env,LOCALAPPDATA=str(sandbox.resolve()))
    report["portable"]=smoke(executable,out/"portable-native.json",smoke_env)
    actual_data=Path(os.environ["LOCALAPPDATA"])/"ScapeFromStoneDeCut"
    before=user_data_fingerprint(actual_data)
    if args.skip_install or installed():
        report["installation_skipped"]="Solicitado ou instalação pessoal já registrada; preservada."
    else:
        with tempfile.TemporaryDirectory(prefix="windows-install-qa-",dir=ROOT/"build") as temporary:
            temporary=Path(temporary).resolve()
            assert temporary.is_relative_to((ROOT/"build").resolve())
            destination=temporary/"game"
            print("Instalando em pasta temporária e verificando o executável instalado…",flush=True)
            try:
                run_command([str(setup),"/VERYSILENT","/SUPPRESSMSGBOXES","/NORESTART","/NOICONS","/TASKS=",
                    "/DIR="+str(destination),"/LOG="+str(out/"install.log")],out/"install-process.log",env=env)
                report["installed"]=smoke(destination/"ScapeFromStoneDeCut.exe",out/"installed-native.json",smoke_env)
            finally:
                uninstaller=destination/"unins000.exe"
                if uninstaller.is_file():
                    print("Removendo somente a instalação de QA…",flush=True)
                    run_command([str(uninstaller),"/VERYSILENT","/SUPPRESSMSGBOXES","/NORESTART",
                        "/LOG="+str(out/"uninstall.log")],out/"uninstall-process.log",env=env)
                    deadline=time.monotonic()+10
                    while uninstaller.exists() and time.monotonic()<deadline:time.sleep(.1)
            if installed():raise RuntimeError("A instalação de QA deixou registro de instalação.")
            report["silent_uninstall"]=True
    after=user_data_fingerprint(actual_data)
    if after!=before:raise RuntimeError("Dados pessoais foram alterados durante QA.")
    report["personal_json_data_preserved"]=True
    report["passed"]=True
    (out/"windows-result.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(passed=True,installer_bytes=setup.stat().st_size,installed_test="installed" in report),ensure_ascii=True),flush=True)
if __name__=="__main__":main()

