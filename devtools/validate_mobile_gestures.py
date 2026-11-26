"""Tempos e cancelamentos do host touch com relógio Chromium controlado."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]


def main():
    checks=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        context=browser.new_context(viewport=dict(width=844,height=390),is_mobile=True,has_touch=True)
        page=context.new_page()
        page.set_content('<canvas id="canvas" width="960" height="540" style="width:844px;height:390px"></canvas><div id="mobile-ui"></div><div id="mobile-rotate" hidden></div><style>.hold-inspection{pointer-events:none}</style>')
        page.evaluate("document.querySelector('#canvas').setPointerCapture=()=>{}")
        page.clock.install(time="2026-11-26T12:00:00")
        page.clock.pause_at("2026-11-26T12:00:01")
        page.add_script_tag(path=str(ROOT/"web/mobile.js"))
        model=dict(epoch="1",pending=False,kind="battle",scene="CampaignBattle",combat_touch=True,hold_targets=[[0,0,1920,1080]])
        def reset():
            page.evaluate("scapeMobile.cancel()")
            page.evaluate("v=>scapeMobile.publish(JSON.stringify(v))",model)
        def event(kind,id=1,x=100,y=100):
            page.dispatch_event("#canvas","pointer"+kind,dict(pointerId=id,pointerType="touch",clientX=x,clientY=y,bubbles=True))
        def drain():return page.evaluate("JSON.parse(scapeMobile.drain()).map(v=>v.id)")
        reset();event("down");page.clock.run_for(219);assert drain()==[];event("up")
        actual=drain();assert actual==["native-tap"],actual;checks.append("tap_at_219ms_is_immediate_single_command")
        reset();event("down");page.clock.run_for(220);assert drain()==["native-hold-start"]
        selected={**model,"selection":dict(title="Carta",image=None,text="Texto",holding=True,actions=[])}
        page.evaluate("v=>scapeMobile.publish(JSON.stringify(v))",selected)
        assert page.locator(".hold-inspection button").count()==0
        assert page.locator(".hold-inspection").evaluate("e=>getComputedStyle(e).pointerEvents")=="none"
        event("up");assert drain()==["native-hold-end"]
        assert page.locator(".hold-inspection").count()==0
        checks.append("hold_at_220ms_has_no_confirm_and_release_never_taps")
        reset();event("down");event("move",x=150);page.clock.run_for(300);event("up",x=150)
        assert drain()==[];checks.append("drag_cancels_hold_and_does_not_play")
        reset();event("down");page.clock.run_for(250);drain();event("cancel");event("up")
        assert drain()==[];checks.append("pointercancel_cannot_play")
        reset();event("down");event("down",id=2);page.clock.run_for(300);event("up");event("up",id=2)
        assert drain()==[];checks.append("second_finger_cancels_without_duplicate_action")
        reset();event("down");page.evaluate("window.dispatchEvent(new Event('blur'))");page.clock.run_for(300);event("up")
        assert drain()==[];checks.append("blur_invalidates_gesture")
        reset();page.evaluate("v=>scapeMobile.publish(JSON.stringify(v))",{**model,"pending":True})
        event("down");event("up");assert drain()==[];checks.append("pending_commit_blocks_touch")
        context.close();browser.close()
    out=ROOT/"build/mobile-gestures.json";out.write_text(json.dumps(dict(passed=True,checks=checks),indent=2)+"\n",encoding="utf-8")
    print(out.read_text(),flush=True)

if __name__=="__main__":main()
