"""A entrada nativa real desenha o menu e encerra sem carregar bibliotecas web."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class NativeEntrySmokeTests(unittest.TestCase):
    def test_menu_source_smoke_is_isolated_and_rendered(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/"native.json"
            env=dict(os.environ,SDL_VIDEODRIVER="dummy",SDL_AUDIODRIVER="dummy")
            process=subprocess.run([sys.executable,str(ROOT/"main.py"),"--smoke-report",str(target)],
                cwd=ROOT,env=env,capture_output=True,text=True,timeout=60)
            self.assertEqual(process.returncode,0,process.stderr)
            report=json.loads(target.read_text(encoding="utf-8"))
            self.assertTrue(report["passed"])
            self.assertEqual(report["scene"],"MenuScene")
            self.assertEqual(report["window"],"WindowManager")
            self.assertEqual(report["virtual_size"],[1920,1080])
            self.assertEqual(report["frames"],4)
            self.assertTrue(report["assets_exist"])
            self.assertEqual(report["web_dependencies_loaded"],[])
            self.assertTrue(target.with_suffix(".png").exists())
            self.assertFalse((Path(folder)/"preferences-smoke.json").exists())

