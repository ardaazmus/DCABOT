"""Bounded scaffold checks. This is not a filesystem security sandbox."""

import ast
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACTIVE = ("src", "tests", "tools")
REQUIRED = (
    "README.md",
    "AGENTS.md",
    "STATE.md",
    "TASK.md",
    "WORKFLOW.md",
    "pyproject.toml",
    "uv.lock",
    ".gitignore",
    ".ignore",
    "config/offline.json",
    "docs/YEDEKTEN_AKTARIM.md",
    "reuse/REGISTER.md",
)


def active_python_files(root: Path) -> list[Path]:
    pending = [root / name for name in ACTIVE]
    result = []
    while pending:
        path = pending.pop()
        if path.is_symlink() or path.is_junction():
            raise ValueError(
                f"Active path must not be a link: {path.relative_to(root)}"
            )
        if path.is_dir():
            pending.extend(p for p in path.iterdir() if p.name != "__pycache__")
        elif path.suffix == ".py":
            result.append(path)
    return sorted(result)


def check(root: Path = ROOT) -> dict[str, object]:
    errors = [f"Missing: {name}" for name in REQUIRED if not (root / name).is_file()]
    errors.extend(
        f"Missing directory: {name}"
        for name in (*ACTIVE, "YEDEK_ESKI_PROJE")
        if not (root / name).is_dir()
    )
    if sys.version_info[:2] != (3, 13):
        errors.append("Python 3.13 is required")
    files = []
    try:
        files = active_python_files(root)
        for path in files:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                names = (
                    [a.name for a in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module or ""]
                    if isinstance(node, ast.ImportFrom)
                    else []
                )
                if any("YEDEK_ESKI_PROJE" in name.split(".") for name in names):
                    errors.append(f"Legacy import: {path.relative_to(root)}")
        config = json.loads((root / "config/offline.json").read_text(encoding="utf-8"))
        if config != {"mode": "offline"}:
            errors.append("Initial config must be offline only")
        project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        if project["project"]["requires-python"] != ">=3.13,<3.14":
            errors.append("Python version contract changed")
        if "/YEDEK_ESKI_PROJE/" not in (root / ".gitignore").read_text().splitlines():
            errors.append("Backup must be ignored by Git")
    except (OSError, ValueError, SyntaxError, KeyError, AttributeError) as exc:
        errors.append(str(exc))
    backup = root / "YEDEK_ESKI_PROJE"
    if backup.is_symlink() or backup.is_junction():
        errors.append("Backup must be an actual directory, not a link")
    layout = (
        "PRESENT_NOT_CONTENT_VERIFIED"
        if (backup / "src").is_dir() and (backup / "docs").is_dir()
        else "EMPTY_OR_NOT_PLACED"
    )
    return {
        "status": "FAIL" if errors else "PASS",
        "errors": errors,
        "active_python_files": len(files),
        "backup_layout": layout,
        "scope": "SCAFFOLD_WORKSPACE_ONLY",
    }


if __name__ == "__main__":
    report = check()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(bool(report["errors"]))
