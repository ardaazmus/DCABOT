"""Offline DCABOT CLI. No credential loader, HTTP client or live-order command."""

import argparse
import json
import sqlite3
import sys
import tempfile
from pathlib import Path
from check_workspace import ROOT, active_python_files


def read_json(path: Path):
    if "YEDEK_ESKI_PROJE" in path.resolve().parts:
        raise ValueError("Legacy runtime inputs are not allowed")
    if path.stat().st_size > 2_000_000:
        raise ValueError("JSON input exceeds 2 MB")

    def pairs(values):
        result = {}
        for k, v in values:
            if k in result:
                raise ValueError(f"Duplicate JSON key: {k}")
            result[k] = v
        return result

    def constant(_):
        raise ValueError("Nonfinite JSON number")

    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=pairs,
        parse_constant=constant,
    )


def database_path(value: Path) -> Path:
    path = value if value.is_absolute() else ROOT / value
    path.resolve().relative_to((ROOT / "data").resolve())
    if any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)):
        raise ValueError("Linked database paths are not allowed")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("notional")
    p.add_argument("--input", type=Path, required=True)
    p = commands.add_parser("preview")
    p.add_argument("--config", type=Path, default=ROOT / "config/paper.json")
    p.add_argument("--anchor", required=True)
    p = commands.add_parser("init")
    p.add_argument("--config", type=Path, default=ROOT / "config/paper.json")
    p.add_argument("--db", type=Path, default=Path("data/paper.db"))
    for name in ("status", "audit", "replay", "event"):
        p = commands.add_parser(name)
        p.add_argument("--db", type=Path, default=Path("data/paper.db"))
        if name in ("replay", "event"):
            p.add_argument("--input", type=Path, required=True)
        if name == "event":
            p.add_argument("--id", required=True)
    p = commands.add_parser("demo")
    p.add_argument("--config", type=Path, default=ROOT / "config/paper.json")
    args = parser.parse_args()
    try:
        if sys.version_info[:2] != (3, 13):
            raise ValueError("Python 3.13 is required")
        active_python_files(ROOT)
        if any("YEDEK_ESKI_PROJE" in Path(p).parts for p in sys.path):
            raise ValueError("Legacy interpreter search path")
        sys.path.insert(0, str(ROOT / "src"))
        from dcabot.application.service import preview, notional, replay
        from dcabot.domain.engine import report
        from dcabot.persistence.store import Store

        if args.command == "notional":
            result = notional(read_json(args.input))
        elif args.command == "preview":
            result = preview(read_json(args.config), args.anchor)
        elif args.command == "demo":
            with tempfile.TemporaryDirectory(prefix="dcabot-offline-") as td:
                with Store(Path(td) / "demo.db", read_json(args.config)) as store:
                    result = replay(
                        store, read_json(ROOT / "tests/fixtures/demo_ticks.json")
                    )
        else:
            path = database_path(args.db)
            if args.command == "init":
                path.parent.mkdir(parents=True, exist_ok=True)
                with Store(path, read_json(args.config)) as store:
                    result = report(store.load(), store.config)
            else:
                with Store(path) as store:
                    if args.command == "replay":
                        result = replay(store, read_json(args.input))
                    elif args.command == "event":
                        applied = store.append(args.id, read_json(args.input))
                        result = report(store.load(), store.config)
                        result["batch_applied"] = applied
                    elif args.command == "audit":
                        result = store.audit()
                    else:
                        result = report(store.load(), store.config)
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except (OSError, ValueError, sqlite3.Error, KeyError, TypeError) as exc:
        print(f"Offline bot error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
