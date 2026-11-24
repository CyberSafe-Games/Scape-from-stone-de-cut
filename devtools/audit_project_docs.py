"""Auditoria de Markdown, links locais e inventário unittest, sem alterar regras."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def markdown_files(root=ROOT):
    try:
        paths = subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", "*.md"],
            cwd=root).decode("utf-8").split("\0")
        return sorted({root/p for p in paths if p and (root/p).is_file()})
    except (subprocess.CalledProcessError, FileNotFoundError):
        return sorted([*root.glob("*.md"), *(root/"docs").rglob("*.md"),
                       *(root/"assets/audio").glob("*.md")])


def local_links(path):
    text = path.read_text(encoding="utf-8-sig")
    text = re.sub(r"\x60{3}.*?\x60{3}", "", text, flags=re.S)
    for match in re.finditer(r"!?\[([^\]]*)\]\(([^)\n]+)\)", text):
        target = match[2].strip()
        if target.startswith("<"):
            target = target[1:target.index(">")]
        else:
            target = re.split(r'\s+"', target, maxsplit=1)[0]
        url = urlsplit(target)
        if url.scheme or target.startswith(("#", "//")):
            continue
        name = unquote(url.path)
        if name:
            yield match[0], path.parent/name


def broken_links(root=ROOT):
    return [{"document": p.relative_to(root).as_posix(), "link": token}
            for p in markdown_files(root) for token, target in local_links(p)
            if not target.exists()]


def test_inventory(root=ROOT):
    files = []
    for path in sorted((root/"tests").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        cases = [f"{cls.name}.{node.name}" for cls in ast.walk(tree) if isinstance(cls, ast.ClassDef)
                 for node in cls.body if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")]
        files.append(dict(file=path.relative_to(root).as_posix(), cases=cases))
    return dict(files=files, modules=sum(bool(f["cases"]) for f in files),
                methods=sum(len(f["cases"]) for f in files))


def current_contract():
    from src.systems.card_catalog import AVAILABLE_CARD_POOL, UNAVAILABLE_CARD_NAMES
    from src.systems.card_definitions import CARD_SPECS
    from src.systems.roguelite import instance_card, MATERIAL_PRICE, MATERIAL_LIMIT, UPGRADE_LIMIT, UPGRADE_PRICES
    from src.systems.deck_loadout import DECK_MIN_CARDS, DECK_SLOT_LIMIT, COPIES_PER_CARD
    from src.systems.save_manager import SAVE_VERSION
    from src.config.shop_balance import HEAL_AMOUNT, HEAL_PRICES, HEAL_LIMIT
    from src.config.settings import WIDTH, HEIGHT, FPS
    from src.models.effects.ultimate_effect import ULTIMATE_METADATA
    from src.systems.territory_map import ROAD_FIGHTS, TERRITORIES
    from src.config.boss_names import boss_display_name
    from src.systems.enemy_factory import create_point_enemy
    from src.systems.boss_sheet_kits import SHEET_KITS, SHEET_GRID, SHEET_CELL_SIZE
    from src.ui.enemy_reactions import JOZEPHINO_IDLE_MS
    from src.systems.jan_pietro_animation import IDLE_FRAME_MS
    from src.models.entity import STACK_STATUS_DAMAGE, STACK_STATUS_LIMIT, STACK_STATUS_TURNS, BLEED_TRIGGER_LIMIT
    regular_art = json.loads((ROOT/'assets/cards/art_manifest.json').read_text(encoding='utf-8'))['cards']
    ultimate_art = json.loads((ROOT/'assets/ultimates/art_manifest.json').read_text(encoding='utf-8'))['cards']
    art = dict(regular_count=len(regular_art),
               regular_geometry_by_card=len({tuple(v['size']) for v in regular_art.values()}) > 1,
               ultimate_template=ultimate_art['mana_ancestral']['size'])
    ids = {s[1]: s[0] for s in CARD_SPECS}
    cards = []
    for card in AVAILABLE_CARD_POOL:
        levels = [instance_card(dict(id="documentation", name=card.name, level=level)) for level in (1, 2)]
        cards.append(dict(id=ids[card.name], name=card.name,
                          levels=[dict(level=c.level, cost=c.cost, description=c.description) for c in levels]))
    return dict(art=art, statuses=dict(damage=STACK_STATUS_DAMAGE, maximum=STACK_STATUS_LIMIT, turns=STACK_STATUS_TURNS, bleed_trigger_limit=BLEED_TRIGGER_LIMIT),
                cards=cards, unavailable_cards=sorted(UNAVAILABLE_CARD_NAMES),
                ultimates={uid:dict(name=m["name"], cost=m["energy_cost"], charge=m["charge_requirement"],
                                    description=m["description"]) for uid,m in ULTIMATE_METADATA.items()},
                runtime=dict(virtual=[WIDTH,HEIGHT], fps=FPS, save_version=SAVE_VERSION),
                shop=dict(heal_amount=HEAL_AMOUNT, heal_prices=list(HEAL_PRICES), heal_limit=HEAL_LIMIT),
                deck=dict(minimum=DECK_MIN_CARDS, maximum=DECK_SLOT_LIMIT, copies_per_type=COPIES_PER_CARD),
                upgrade=dict(material_price=MATERIAL_PRICE, material_limit=MATERIAL_LIMIT,
                             limit=UPGRADE_LIMIT, prices=UPGRADE_PRICES),
                campaign=dict(road_fights=ROAD_FIGHTS,
                              bosses=[dict(level=t.level, territory=t.title, internal=create_point_enemy(t.level).name,
                                           display=boss_display_name(create_point_enemy(t.level).name)) for t in TERRITORIES]),
                animation=dict(native_sheets=sorted(SHEET_KITS), grid=list(SHEET_GRID),
                               cell=list(SHEET_CELL_SIZE), jan_idle_ms=IDLE_FRAME_MS, jozephino_idle_ms=JOZEPHINO_IDLE_MS))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = []
    for p in markdown_files():
        raw = p.read_bytes()
        records.append(dict(file=p.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(raw).hexdigest()))
    result = dict(markdown=records, broken_links=broken_links(), tests=test_inventory())
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"{len(records)} documentos; {result['tests']['modules']} módulos; "
          f"{result['tests']['methods']} testes; {len(result['broken_links'])} links locais quebrados.")
    return bool(result["broken_links"])


if __name__ == "__main__":
    raise SystemExit(main())
