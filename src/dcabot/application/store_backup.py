"""Consistent SQLite backup with hash manifest and verify-only restore (F36).

Backups are taken through the SQLite backup API so a live database (WAL
included) copies consistently. Restore is deliberately verify-only: the
operator copies a VERIFIED file while the server is stopped. No automatic
overwrite exists.
"""
import hashlib
import json
import re
import sqlite3
from pathlib import Path


_STORE = re.compile(r"[A-Za-z0-9_.-]{1,64}\Z", re.ASCII)
_CHUNK = 64 * 1024


class StoreBackupError(ValueError):
    """Raised when a backup cannot be taken or verified safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def backup_sqlite_file(
    source: Path, dest_dir: Path, *, store: str, now_us: int
) -> dict[str, object]:
    """Copy one live database consistently and write its hash manifest."""
    if not isinstance(source, Path) or not isinstance(dest_dir, Path):
        raise StoreBackupError("BACKUP_PATH_INVALID", "Backup yolu geçersiz.")
    if type(store) is not str or _STORE.fullmatch(store) is None:
        raise StoreBackupError("BACKUP_STORE_INVALID", "Store adı geçersiz.")
    if type(now_us) is not int or now_us < 0:
        raise StoreBackupError("BACKUP_TIME_INVALID", "Backup zamanı geçersiz.")
    if not source.is_file():
        raise StoreBackupError("BACKUP_SOURCE_MISSING", "Kaynak veritabanı yok.")
    _require_sqlite(source)
    dest_dir.mkdir(parents=True, exist_ok=True)
    backup_name = f"{store}-{now_us}.sqlite3"
    manifest_name = f"{store}-{now_us}.manifest.json"
    backup_path = dest_dir / backup_name
    manifest_path = dest_dir / manifest_name
    if backup_path.exists() or manifest_path.exists():
        raise StoreBackupError("BACKUP_ALREADY_EXISTS", "Bu zaman damgası kullanılmış.")
    try:
        source_db = sqlite3.connect(f"file:{source}?mode=ro", uri=True, timeout=5)
    except sqlite3.Error as exc:
        raise StoreBackupError("BACKUP_SOURCE_INVALID", "Kaynak açılamadı.") from exc
    try:
        dest_db = sqlite3.connect(backup_path, timeout=30)
        try:
            source_db.backup(dest_db)
        finally:
            dest_db.close()
    except sqlite3.Error as exc:
        backup_path.unlink(missing_ok=True)
        raise StoreBackupError("BACKUP_FAILED", "Backup kopyası alınamadı.") from exc
    finally:
        source_db.close()
    digest = _sha256_file(backup_path)
    manifest: dict[str, object] = {
        "store": store,
        "backup_file": backup_name,
        "manifest_file": manifest_name,
        "bytes": backup_path.stat().st_size,
        "sha256": digest,
        "created_us": now_us,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=True, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    return manifest


def verify_backup(backup_path: Path, manifest: dict[str, object]) -> dict[str, object]:
    """Verify one backup file against its manifest without restoring it."""
    if not isinstance(backup_path, Path) or not isinstance(manifest, dict):
        raise StoreBackupError("BACKUP_VERIFY_INVALID", "Doğrulama girdisi geçersiz.")
    if backup_path.name != manifest.get("backup_file"):
        raise StoreBackupError(
            "BACKUP_MANIFEST_MISMATCH", "Manifest bu backup dosyasına ait değil."
        )
    if not backup_path.is_file():
        raise StoreBackupError("BACKUP_SOURCE_MISSING", "Backup dosyası yok.")
    digest = _sha256_file(backup_path)
    if digest != manifest.get("sha256"):
        return {"verdict": "CORRUPT", "reason": "SHA256 eşleşmiyor."}
    try:
        db = sqlite3.connect(f"file:{backup_path}?mode=ro", uri=True, timeout=5)
    except sqlite3.Error:
        return {"verdict": "CORRUPT", "reason": "Backup açılamıyor."}
    try:
        app_id = db.execute("PRAGMA application_id").fetchone()[0]
        user_version = db.execute("PRAGMA user_version").fetchone()[0]
        integrity = db.execute("PRAGMA quick_check").fetchone()[0]
    except sqlite3.Error:
        return {"verdict": "CORRUPT", "reason": "Backup okunamıyor."}
    finally:
        db.close()
    if integrity != "ok":
        return {"verdict": "CORRUPT", "reason": f"Integrity: {integrity}."}
    return {
        "verdict": "VERIFIED",
        "application_id": app_id,
        "user_version": user_version,
    }


def list_backup_manifests(dest_dir: Path) -> list[dict[str, object]]:
    """List stored manifests oldest-first; skips unreadable files."""
    if not isinstance(dest_dir, Path) or not dest_dir.is_dir():
        return []
    manifests: list[dict[str, object]] = []
    for path in sorted(dest_dir.glob("*.manifest.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if (
            isinstance(raw, dict)
            and raw.get("manifest_file") == path.name
            and isinstance(raw.get("created_us"), int)
        ):
            manifests.append(raw)
    manifests.sort(key=lambda item: (item["created_us"], item["manifest_file"]))
    return manifests


def _require_sqlite(source: Path) -> None:
    try:
        db = sqlite3.connect(f"file:{source}?mode=ro", uri=True, timeout=5)
    except sqlite3.Error as exc:
        raise StoreBackupError("BACKUP_SOURCE_INVALID", "Kaynak açılamadı.") from exc
    try:
        db.execute("SELECT name FROM sqlite_master LIMIT 1").fetchall()
    except sqlite3.Error as exc:
        raise StoreBackupError(
            "BACKUP_SOURCE_INVALID", "Kaynak SQLite veritabanı değil."
        ) from exc
    finally:
        db.close()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()
