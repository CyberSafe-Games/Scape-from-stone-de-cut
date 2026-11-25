"""Runner deve funcionar no checkout limpo, inclusive quando o módulo falha."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from devtools import validate_isolated_tests as runner


class FreshCheckoutRunnerTests(unittest.TestCase):
    def run_fixture(self, passes):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"tests").mkdir()
            (root/"tests/__init__.py").write_text("",encoding="utf-8")
            (root/"tests/test_example.py").write_text(
                "import unittest\nclass Example(unittest.TestCase):\n"
                f"    def test_example(self): self.assertTrue({passes!r})\n",encoding="utf-8")
            target=root/"build/nested/ci-tests.json"
            self.assertFalse(target.parent.exists())
            with patch.object(runner,"ROOT",root),patch.object(sys,"argv",["runner","--report","build/nested/ci-tests.json"]),patch("sys.stdout",io.StringIO()):
                failed=runner.main()
            self.assertTrue(target.is_file())
            report=json.loads(target.read_text(encoding="utf-8"))
            self.assertTrue(report["concluido"])
            self.assertEqual(report["total_testes"],1)
            self.assertEqual(report["modulos"][0]["modulo"],"tests.test_example")
            return failed,report

    def test_fresh_checkout_creates_nested_report_directory(self):
        failed,report=self.run_fixture(True)
        self.assertFalse(failed)
        self.assertEqual(report["falhas"],0)

    def test_failed_module_still_writes_report_and_returns_failure(self):
        failed,report=self.run_fixture(False)
        self.assertTrue(failed)
        self.assertEqual(report["falhas"],1)
        self.assertIn("AssertionError",report["modulos"][0]["erro"])
