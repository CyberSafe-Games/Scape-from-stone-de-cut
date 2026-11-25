"""Contratos de MEMFS e limites de hospedagem sem tocar nos assets reais."""
import asyncio
import base64
from contextlib import chdir
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import Mock, patch, AsyncMock
from devtools.web_hosting import evaluate_files, MIB
from web.memfs import asset_path, prune_animations
from web.assets import CampaignAssets


class MemfsTests(unittest.IsolatedAsyncioTestCase):
    def fixture(self, files):
        data=io.BytesIO()
        with tarfile.open(fileobj=data,mode="w:gz") as archive:
            for name,content in files:
                info=tarfile.TarInfo(name);info.size=len(content)
                archive.addfile(info,io.BytesIO(content))
        data=data.getvalue()
        pack=dict(url="packs/test",bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),files=[n for n,_ in files])
        bridge=Mock()
        bridge.poll.return_value=json.dumps(dict(pending=False,received=len(data),total=len(data)))
        bridge.chunk.side_effect=lambda token,offset:base64.b64encode(data[offset:offset+262144]).decode()
        owner=CampaignAssets.__new__(CampaignAssets)
        owner._completed_packs=0;owner._total_packs=1;owner.transfer_bytes=0
        return owner,pack,bridge

    async def test_download_releases_bridge_before_stream_extraction_and_removes_temp(self):
        with tempfile.TemporaryDirectory() as folder,chdir(folder):
            owner,pack,bridge=self.fixture([("assets/player/test.png",b"texture")])
            real_open=tarfile.open
            def extract(*args,**kwargs):
                bridge.release.assert_called_once()
                return real_open(*args,**kwargs)
            with patch("platform.window",Mock(scapeResources=bridge),create=True),patch("web.assets.tarfile.open",side_effect=extract),patch("tempfile.tempdir",folder):
                await owner.download(pack)
            self.assertEqual(Path("assets/player/test.png").read_bytes(),b"texture")
            self.assertFalse(list(Path(folder).glob("scape-pack-*")))
            self.assertEqual(owner.pack_temporary_bytes,0)

    async def test_invalid_digest_leaves_no_extracted_or_temporary_files(self):
        with tempfile.TemporaryDirectory() as folder,chdir(folder):
            owner,pack,bridge=self.fixture([("assets/player/a.png",b"bad")]);pack["sha256"]="0"*64
            with patch("platform.window",Mock(scapeResources=bridge),create=True),patch("tempfile.tempdir",folder):
                with self.assertRaises(OSError):await owner.download(pack)
            self.assertFalse(Path("assets").exists());self.assertFalse(list(Path(folder).glob("scape-pack-*")))
            bridge.release.assert_called_once()

    async def test_inventory_failure_removes_partial_extraction(self):
        with tempfile.TemporaryDirectory() as folder,chdir(folder):
            owner,pack,bridge=self.fixture([("assets/player/a.png",b"a"),("assets/player/b.png",b"b")])
            pack["files"].pop()
            with patch("platform.window",Mock(scapeResources=bridge),create=True):
                with self.assertRaises(OSError):await owner.download(pack)
            self.assertFalse(Path("assets/player/a.png").exists())
            self.assertEqual(owner.pack_temporary_bytes,0)

    async def test_prune_keeps_lazy_ui_music_metadata_and_only_drops_animation_png(self):
        with tempfile.TemporaryDirectory() as folder,chdir(folder):
            names=["assets/player/a.png","assets/player/manifest.json","assets/audio/music/a.ogg","assets/intent_art/slime/atk.png"]
            for name in names:
                path=Path(name);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b"abc")
            manifest={"groups":{"player":[{"files":names}]}}
            removed,freed=prune_animations(manifest,{"player"})
            self.assertEqual((removed,freed),({"player"},3))
            self.assertFalse(Path(names[0]).exists())
            self.assertTrue(all(Path(n).exists() for n in names[1:]))

    async def test_pruned_group_is_downloaded_again_before_loading_next_context(self):
        with tempfile.TemporaryDirectory() as folder,chdir(folder):
            owner=CampaignAssets.__new__(CampaignAssets)
            owner.manifest={"groups":{"player":[{"files":["assets/player/a.png"]}]}}
            owner.resident={"menu","player"};owner.pruned_groups={"player"}
            owner.release_surfaces=Mock();owner.download=AsyncMock()
            owner._load_ui_images=Mock();owner._load_ultimate_images=Mock();owner._load_coin_icon=Mock()
            owner.memfs_freed_bytes=0
            for method in ("_load_player_sprites","_load_card_action_sprites","_load_player_eight_frames",
                           "_load_enemy_sprites","_load_common_eight_frames","_load_boss_ultimate_sprites",
                           "_load_boss_eight_frame_sprites","_load_defeat_poses","_load_territory_backgrounds"):
                setattr(owner,method,Mock())
            with patch("web.assets.working_set",return_value={"menu","player","management"}):
                await owner.prepare("map")
                owner.download.assert_not_awaited()
                self.assertIn("player",owner.pruned_groups)
                await owner.prepare("battle")
            owner.download.assert_awaited_once()
            self.assertIn("player",owner.resident)

    async def test_asset_cleanup_rejects_traversal_and_non_asset_paths(self):
        for name in ("../x","/assets/x","saves/a.json","assets/../saves/a","assets\\x","assets/C:/x"):
            with self.assertRaises(OSError):asset_path(name)


class HostingLimitsTests(unittest.TestCase):
    def test_exact_limits_are_accepted(self):
        self.assertFalse(evaluate_files([("a",25*MIB)])["warnings"])
    def test_file_above_25_mib_warns_cloudflare(self):
        self.assertEqual(evaluate_files([("a",25*MIB+1)])["warnings"][0]["code"],"cloudflare_file")
    def test_itch_total_and_single_file_limits(self):
        codes={w["code"] for w in evaluate_files([("a",250_000_001),("b",250_000_001)])["warnings"]}
        self.assertTrue({"itch_total","itch_file"}<=codes)
    def test_count_limits_are_distinct(self):
        self.assertEqual({w["code"] for w in evaluate_files([(str(i),0) for i in range(1001)])["warnings"]},{"itch_count"})
        self.assertIn("cloudflare_count",{w["code"] for w in evaluate_files([(str(i),0) for i in range(20001)])["warnings"]})
    def test_long_path_warns_and_metrics_include_all_files(self):
        report=evaluate_files([("x"*241,12),("b",34)])
        self.assertEqual((report["file_count"],report["total_bytes"]),(2,46))
        self.assertIn("itch_path",{w["code"] for w in report["warnings"]})
