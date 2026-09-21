"""Phase acceptance gate: mechanical anti-hallucination checks for roadmap slices.

Usage: uv run --frozen python tools/phase_gate.py <PHASE_ID>

Verifies that a claimed-done phase actually has its artifacts:
  1. listed test files exist, compile, match unittest discovery, contain tests
  2. OZELLIK_MATRISI rows for the phase's F-codes carry a terminal token
  3. evidence/<faz>/SONUC.md exists, is <= 60 lines, cites real test counts
  4. STATE/TASK/YOL_HARITASI stay within byte limits
  5. no secret-looking literals in the phase's new/changed files

This gate does NOT replace tools/run_checks.py or frontend tsc/vitest.
Those remain mandatory; their observed counts must be written into the
evidence file (check 3 forces the citation, a human re-run verifies it).
"""

import glob
import re
import sys
from pathlib import Path

from check_workspace import ROOT, check_doc_sizes

EVIDENCE_RE = re.compile(r"\d+\s*/\s*\d+\s*PASS", re.IGNORECASE)
TEST_DEF_RE = re.compile(r"^\s*(?:async\s+)?def\s+test_\w+", re.MULTILINE)
TOKEN_BLOCK_END = "/* === TOKEN BLOCK END === */"
COLOR_LIT_RES = [
    re.compile(r"#[0-9a-fA-F]{3,8}\b"),
    re.compile(r"rgba?\([^)]*\)"),
    re.compile(r"(?<![a-zA-Z-])white(?![a-zA-Z-])"),
]
SECRET_RES = [
    re.compile(r"BEGIN [A-Z0-9 ]*PRIVATE KEY"),
    re.compile(r"sk-[A-Za-z0-9]{8,}"),
    re.compile(r"""api[_-]?secret\s*[:=]\s*['"][^'"]+['"]""", re.IGNORECASE),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]
TERMINAL_TOKENS = (
    "COMPLETE_WITH_LIMITATION",
    "IMPLEMENTED_WITH_LIMITATION",
    "LOCAL_PASS",
    "REAL_TESTNET",
    "TESTNET",
    "DEFERRED",
    "NO-GO",
)

