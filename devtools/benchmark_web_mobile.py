"""Benchmark Chromium isolado de uma batalha real sobre dois builds da mesma arte."""
import sys,io,tarfile,subprocess,json,time,statistics,threading
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
import argparse
parser=argparse.ArgumentParser(description="Compara frame time mobile com referência Git, sem alterar o checkout ou saves.")
parser.add_argument("--baseline-ref",default="e7b1ff5")
args=parser.parse_args()
root=Path(__file__).resolve().parents[1];dist=root/"dist/web"
baseline=subprocess.check_output(["git","rev-parse","--verify",args.baseline_ref+"^{commit}"],cwd=root,text=True).strip()

old_sources={}
for name in subprocess.check_output(["git","diff",baseline,"--name-only","--","src","web"],cwd=root,text=True).splitlines():
 if name.startswith(("src/","web/")) and name.endswith(".py"):
  old_sources["assets/"+name]=subprocess.check_output(["git","show",baseline+":"+name],cwd=root)
old_host={name:subprocess.check_output(["git","show",baseline+":web/"+name],cwd=root) for name in ("styles.css","mobile.js","bridge.js")}
archive=io.BytesIO()
with tarfile.open(dist/"web-poc.tar.gz","r:gz") as source,tarfile.open(fileobj=archive,mode="w:gz") as target:
 for member in source:
  data=source.extractfile(member).read() if member.isfile() else None
  if member.name in old_sources:
   data=old_sources[member.name];member.size=len(data)
  target.addfile(member,io.BytesIO(data) if data is not None else None)
class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  path=self.path.split("?")[0];mode,_,relative=path.lstrip("/").partition("/")
  if relative=="pwa.js":data=b"window.scapePWA={offlineReady:true,updating:false};";kind="text/javascript"
  elif mode=="baseline" and relative=="web-poc.tar.gz":data=archive.getvalue();kind="application/gzip"
  elif mode=="baseline" and relative in old_host:data=old_host[relative];kind="text/css" if relative.endswith(".css") else "text/javascript"
  else:
   self.path="/"+relative
   return super().do_GET()
  self.send_response(200);self.send_header("Content-Type",kind);self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data)
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(dist),**kwargs)
server=ThreadingHTTPServer(("127.0.0.1",0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
results={}
print("Baseline "+baseline,flush=True)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 for mode in ("baseline","current"):
  context=browser.new_context(viewport=dict(width=844,height=390),is_mobile=True,has_touch=True,device_scale_factor=3)
  page=context.new_page();page.goto(f"http://127.0.0.1:{server.server_port}/{mode}/?profile=1")
  def state():return page.evaluate("window.webStorageMetrics ? JSON.parse(webStorageMetrics):null")
  def wait(fn):
   end=time.monotonic()+120
   while time.monotonic()<end:
    m=state()
    if m and fn(m):return m
    page.wait_for_timeout(100)
   raise AssertionError((mode,(state() or {}).get("scene")))
  def scene(name):return wait(lambda m:m["scene"]==name and not m["saving"])
  def click(x,y):
   r=page.locator("#canvas").bounding_box();page.touchscreen.tap(r["x"]+x*r["width"]/1920,r["y"]+y*r["height"]/1080)
  def rect(r):click(r[0]+r[2]/2,r[1]+r[3]/2)
  menu=scene("CampaignMenu")
  rect(menu["ui"]["play_button"]);scene("CampaignSlots")
  rect(state()["rect_maps"]["backup_buttons"]["import"]);wait(lambda m:m["modal"]=="BackupModal")
  with page.expect_file_chooser() as chooser:click(960,366)
  chooser.value.set_files(str(root/"build/web-stage4/fixtures/1-0.json"));wait(lambda m:m["modal"] is None and not m["saving"])
  click(443,520);world=scene("CampaignMap");rect(world["ui"]["play_button"]);scene("CampaignBattle")
  page.mouse.move(5,400);page.wait_for_timeout(5000)
  samples=[]
  for _ in range(35):
   page.wait_for_timeout(200);samples.append(state())
  results[mode]=dict(fps=statistics.median(x["fps"] for x in samples),buffer=samples[-1]["render_buffer"],physical_canvas=samples[-1].get("physical_canvas",[1920,1080]),cache=samples[-1].get("mobile_render_cache",{}),
   frame_ms={k:statistics.median(x["frame_cost_ms"][k] for x in samples) for k in ("draw","present","update")},
   raster_samples=[x.get("mobile_render_cache",{}) for x in samples])
  print(json.dumps({mode:results[mode]}),flush=True);context.close()
 browser.close()
server.shutdown()
samples=results["current"]["raster_samples"]
assert all(x.get("native_scale_calls")==0 and x.get("text_renders_this_frame")==0 and x.get("scratch_created_this_frame")==0 for x in samples),samples
(root/"build/mobile-tap-hold-ab.json").write_text(json.dumps(dict(baseline_ref=baseline,**results),indent=2)+"\n",encoding="utf-8")
