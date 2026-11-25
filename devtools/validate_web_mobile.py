"""Fluxo touch real no Chromium; checkpoints QA v15, sem alterar o runtime."""
from pathlib import Path
import json,time,statistics
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"build/web-stage5";OUT.mkdir(exist_ok=True)
source=json.loads((ROOT/"build/web-stage4/management.json").read_text(encoding="utf-8"))
source["run"]["combat_snapshot"]=None
fixture=OUT/"management.json";fixture.write_text(json.dumps(source,ensure_ascii=False),encoding="utf-8")

def run_device(p,name,size):
 browser=p.chromium.launch(headless=True)
 context=browser.new_context(viewport=dict(width=size[0],height=size[1]),is_mobile=True,has_touch=True,device_scale_factor=1)
 page=context.new_page();logs=[];errors=[];checks=[];samples=[]
 page.on("console",lambda m:logs.append(m.text))
 page.on("pageerror",lambda e:errors.append(str(e)))
 page.goto("http://127.0.0.1:8765/")
 def metrics():return page.evaluate("window.webStorageMetrics ? JSON.parse(webStorageMetrics):null")
 def wait(check,seconds=120):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   error=page.evaluate("window.webRuntimeError||null")
   if error:raise AssertionError(error)
   m=metrics()
   if m and check(m):return m
   if m and m.get("error"):raise AssertionError(str(m["error"]))
   page.wait_for_timeout(150)
  raise AssertionError("Timeout "+str(metrics())+" buttons="+str(page.locator("#mobile-ui button").all_text_contents()))
 def scene(n):return wait(lambda m:m["scene"]==n and not m["saving"])
 def tap(text):
  print(name+" TAP "+text,flush=True)
  page.get_by_role("button",name=text,exact=True).tap(timeout=15000)
  page.wait_for_timeout(220)
 def contains(text):
  page.locator("#mobile-ui button").filter(has_text=text).first.tap(timeout=15000)
  page.wait_for_timeout(220)
 def screenshot(label):page.screenshot(path=str(OUT/(name+"-"+label+".png")))
 def guide():
  while page.locator(".mobile-guide").count():
   buttons=page.locator(".mobile-guide button")
   label="CONCLUIR" if "CONCLUIR" in buttons.all_text_contents() else "PRÓXIMO"
   page.locator(".mobile-guide").get_by_role("button",name=label,exact=True).tap()
   page.wait_for_timeout(500)
  wait(lambda m:not m["saving"])
 def import_fixture(path,occupied=False):
  scene("CampaignMenu");tap("JOGAR");scene("CampaignSlots");tap("IMPORTAR")
  wait(lambda m:m["modal"]=="BackupModal")
  if occupied:
   tap("ESPAÇO 1");wait(lambda m:m["modal"]=="ConfirmationModal")
   with page.expect_file_chooser() as chooser:tap("SIM, IMPORTAR")
  else:
   with page.expect_file_chooser() as chooser:tap("ESPAÇO 1")
  chooser.value.set_files(str(path))
  wait(lambda m:m["modal"] is None and not m["saving"])
  tap("JORNADA 1");scene("CampaignMap")
 try:
  scene("CampaignMenu")
  assert metrics()["compact"]
  # Rotação pausa frames e relógio; retornar descarta gesto antigo.
  page.set_viewport_size(dict(width=size[1],height=size[0]))
  wait(lambda m:m["portrait_blocked"] and not m["active"])
  frames=metrics()["frames"];page.wait_for_timeout(1000)
  assert metrics()["frames"]==frames
  screenshot("portrait")
  page.set_viewport_size(dict(width=size[0],height=size[1]))
  wait(lambda m:m["active"] and not m["portrait_blocked"])
  checks.append("orientation_pause_resume")
  page.evaluate("window.dispatchEvent(new Event('blur'))")
  wait(lambda m:not m["active"])
  frozen=metrics()["frames"];page.wait_for_timeout(600)
  assert metrics()["frames"]==frozen
  page.evaluate("window.dispatchEvent(new Event('focus'))")
  wait(lambda m:m["active"])
  checks.append("focus_suspend_resume")
  import_fixture(fixture)
  tap("LOJA");scene("ShopScene");guide()
  screenshot("shop")
  # Duas ofertas por página em smartphone; navegação real para Investida.
  for _ in range(12):
   if any("Investida" in t for t in page.locator(".mobile-item").all_text_contents()):break
   contains("PRÓXIMA")
  before=metrics()["data"]["progresso"]["moedas"]
  contains("Investida");assert page.locator(".inspection-panel").is_visible()
  assert metrics()["data"]["progresso"]["moedas"]==before
  screenshot("inspection")
  tap("COMPRAR")
  wait(lambda m:not m["saving"] and "Investida" in m["data"]["progresso"]["cartas_colecao"])
  checks.append("shop_inspect_confirm")
  tap("MAPA");scene("CampaignMap");tap("MOCHILA");scene("BackpackScene");guide()
  for _ in range(12):
   if any("Investida" in t for t in page.locator(".mobile-item").all_text_contents()):break
   contains("PRÓXIMA")
  deck=metrics()["draft_slots"]
  contains("Investida")
  assert metrics()["draft_slots"]==deck
  tap("EQUIPAR")
  wait(lambda m:not m["saving"] and "Investida" in m["draft_slots"])
  tap("EQUIPADO");contains("Investida");tap("REMOVER")
  wait(lambda m:not m["saving"] and "Investida" not in m["draft_slots"])
  tap("ULTIMATES");contains("Forças Ancestrais");tap("EQUIPAR")
  wait(lambda m:not m["saving"] and m["data"]["progresso"]["ultimate_equipada"]=="forcas_ancestrais")
  checks.append("backpack_tabs_equipment_ultimate")
  screenshot("backpack")
  tap("VOLTAR");scene("CampaignMap");tap("LOJA");scene("ShopScene")
  tap("ALTAR");scene("RogueliteScene");guide()
  contains("Soco Simples")
  assert "ANTES" in page.locator(".inspection-content").inner_text()
  assert "DEPOIS" in page.locator(".inspection-content").inner_text()
  tap("ANTES · LV1");before_art=page.locator(".inspection-panel>img").get_attribute("src")
  tap("DEPOIS · LV2");after_art=page.locator(".inspection-panel>img").get_attribute("src")
  assert before_art!=after_art
  screenshot("upgrade")
  tap("APRIMORAR")
  wait(lambda m:not m["saving"] and any(c["name"]=="Soco Simples" and c["level"]==2 for c in m["data"]["progresso"]["copies"]))
  checks.append("upgrade_copy_before_after")
  tap("CONFIGURAÇÕES");wait(lambda m:m["modal"]=="OptionsScene")
  count=page.locator(".mobile-range").count()
  assert count==4,count
  plus=page.locator(".mobile-range").nth(1).get_by_role("button",name="+",exact=True)
  prior=metrics()["preferences"]["music_volume"];plus.tap()
  wait(lambda m:m["preferences"]["music_volume"]>prior)
  saved=metrics()["preferences"]["music_volume"]
  tap("VÍDEO");tap("ÁUDIO")
  screenshot("settings")
  tap("RETORNAR");wait(lambda m:m["modal"] is None)
  tap("VOLTAR");scene("CampaignMap")
  page.reload();scene("CampaignMenu");tap("JOGAR");scene("CampaignSlots");tap("JORNADA 1")
  scene("CampaignMap");assert metrics()["preferences"]["music_volume"]==saved
  checks.append("settings_persist_reload")
  # Retomar combate de QA pela mesma importação usada no Desktop.
  tap("MENU");scene("CampaignMenu")
  import_fixture(ROOT/"build/web-stage4/fixtures/1-0.json",occupied=True)
  tap("JOGAR");scene("CampaignBattle")
  wait(lambda m:m["state"]=="player_turn")
  # Ultimate também usa inspeção, custo real e confirmação explícita.
  contains("Mana Ancestral")
  assert metrics()["data"]["progresso"]["ultimate_equipada"]=="mana_ancestral"
  tap("JOGAR ULTIMATE")
  wait(lambda m:m["action"]=="Mana Ancestral")
  wait(lambda m:not m["action"] and not m["saving"])
  checks.append("ultimate_inspect_confirm")
  # Inspeção de intenção não altera energia; fechar fora não joga carta.
  if page.get_by_role("button",name="INTENÇÃO 1",exact=True).count():
   tap("INTENÇÃO 1");tap("FECHAR")
  hand=page.locator("#mobile-ui .mobile-item").first
  energy=metrics()["energy"];hand.tap();page.wait_for_timeout(200)
  assert metrics()["energy"]==energy
  screenshot("battle-preview")
  page.evaluate("document.dispatchEvent(new PointerEvent('pointercancel'))")
  page.wait_for_timeout(400)
  assert page.locator(".inspection-panel").count()==0
  page.locator("#mobile-ui .mobile-item").first.tap();page.wait_for_timeout(200)
  checks.append("pointercancel_clears_selection")
  # Rotacionar com seleção aberta cancela sem ativar.
  page.set_viewport_size(dict(width=size[1],height=size[0]))
  wait(lambda m:m["portrait_blocked"]);page.set_viewport_size(dict(width=size[0],height=size[1]))
  wait(lambda m:m["active"] and not m["portrait_blocked"])
  assert page.locator(".inspection-panel").count()==0
  checks.append("touch_inspection_rotation_cancel")
  # Combate real com confirmação, encerramento de turno e recompensa.
  end=time.monotonic()+120
  while time.monotonic()<end:
   m=metrics();samples.append(m["fps"])
   if m["victory_ready"]:break
   if m["state"]=="player_turn" and not m["action"] and not m["saving"]:
    usable=next((i for i,c in enumerate(m["hand"]) if c["cost"]<=m["energy"]),None)
    if usable is not None:
     page.locator("#mobile-ui .mobile-item").nth(usable).tap()
     page.wait_for_timeout(150)
     tap("JOGAR")
    else:tap("FIM DO TURNO")
   page.wait_for_timeout(300)
  wait(lambda m:m["victory_ready"])
  screenshot("reward")
  page.locator("#mobile-ui .mobile-item").first.tap();page.wait_for_timeout(200)
  tap("ESCOLHER");scene("CampaignMap")
  checks.append("battle_reward_confirm")
  # Cada controle exposto mede ao menos 44 CSS px em ambos os eixos.
  sizes=page.locator("#mobile-ui button,#mobile-ui input").evaluate_all("(els)=>els.filter(e=>e.getClientRects().length).map(e=>{let r=e.getBoundingClientRect();return [r.width,r.height]})")
  assert all(w>=43.9 and h>=43.9 for w,h in sizes),sizes
  checks.append("minimum_touch_targets")
  memory=page.evaluate("({js:performance.memory?.usedJSHeapSize||0,wasm:window.python?.HEAPU8?.buffer.byteLength||window.VM?.HEAPU8?.buffer.byteLength||0})")
  assert not errors,errors
  result=dict(device=name,viewport=size,passed=True,checks=checks,fps_median=statistics.median(samples),memory=memory,errors=errors)
  (OUT/(name+"-result.json")).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
  print(json.dumps(result,ensure_ascii=True),flush=True)
 except Exception:
  screenshot("failure")
  (OUT/(name+"-console.log")).write_text("\n".join(logs),encoding="utf-8")
  raise
 finally:browser.close()
with sync_playwright() as p:
 for name,size in (("android",(915,412)),("iphone",(844,390))):
  run_device(p,name,size)