# phase_id -> acceptance contract. Extend as phases land; a phase that is
# not listed here cannot be gated (and therefore cannot be claimed done).
PHASES: dict[str, dict[str, object]] = {
    "F11.1": {
        "f_codes": [],
        "tests": ["frontend/src/AppShell.test.tsx"],
        "evidence": "evidence/F11/SONUC.md",
        "css_no_raw_colors": "frontend/src/styles.css",
        "sources": [
            "frontend/src/App.tsx",
            "frontend/src/styles.css",
            "frontend/src/AppShell.test.tsx",
        ],
    },
    "F7": {
        "f_codes": ["F17", "F19"],
        "tests": ["tests/test_rebalance_*.py", "tests/test_signal_*.py"],
        "evidence": "evidence/F7/SONUC.md",
        "sources": ["src/dcabot/application/rebalance_*.py", "src/dcabot/application/signal_*.py"],
    },
    "F27": {
        "f_codes": ["F27"],
        "tests": ["tests/test_paper_*.py"],
        "evidence": "evidence/F9/SONUC.md",
        "sources": ["src/dcabot/application/paper_*.py"],
    },
    "F20": {
        "f_codes": ["F20"],
        "tests": ["tests/test_strategy_template*.py", "tests/test_template_*.py"],
        "evidence": "evidence/F10/SONUC.md",
        "sources": ["src/dcabot/application/strategy_template.py", "src/dcabot/application/template_*.py"],
    },
    "F5": {
        "f_codes": ["F12", "F13", "F14"],
        "tests": ["tests/api/test_futures_*.py", "frontend/src/FuturesPanel.test.tsx"],
        "evidence": "evidence/F5/SONUC.md",
        "sources": [
            "src/dcabot/server/api.py",
            "frontend/src/FuturesPanel.tsx",
            "frontend/src/App.tsx",
        ],
    },
    "F6": {
        "f_codes": ["F18", "F34"],
        "tests": [
            "tests/test_two_leg_journal.py",
            "tests/api/test_two_leg.py",
            "frontend/src/TwoLegPanel.test.tsx",
        ],
        "evidence": "evidence/F6/SONUC.md",
        "sources": [
            "src/dcabot/persistence/two_leg_journal.py",
            "src/dcabot/application/two_leg_fill_projection.py",
            "src/dcabot/server/api.py",
            "frontend/src/TwoLegPanel.tsx",
            "frontend/src/App.tsx",
        ],
    },
    "F8": {
        "f_codes": ["F05", "F32"],
        "tests": [
            "tests/test_bot_registry.py",
            "tests/api/test_bots.py",
            "tests/test_read_only_explanations.py",
            "frontend/src/BotPanel.test.tsx",
        ],
        "evidence": "evidence/F8/SONUC.md",
        "sources": [
            "src/dcabot/application/bot_registry.py",
            "src/dcabot/server/api.py",
            "frontend/src/BotPanel.tsx",
            "frontend/src/App.tsx",
        ],
    },
    "F10": {
        "f_codes": ["F16", "F22", "F28", "F29", "F33", "F35", "F36", "F39", "F40"],
        "tests": [
            "tests/api/test_recurring.py",
            "tests/api/test_run_export.py",
            "tests/api/test_dashboard.py",
            "tests/api/test_draft_level.py",
            "tests/api/test_events.py",
            "tests/test_settlement_profile.py",
            "tests/api/test_backup.py",
            "tests/api/test_risk_explain.py",
            "tests/api/test_deal_timeline.py",
            "frontend/src/RecurringPanel.test.tsx",
            "frontend/src/DashboardPanel.test.tsx",
            "frontend/src/HistoricalChart.test.tsx",
            "frontend/src/EventPanel.test.tsx",
            "frontend/src/RiskPanel.test.tsx",
            "frontend/src/BackupPanel.test.tsx",
            "frontend/src/TimelinePanel.test.tsx",
        ],
        "evidence": "evidence/F10/SONUC.md",
        "sources": [
            "src/dcabot/server/api.py",
            "src/dcabot/application/draft_level.py",
            "src/dcabot/application/settlement_profile.py",
            "frontend/src/RecurringPanel.tsx",
            "frontend/src/DashboardPanel.tsx",
            "frontend/src/HistoricalChart.tsx",
            "frontend/src/EventPanel.tsx",
            "frontend/src/RiskPanel.tsx",
            "frontend/src/BackupPanel.tsx",
            "frontend/src/TimelinePanel.tsx",
            "frontend/src/App.tsx",
        ],
    },
    "F4": {
        "f_codes": [],
        "tests": [
            "tests/test_single_worker.py",
            "tests/test_canary_policy.py",
            "tests/test_live_gate.py",
            "tests/test_run_api_packaging.py",
        ],
        "evidence": "evidence/F4/SONUC.md",
        "sources": [
            "src/dcabot/application/single_worker.py",
            "src/dcabot/application/canary_policy.py",
            "src/dcabot/application/live_gate.py",
            "src/dcabot/server/api.py",
            "tools/run_api.py",
            "config/canary.json",
        ],
    },
    "F11": {
        "f_codes": [],
        "tests": [
            "frontend/src/AppShell.test.tsx",
            "frontend/src/forms.test.tsx",
            "frontend/src/BotWizard.test.tsx",
            "frontend/src/BotTable.test.tsx",
            "frontend/src/notifications.test.tsx",
            "frontend/src/renderWindow.test.tsx",
            "frontend/src/BotPanel.test.tsx",
            "frontend/src/PaperPanel.test.tsx",
            "frontend/src/DatasetCatalogPanel.test.tsx",
        ],
        "evidence": "evidence/F11/SONUC.md",
        "css_no_raw_colors": "frontend/src/styles.css",
        "sources": [
            "frontend/src/App.tsx",
            "frontend/src/forms.tsx",
            "frontend/src/BotWizard.tsx",
            "frontend/src/BotTable.tsx",
            "frontend/src/notifications.tsx",
            "frontend/src/renderWindow.tsx",
            "frontend/src/BotPanel.tsx",
            "frontend/src/PaperPanel.tsx",
            "frontend/src/DatasetCatalogPanel.tsx",
            "frontend/src/styles.css",
        ],
    },
    "F1": {
        "f_codes": [],
        "tests": [
            "tests/test_engine_store.py",
            "tests/api/test_request_limits.py",
            "frontend/src/AppState.test.ts",
        ],
        "evidence": "evidence/F1/SONUC.md",
        "sources": [
            "src/dcabot/domain/engine.py",
            "src/dcabot/server/api.py",
            "src/dcabot/persistence/store.py",
            "frontend/src/App.tsx",
        ],
    },
    "F9": {
        "f_codes": ["F31", "F09", "F30"],
        "tests": [
            "tests/api/test_deals.py",
            "tests/api/test_exits.py",
            "frontend/src/DealPanel.test.tsx",
            "frontend/src/ExitPanel.test.tsx",
            "frontend/src/themeContrast.test.ts",
            "frontend/src/a11yStatic.test.ts",
        ],
        "evidence": "evidence/F9/SONUC.md",
        "sources": [
            "src/dcabot/server/api.py",
            "frontend/src/DealPanel.tsx",
            "frontend/src/ExitPanel.tsx",
            "frontend/src/App.tsx",
        ],
    },
}


def _expand(patterns: list[str]) -> list[Path]:
    out: list[Path] = []
    for pat in patterns:
        out.extend(Path(p) for p in glob.glob(str(ROOT / pat)))
    return sorted(set(out))


