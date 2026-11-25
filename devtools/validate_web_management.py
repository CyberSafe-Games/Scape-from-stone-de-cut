"""Regressão das telas reais de gerenciamento no build completo da campanha."""
from pathlib import Path
import json,time,statistics
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"build/web-stage4"
data=json.loads((OUT/"fixtures/1-0.json").read_text(encoding="utf-8"))
data["run"]["combat_snapshot"]=None
data["perfil"]["tutoriais_gerenciamento"]={k:False for k in ("shop","backpack","workshop")}
fixture=OUT/"management.json";fixture.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 context=browser.new_context(viewport={"width":1280,"height":720})
 page=context.new_page();logs=[];page.on("console",lambda m:logs.append(m.text))
 page.goto("http://127.0.0.1:8765/?profile=1")
 def metrics():return page.evaluate("window.webStorageMetrics ? JSON.parse(window.webStorageMetrics):null")
 def wait(check):
  end=time.time()+120
  while time.time()<end:
   m=metrics()
   if m and check(m):return m
   if m and m.get("error"):raise AssertionError(str(m))
   page.wait_for_timeout(120)
  page.screenshot(path=str(OUT/"management-failure.png"))
  raise AssertionError(str(metrics()))
 def scene(name):return wait(lambda m:m["scene"]==name and not m["saving"])
 def click(x,y):page.mouse.click(x*2/3,y*2/3)
 def rect(r):click(r[0]+r[2]/2,r[1]+r[3]/2)
 def guide():
  if metrics().get("guide",{}).get("active"):
   page.keyboard.press("Escape")
   wait(lambda m:not m["saving"] and not m["guide"]["active"])
 menu=scene("CampaignMenu");rect(menu["ui"]["play_button"]);slots=scene("CampaignSlots")
 rect(slots["rect_maps"]["backup_buttons"]["import"]);wait(lambda m:m["modal"]=="BackupModal")
 with page.expect_file_chooser() as chooser:click(960,366)
 chooser.value.set_files(str(fixture));wait(lambda m:m["modal"] is None and not m["saving"])
 click(443,520);world=scene("CampaignMap")
 rect(world["ui"]["shop_button"]);shop=scene("ShopScene");guide()
 page.mouse.move(5,200)
 starting=metrics()["frames"]
 wait(lambda m:m["frames"]>=starting+60)
 performance=[]
 for _ in range(8):
  page.wait_for_timeout(250)
  m=metrics();performance.append(dict(fps=m["fps"],draw_ms=m["draw_profile"]["total"]))
 page.mouse.move(1020,350);page.mouse.wheel(0,600)
 wait(lambda m:m["page"]>0)
 page.mouse.wheel(0,-600);wait(lambda m:m["page"]==0)
 rect(metrics()["rect_maps"]["offer_rects"]["Investida"])
 wait(lambda m:not m["saving"] and "Investida" in m["data"]["progresso"]["cartas_colecao"])
 page.screenshot(path=str(OUT/"shop.png"))
 rect(metrics()["ui"]["back_button"]);world=scene("CampaignMap")
 rect(world["ui"]["backpack_button"]);scene("BackpackScene");guide()
 rect(metrics()["rect_maps"]["cards"]["Investida"])
 wait(lambda m:not m["saving"] and "Investida" in m["data"]["progresso"]["deck_slots"])
 rect(metrics()["ui"]["ultimate_tab_rect"]);page.wait_for_timeout(200)
 rect(metrics()["rect_maps"]["ultimate_buttons"]["forcas_ancestrais"])
 wait(lambda m:not m["saving"] and m["data"]["progresso"]["ultimate_equipada"]=="forcas_ancestrais")
 page.screenshot(path=str(OUT/"backpack.png"))
 rect(metrics()["ui"]["back_rect"]);world=scene("CampaignMap")
 rect(world["ui"]["shop_button"]);scene("ShopScene")
 rect(metrics()["ui"]["workshop_button"]);scene("RogueliteScene");guide()
 rect(metrics()["rect_maps"]["type_rects"]["Soco Simples"]);page.wait_for_timeout(150)
 page.screenshot(path=str(OUT/"upgrade-preview.png"))
 rect(metrics()["ui"]["upgrade_button"])
 wait(lambda m:not m["saving"] and any(c["name"]=="Soco Simples" and c["level"]==2 for c in m["data"]["progresso"]["copies"]))
 page.keyboard.press("Escape");world=scene("CampaignMap")
 click(1878,56);wait(lambda m:m["modal"]=="OptionsScene")
 slider=metrics()["rect_maps"]["sliders"]["master_volume"]
 x,y,w,h=slider
 page.mouse.move((x+w*.8)*2/3,(y+h/2)*2/3)
 page.mouse.down()
 page.mouse.move((x+w*.35)*2/3,(y+h/2)*2/3,steps=8)
 page.mouse.up()
 wait(lambda m:.3<m["preferences"]["master_volume"]<.4)
 tab=metrics()["rect_maps"]["tab_rects"]["video"]
 rect(tab);wait(lambda m:m["active_tab"]=="video")
 rect(metrics()["rect_maps"]["tab_rects"]["audio"])
 wait(lambda m:m["active_tab"]=="audio")
 previous_volume=metrics()["preferences"]["master_volume"]
 page.keyboard.press("ArrowLeft")
 volume=wait(lambda m:m["preferences"]["master_volume"]<previous_volume-.001)["preferences"]["master_volume"]
 page.screenshot(path=str(OUT/"options.png"))
 page.keyboard.press("Escape");wait(lambda m:m["modal"] is None)
 page.reload();menu=scene("CampaignMenu");rect(menu["ui"]["play_button"]);scene("CampaignSlots");click(443,520);world=scene("CampaignMap")
 assert world["preferences"]["master_volume"]==volume
 assert "Investida" in world["data"]["progresso"]["deck_slots"]
 assert world["data"]["progresso"]["ultimate_equipada"]=="forcas_ancestrais"
 assert all(world["data"]["perfil"]["tutoriais_gerenciamento"].values())
 assert any(c["name"]=="Soco Simples" and c["level"]==2 for c in world["data"]["progresso"]["copies"])
 result=dict(passed=True,shop_fps_median=statistics.median(m["fps"] for m in performance),shop_draw_ms_median=statistics.median(m["draw_ms"] for m in performance),checks=["shop_purchase","shop_wheel","backpack_equipment","ultimate_equipment",
  "upgrade_comparison_lv1_lv2","settings_keyboard","settings_slider","settings_tabs","guides","indexeddb_reload","preferences_reload"])
 (OUT/"management-result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
 (OUT/"management-browser.log").write_text("\n".join(logs),encoding="utf-8")
 print(json.dumps(result),flush=True)
 browser.close()

