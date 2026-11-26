"""Fluxos mobile sobre a arte nativa; perfis e screenshots isolados em build/."""
import argparse,json,time,statistics
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url",default="http://127.0.0.1:8765/")
    args=parser.parse_args()
    out=ROOT/"build/mobile-original-art";out.mkdir(parents=True,exist_ok=True)
    checks=[];screens=[];samples=[];errors=[];memory_samples=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        context=browser.new_context(viewport=dict(width=844,height=390),is_mobile=True,has_touch=True,device_scale_factor=3)
        page=context.new_page();page.on("pageerror",lambda e:errors.append(str(e)))
        def metrics():return page.evaluate("window.webStorageMetrics?JSON.parse(webStorageMetrics):null")
        def wait(check,seconds=150):
            deadline=time.monotonic()+seconds
            while time.monotonic()<deadline:
                error=page.evaluate("window.webRuntimeError||null")
                if error or errors:raise AssertionError(error or errors)
                m=metrics()
                if m and check(m):return m
                page.wait_for_timeout(100)
            raise AssertionError({k:(metrics() or {}).get(k) for k in ("scene","message","saving","error","modal")})
        def scene(name):
            value=wait(lambda m:m["scene"]==name and not m["saving"])
            print("OK "+name,flush=True);return value
        def tap(x,y):
            r=page.locator("#canvas").bounding_box()
            page.touchscreen.tap(r["x"]+x*r["width"]/1920,r["y"]+y*r["height"]/1080)
        def rect(r):tap(r[0]+r[2]/2,r[1]+r[3]/2)
        def action(label):
            page.get_by_role("button",name=label,exact=True).tap()
        def snapshot(name):
            page.wait_for_timeout(250)
            assert page.locator(".mobile-header,.combat-header,.mobile-grid,.mobile-footer").count()==0
            assert metrics()["physical_canvas"]==[960,540]
            assert metrics()["render_buffer"]==[960,540]
            assert page.evaluate("JSON.parse(scapePlatform.renderViewport()).dpr")==1
            assert page.evaluate("getComputedStyle(document.body).backgroundColor")!="rgb(128, 128, 128)"
            memory=page.evaluate("({wasm:window.python?.HEAPU8?.buffer.byteLength||window.VM?.HEAPU8?.buffer.byteLength||null,js:performance.memory?.usedJSHeapSize||null})")
            memory_samples.append(dict(screen=name,memfs=metrics().get("memfs"),heap=memory))
            page.screenshot(path=str(out/(name+".png")));screens.append(name)
        def import_save(path,replace=False):
            rect(metrics()["rect_maps"]["backup_buttons"]["import"])
            wait(lambda m:m["modal"]=="BackupModal")
            if replace:
                tap(960,366);wait(lambda m:m["modal"]=="ConfirmationModal")
            with page.expect_file_chooser() as chooser:
                rect(metrics()["ui"]["confirm_button"]) if replace else tap(960,366)
            chooser.value.set_files(str(path))
            wait(lambda m:m["modal"] is None and not m["saving"])
        try:
            page.goto(args.url)
            menu=scene("CampaignMenu");snapshot("menu")
            rect(menu["ui"]["play_button"]);scene("CampaignSlots");snapshot("saves")
            import_save(ROOT/"build/web-stage4/management.json")
            tap(443,520);world=scene("CampaignMap");snapshot("mapa")
            rect(world["ui"]["shop_button"]);scene("ShopScene")
            # Este checkpoint já viu os guias; testar o guia nativo depois.
            if metrics().get("guide",{}).get("active"):
                rect(metrics()["guide"]["rects"][-1]);wait(lambda m:not m["guide"]["active"] and not m["saving"])
            snapshot("loja")
            before=metrics()["data"]["progresso"]["moedas"]
            rect(metrics()["rect_maps"]["card_rects"]["Investida"])
            wait(lambda m:page.locator(".art-inspection img").count()==1)
            assert metrics()["data"]["progresso"]["moedas"]==before
            action("COMPRAR")
            wait(lambda m:not m["saving"] and "Investida" in m["data"]["progresso"]["cartas_colecao"])
            checks.append("shop_native_art_inspect_then_purchase")
            rect(metrics()["ui"]["back_button"]);world=scene("CampaignMap")
            rect(world["ui"]["backpack_button"]);scene("BackpackScene")
            if metrics().get("guide",{}).get("active"):
                rect(metrics()["guide"]["rects"][-1]);wait(lambda m:not m["guide"]["active"] and not m["saving"])
            snapshot("mochila")
            rect(metrics()["rect_maps"]["cards"]["Investida"]);action("EQUIPAR")
            wait(lambda m:not m["saving"] and "Investida" in m["draft_slots"])
            checks.append("backpack_native_equip")
            rect(metrics()["ui"]["ultimate_tab_rect"]);wait(lambda m:len(m["rect_maps"].get("ultimate_rects",{}))>0)
            snapshot("ultimates_mochila")
            rect(metrics()["rect_maps"]["ultimate_rects"]["forcas_ancestrais"]);action("EQUIPAR")
            wait(lambda m:not m["saving"] and m["data"]["progresso"]["ultimate_equipada"]=="forcas_ancestrais")
            checks.append("backpack_native_ultimate")
            rect(metrics()["ui"]["back_rect"]);world=scene("CampaignMap")
            rect(world["ui"]["shop_button"]);scene("ShopScene")
            rect(metrics()["ui"]["workshop_button"]);scene("RogueliteScene")
            if metrics().get("guide",{}).get("active"):
                rect(metrics()["guide"]["rects"][-1]);wait(lambda m:not m["guide"]["active"] and not m["saving"])
            rect(metrics()["rect_maps"]["type_rects"]["Soco Simples"])
            wait(lambda m:bool(m["rect_maps"].get("copy_rects")))
            snapshot("altar")
            rect(next(iter(metrics()["rect_maps"]["copy_rects"].values())))
            action("DEPOIS · LV2")
            after=page.locator(".art-inspection img").get_attribute("src")
            action("ANTES · LV1")
            page.wait_for_function("(old)=>document.querySelector('.art-inspection img')?.src!==old",arg=after,timeout=15000,polling=100)
            action("APRIMORAR")
            wait(lambda m:not m["saving"] and any(c["name"]=="Soco Simples" and c["level"]==2 for c in m["data"]["progresso"]["copies"]))
            checks.append("altar_native_art_before_after_confirm")
            tap(1878,56);wait(lambda m:m["modal"]=="OptionsScene")
            snapshot("configuracoes")
            slider=metrics()["rect_maps"]["sliders"]["master_volume"]
            tap(slider[0]+slider[2]*.35,slider[1]-18)
            wait(lambda m:.3<m["preferences"]["master_volume"]<.4)
            rect(metrics()["ui"]["back_button"]);wait(lambda m:m["modal"] is None)
            checks.append("settings_native_slider")
            rect(metrics()["ui"]["back_button"]);world=scene("CampaignMap")
            rect(world["ui"]["back_button"]);menu=scene("CampaignMenu")
            rect(menu["ui"]["play_button"]);scene("CampaignSlots")
            import_save(ROOT/"build/web-stage4/fixtures/1-0.json",replace=True)
            tap(443,520);world=scene("CampaignMap");rect(world["ui"]["play_button"])
            battle=scene("CampaignBattle");snapshot("combate")
            assert battle["memfs"]["freed_bytes"]>0 and battle["memfs"]["temporary_bytes"]==0
            assert "player" in battle["memfs"]["pruned_groups"]
            page.wait_for_timeout(1000)
            for _ in range(20):page.wait_for_timeout(150);samples.append(metrics()["fps"])
            result=dict(combat_fps_median=statistics.median(samples),frame_cost_ms=metrics()["frame_cost_ms"],
                mobile_render_cache=metrics()["mobile_render_cache"])
            (out/"benchmark.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
            rect(metrics()["intents"][0]);wait(lambda m:page.locator(".art-inspection img").count()==1)
            assert page.get_by_role("button",name="JOGAR",exact=True).count()==0
            snapshot("intencao");action("FECHAR")
            energy=metrics()["energy"]
            hand_before=len(metrics()["hand"])
            card_rect=metrics()["hand"][0]["rect"]
            box=page.locator("#canvas").bounding_box()
            x=box["x"]+(card_rect[0]+card_rect[2]/2)*box["width"]/1920
            y=box["y"]+(card_rect[1]+card_rect[3]/2)*box["height"]/1080
            touch=page.context.new_cdp_session(page)
            touch.send("Input.dispatchTouchEvent",{"type":"touchStart","touchPoints":[{"x":x,"y":y,"id":1}]})
            wait(lambda m:page.locator(".hold-inspection img").count()==1)
            assert page.locator(".hold-inspection button").count()==0
            assert metrics()["energy"]==energy and len(metrics()["hand"])==hand_before
            snapshot("carta_segurada")
            touch.send("Input.dispatchTouchEvent",{"type":"touchEnd","touchPoints":[]});touch.detach()
            wait(lambda m:page.locator(".art-inspection").count()==0)
            assert metrics()["energy"]==energy and len(metrics()["hand"])==hand_before
            checks.append("hold_reads_and_release_never_plays")
            rect(metrics()["ui"]["ultimate_hand_rect"])
            wait(lambda m:m["data"]["progresso"]["combat_snapshot"]["player"]["ultimate_charge"]==0)
            assert page.get_by_role("button",name="JOGAR ULTIMATE",exact=True).count()==0
            checks.append("short_tap_ultimate_without_confirmation")
            wait(lambda m:m["action"] is None)
            rect(metrics()["hand"][0]["rect"])
            wait(lambda m:m.get("victory_ready"));snapshot("recompensa")
            if metrics()["reward_offers"]:
                rect(metrics()["reward_offers"][0]["rect"]);action("ESCOLHER")
            else:tap(900,953)
            scene("CampaignMap");checks.append("instant_hand_play_and_reward_confirmation")
            page.set_viewport_size(dict(width=390,height=844));wait(lambda m:m["portrait_blocked"] and not m["active"])
            page.set_viewport_size(dict(width=844,height=390));wait(lambda m:not m["portrait_blocked"] and m["active"])
            checks.append("rotation_safe_pause_resume")
            # Jornada nova: quadrinhos e tutorial preservam a composição nativa.
            world=metrics();rect(world["ui"]["back_button"]);menu=scene("CampaignMenu")
            rect(menu["ui"]["play_button"]);scene("CampaignSlots");tap(960,520)
            scene("CampaignCutscene");snapshot("quadrinhos_intro")
            rect(metrics()["ui"]["skip_button"]);scene("CampaignTutorial");snapshot("tutorial")
            before=metrics().get("tutorial_step",0)
            tap(960,530);wait(lambda m:m.get("tutorial_step",0)>before)
            checks.append("native_intro_and_tutorial_touch")
            # Epílogo real via checkpoint de QA com boss a 1 HP, sem alterar regras.
            context.close()
            context=browser.new_context(viewport=dict(width=844,height=390),is_mobile=True,has_touch=True,device_scale_factor=3)
            page=context.new_page();page.on("pageerror",lambda e:errors.append(str(e)))
            page.goto(args.url);menu=scene("CampaignMenu")
            rect(menu["ui"]["play_button"]);scene("CampaignSlots")
            final=json.loads((ROOT/"build/web-stage4/fixtures/7-boss.json").read_text(encoding="utf-8"))
            final["run"]["combat_snapshot"]["enemy"]["hp"]=1
            final_path=out/"final-boss-one-hit.json"
            final_path.write_text(json.dumps(final,ensure_ascii=False),encoding="utf-8")
            import_save(final_path)
            tap(443,520);world=scene("CampaignMap");rect(world["ui"]["play_button"])
            scene("CampaignBattle")
            for _ in range(25):
                if not metrics().get("boss_dialogue"):break
                tap(960,530);page.wait_for_timeout(200)
            wait(lambda m:m.get("state")=="player_turn")
            rect(metrics()["hand"][0]["rect"])
            wait(lambda m:m.get("victory_ready") or m["scene"]=="CampaignCutscene")
            if metrics()["scene"]!="CampaignCutscene":
                if metrics()["reward_offers"]:
                    rect(metrics()["reward_offers"][0]["rect"]);action("ESCOLHER")
                else:tap(900,953)
            scene("CampaignCutscene");snapshot("epilogo")
            checks.append("native_final_boss_and_epilogue")
            # Todas as cenas usam a mesma camada: garantir ausência do painel paralelo.
            result.update(memory_samples=memory_samples,passed=True,checks=checks,screens=screens,errors=errors,
                viewport=[844,390],device_dpr=3,mobile_dpr=1,physical_canvas=[960,540])
            (out/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            print(json.dumps(result,ensure_ascii=True),flush=True)
        except Exception:
            page.screenshot(path=str(out/"failure.png"))
            print(json.dumps(dict(state={k:(metrics() or {}).get(k) for k in ("scene","modal","message","error")},errors=errors)),flush=True)
            raise
        finally:context.close();browser.close()
if __name__=="__main__":main()