def check_tests(patterns: list[str]) -> list[str]:
    errors: list[str] = []
    for pat in patterns:
        files = [Path(p) for p in glob.glob(str(ROOT / pat))]
        if not files:
            errors.append(f"No test file matches: {pat}")
            continue
        for path in files:
            rel = path.relative_to(ROOT)
            try:
                text = path.read_text(encoding="utf-8")
            except OSError as exc:
                errors.append(f"Unreadable test file {rel}: {exc}")
                continue
            if path.suffix == ".py":
                if not (rel.parts[0] == "tests" and path.name.startswith("test_")):
                    errors.append(f"Not collected by unittest discovery: {rel}")
                try:
                    compile(text, str(path), "exec")
                except SyntaxError as exc:
                    errors.append(f"Syntax error in {rel}: {exc}")
                if not TEST_DEF_RE.search(text):
                    errors.append(f"No test_ function in {rel}")
            elif path.suffix in (".ts", ".tsx"):
                if not re.search(r"\b(?:it|test)\s*\(", text):
                    errors.append(f"No it()/test() block in {rel}")
            else:
                errors.append(f"Unsupported test suffix: {rel}")
    return errors


def check_matrix(f_codes: list[str]) -> list[str]:
    errors: list[str] = []
    if not f_codes:
        return errors
    matrix = (ROOT / "docs/OZELLIK_MATRISI.md").read_text(encoding="utf-8")
    for code in f_codes:
        row = next(
            (ln for ln in matrix.splitlines() if ln.startswith(f"| {code} |")),
            "",
        )
        if not row:
            errors.append(f"Matrix row missing: {code}")
        elif not any(tok in row for tok in TERMINAL_TOKENS):
            errors.append(f"Matrix row {code} has no terminal token")
        elif re.search(r"\|\s*PLAN\s*\|?\s*$", row):
            errors.append(f"Matrix row {code} still ends in bare PLAN")
    return errors


def check_evidence(path: str) -> list[str]:
    errors: list[str] = []
    full = ROOT / path
    if not full.is_file():
        return [f"Missing evidence file: {path}"]
    lines = full.read_text(encoding="utf-8").splitlines()
    if not lines:
        errors.append(f"Empty evidence file: {path}")
    if len(lines) > 60:
        errors.append(f"Evidence too long: {path} has {len(lines)} lines (limit 60)")
    if not EVIDENCE_RE.search("\n".join(lines)):
        errors.append(f"Evidence cites no N/M PASS count: {path}")
    return errors


def check_no_raw_colors(css_rel_path: str) -> list[str]:
    """Component CSS must reference tokens only; raw literals live in the block."""
    full = ROOT / css_rel_path
    if not full.is_file():
        return [f"Missing CSS file: {css_rel_path}"]
    text = full.read_text(encoding="utf-8")
    if TOKEN_BLOCK_END not in text:
        return [f"Token block end marker missing: {css_rel_path}"]
    outside = text.split(TOKEN_BLOCK_END, 1)[1]
    errors = []
    for rx in COLOR_LIT_RES:
        found = rx.findall(outside)
        if found:
            errors.append(f"Raw color outside token block ({rx.pattern}): {found[:3]}")
    block = text.split(TOKEN_BLOCK_END, 1)[0]
    defined = set(re.findall(r"(--[a-zA-Z0-9-]+)\s*:", block))
    for ref in sorted(set(re.findall(r"var\((--[a-zA-Z0-9-]+)\)", outside))):
        if ref not in defined:
            errors.append(f"Undefined token referenced: {ref}")
    return errors


def check_secrets(patterns: list[str]) -> list[str]:
    errors: list[str] = []
    for path in _expand(patterns):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for rx in SECRET_RES:
            if rx.search(text):
                errors.append(f"Secret-looking literal in {path.relative_to(ROOT)}: {rx.pattern}")
    return errors


def gate(phase_id: str) -> list[str]:
    contract = PHASES.get(phase_id)
    if contract is None:
        known = ", ".join(sorted(PHASES)) or "(none)"
        return [f"Unknown phase {phase_id!r}. Known: {known}"]
    errors: list[str] = []
    errors.extend(check_tests(contract["tests"]))  # type: ignore[arg-type]
    errors.extend(check_matrix(contract["f_codes"]))  # type: ignore[arg-type]
    errors.extend(check_evidence(contract["evidence"]))  # type: ignore[arg-type]
    if "css_no_raw_colors" in contract:
        errors.extend(check_no_raw_colors(contract["css_no_raw_colors"]))  # type: ignore[arg-type]
    errors.extend(check_secrets(contract["sources"]))  # type: ignore[arg-type]
    errors.extend(check_doc_sizes())
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("Usage: python tools/phase_gate.py <PHASE_ID>", file=sys.stderr)
        return 2
    errors = gate(argv[0])
    if errors:
        print(f"GATE FAIL ({argv[0]}):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print(f"GATE PASS ({argv[0]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
