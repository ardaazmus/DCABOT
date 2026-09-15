"""Verify or generate the tracked-file SHA-256 release manifest."""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_NAME = "SHA256SUMS.txt"
_ENTRY = re.compile(r"([0-9a-f]{64})  ([^\r\n]+)\Z", re.IGNORECASE)
_CHUNK_BYTES = 64 * 1024


def _tracked_files(root: Path) -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    paths = tuple(
        item.decode("utf-8") for item in result.stdout.split(b"\0") if item
    )
    if any(PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts for path in paths):
        raise ValueError("Git takip listesinde güvenli olmayan dosya yolu var.")
    return tuple(sorted(paths))


def _sha256_stream(stream) -> str:
    digest = hashlib.sha256()
    while chunk := stream.read(_CHUNK_BYTES):
        digest.update(chunk)
    return digest.hexdigest()


def _index_sha256(root: Path, name: str) -> str:
    process = subprocess.Popen(
        ["git", "-C", str(root), "show", f":{name}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdout is not None
    checksum = _sha256_stream(process.stdout)
    stderr = process.stderr.read() if process.stderr is not None else b""
    return_code = process.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, process.args, stderr=stderr)
    return checksum


def _parse_manifest(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        match = _ENTRY.fullmatch(line)
        if match is None:
            raise ValueError("SHA manifest satırı geçersiz.")
        checksum, name = match.groups()
        if name == MANIFEST_NAME or name in entries:
            raise ValueError("SHA manifest duplicate veya kendine referans içeriyor.")
        posix_name = PurePosixPath(name)
        if posix_name.is_absolute() or ".." in posix_name.parts or "\\" in name:
            raise ValueError("SHA manifest yolu güvenli değil.")
        entries[name] = checksum.lower()
    return entries


def check(root: Path = ROOT) -> dict[str, object]:
    errors: list[str] = []
    try:
        tracked = _tracked_files(root)
        entries = _parse_manifest(root / MANIFEST_NAME)
        expected = set(tracked) - {MANIFEST_NAME}
        actual = set(entries)
        errors.extend(f"Manifest missing tracked file: {name}" for name in sorted(expected - actual))
        errors.extend(f"Manifest contains untracked file: {name}" for name in sorted(actual - expected))
        for name in sorted(expected & actual):
            file_path = root / Path(*PurePosixPath(name).parts)
            if not file_path.is_file():
                errors.append(f"Tracked file is missing from checkout: {name}")
            elif _index_sha256(root, name) != entries[name]:
                errors.append(f"SHA-256 mismatch: {name}")
    except (OSError, UnicodeError, ValueError, subprocess.SubprocessError) as exc:
        errors.append(str(exc))
        tracked = ()
        entries = {}
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "tracked_files": len(tracked),
        "manifest_entries": len(entries),
        "manifest": MANIFEST_NAME,
    }


def generate(root: Path = ROOT) -> dict[str, object]:
    tracked = tuple(name for name in _tracked_files(root) if name != MANIFEST_NAME)
    content = "\n".join(
        f"{_index_sha256(root, name)}  {name}"
        for name in tracked
    ) + "\n"
    (root / MANIFEST_NAME).write_text(content, encoding="ascii")
    return {"status": "GENERATED", "manifest": MANIFEST_NAME, "entries": len(tracked)}


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) == 2 else "check"
    try:
        result = generate() if command == "generate" else check()
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        result = {"status": "FAIL", "errors": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] in ("PASS", "GENERATED") else 1)
