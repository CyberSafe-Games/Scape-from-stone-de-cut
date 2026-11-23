"""Impede que guias vigentes e tabelas voltem a divergir do código."""
import json
from pathlib import Path
import unittest
from devtools.audit_project_docs import ROOT, markdown_files, broken_links, current_contract, test_inventory


class DocumentationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads((ROOT/"docs/contrato_atual.json").read_text(encoding="utf-8"))
        cls.actual = current_contract()
        cls.docs = json.loads((ROOT/"docs/documentacao_manifest.json").read_text(encoding="utf-8"))["documents"]

    def test_every_markdown_is_declared_as_current_or_historical(self):
        found = {p.relative_to(ROOT).as_posix() for p in markdown_files()}
        self.assertEqual({r["file"] for r in self.docs}, found)
        self.assertTrue(all(r["kind"] in ("current", "historical") for r in self.docs))

    def test_local_links_resolve_for_all_markdown_files(self):
        self.assertEqual(broken_links(), [])

    def test_available_lv1_lv2_card_table_matches_real_models(self):
        self.assertEqual(self.contract["cards"], self.actual["cards"])
        self.assertEqual(self.contract["art"], self.actual["art"])
        self.assertEqual(self.contract["unavailable_cards"], self.actual["unavailable_cards"])
        table = (ROOT/"docs/cartas_e_estados.md").read_text(encoding="utf-8")
        for c in self.actual["cards"]:
            a,b = c["levels"]
            row = f"| {c['id']} | {c['name']} | {a['cost']} | {a['description']} | {b['cost']} | {b['description']} |"
            self.assertIn(row, table, c["name"])

    def test_ultimate_documentation_matches_real_cost_charge_and_effects(self):
        self.assertEqual(self.contract["ultimates"], self.actual["ultimates"])
        state = (ROOT/"docs/estado_atual.md").read_text(encoding="utf-8")
        for uid, u in self.actual["ultimates"].items():
            self.assertIn(f"| {uid} | {u['name']} | {u['cost']} | {u['charge']} | {u['description']} |", state)

    def test_shop_deck_upgrades_and_save_version_match_documented_contract(self):
        for section in ("shop", "deck", "upgrade", "runtime"):
            self.assertEqual(self.contract[section], self.actual[section], section)

    def test_native_sheet_membership_is_not_confused_with_jozephino(self):
        self.assertEqual(self.contract["animation"], self.actual["animation"])
        self.assertEqual(self.actual["animation"]["native_sheets"],
                         ["carrasco da vigília", "corpo seco", "guardião da pedra"])
        self.assertNotIn("goblin nerd", self.actual["animation"]["native_sheets"])

    def test_stack_rules_and_campaign_match_documented_contract(self):
        for section in ("statuses", "campaign"):
            self.assertEqual(self.contract[section], self.actual[section], section)

    def test_test_inventory_includes_every_python_test_file_and_case(self):
        inventory = json.loads((ROOT/"docs/inventario_testes.json").read_text(encoding="utf-8"))
        self.assertEqual(inventory, test_inventory())

    def test_old_reports_are_explicitly_marked_and_current_guides_are_linked(self):
        for row in self.docs:
            text = (ROOT/row["file"]).read_text(encoding="utf-8-sig")
            with self.subTest(document=row["file"]):
                if row["file"] == "docs/estado_atual.md":
                    self.assertIn("contrato_atual.json", text)
                elif row["kind"] == "historical":
                    self.assertIn("Registro histórico — não é especificação vigente", text[:850])
                else:
                    self.assertIn("estado_atual.md", text)


if __name__ == "__main__":
    unittest.main()
