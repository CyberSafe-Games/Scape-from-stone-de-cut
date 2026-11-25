"""Prova por cliques reais: menu, áudio, combate, vitória, derrota e retorno."""
import json
from pathlib import Path
import statistics
import time
from playwright.sync_api import sync_playwright

OUT=Path(__file__).resolve().parents[1]/"build/web-poc-validation"
OUT.mkdir(parents=True,exist_ok=True)


def run(url="http://127.0.0.1:8765/?render=1"):
    logs, network, fps=[], [], []
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        context=browser.new_context(viewport={"width":1280,"height":720})
        page=context.new_page()
        cdp=page.context.new_cdp_session(page)
        cdp.send("Network.enable")
        cdp.on("Network.loadingFinished",lambda event:network.append(event["encodedDataLength"]))
        page.on("console",lambda m:logs.append(m.type+": "+m.text))
        page.on("pageerror",lambda e:logs.append("PAGEERROR: "+str(e)))

        def metrics():
            text=page.evaluate("window.webPocMetrics || null")
            return json.loads(text) if text else None

        def click(x,y):
            box=page.locator("#canvas").bounding_box()
            page.mouse.click(box["x"]+x/1920*box["width"],box["y"]+y/1080*box["height"])

        def wait_for(check,timeout=25):
            end=time.perf_counter()+timeout
            while time.perf_counter()<end:
                value=metrics()
                if value and check(value):
                    return value
                page.wait_for_timeout(100)
            terminal=page.locator(".xterm-rows").inner_text()[-4000:]
            (OUT/"browser.log").write_text("\n".join(logs)+"\n"+terminal,encoding="utf-8")
            raise AssertionError("Tempo excedido: "+str(metrics())+"\n"+terminal)

        started=time.perf_counter()
        page.goto(url,wait_until="domcontentloaded")
        # Menu deve abrir sem gesto. O clique de Iniciar desbloqueia o áudio.
        for i in range(45):
            page.wait_for_timeout(500)
            if metrics():
                break
        menu=wait_for(lambda m:m["scene"]=="ProofMenu")
        menu_seconds=time.perf_counter()-started
        assert not menu["audio_unlocked"],menu
        page.screenshot(path=str(OUT/"menu.png"))
        battle_started=time.perf_counter()
        click(450,725)
        battle=wait_for(lambda m:m["scene"]=="ProofBattle")
        battle_seconds=time.perf_counter()-battle_started
        assert battle["audio_unlocked"] and battle["music_playing"],battle
        page.screenshot(path=str(OUT/"battle.png"))

        fullscreen={"supported":page.evaluate("Boolean(document.fullscreenEnabled)")}
        if fullscreen["supported"]:
            page.locator("#web-fullscreen").click()
            page.wait_for_function("Boolean(document.fullscreenElement)",timeout=5000)
            fullscreen["entered"]=True
            page.locator("#web-fullscreen").click()
            page.wait_for_function("!document.fullscreenElement",timeout=5000)
            fullscreen["exited"]=True
            assert page.evaluate("window.scapePlatform.lastFullscreenError")==None

        # Eventos DOM reais do host; nenhum atalho de depuração no motor.
        before=metrics()
        page.evaluate("window.dispatchEvent(new Event('blur'))")
        paused=wait_for(lambda m:not m["active"])
        page.wait_for_timeout(400)
        assert metrics()["frames"]==paused["frames"]
        assert paused["audio_suspended"]
        page.evaluate("window.dispatchEvent(new Event('focus'))")
        resumed=wait_for(lambda m:m["active"] and m["resume_serial"]>before["resume_serial"])
        assert resumed["player_hp"]==before["player_hp"]
        assert not resumed["audio_suspended"]
        background_tab=page.context.new_page()
        background_tab.goto("about:blank")
        background_tab.bring_to_front()
        page.wait_for_timeout(600)
        visibility=page.evaluate("({state:document.visibilityState, active:JSON.parse(window.scapePlatform.snapshot()).active})")
        if visibility["active"]:
            # Chromium headless pode manter todas as abas como visíveis.
            # Exercita a mesma fronteira DOM, sem modificar o motor do jogo.
            page.evaluate("""() => {
                Object.defineProperty(document, 'hidden', {configurable:true, get:() => true});
                document.dispatchEvent(new Event('visibilitychange'));
            }""")
            wait_for(lambda m:not m["active"])
            visibility["headless_visibility_emulated"]=True
            page.evaluate("""() => {
                delete document.hidden;
                document.dispatchEvent(new Event('visibilitychange'));
            }""")
        else:
            visibility["headless_visibility_emulated"]=False
        background_tab.close()
        page.bring_to_front()
        restored=wait_for(lambda m:m["active"] and m["resume_serial"]>resumed["resume_serial"])
        assert restored["player_hp"]==before["player_hp"]
        focus={"paused_frames":paused["frames"],"resumed_serial":restored["resume_serial"],
               "background_tab":visibility,"passed":True}
        resumed=restored
        # Descarta a amostra que contém a pausa antes de medir FPS.
        battle=wait_for(lambda m:m["frames"]>resumed["frames"]+30)

        # Hover sobre carta e intenção; as coordenadas pertencem à UI real.
        first=battle["hand"][0]["rect"]
        box=page.locator("#canvas").bounding_box()
        page.mouse.move(box["x"]+(first[0]+first[2]/2)/1920*box["width"],
                        box["y"]+(first[1]+first[3]/2)/1080*box["height"])
        page.wait_for_timeout(400)
        page.screenshot(path=str(OUT/"card-hover.png"))
        assert battle["intents"], "Intenção não renderizada"
        rect=battle["intents"][0]
        page.mouse.move(box["x"]+(rect[0]+rect[2]/2)/1920*box["width"],
                        box["y"]+(rect[1]+rect[3]/2)/1080*box["height"])
        page.wait_for_timeout(400)
        page.screenshot(path=str(OUT/"intent-hover.png"))

        deadline=time.perf_counter()+150
        moves=0
        minimum_hp=60
        while time.perf_counter()<deadline:
            m=metrics()
            fps.append(m["fps"])
            minimum_hp=min(minimum_hp,m.get("player_hp",60))
            if m.get("state")=="victory":
                break
            if m.get("state")=="game_over":
                raise AssertionError("Jogador perdeu durante o teste de vitória")
            if m.get("state")=="player_turn" and not m.get("action"):
                playable=[c for c in m["hand"] if c["cost"]<=m["energy"]]
                card=next((c for c in playable if c["name"]=="Soco Simples"),None)
                if card:
                    rect=card["rect"]
                    click(rect[0]+rect[2]/2,rect[1]+rect[3]/2)
                    moves+=1
                    page.wait_for_timeout(1600)
                else:
                    click(1815,975)
                    page.wait_for_timeout(1400)
            else:
                page.wait_for_timeout(200)
        victory=wait_for(lambda m:m.get("state")=="victory")
        page.wait_for_timeout(1500)
        page.screenshot(path=str(OUT/"victory.png"))
        print("VITÓRIA",victory,flush=True)

        page.keyboard.press("r")
        wait_for(lambda m:m.get("state")=="player_turn" and m.get("enemy_hp")==23)
        deadline=time.perf_counter()+150
        while time.perf_counter()<deadline:
            m=metrics()
            if m.get("state")=="game_over":
                break
            if m.get("state")=="player_turn":
                click(1815,975)
            page.wait_for_timeout(1300)
        defeat=wait_for(lambda m:m.get("state")=="game_over")
        page.wait_for_timeout(4000)
        page.screenshot(path=str(OUT/"defeat.png"))
        page.keyboard.press("Escape")
        menu_after=wait_for(lambda m:m["scene"]=="ProofMenu")
        click(450,934)
        wait_for(lambda m:m["scene"]=="ProofMenu" and m["frames"]>menu_after["frames"]+15)
        # Não cria saves no FS virtual, além de não acessar disco do computador.
        storage=page.evaluate("""() => ({localStorageKeys:Object.keys(localStorage),
          wasm_heap_bytes:window.python?.HEAPU8?.buffer.byteLength || window.VM?.HEAPU8?.buffer.byteLength || null,
          js_heap:performance.memory?.usedJSHeapSize || null})""")
        result={
            "browser":browser.version, "mode":"Chromium headless, viewport 1280x720, sem throttling",
            "navigation_to_menu_seconds":menu_seconds,
            "menu_click_to_battle_seconds":battle_seconds,
            "network_encoded_bytes":sum(network),
            "menu":menu,"first_battle":battle,"victory":victory,"defeat":defeat,
            "fps_median_combat":statistics.median(fps),"fps_min_sample":min(fps),
            "attack_clicks":moves,"minimum_player_hp_during_win":minimum_hp,
            "storage":storage,
            "fullscreen":fullscreen,"focus":focus,"web_exit_returned_home":True,
            "passed":True,
        }
        (OUT/"metrics.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        (OUT/"browser.log").write_text("\n".join(logs),encoding="utf-8")
        print(json.dumps(result,ensure_ascii=False),flush=True)
        browser.close()


if __name__=="__main__":
    run()

