"""Faz 14 §4 güvenlik sınırı: float64 yalnız analytics'te, tek yönlü bağımlılık."""
import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYTICS = ROOT / "src" / "dcabot" / "analytics"
LEDGER_DIRS = ("application", "domain", "persistence", "data_adapters", "server", "venue", "ports", "security", "replay", "ui")

FORBIDDEN_EVERYWHERE = {"numpy", "scipy", "pandas", "sklearn"}


def _imports_of(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    tops: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                tops.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                tops.add(node.module.split(".")[0])
    return tops


def _full_imports_of(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    full: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                full.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                full.add(node.module)
    return full


# Köprü izni: yalnız bu iki değerlendirme modülü analytics'i çağırabilir
# (CPCV path skoru, PBO/DSR skoru). Emir/defter/pozisyon/rezerv/fill
# yürütme kodları bu listeye ASLA eklenemez.
ANALYTICS_BRIDGE_ALLOWLIST = {
    "src/dcabot/application/combinatorial_purged_cv.py",
    "src/dcabot/application/overfitting_probability.py",
}


class AnalyticsBoundaryTests(unittest.TestCase):
    def test_analytics_imports_stdlib_only(self):
        self.assertTrue(ANALYTICS.is_dir(), "src/dcabot/analytics paketi yok.")
        stdlib = set(sys.stdlib_module_names)
        for path in sorted(ANALYTICS.rglob("*.py")):
            with self.subTest(file=str(path.relative_to(ROOT))):
                for full in _full_imports_of(path):
                    if full.split(".")[:2] == ["dcabot", "analytics"]:
                        continue  # paket-içi import serbest
                    top = full.split(".")[0]
                    self.assertIn(top, stdlib, f"{path.name}: stdlib dışı import: {top}")
                    self.assertNotIn(top, {"fractions", "decimal"}, f"{path.name}: exact import yasak: {top}")

    def test_no_third_party_statistics_stack(self):
        for path in list(ANALYTICS.rglob("*.py")) if ANALYTICS.is_dir() else []:
            with self.subTest(file=str(path.relative_to(ROOT))):
                self.assertTrue(_imports_of(path).isdisjoint(FORBIDDEN_EVERYWHERE))

    def test_ledger_layers_never_import_analytics(self):
        offenders: list[str] = []
        for dirname in LEDGER_DIRS:
            folder = ROOT / "src" / "dcabot" / dirname
            if not folder.is_dir():
                continue
            for path in sorted(folder.rglob("*.py")):
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                for node in ast.walk(tree):
                    names = (
                        [a.name for a in node.names]
                        if isinstance(node, ast.Import)
                        else [node.module or ""]
                        if isinstance(node, ast.ImportFrom)
                        else []
                    )
                    if any(name.split(".")[:2] == ["dcabot", "analytics"] for name in names):
                        rel = str(path.relative_to(ROOT)).replace("\\", "/")
                        if rel not in ANALYTICS_BRIDGE_ALLOWLIST:
                            offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])
