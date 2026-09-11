"""Hash one explicitly selected legacy source. Never execute or change it."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKUP = ROOT / "YEDEK_ESKI_PROJE"


def inspect(relative: str, backup: Path = BACKUP) -> dict[str, object]:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("Select a relative file within src, tests or docs")
    if path.parts[0] not in {"src", "tests", "docs"} or path.suffix not in {
        ".py",
        ".md",
        ".toml",
    }:
        raise ValueError("Only source/document candidates are supported")
    current = backup
    for part in ("", *path.parts):
        current = current / part
        if current.is_symlink() or current.is_junction():
            raise ValueError("Linked legacy paths are not supported")
    current.resolve().relative_to(backup.resolve())
    if not current.is_file() or current.stat().st_size > 2_000_000:
        raise ValueError("Candidate missing or exceeds 2 MB")
    data = current.read_bytes()
    return {
        "source": f"YEDEK_ESKI_PROJE/{path.as_posix()}",
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "status": "CANDIDATE_ONLY",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", required=True)
    args = parser.parse_args()
    try:
        report = inspect(args.path)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
