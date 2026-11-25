"""Iframe cross-origin com SW bloqueado e backup real pela UI; perfil isolado."""
import json
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import threading
from pathlib import Path
import sys
import tempfile
import time
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.systems.save_manager import SaveManager
OUT=ROOT/"build/web-hardening";OUT.mkdir(parents=True,exist_ok=True)


@contextmanager
def iframe_host():
    # Servidor real: route.fulfill simula origem pública e o Chromium bloqueia
    # acesso à rede local antes mesmo de carregar o iframe.
    (OUT/"__qa_embed.html").write_text('<!doctype html><iframe src="http://127.0.0.1:8765/?profile=1" allow="autoplay; fullscreen" style="width:1240px;height:710px;border:0"></iframe>',encoding="utf-8")
    server=ThreadingHTTPServer(("127.0.0.1",0),partial(SimpleHTTPRequestHandler,directory=str(OUT)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield f"http://127.0.0.1:{server.server_port}/__qa_embed.html"
    finally:server.shutdown();server.server_close();thread.join(timeout=2)


def main():
    checks=[];errors=[]
    with iframe_host() as parent,sync_playwright() as p:
        print("Iniciando Chromium",flush=True)
        browser=p.chromium.launch(headless=True)
        context=browser.new_context(viewport=dict(width=1280,height=760),accept_downloads=True)
        context.add_init_script('''if(location.port==='8765') {
          Object.defineProperty(navigator,'serviceWorker',{value:{controller:null,
            addEventListener(){},getRegistration:async()=>null,
            register:async()=>{throw new DOMException('iframe policy','SecurityError');}}});
        }''')
        page=context.new_page();page.on("requestfailed",lambda r:print("FAILED "+r.url+" "+str(r.failure),flush=True));page.on("pageerror",lambda e:errors.append(str(e)))
        print("Abrindo iframe",flush=True)
        page.goto(parent,wait_until="domcontentloaded",timeout=30000)
        print("Parent carregado",flush=True)
        page.wait_for_selector("iframe")
        page.wait_for_function("document.querySelector('iframe').contentWindow !== null")
        page.wait_for_timeout(3000)
        print("Frames: "+str([f.url for f in page.frames]),flush=True)
        page.screenshot(path=str(OUT/"frame-boot.png"))
        frame=page.frames[1]
        frame.wait_for_url("http://127.0.0.1:8765/**",wait_until="domcontentloaded",timeout=30000)
        print("Iframe conectado "+frame.url,flush=True)
        def metrics():return frame.evaluate("window.webStorageMetrics?JSON.parse(webStorageMetrics):null")
        def wait(check,seconds=160):
            until=time.monotonic()+seconds
            while time.monotonic()<until:
                if errors:raise AssertionError(errors)
                error=frame.evaluate("window.webRuntimeError||null")
                if error:raise AssertionError(error)
                m=metrics()
                if m and check(m):return m
                page.wait_for_timeout(100)
            raise AssertionError(metrics())
        def scene(name):
            result=wait(lambda m:m["scene"]==name and not m["saving"])
            print("OK "+name,flush=True);return result
        def click(r):
            b=frame.locator("#canvas").bounding_box()
            page.mouse.click(b["x"]+(r[0]+r[2]/2)*b["width"]/1920,b["y"]+(r[1]+r[3]/2)*b["height"]/1080)
        def button(op):click(metrics()["rect_maps"]["backup_buttons"][op]);wait(lambda m:m["modal"]=="BackupModal")
        try:
            m=scene("CampaignMenu")
            assert frame.evaluate("scapePWA.fallback && !scapePWA.warning && document.querySelector('#pwa-status').hidden")
            assert frame.evaluate("scapePlatform.embedded")
            assert isinstance(frame.evaluate("scapePlatform.requestPersistence()"),bool)
            print("Checkpoint validado",flush=True)
            checks.append("cross_origin_iframe_registration_denied_silent_with_persistence_request")
            click(m["ui"]["play_button"]);scene("CampaignSlots")
            print("Abrindo importacao",flush=True)
            button("import")
            with page.expect_file_chooser() as picker:click([660,330,600,72])
            picker.value.set_files(str(ROOT/"build/web-stage4/management.json"))
            print("Arquivo escolhido; aguardando transacao",flush=True)
            wait(lambda m:m["modal"] is None and not m["saving"])
            print("Checkpoint validado",flush=True)
            checks.append("iframe_import_desktop_v15_via_native_slot_ui")
            print("Abrindo exportacao",flush=True)
            button("export")
            with page.expect_download() as download:click([660,330,600,72])
            exported=OUT/"exported-v15.json";download.value.save_as(str(exported))
            print("Arquivo escolhido; aguardando transacao",flush=True)
            wait(lambda m:m["modal"] is None and not m["saving"])
            text=exported.read_text(encoding="utf-8-sig");document=json.loads(text)
            assert document["versao"]==15 and "perfil" in document and "run" in document
            with tempfile.TemporaryDirectory() as folder:
                native=SaveManager(folder);native.import_json(text,1)
                assert native.load_save("slot_1")["progresso"]["moedas"]==document["run"]["moedas"]
            print("Checkpoint validado",flush=True)
            checks.append("iframe_download_is_valid_native_desktop_save")
            print("Abrindo importacao",flush=True)
            button("import")
            with page.expect_file_chooser() as picker:click([660,430,600,72])
            picker.value.set_files(dict(name="bad.json",mimeType="application/json",buffer=b"{}"))
            wait(lambda m:m["modal"]=="BackupModal" and not m["saving"] and "inv" in m.get("error","").lower())
            records=frame.evaluate('''async()=>{await new Promise(r=>{const q=indexedDB.open('scape-from-stone');q.onsuccess=()=>{window.qaDB=q.result;r();}});
              return await new Promise(r=>{const q=qaDB.transaction('saves').objectStore('saves').getAll();q.onsuccess=()=>r(q.result);});}''')
            assert len(records)==1 and records[0]["id"]=="slot_1"
            print("Checkpoint validado",flush=True)
            checks.append("invalid_import_rejected_without_mutating_existing_slot")
            click(metrics()["ui"]["close"])
            page.reload(wait_until="domcontentloaded");frame=page.frames[1]
            frame.wait_for_url("http://127.0.0.1:8765/**",wait_until="domcontentloaded")
            m=scene("CampaignMenu");click(m["ui"]["play_button"]);scene("CampaignSlots")
            assert frame.evaluate("scapeStorage.status.available")
            print("Checkpoint validado",flush=True)
            checks.append("iframe_indexeddb_survives_reload_without_service_worker")
            page.screenshot(path=str(OUT/"iframe-slots.png"))
            # Getter bloqueado pelo sandbox, antes mesmo de registrar o worker.
            other=browser.new_context()
            other.add_init_script('''if(location.port==='8765')Object.defineProperty(navigator,'serviceWorker',
                {get(){throw new DOMException('sandbox','SecurityError');}});''')
            simple=other.new_page();simple.on("pageerror",lambda e:errors.append(str(e)))
            simple.goto(parent)
            simple.wait_for_selector("iframe")
            child=simple.frames[1]
            child.wait_for_url("http://127.0.0.1:8765/**",wait_until="domcontentloaded")
            child.wait_for_function("window.scapePWA?.fallback")
            assert child.evaluate("!scapePWA.warning && document.querySelector('#pwa-status').hidden")
            print("Checkpoint validado",flush=True)
            checks.append("service_worker_getter_security_error_is_silent")
            other.close()
            result=dict(passed=True,checks=checks,errors=errors)
            (OUT/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            print(json.dumps(result),flush=True)
        except Exception:
            print(json.dumps(dict(metrics=metrics(),errors=errors),default=str),flush=True)
            page.screenshot(path=str(OUT/"failure.png"));raise
        finally:
            context.close();browser.close()

if __name__=="__main__":main()
