"""Validação de persistência por UI em contexto Chromium isolado dos dados reais."""
from pathlib import Path
import json
import sys
import tempfile
import time
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.systems.save_manager import SaveManager
from src.systems.roguelite import CARD_PRICES,UPGRADE_PRICES

OUT=ROOT/"build/web-storage-validation"
OUT.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory() as directory:
    native=SaveManager(directory)
    data=native.create_save("slot_1","Jornada de validação")
    data["progresso"]["moedas"]=1000
    data["progresso"]["materials"]["Soco Simples"]=3
    native.save(data)
    fixture=OUT/"desktop-v15.json"
    fixture.write_text(native.export_json("slot_1"),encoding="utf-8")


def run():
    checks={}
    logs=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        context=browser.new_context(viewport={"width":1280,"height":720},accept_downloads=True)
        page=context.new_page()
        page.on("console",lambda m:logs.append(m.type+": "+m.text))
        page.on("pageerror",lambda e:logs.append("PAGEERROR: "+str(e)))

        def metrics(tab=page):
            value=tab.evaluate("window.webStorageMetrics || null")
            return json.loads(value) if value else None
        def wait(check,tab=page,timeout=35):
            end=time.perf_counter()+timeout
            while time.perf_counter()<end:
                value=metrics(tab)
                if value and check(value):return value
                tab.wait_for_timeout(100)
            (OUT/"browser.log").write_text("\n".join(logs),encoding="utf-8")
            tab.screenshot(path=str(OUT/"failure.png"))
            terminal=tab.locator(".xterm-rows").inner_text()[-4000:]
            raise AssertionError(str(metrics(tab))+"\n"+terminal)
        def click(x,y,tab=page):
            box=tab.locator("#canvas").bounding_box()
            tab.mouse.click(box["x"]+x/1920*box["width"],box["y"]+y/1080*box["height"])
        def rect_click(rect,tab=page):
            click(rect[0]+rect[2]/2,rect[1]+rect[3]/2,tab)
        def scene(name,tab=page):
            return wait(lambda m:m["scene"]==name and not m["saving"],tab)
        def slots(tab=page):
            value=metrics(tab)
            if value["scene"]=="PersistentMenu":
                rect_click(value["ui"]["play_button"],tab)
            elif value["scene"]=="PersistenceHub":
                click(960,783,tab)
            elif value["scene"]!="WebSlots":
                tab.keyboard.press("Escape")
                scene("PersistenceHub",tab)
                click(960,783,tab)
            return scene("WebSlots",tab)
        def select(tab=page,index=0):
            click(443+index*507,520,tab)
            return scene("PersistenceHub",tab)
        def reload_hub():
            page.reload()
            scene("PersistentMenu")
            slots()
            return select()
        def dismiss_guide():
            value=metrics()
            if value.get("guide",{}).get("active"):
                page.keyboard.press("Escape")
                wait(lambda m:not m["saving"] and not m.get("guide",{}).get("active"))
        def hub():
            value=metrics()
            if value["scene"]=="ShopScene":
                rect_click(value["ui"]["back_button"])
            elif value["scene"]=="BackpackScene":
                rect_click(value["ui"]["back_rect"])
            elif value["scene"]=="RogueliteScene":
                page.keyboard.press("Escape")
            return scene("PersistenceHub")

        page.goto("http://127.0.0.1:8765")
        scene("PersistentMenu")
        slots();created=select()
        assert created["data"]["versao"]==15
        original_run=created["data"]["progresso"]["run_id"]
        restored=reload_hub()
        assert restored["data"]["progresso"]["run_id"]==original_run
        checks["slot_creation_reload"]=True
        print("Slots e recarga: OK",flush=True)

        slots()
        rect_click(metrics()["rect_maps"]["backup_buttons"]["import"])
        wait(lambda m:m["modal"]=="BackupModal")
        click(960,366)
        confirmation=wait(lambda m:m["modal"]=="ConfirmationModal")
        with page.expect_file_chooser() as picker:
            rect_click(confirmation["ui"]["confirm_button"])
        picker.value.set_files(str(fixture))
        wait(lambda m:m["modal"] is None and not m["saving"])
        imported=select()
        assert imported["data"]["progresso"]["moedas"]==1000
        assert imported["data"]["nome"]==json.loads(fixture.read_text(encoding="utf-8"))["nome"]
        checks["desktop_import_v15"]=True
        print("Importação do desktop: OK",flush=True)

        click(960,333);scene("ShopScene");dismiss_guide()
        value=metrics();gold=value["data"]["progresso"]["moedas"]
        page.evaluate("""() => {
          const begin=scapeStorage.begin.bind(scapeStorage), poll=scapeStorage.poll.bind(scapeStorage);
          const deadlines=new Map();
          scapeStorage.begin=(op,text)=>{const id=begin(op,text);if(op==='commit')deadlines.set(id,performance.now()+700);return id;};
          scapeStorage.poll=id=> performance.now()<(deadlines.get(id)||0) ? JSON.stringify({pending:true}) : poll(id);
        }""")
        rect=value["rect_maps"]["offer_rects"]["Investida"]
        rect_click(rect);rect_click(rect)
        pending=wait(lambda m:m["saving"])
        assert pending["data"]["progresso"]["moedas"]==gold
        purchased=wait(lambda m:not m["saving"] and "Investida" in m["data"]["progresso"]["cartas_colecao"])
        assert purchased["data"]["progresso"]["moedas"]==gold-CARD_PRICES["Investida"]
        checks["async_ack_and_double_click"]=True
        print("Confirmação e clique duplo: OK",flush=True)

        before=json.loads(json.dumps(purchased["data"]))
        page.evaluate("""() => {
          const put=IDBObjectStore.prototype.put;
          IDBObjectStore.prototype.put=function(...args){
            if(this.name==='saves'){
              IDBObjectStore.prototype.put=put;
              throw new DOMException('Falha de quota injetada','QuotaExceededError');
            }
            return put.apply(this,args);
          };
        }""")
        rect_click(metrics()["rect_maps"]["offer_rects"]["Aura Rubra"])
        failed=wait(lambda m:not m["saving"] and "backup" in m["error"].lower())
        assert failed["data"]==before
        checks["quota_rollback"]=True
        restored=reload_hub()
        assert restored["data"]["progresso"]["moedas"]==before["progresso"]["moedas"]
        assert "Aura Rubra" not in restored["data"]["progresso"]["cartas_colecao"]
        print("Falha/rollback e recarga: OK",flush=True)

        click(960,423);scene("BackpackScene");dismiss_guide()
        value=metrics()
        rect_click(value["rect_maps"]["cards"]["Investida"])
        equipped=wait(lambda m:not m["saving"] and m["data"]["progresso"]["deck_slots"].count("Investida")==1)
        deck=equipped["data"]["progresso"]["deck_slots"]
        restored=reload_hub()
        assert restored["data"]["progresso"]["deck_slots"]==deck
        checks["deck_reload"]=True
        print("Mochila: OK",flush=True)

        click(960,513);scene("RogueliteScene");dismiss_guide()
        value=metrics()
        rect_click(value["rect_maps"]["type_rects"]["Soco Simples"])
        value=metrics()
        rect_click(value["ui"]["upgrade_button"])
        upgraded=wait(lambda m:not m["saving"] and any(c["name"]=="Soco Simples" and c["level"]==2 for c in m["data"]["progresso"]["copies"]))
        restored=reload_hub()
        assert any(c["name"]=="Soco Simples" and c["level"]==2 for c in restored["data"]["progresso"]["copies"])
        assert all(restored["data"]["perfil"]["tutoriais_gerenciamento"].values())
        checks["upgrade_and_guides_reload"]=True
        print("Altar e guias: OK",flush=True)

        click(960,693);wait(lambda m:m["modal"]=="OptionsScene")
        page.keyboard.press("ArrowLeft")
        changed=wait(lambda m:m["preferences"]["master_volume"]<1)
        volume=changed["preferences"]["master_volume"]
        restored=reload_hub()
        assert restored["preferences"]["master_volume"]==volume
        checks["preferences_reload"]=True
        print("Preferências: OK",flush=True)

        second=context.new_page()
        second.goto("http://127.0.0.1:8765")
        scene("PersistentMenu",second);slots(second);select(second)
        click(960,333,second);scene("ShopScene",second)
        click(960,333);scene("ShopScene")
        before_b=metrics(second)["data"]
        rect_click(metrics()["rect_maps"]["offer_rects"]["Aura Rubra"])
        wait(lambda m:not m["saving"] and "Aura Rubra" in m["data"]["progresso"]["cartas_colecao"])
        rect_click(metrics(second)["rect_maps"]["offer_rects"]["Aura Rubra"],second)
        conflict=wait(lambda m:not m["saving"] and "outra aba" in m["error"].lower(),second)
        assert conflict["data"]==before_b
        second.close();page.bring_to_front()
        checks["two_tab_revision_conflict"]=True
        print("Conflito entre abas: OK",flush=True)

        slots()
        rect_click(metrics()["rect_maps"]["backup_buttons"]["export"])
        wait(lambda m:m["modal"]=="BackupModal")
        with page.expect_download() as exported:
            click(960,366)
        exported.value.save_as(str(OUT/"exported-v15.json"))
        payload=json.loads((OUT/"exported-v15.json").read_text(encoding="utf-8"))
        assert payload["versao"]==15 and "perfil" in payload and "run" in payload
        assert "progresso" not in payload
        wait(lambda m:m["modal"] is None and not m["saving"])
        assert payload["nome"]==json.loads(fixture.read_text(encoding="utf-8"))["nome"]
        checks["unicode_roundtrip"]=True
        checks["export_json"]=True

        rect_click(metrics()["rect_maps"]["backup_buttons"]["import"])
        wait(lambda m:m["modal"]=="BackupModal")
        with page.expect_file_chooser() as picker:click(960,466)
        picker.value.set_files(str(OUT/"exported-v15.json"))
        wait(lambda m:m["modal"] is None and not m["saving"])
        copied=select(index=1)
        assert copied["data"]["id"]=="slot_2"
        assert copied["data"]["progresso"]["moedas"]==payload["run"]["moedas"]
        checks["export_import_roundtrip"]=True
        print("Backup completo: OK",flush=True)

        # Snapshot real pelo motor; recarga recupera pilhas, energia, vida e revisão.
        click(960,603);battle=scene("PersistentBattle")
        attacks=[c for c in battle["hand"] if c["name"]=="Soco Simples" and c["cost"]<=battle["energy"]]
        if attacks:
            rect_click(attacks[0]["rect"])
            saved=wait(lambda m:not m["saving"] and m["data"]["progresso"]["combat_snapshot"]["enemy"]["hp"]<23)
        else:
            saved=battle
        snapshot=saved["data"]["progresso"]["combat_snapshot"]
        page.reload();scene("PersistentMenu");slots();select(index=1)
        click(960,603);resumed=scene("PersistentBattle")
        assert resumed["enemy_hp"]==snapshot["enemy"]["hp"]
        assert resumed["energy"]==snapshot["player"]["energy"]
        checks["combat_checkpoint_reload"]=True



        # Falha em checkpoint de ação: restaura o estado confirmado do motor.
        baseline=metrics()
        old_snapshot=json.loads(json.dumps(baseline["data"]["progresso"]["combat_snapshot"]))
        page.evaluate("""() => {
          const put=IDBObjectStore.prototype.put;
          IDBObjectStore.prototype.put=function(...args){
            if(this.name==='saves'){
              IDBObjectStore.prototype.put=put;
              throw new DOMException('Checkpoint failure','QuotaExceededError');
            }
            return put.apply(this,args);
          };
        }""")
        playable=next((c for c in baseline["hand"] if c["name"]=="Soco Simples" and c["cost"]<=baseline["energy"]),None)
        if playable:rect_click(playable["rect"])
        else:click(1815,975)
        rolled_back=wait(lambda m:not m["saving"] and "backup" in m["error"].lower())
        assert rolled_back["enemy_hp"]==old_snapshot["enemy"]["hp"]
        assert rolled_back["player_hp"]==old_snapshot["player"]["hp"]
        assert rolled_back["energy"]==old_snapshot["player"]["energy"]
        assert rolled_back["data"]["progresso"]["combat_snapshot"]==old_snapshot
        checks["combat_checkpoint_rollback"]=True

        # Encerra a luta real e confirma uma recompensa pela interface.
        deadline=time.perf_counter()+150
        while time.perf_counter()<deadline:
            m=metrics()
            if m.get("state")=="victory" and m.get("victory_ready") and not m["saving"]:break
            if m.get("state")=="game_over":raise AssertionError("Perdeu durante teste de recompensa")
            if not m["saving"] and m.get("state")=="player_turn" and not m.get("action"):
                card=next((c for c in m["hand"] if c["name"]=="Soco Simples" and c["cost"]<=m["energy"]),None)
                if card:rect_click(card["rect"])
                else:click(1815,975)
                page.wait_for_timeout(1200)
            else:page.wait_for_timeout(150)
        victory=wait(lambda m:m.get("victory_ready") and not m["saving"])
        collection=len(victory["data"]["progresso"]["cartas_colecao"])
        rect_click(victory["reward_offers"][0]["rect"])
        page.wait_for_timeout(200)
        click(1477,953)
        rewarded=scene("PersistenceHub")
        assert rewarded["data"]["progresso"]["combat_snapshot"] is None
        assert len(rewarded["data"]["progresso"]["cartas_colecao"])==collection+1
        assert rewarded["data"]["progresso"]["encontros_por_territorio"]["stone_the_cut"]==1
        reward_gold=rewarded["data"]["progresso"]["moedas"]
        page.reload();scene("PersistentMenu");slots();reloaded_reward=select(index=1)
        assert reloaded_reward["data"]["progresso"]["moedas"]==reward_gold
        assert len(reloaded_reward["data"]["progresso"]["cartas_colecao"])==collection+1
        checks["victory_reward_reload"]=True
        print("Vitoria e recompensa: OK",flush=True)

        # Uma derrota encerra a run, preserva o perfil e não volta ativa após F5.
        click(960,603);scene("PersistentBattle")
        deadline=time.perf_counter()+150
        while time.perf_counter()<deadline:
            m=metrics()
            if m.get("state")=="game_over" and not m["saving"]:break
            if m.get("state")=="player_turn" and not m["saving"] and not m.get("action"):
                click(1815,975)
            page.wait_for_timeout(700)
        dead=wait(lambda m:not m["saving"] and m.get("data",{}).get("progresso",{}).get("estado")=="morta")
        profile=dead["data"]["perfil"]["id"]
        page.reload();scene("PersistentMenu");slots();dead_reload=select(index=1)
        assert dead_reload["data"]["progresso"]["estado"]=="morta"
        assert dead_reload["data"]["perfil"]["id"]==profile
        assert dead_reload["data"]["progresso"]["combat_snapshot"] is None
        checks["death_profile_reload"]=True
        print("Morte e perfil: OK",flush=True)
        ended_run=dead_reload["data"]["progresso"]["run_id"]
        click(960,603);scene("RogueliteScene")
        click(1465,965)
        restarted=scene("PersistenceHub")
        assert restarted["data"]["progresso"]["estado"]=="ativa"
        assert restarted["data"]["progresso"]["run_id"]!=ended_run
        assert restarted["data"]["perfil"]["id"]==profile
        page.reload();scene("PersistentMenu");slots();restart_reload=select(index=1)
        assert restart_reload["data"]["progresso"]["run_id"]==restarted["data"]["progresso"]["run_id"]
        checks["new_run_profile_reload"]=True
        click(960,873)
        wait(lambda m:not m["saving"] and bool(m["error"]))
        assert page.evaluate("typeof scapeStorage.status.persistent === 'boolean'")
        checks["persistent_storage_request"]=True


        # Simula um registro legado preexistente; a migração preserva backup no IDB.
        legacy=json.loads(fixture.read_text(encoding="utf-8"))
        legacy.update(id="slot_3",versao=14,revisao=7)
        page.evaluate("""async payload => {
          const db=await new Promise((resolve,reject)=>{
            const request=indexedDB.open('scape-from-stone',1);
            request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error);
          });
          await new Promise((resolve,reject)=>{
            const tx=db.transaction('saves','readwrite');
            tx.objectStore('saves').put(payload);
            tx.oncomplete=resolve;tx.onabort=()=>reject(tx.error);
          });db.close();
        }""",legacy)
        slots();migrated=select(index=2)
        assert migrated["data"]["versao"]==15
        click(960,333);scene("ShopScene");dismiss_guide()
        backup=page.evaluate("""async () => {
          const db=await new Promise(resolve=>{
            const request=indexedDB.open('scape-from-stone',1);
            request.onsuccess=()=>resolve(request.result);
          });
          const value=await new Promise(resolve=>{
            const tx=db.transaction(['saves','backups'],'readonly');
            const r=tx.objectStore('saves').get('slot_3'),b=tx.objectStore('backups').getAll();
            tx.oncomplete=()=>resolve({save:r.result,backups:b.result});
          });db.close();return value;
        }""")
        assert backup["save"]["versao"]==15
        assert any(b["data"]["versao"]==14 and b["data"]["id"]=="slot_3" for b in backup["backups"])
        checks["indexeddb_legacy_migration_backup"]=True
        print("Migracao e backup legado: OK",flush=True)

        # IndexedDB restrito: erro amigável sem habilitar gravações falsas.
        blocked=browser.new_context(viewport={"width":1280,"height":720})
        blocked.add_init_script("Object.defineProperty(window,'indexedDB',{get:()=>undefined})")
        restricted=blocked.new_page();restricted.goto("http://127.0.0.1:8765")
        scene("StorageUnavailable",restricted)
        checks["indexeddb_unavailable"]=True
        blocked.close()

        result=dict(checks=checks,passed=all(checks.values()),browser=browser.version)
        (OUT/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        (OUT/"browser.log").write_text("\n".join(logs),encoding="utf-8")
        page.screenshot(path=str(OUT/"checkpoint.png"))
        print(json.dumps(result,ensure_ascii=False),flush=True)
        browser.close()


if __name__=="__main__":run()



