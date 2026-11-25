"""Integridade do build PWA, ícones oficiais, arquivos e lock do runtime."""
import hashlib,io,json,tarfile,tempfile,unittest
from pathlib import Path
from PIL import Image
from devtools.web_distribution import safe_relative,verify_pack,verify_distribution,runtime_resources
ROOT=Path(__file__).resolve().parents[1]

class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest=json.loads((ROOT/"web/manifest.webmanifest").read_text(encoding="utf-8"))
    def test_pwa_identity_and_relative_scope(self):
        self.assertNotIn("id",self.manifest)  # Identidade padrão = start_url, inclusive sob subpastas.
        self.assertEqual(self.manifest["scope"],"./")
        self.assertEqual(self.manifest["start_url"],"./")
        self.assertEqual(self.manifest["lang"],"pt-BR")
    def test_standalone_landscape_palette(self):
        self.assertEqual(self.manifest["display"],"standalone")
        self.assertEqual(self.manifest["orientation"],"landscape")
        self.assertEqual(self.manifest["background_color"],"#090e0d")
    def test_icons_exist_have_declared_dimensions(self):
        for spec in self.manifest["icons"]:
            with Image.open(ROOT/"web"/spec["src"]) as image:
                self.assertEqual("x".join(map(str,image.size)),spec["sizes"])
                self.assertEqual(image.mode,"RGB")
    def test_maskable_is_separate_from_any_icon(self):
        records=self.manifest["icons"]
        self.assertEqual(sum(r["purpose"]=="maskable" for r in records),1)
        self.assertNotEqual((ROOT/"web/icons/pwa-512.png").read_bytes(),(ROOT/"web/icons/pwa-maskable-512.png").read_bytes())
    def test_maskable_identity_fits_safe_circle(self):
        with Image.open(ROOT/"web/icons/pwa-maskable-512.png") as image:
            pixels=image.load()
            for y in range(512):
                for x in range(512):
                    if (x-256)**2+(y-256)**2>205**2:self.assertEqual(pixels[x,y],(9,14,13))
    def test_icon_sources_and_derivatives_match_manifest(self):
        manifest=json.loads((ROOT/"web/icons/art_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256((ROOT/manifest["source"]).read_bytes()).hexdigest(),manifest["source_sha256"])
        for name,record in manifest["icons"].items():
            self.assertEqual(hashlib.sha256((ROOT/"web/icons"/name).read_bytes()).hexdigest(),record["sha256"])
    def test_apple_touch_icon_is_180(self):
        with Image.open(ROOT/"web/icons/apple-touch-icon.png") as image:self.assertEqual(image.size,(180,180))

class PackageValidationTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.root=Path(self.folder.name)
    def pack(self,members):
        target=self.root/"pack.tar.gz"
        with tarfile.open(target,"w:gz") as archive:
            for name,kind in members:
                info=tarfile.TarInfo(name)
                if kind=="file":
                    info.size=3;archive.addfile(info,io.BytesIO(b"abc"))
                else:info.type=tarfile.SYMTYPE;info.linkname="../escape";archive.addfile(info)
        return dict(url=target.name,bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),files=[n for n,_ in members])
    def test_valid_package_inventory(self):
        self.assertTrue(verify_pack(self.root,self.pack([("assets/test.png","file")])))
    def test_truncated_package_rejected(self):
        record=self.pack([("assets/test.png","file")])
        (self.root/record["url"]).write_bytes(b"partial")
        with self.assertRaises(ValueError):verify_pack(self.root,record)
    def test_same_size_corruption_rejected(self):
        record=self.pack([("assets/test.png","file")]);p=self.root/record["url"]
        data=p.read_bytes();p.write_bytes(bytes([data[0]^1])+data[1:])
        with self.assertRaises(ValueError):verify_pack(self.root,record)
    def test_traversal_inside_tar_rejected(self):
        record=self.pack([("../outside","file")])
        with self.assertRaises(ValueError):verify_pack(self.root,record)
    def test_symlink_member_rejected(self):
        record=self.pack([("assets/link","link")])
        with self.assertRaises(ValueError):verify_pack(self.root,record)
    def test_inventory_mismatch_rejected(self):
        record=self.pack([("assets/a","file")]);record["files"]=["assets/b"]
        with self.assertRaises(ValueError):verify_pack(self.root,record)
    def test_untrusted_paths_rejected(self):
        for path in ("../x","/x","packs/../../save.json","packs\\x","C:/secret",""):
            with self.assertRaises(ValueError):safe_relative(path)
    def test_duplicate_inventory_rejected(self):
        record=self.pack([("assets/a","file"),("assets/a","file")])
        with self.assertRaises(ValueError):verify_pack(self.root,record)
    def test_unknown_runtime_origin_rejected_before_download(self):
        with self.assertRaises(ValueError):
            runtime_resources(self.root,dict(resources=[dict(url="https://untrusted.invalid/a",sha256="0"*64,bytes=1)]))
    def test_corrupted_runtime_cache_rejected(self):
        cache=self.root/"build/runtime-cache";cache.mkdir(parents=True)
        (cache/("0"*64)).write_bytes(b"bad")
        with self.assertRaises(ValueError):
            runtime_resources(self.root,dict(resources=[dict(url="https://pygame-web.github.io/cdn/fake",sha256="0"*64,bytes=3)]))
    def test_distribution_rejects_unlisted_files(self):
        (self.root/"web_manifest.json").write_text('{"groups":{}}')
        data=(self.root/"web_manifest.json").read_bytes()
        release=dict(version="test",files=[dict(path="web_manifest.json",bytes=len(data),sha256=hashlib.sha256(data).hexdigest())])
        (self.root/"release.json").write_text(json.dumps(release))
        self.assertEqual(verify_distribution(self.root)["version"],"test")
        (self.root/"saves.json").write_text("{}")
        with self.assertRaises(ValueError):verify_distribution(self.root)

class RuntimeLockTests(unittest.TestCase):
    def test_runtime_includes_python_wasm_data_and_pygame(self):
        lock=json.loads((ROOT/"web/runtime-lock.json").read_text())
        urls=[r["url"] for r in lock["resources"]]
        self.assertTrue(any(u.endswith("main.wasm") for u in urls))
        self.assertTrue(any(u.endswith("main.data") for u in urls))
        self.assertTrue(any("pygame_ce-" in u and u.endswith(".whl") for u in urls))
        self.assertEqual(len(urls),len(set(urls)))
        for record in lock["resources"]:
            self.assertRegex(record["sha256"],r"^[a-f0-9]{64}$")
            self.assertGreater(record["bytes"],0)

