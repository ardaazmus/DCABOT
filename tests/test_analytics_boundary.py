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
    # Faz 17 F.1: BB-Width needs stdev (sqrt) -> analytics/regime_scores.py;
    # this module is the only bridge, converting at the float boundary only.
    "src/dcabot/application/regime_detection.py",
    # Faz 17 F.2: log-return covariance/variance/implied-correlation (sqrt)
    # -> analytics/correlation_scores.py; the breach DECISION itself stays
    # integer-only (see correlation_risk.py's module docstring).
    "src/dcabot/application/correlation_risk.py",
    # Faz 17 G.4: Bollinger upper/lower/%B need stdev (sqrt) ->
    # analytics/bollinger_scores.py; middle band/variance stay exact
    # Fraction in this module, only the stdev crosses the float boundary.
    "src/dcabot/application/bollinger_bands.py",
    # Faz 17 AA.7a-2: per-bar Sharpe ratio over an exact equity curve needs
    # stdev (sqrt) -> analytics/scores.py's sharpe_ratio; bar-over-bar
    # returns stay exact Fraction in this module, only the final Sharpe
    # statistic crosses the float boundary.
    "src/dcabot/application/equity_curve_scores.py",
    # Q2: read-only risk matrix; display coefficients via the tested
    # correlation_scores advisors, breach verdicts via the exact
    # integer comparison. No execution path (no orders/reservations).
    "src/dcabot/application/correlation_matrix.py",
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
