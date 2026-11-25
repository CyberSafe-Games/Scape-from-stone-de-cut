"""Valida backing HiDPI, entrada e PCM real do mixer WASM no Chromium."""
import argparse,base64,json,statistics,time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
AUDIO_PROBE=r"""
(() => {
  window.qaAudio={nodes:[],samples:[],connections:0,buffers:[]};
  const original=AudioNode.prototype.connect;
  const taps=new WeakMap();
  AudioNode.prototype.connect=function(destination,...args){
    if(destination instanceof AudioDestinationNode){
      let analyser=taps.get(this);
      if(!analyser){
        analyser=this.context.createAnalyser();analyser.fftSize=2048;
        taps.set(this,analyser);qaAudio.nodes.push(analyser);
        original.call(analyser,destination);
      }
      qaAudio.connections++;
      qaAudio.buffers.push({buffer:this.bufferSize||null,sampleRate:this.context.sampleRate});
      original.call(this,analyser,...args);return destination;
    }
    return original.call(this,destination,...args);
  };
  setInterval(()=>{
    for(const node of qaAudio.nodes){
      const values=new Float32Array(node.fftSize);node.getFloatTimeDomainData(values);
      let peak=0,sum=0,clipped=0;
      for(const v of values){peak=Math.max(peak,Math.abs(v));sum+=v*v;if(Math.abs(v)>=0.9999)clipped++;}
      qaAudio.samples.push({peak,rms:Math.sqrt(sum/values.length),clipped,state:node.context.state});
      if(qaAudio.samples.length>2400)qaAudio.samples.shift();
    }
  },50);
})();
"""
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url",default="http://127.0.0.1:8765/")
    parser.add_argument("--output",default="build/web-quality")
    args=parser.parse_args()
    out=ROOT/args.output;out.mkdir(parents=True,exist_ok=True)
    result=dict(passed=False,density=[],checks=[])
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        context=browser.new_context(viewport=dict(width=1280,height=720),device_scale_factor=1.25)
        context.add_init_script(AUDIO_PROBE)
        context.add_init_script("""localStorage.setItem('scape.preferences.v1',JSON.stringify({
            master_volume:1,sfx_volume:1,music_volume:1,combat_volume:1,damage_volume:1}));""")
        page=context.new_page();errors=[]
        page.on("pageerror",lambda e:errors.append(str(e)))
        def metrics():return page.evaluate("window.webStorageMetrics ? JSON.parse(webStorageMetrics):null")
        def wait(check):
            deadline=time.monotonic()+150
            while time.monotonic()<deadline:
                m=metrics()
                if errors:raise AssertionError(errors)
                if m and check(m):return m
                page.wait_for_timeout(100)
            raise AssertionError(str(metrics()))
        def scene(name):
            value=wait(lambda m:m["scene"]==name and not m["saving"])
            print("OK "+name,flush=True)
            return value
        def click(x,y):
            bounds=page.locator("#canvas").bounding_box()
            page.mouse.click(bounds["x"]+x/1920*bounds["width"],bounds["y"]+y/1080*bounds["height"])
        def rect(r):click(r[0]+r[2]/2,r[1]+r[3]/2)
        def density(dpr,expected):
            wait(lambda m:m["render_buffer"]==list(expected))
            canvas=page.evaluate("""()=>{const c=document.querySelector('#canvas'),r=c.getBoundingClientRect();
                return {buffer:[c.width,c.height],css:[r.width,r.height],dpr:devicePixelRatio,
                    rendering:getComputedStyle(c).imageRendering};}""")
            assert canvas["buffer"]==list(expected),canvas
            assert canvas["rendering"]=="pixelated",canvas
            result["density"].append(canvas)
        try:
            page.goto(args.url)
            menu=scene("CampaignMenu")
            assert not menu["audio_available"]
            assert menu["audio_mix"]["format"] is None,menu["audio_mix"]
            result["before_gesture"]=menu["audio_mix"]
            density(1.25,(1600,900))
            cdp=context.new_cdp_session(page)
            for dpr in (1.5,2):
                cdp.send("Emulation.setDeviceMetricsOverride",dict(width=1280,height=720,deviceScaleFactor=dpr,mobile=False))
                density(dpr,(1920,1080))
            result["checks"].append("windows_125_150_200_percent_backing_and_css")
            rect(metrics()["ui"]["play_button"]);scene("CampaignSlots")
            wait(lambda m:m["audio_available"])
            mix=metrics()["audio_mix"]
            assert mix["format"] in ([44100,-16,2],[48000,-16,2]) and mix["channels"]==4,mix
            result["checks"].append("hidpi_mouse_mapping_and_gesture_audio")
            rect(metrics()["rect_maps"]["backup_buttons"]["import"]);wait(lambda m:m["modal"]=="BackupModal")
            with page.expect_file_chooser() as chooser:click(960,366)
            chooser.value.set_files(str(ROOT/"build/web-stage4/fixtures/1-0.json"))
            wait(lambda m:m["modal"] is None and not m["saving"])
            click(443,520);world=scene("CampaignMap")
            rect(world["ui"]["play_button"]);scene("CampaignBattle")
            page.wait_for_function("window.scapePWA?.offlineReady",timeout=120000)
            page.wait_for_timeout(1500)
            fps=[]
            for _ in range(20):
                page.wait_for_timeout(200);fps.append(metrics()["fps"])
            result["combat_fps_median"]=statistics.median(fps)
            result["frame_cost_ms"]=metrics()["frame_cost_ms"]
            result["render_buffer"]=metrics()["render_buffer"]
            (out/"desktop-dpr2.png").write_bytes(base64.b64decode(cdp.send("Page.captureScreenshot",dict(format="png"))["data"]))
            # Música e efeitos reais de cartas; sem sintetizar áudio no probe.
            hand=metrics()["hand"]
            rect(hand[0]["rect"])
            wait(lambda m:m["energy"]<8)
            page.wait_for_timeout(2500)
            samples=page.evaluate("qaAudio.samples")
            audible=[x for x in samples if x["peak"]>0.00001]
            assert audible,"Nenhum PCM real capturado"
            assert max(x["peak"] for x in audible)<0.9999,audible[-10:]
            assert all(x["clipped"]==0 for x in samples)
            mix=metrics()["audio_mix"]
            assert mix["music_volume"]<=0.25 and mix["max_sfx_gain"]<=0.16,mix
            result["audio"]=dict(samples=len(samples),audible_samples=len(audible),
                peak=max(x["peak"] for x in samples),clipped_samples=sum(x["clipped"] for x in samples),
                mix=mix,connections=page.evaluate("qaAudio.connections"),
                browser_buffers=page.evaluate("qaAudio.buffers"))
            result["checks"].append("real_music_and_card_sfx_pcm_without_clipping")
            # Gesto repetido/retomada não cria outra saída de áudio.
            connections=page.evaluate("qaAudio.connections")
            click(25,400);click(25,400)
            page.evaluate("window.dispatchEvent(new Event('blur'))")
            wait(lambda m:not m["active"])
            page.evaluate("window.dispatchEvent(new Event('focus'))")
            wait(lambda m:m["active"])
            page.wait_for_timeout(500)
            assert page.evaluate("qaAudio.connections")==connections
            result["checks"].append("repeated_unlock_focus_no_duplicate_audio_output")
            context.close()
            context=browser.new_context(viewport=dict(width=844,height=390),is_mobile=True,
                                        has_touch=True,device_scale_factor=3)
            page=context.new_page();errors=[]
            page.on("pageerror",lambda e:errors.append(str(e)))
            page.goto(args.url);scene("CampaignMenu")
            canvas=page.locator("#canvas").bounding_box()
            factor=min(canvas["width"]*2/1920,canvas["height"]*2/1080,1)
            expected=(round(1920*factor),round(1080*factor))
            density(3,expected)
            result["checks"].append("mobile_dpr3_capped_to_two")
            page.screenshot(path=str(out/"mobile-dpr3.png"))
            result["errors"]=errors
            result["passed"]=True
            (out/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            print(json.dumps(result,ensure_ascii=True),flush=True)
        except Exception:
            page.screenshot(path=str(out/"failure.png"))
            print(json.dumps(dict(scene=(metrics() or {}).get("scene"),errors=errors),ensure_ascii=True),flush=True)
            raise
        finally:
            context.close();browser.close()
if __name__=="__main__":main()
