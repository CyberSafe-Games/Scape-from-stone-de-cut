"""Validação PWA Chromium em perfil isolado, subpasta /game/ e servidor de falhas."""
import json,shutil,time,threading,tempfile,socket,runpy,os
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"build/web-stage6";OUT.mkdir(exist_ok=True)

def run():
    if not (ROOT/"build/web-stage4/fixtures/1-0.json").exists():
        runpy.run_path(str(ROOT/"devtools/generate_web_campaign_fixtures.py"),run_name="__main__")
    with tempfile.TemporaryDirectory(prefix="pwa-qa-",dir=ROOT/"build") as temporary:
        base=Path(temporary).resolve()
        assert base.is_relative_to((ROOT/"build").resolve())
        game=base/"game";shutil.copytree(ROOT/"dist/web",game)
        faults={}
        class Handler(SimpleHTTPRequestHandler):
            def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(base),**kwargs)
            def log_message(self,*args):pass
            def do_GET(self):
                if self.path==faults.get("truncate"):
                    data=(base/self.path.lstrip("/")).read_bytes()
                    self.send_response(200);self.send_header("Content-Length",str(len(data)));self.end_headers()
                    self.wfile.write(data[:1024]);self.wfile.flush()
                    self.connection.shutdown(socket.SHUT_RDWR);self.connection.close();return
                super().do_GET()
        server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        url=f"http://127.0.0.1:{server.server_port}/game/"
        logs=[];checks=[];installed=False
        with sync_playwright() as p:
            context=p.chromium.launch_persistent_context(str(base/"profile"),channel="chromium",headless=os.environ.get("SCAPE_PWA_HEADED")!="1",args=["--window-position=-32000,-32000"],viewport={"width":1280,"height":720})
            page=context.pages[0]
            page.on("console",lambda m:logs.append(m.type+": "+m.text))
            page.on("pageerror",lambda e:logs.append("PAGEERROR "+str(e)))
            cdp=context.new_cdp_session(page)
            browser_cdp=context.browser.new_browser_cdp_session()
            def record(name):
                checks.append(name);print("OK "+name,flush=True)
            def state():return page.evaluate("window.webStorageMetrics ? JSON.parse(webStorageMetrics):null")
            def wait(predicate,seconds=150,target=None):
                target=target or page;end=time.monotonic()+seconds
                while time.monotonic()<end:
                    try:
                        error=target.evaluate("window.webRuntimeError||null")
                        if error:raise AssertionError(error)
                        data=target.evaluate("window.webStorageMetrics ? JSON.parse(webStorageMetrics):null")
                        if predicate(data):return data
                        if data and data.get("error"):raise AssertionError(data["error"])
                    except Exception as e:
                        if "Execution context was destroyed" not in str(e):raise
                    target.wait_for_timeout(180)
                raise AssertionError("Timeout: "+str(state()))
            def scene(name):return wait(lambda m:m and m["scene"]==name and not m["saving"])
            def click(x,y):page.mouse.click(x*2/3,y*2/3);page.wait_for_timeout(120)
            def rect(r):click(r[0]+r[2]/2,r[1]+r[3]/2)
            def sw_status():
                return page.evaluate("window.scapePWA ? JSON.parse(JSON.stringify(scapePWA)):null")
            def fight():
                end=time.monotonic()+90
                while time.monotonic()<end:
                    m=state()
                    if m["victory_ready"]:return m
                    if m["state"]=="player_turn" and not m["saving"] and not m["action"]:
                        indices=sorted(range(len(m["hand"])),key=lambda i:"Soco" not in m["hand"][i]["name"])
                        usable=next((i for i in indices if m["hand"][i]["cost"]<=m["energy"]),None)
                        if usable is None:rect(m["ui"]["end_turn_rect"])
                        else:rect(m["hand"][usable]["rect"])
                    page.wait_for_timeout(300)
                raise AssertionError("Combate não terminou: "+str(state()))
            try:
                page.goto(url);scene("CampaignMenu")
                page.wait_for_function("window.scapePWA?.offlineReady",timeout=180000)
                version=sw_status()["version"]
                cdp.send("Page.enable")
                app_manifest=cdp.send("Page.getAppManifest")
                (OUT/"install-manifest.json").write_text(json.dumps(app_manifest,indent=2),encoding="utf-8")
                assert not app_manifest.get("errors"),app_manifest
                issues=cdp.send("Page.getInstallabilityErrors")
                assert not issues.get("installabilityErrors"),issues
                record("manifest_installability_and_subpath_scope")
                # Instalação real no perfil temporário, removida ao final.
                for attempt in range(2):
                    try:
                        browser_cdp.send("PWA.install",{"manifestId":url,"installUrlOrBundleUrl":url+"install.html"})
                        break
                    except Exception as error:
                        if attempt or "Couldn't fetch install info" not in str(error):raise
                        page.wait_for_timeout(1000)
                installed=True
                browser_cdp.send("PWA.changeAppUserSettings",{"manifestId":url,"displayMode":"standalone"})
                launched=browser_cdp.send("PWA.launch",{"manifestId":url})
                assert launched.get("targetId"),launched
                page.wait_for_timeout(1000)
                app_pages=[candidate for candidate in context.pages if candidate!=page and candidate.url.startswith(url)]
                assert app_pages,"Janela instalada não encontrada"
                app_page=app_pages[-1]
                app_page.wait_for_load_state("domcontentloaded")
                assert app_page.evaluate("matchMedia('(display-mode: standalone)').matches")
                for candidate in app_pages:candidate.close()
                page.bring_to_front()
                page.evaluate("window.dispatchEvent(new Event('focus'))")
                record("install_and_launch_standalone")
                # Desativar cache HTTP prova que o SW, e não o cache comum, fornece o runtime.
                cdp.send("Network.enable");cdp.send("Network.setCacheDisabled",{"cacheDisabled":True})
                cdp.send("Network.clearBrowserCache")
                context.set_offline(True);page.reload();scene("CampaignMenu")
                page.wait_for_function("window.scapePWA?.offlineReady",timeout=15000)
                record("cold_reload_offline_runtime_without_http_cache")
                # Jornada nova offline, introdução, tutorial real e gravação v15.
                rect(state()["ui"]["play_button"]);scene("CampaignSlots")
                click(960,520);scene("CampaignCutscene");rect(state()["ui"]["skip_button"])
                scene("CampaignTutorial");page.keyboard.press("Escape")
                wait(lambda m:not m.get("tutorial_active",False))
                fight();rect(state()["ui"]["finish_tutorial_button_rect"])
                scene("CampaignCutscene");rect(state()["ui"]["skip_button"]);scene("CampaignMap")
                if state().get("guide_open"):rect(state()["ui"]["guide_button"]);wait(lambda m:not m["guide_open"] and not m["saving"])
                assert state()["data"]["perfil"]["tutorial_concluido"]
                page.screenshot(path=str(OUT/"offline-map.png"))
                record("offline_new_slot_intro_tutorial_and_indexeddb")
                rect(state()["ui"]["back_button"]);scene("CampaignMenu")
                # Importar checkpoint QA em slot vazio, pela interface original.
                rect(state()["ui"]["play_button"]);scene("CampaignSlots")
                rect(state()["rect_maps"]["backup_buttons"]["import"]);wait(lambda m:m["modal"]=="BackupModal")
                with page.expect_file_chooser() as chooser:click(960,366)
                chooser.value.set_files(str(ROOT/"build/web-stage4/fixtures/1-0.json"))
                wait(lambda m:m["modal"] is None and not m["saving"])
                click(443,520);scene("CampaignMap");rect(state()["ui"]["play_button"]);scene("CampaignBattle")
                record("offline_context_loading_and_live_battle")
                manifest=json.loads((game/"web_manifest.json").read_text())
                config_script=(game/"service-worker.js").read_text(encoding="utf-8")
                config=json.loads(config_script.split("const CONFIG=",1)[1].split(";\n",1)[0])
                essential={r["url"] for r in config["essential"]}
                optional=next(r for r in config["packs"] if r["url"] not in essential)
                missing=page.evaluate("async path=>{const r=await fetch(path);return {status:r.status,body:await r.json()}}",optional["url"])
                assert missing["status"]==503 and "conexão" in missing["body"]["message"],missing
                record("offline_missing_context_friendly_retry")
                context.set_offline(False)
                faults["truncate"]="/game/"+optional["url"]
                partial=page.evaluate("async path=>{const r=await fetch(path);await r.arrayBuffer();return {status:r.status};}",optional["url"])
                assert partial["status"]==503,partial
                cached=page.evaluate("async path=>{for(const n of await caches.keys()){if(n.endsWith(':packs')&&await (await caches.open(n)).match(new URL(path,location.href)))return true;}return false;}",optional["url"])
                assert not cached,"Pacote parcial foi publicado no cache"
                faults.clear()
                complete=page.evaluate("async path=>{const r=await fetch(path);const data=await r.arrayBuffer();return {status:r.status,bytes:data.byteLength};}",optional["url"])
                assert complete["status"]==200,complete
                record("interrupted_package_not_cached_and_retry_succeeds")
                # Preparar worker v2 sem alterar assets: atualização permanece em espera.
                next_version=version+"-qa2"
                (game/"service-worker.js").write_text(config_script.replace('"version": "'+version+'"','"version": "'+next_version+'"',1),encoding="utf-8")
                page.evaluate("async()=>{const r=await navigator.serviceWorker.getRegistration();await r.update();}")
                waiting_deadline=time.monotonic()+90
                while not page.evaluate("navigator.serviceWorker.getRegistration().then(r=>Boolean(r.waiting))"):
                    if time.monotonic()>waiting_deadline:raise AssertionError("Worker novo não concluiu a instalação")
                    page.wait_for_timeout(250)
                frame=state()["frames"]
                page.evaluate("navigator.serviceWorker.getRegistration().then(r=>r.waiting.postMessage({type:'APPLY_UPDATE'}))")
                page.wait_for_timeout(3500)
                assert sw_status()["version"]==version
                assert state()["scene"]=="CampaignBattle" and state()["frames"]>frame
                record("waiting_update_does_not_interrupt_battle")
                other=context.new_page();other.goto(url)
                wait(lambda m:m and m["scene"]=="CampaignMenu" and not m["saving"],target=other)
                other.evaluate("navigator.serviceWorker.getRegistration().then(r=>r.waiting.postMessage({type:'APPLY_UPDATE'}))")
                other.wait_for_timeout(3500)
                assert state()["scene"]=="CampaignBattle"
                assert other.evaluate("window.scapePWA.version")==version
                assert not other.evaluate("window.scapePWA.updating")
                record("update_rejected_while_other_tab_is_in_battle")
                page.bring_to_front();page.evaluate("window.dispatchEvent(new Event('focus'))")
                victory=fight()
                if victory["reward_offers"]:rect(victory["reward_offers"][0]["rect"]);click(1477,953)
                else:click(900,953)
                scene("CampaignMap");rect(state()["ui"]["back_button"]);scene("CampaignMenu")
                page.evaluate("navigator.serviceWorker.getRegistration().then(r=>r.waiting.postMessage({type:'APPLY_UPDATE'}))")
                page.wait_for_function("window.scapePWA?.version=== '"+next_version+"'",timeout=90000,polling=200)
                wait(lambda m:m and m["scene"]=="CampaignMenu" and not m["saving"])
                other.wait_for_function("window.scapePWA?.version=== '"+next_version+"'",timeout=90000,polling=200)
                keys=page.evaluate("caches.keys()")
                assert not any(n.endswith("shell-"+version) for n in keys),keys
                rect(state()["ui"]["play_button"]);scene("CampaignSlots")
                click(443,520);scene("CampaignMap")
                assert state()["data"]["progresso"]["encontros_por_territorio"]["stone_the_cut"]==1
                record("safe_menu_update_all_tabs_and_save_preserved")
                result=dict(passed=True,browser=context.browser.version,checks=checks,installability=issues,
                    pwa_installed_launched=True,initial_version=version,updated_version=next_version,
                    offline_resources=dict(runtime=len(config["runtime"]),essential_packs=len(config["essential"])),
                    storage_estimate=page.evaluate("navigator.storage.estimate()"),
                    errors=[line for line in logs if line.startswith("PAGEERROR")])
                assert not result["errors"],result["errors"]
                (OUT/"pwa-result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
                print(json.dumps(result,ensure_ascii=True),flush=True)
            except Exception:
                page.screenshot(path=str(OUT/"pwa-failure.png"))
                print(json.dumps(dict(state=state(),pwa=sw_status()),ensure_ascii=True),flush=True)
                raise
            finally:
                if installed:
                    try:browser_cdp.send("PWA.uninstall",{"manifestId":url})
                    except Exception as error:logs.append("Cleanup: "+str(error))
                (OUT/"pwa-console.log").write_text("\n".join(logs),encoding="utf-8")
                context.close();server.shutdown()
if __name__=="__main__":run()
