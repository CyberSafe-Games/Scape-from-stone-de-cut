"""Validação E2E Chromium: fluxo real e matriz de checkpoints QA por encontro."""
from pathlib import Path
import json,statistics,time
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"build/web-stage4"
OUT.mkdir(exist_ok=True)

def run():
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        context=browser.new_context(viewport={"width":1280,"height":720},accept_downloads=True)
        page=context.new_page()
        logs=[];samples=[];contexts=[];coverage=[];ultimates=set()
        page.on("console",lambda m:logs.append(m.type+": "+m.text))
        page.on("pageerror",lambda e:logs.append("PAGEERROR: "+str(e)))
        start=time.perf_counter()
        page.goto("http://127.0.0.1:8765")
        def metrics():return page.evaluate("window.webStorageMetrics ? JSON.parse(window.webStorageMetrics):null")
        def wait(check,timeout=120):
            end=time.perf_counter()+timeout
            while time.perf_counter()<end:
                m=metrics()
                if m and check(m):return m
                if m and m.get("error"):raise AssertionError(str(m))
                page.wait_for_timeout(120)
            (OUT/"browser.log").write_text("\n".join(logs),encoding="utf-8")
            page.screenshot(path=str(OUT/"failure.png"))
            raise AssertionError(str(metrics())+"\n"+page.locator(".xterm-rows").inner_text()[-3500:])
        def scene(name):
            return wait(lambda m:m["scene"]==name and not m["saving"])
        def click(x,y):
            box=page.locator("#canvas").bounding_box()
            page.mouse.click(box["x"]+x/1920*box["width"],box["y"]+y/1080*box["height"])
        def rect_click(rect):click(rect[0]+rect[2]/2,rect[1]+rect[3]/2)
        def memory():
            return page.evaluate("""() => ({js:performance.memory?.usedJSHeapSize||null,
              wasm:window.python?.HEAPU8?.buffer.byteLength||window.VM?.HEAPU8?.buffer.byteLength||null})""")
        def sample(m):
            if m["scene"] in ("CampaignBattle","CampaignTutorial") and not m["saving"] and m.get("fps",0)>0:samples.append(m["fps"])
        def dismiss_dialogue():
            end=time.time()+15
            while metrics().get("boss_dialogue") and time.time()<end:
                page.keyboard.press("Space");page.wait_for_timeout(100)
        def fight(name,timeout=120):
            end=time.time()+timeout
            ultimate_used=False
            while time.time()<end:
                m=metrics();sample(m)
                if m["scene"]=="CampaignCutscene":return m
                if m["saving"]:page.wait_for_timeout(100);continue
                if m.get("boss_dialogue"):dismiss_dialogue();continue
                if m.get("state")=="game_over":raise AssertionError("Derrota QA: "+name)
                if m.get("victory_ready"):return m
                if m.get("tutorial_active"):
                    click(1795,47);page.wait_for_timeout(250);continue
                if m.get("state")=="player_turn" and not m.get("action"):
                    if m["scene"]=="CampaignBattle" and not ultimate_used and m["ui"].get("ultimate_hand_rect",[0,0,0,0])[2]>0:
                        rect_click(m["ui"]["ultimate_hand_rect"])
                        casting=wait(lambda value:value.get("action") in
                            ("Mana Ancestral","Forças Ancestrais","Rugido da Floresta"),5)
                        ultimates.add(casting["action"])
                        ultimate_used=True
                        page.wait_for_timeout(3200)
                        continue
                    attacks=[c for c in m["hand"] if c["cost"]<=m["energy"] and
                             c["name"] in ("Soco Simples","Lança Perfurante","Investida")]
                    if attacks:rect_click(attacks[0]["rect"]);page.wait_for_timeout(1250)
                    else:rect_click(m["ui"]["end_turn_rect"]);page.wait_for_timeout(500)
                else:page.wait_for_timeout(150)
            return wait(lambda m:m.get("victory_ready"),10)
        print("Iniciando fluxo nativo no Chromium",flush=True)
        menu=scene("CampaignMenu");menu_seconds=time.perf_counter()-start
        rect_click(menu["ui"]["play_button"]);scene("CampaignSlots");click(443,520)
        intro=scene("CampaignCutscene")
        page.screenshot(path=str(OUT/"intro.png"))
        rect_click(intro["ui"]["skip_button"]);tutorial=scene("CampaignTutorial")
        fight("tutorial")
        rect_click(metrics()["ui"]["finish_tutorial_button_rect"])
        post=scene("CampaignCutscene");rect_click(post["ui"]["skip_button"])
        world=scene("CampaignMap")
        if world.get("guide_open"):rect_click(world["ui"]["guide_button"]);wait(lambda m:not m["saving"] and not m["guide_open"])
        assert metrics()["data"]["perfil"]["tutorial_concluido"]
        assert metrics()["data"]["progresso"]["moedas"]==30
        print("Tutorial e mapa: OK",flush=True)
        # Um encontro comum desde o início, sem ajustes de atributos.
        rect_click(metrics()["ui"]["play_button"]);normal=scene("CampaignBattle")
        fight("normal desde o início")
        rect_click(metrics()["reward_offers"][0]["rect"]);click(1477,953)
        world=scene("CampaignMap")
        assert world["data"]["progresso"]["encontros_por_territorio"]["stone_the_cut"]==1
        page.screenshot(path=str(OUT/"map.png"))
        # Matriz explícita de fixtures para cobrir todos os territórios e Ultimates sem alterar o runtime.
        for level in range(1,8):
            for encounter in ("0","1","boss"):
                before=time.perf_counter()
                first_sample=len(samples)
                if metrics()["scene"]!="CampaignMap":
                    scene("CampaignMap")
                rect_click(metrics()["ui"]["back_button"]);scene("CampaignMenu")
                rect_click(metrics()["ui"]["play_button"]);scene("CampaignSlots")
                rect_click(metrics()["rect_maps"]["backup_buttons"]["import"])
                wait(lambda m:m["modal"]=="BackupModal")
                click(960,366)
                confirm=wait(lambda m:m["modal"]=="ConfirmationModal")
                with page.expect_file_chooser() as chooser:rect_click(confirm["ui"]["confirm_button"])
                chooser.value.set_files(str(OUT/"fixtures"/f"{level}-{encounter}.json"))
                wait(lambda m:m["modal"] is None and not m["saving"])
                click(443,520);world=scene("CampaignMap")
                rect_click(world["ui"]["play_button"])
                battle=scene("CampaignBattle")
                assert battle["level"]==level
                assert battle["sprite_counts"].get("idle",0)>=8,battle
                if encounter=="boss" and not battle["enemy_name"].lower().startswith("álvaro"):
                    assert battle["boss_effect_frames"]>=8,battle
                dismiss_dialogue()
                # Hover real de intenção e da mão; a UI conserva suas áreas e prévias.
                m=metrics()
                if m.get("intents"):
                    r=m["intents"][0];box=page.locator("#canvas").bounding_box()
                    page.mouse.move(box["x"]+(r[0]+r[2]/2)/1920*box["width"],
                                    box["y"]+(r[1]+r[3]/2)/1080*box["height"])
                    page.wait_for_timeout(250)
                victory=fight(f"{level}-{encounter}")
                used_fps=[victory["fps"]]
                contexts.append(dict(level=level,encounter=encounter,enemy=battle["enemy_name"],
                    audio_available=victory["audio_available"],missing_sounds=victory["missing_sounds"],load_and_fight_seconds=round(time.perf_counter()-before,2),fps_median=statistics.median(samples[first_sample:]),memory=memory(),
                    resident=victory["resident"],transfer_bytes=victory["transfer_bytes"]))
                coverage.append(battle["enemy_name"])
                if not (level==7 and encounter=="boss"):
                    if victory["reward_offers"]:
                        rect_click(victory["reward_offers"][0]["rect"]);click(1477,953)
                    else:click(900,953)
                if level==7 and encounter=="boss":
                    final=scene("CampaignCutscene")
                    assert final["data"]["progresso"]["estado"]=="concluida"
                    page.screenshot(path=str(OUT/"epilogue.png"))
                    rect_click(final["ui"]["skip_button"])
                world=scene("RogueliteScene" if level==7 and encounter=="boss" else "CampaignMap")
                territory_ids=["stone_the_cut","mata_sombria","ruinas_ancestrais","pantano_abissal",
                               "fortaleza_caida","pico_da_vigilia","santuario_de_pedra"]
                if encounter=="boss":
                    assert territory_ids[level-1] in world["data"]["progresso"]["territorios_concluidos"]
                else:
                    assert world["data"]["progresso"]["encontros_por_territorio"][territory_ids[level-1]]==int(encounter)+1
                if level==7 and encounter=="boss":
                    assert world["data"]["progresso"]["estado"]=="concluida"
                    assert world["data"]["perfil"]["campanhas_concluidas"]==1
                (OUT/"progress.json").write_text(json.dumps(dict(cases=contexts,encounters=coverage),ensure_ascii=False,indent=2),encoding="utf-8")
                print(f"OK {level}-{encounter}: {battle['enemy_name']}",flush=True)
        result=dict(passed=True,browser=browser.version,menu_seconds=round(menu_seconds,2),
                    fps_median=statistics.median(samples),fps_min=min(samples),memory_samples=contexts,
                    encounters=coverage,player_ultimates=sorted(ultimates),qa_method="Tutorial e primeiro encontro sem alteração; 21 checkpoints QA v15, força 36/energia 8 e escudo para exercer Ultimates.",
                    errors=[x for x in logs if x.startswith("PAGEERROR")])
        (OUT/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        (OUT/"browser.log").write_text("\n".join(logs),encoding="utf-8")
        print(json.dumps({k:v for k,v in result.items() if k not in ("memory_samples","encounters")},ensure_ascii=False),flush=True)
        browser.close()

if __name__=="__main__":run()

