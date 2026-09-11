"""Dedicated local SQLite store for immutable historical run snapshots."""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from uuid import UUID, uuid4

from dcabot.application.evaluation_run_binding import EvaluationRunBinding
from dcabot.application.historical_run_contract import HistoricalRunCapture, canonical_json


RUN_STORE_APPLICATION_ID = 0x44435255
RUN_STORE_SCHEMA_VERSION = 1
MAX_RUN_RECORD_BYTES = 4 * 1024 * 1024
DEFAULT_RUN_LIST_LIMIT = 50
MAX_RUN_LIST_LIMIT = 100
_SOURCE_EXECUTION_ID = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)


class HistoricalRunStoreError(ValueError):
    """Raised when a local historical run store operation fails safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class HistoricalRunListItem:
    """Bounded metadata returned by the reopen list."""

    run_id: str
    created_at: str
    execution_status: str
    record_health: str
    symbol: str
    interval: str
    period_start: str
    period_end: str
    processed_bar_count: int
    position_status: str


@dataclass(frozen=True, slots=True)
class HistoricalRunDetail:
    """Validated immutable run record returned by the detail read."""

    run_id: str
    created_at: str
    storage_state: str
    execution_status: str
    dataset: dict[str, object]
    input_snapshot: dict[str, object]
    config: dict[str, object]
    instrument_risk: dict[str, object]
    execution: dict[str, object]
    result_snapshot: dict[str, object]
    result_sha256: str
    record_sha256: str
    evaluation_lineage: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class HistoricalRunSave:
    """Result of an immutable save, including retry identity."""

    run_id: str
    created: bool
    list_item: HistoricalRunListItem
    capture: HistoricalRunCapture


class HistoricalRunStore:
    """Own a separate versioned SQLite database for historical run evidence."""

    def __init__(self, path: Path):
        self.path = _validate_store_path(path)
        existed = self.path.exists()
        try:
            self.db = sqlite3.connect(
                self.path.resolve().as_uri() + "?mode=rwc",
                uri=True,
                isolation_level=None,
                timeout=2,
            )
            self.db.execute("PRAGMA foreign_keys=ON")
            self.db.execute("PRAGMA journal_mode=DELETE")
            self.db.execute("PRAGMA synchronous=FULL")
            if existed:
                self._validate_existing_store()
            else:
                self._initialize_store()
        except HistoricalRunStoreError:
            self._close_after_open_failure()
            raise
        except (OSError, sqlite3.Error) as exc:
            self._close_after_open_failure()
            raise HistoricalRunStoreError("RUN_STORE_UNAVAILABLE", "Historical run store açılamadı.") from exc

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "HistoricalRunStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def save(
        self,
        capture: HistoricalRunCapture,
        *,
        source_execution_id: str,
        created_at: str,
    ) -> HistoricalRunSave:
        """Insert one immutable capture or return the same source retry."""

        _validate_source_execution_id(source_execution_id)
        _validate_created_at(created_at)
        record_json, record = _build_record(capture, created_at=created_at, run_id=str(uuid4()))
        if len(record_json.encode("utf-8")) > MAX_RUN_RECORD_BYTES:
            raise HistoricalRunStoreError("RUN_RECORD_TOO_LARGE", "Historical run kaydı byte sınırını aşıyor.")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            prior = self.db.execute(
                "SELECT run_id, created_at, record_json, record_sha256, execution_status, dataset_id, symbol, interval, period_start, period_end, processed_bar_count, position_status FROM historical_runs WHERE source_execution_id=?",
                (source_execution_id,),
            ).fetchone()
            if prior is not None:
                prior_record = _decode_record(prior[2], prior[3], expected_run_id=prior[0])
                if (
                    prior_record["result_sha256"] != record["result_sha256"]
                    or prior_record["execution"]["execution_identity_sha256"]
                    != record["execution"]["execution_identity_sha256"]
                    or prior_record.get("evaluation_lineage") != record.get("evaluation_lineage")
                ):
                    raise HistoricalRunStoreError("SOURCE_EXECUTION_CONFLICT", "Aynı execution kimliği farklı payload ile kullanılamaz.")
                self.db.execute("COMMIT")
                return HistoricalRunSave(
                    run_id=prior[0],
                    created=False,
                    list_item=_list_item_from_row(prior, "OK"),
                    capture=capture,
                )
            self.db.execute(
                "INSERT INTO historical_runs (run_id, source_execution_id, created_at, execution_status, dataset_id, symbol, interval, period_start, period_end, processed_bar_count, position_status, record_json, record_sha256) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record["run_id"],
                    source_execution_id,
                    record["created_at"],
                    record["execution_status"],
                    record["dataset"]["dataset_id"],
                    record["dataset"]["symbol"],
                    record["dataset"]["interval"],
                    record["dataset"]["period_start"],
                    record["dataset"]["period_end"],
                    record["dataset"]["processed_bar_count"],
                    record["result_snapshot"]["summary"]["position_status"],
                    record_json,
                    record["record_sha256"],
                ),
            )
            self.db.execute("COMMIT")
            return HistoricalRunSave(
                run_id=record["run_id"],
                created=True,
                list_item=_list_item_from_record(record, "OK"),
                capture=capture,
            )
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def list_runs(self, limit: int = DEFAULT_RUN_LIST_LIMIT) -> tuple[HistoricalRunListItem, ...]:
        if type(limit) is not int or not 1 <= limit <= MAX_RUN_LIST_LIMIT:
            raise HistoricalRunStoreError("RUN_LIST_LIMIT_INVALID", "Historical run liste sınırı geçersiz.")
        rows = self.db.execute(
            "SELECT run_id, created_at, record_json, record_sha256, execution_status, dataset_id, symbol, interval, period_start, period_end, processed_bar_count, position_status FROM historical_runs ORDER BY created_at DESC, run_id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        items: list[HistoricalRunListItem] = []
        for row in rows:
            try:
                record = _decode_record(row[2], row[3], expected_run_id=row[0])
                if not _record_matches_row(record, row):
                    raise HistoricalRunStoreError("RUN_CORRUPT", "Historical run liste metadata’sı kayıtla eşleşmiyor.")
            except HistoricalRunStoreError:
                items.append(_list_item_from_row(row, "CORRUPT"))
            else:
                items.append(_list_item_from_row(row, "OK"))
        return tuple(items)

    def get(self, run_id: str) -> HistoricalRunDetail:
        _validate_uuid(run_id)
        row = self.db.execute(
            "SELECT run_id, created_at, record_json, record_sha256, execution_status, dataset_id, symbol, interval, period_start, period_end, processed_bar_count, position_status FROM historical_runs WHERE run_id=?",
            (run_id,),
        ).fetchone()
        if row is None:
            raise HistoricalRunStoreError("RUN_NOT_FOUND", "Historical run bulunamadı.")
        record = _decode_record(row[2], row[3], expected_run_id=run_id)
        if not _record_matches_row(record, row):
            raise HistoricalRunStoreError("RUN_CORRUPT", "Historical run liste metadata’sı kayıtla eşleşmiyor.")
        return HistoricalRunDetail(
            run_id=record["run_id"],
            created_at=record["created_at"],
            storage_state=record["storage_state"],
            execution_status=record["execution_status"],
            dataset=record["dataset"],
            input_snapshot=record["input_snapshot"],
            config=record["config"],
            instrument_risk=record["instrument_risk"],
            execution=record["execution"],
            result_snapshot=record["result_snapshot"],
            result_sha256=record["result_sha256"],
            record_sha256=record["record_sha256"],
            evaluation_lineage=record.get("evaluation_lineage"),
        )

    def _initialize_store(self) -> None:
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute(f"PRAGMA application_id={RUN_STORE_APPLICATION_ID}")
            self.db.execute(f"PRAGMA user_version={RUN_STORE_SCHEMA_VERSION}")
            self.db.execute("CREATE TABLE run_store_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            self.db.execute(
                "CREATE TABLE historical_runs (run_id TEXT PRIMARY KEY, source_execution_id TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL, execution_status TEXT NOT NULL, dataset_id TEXT NOT NULL, symbol TEXT NOT NULL, interval TEXT NOT NULL, period_start TEXT NOT NULL, period_end TEXT NOT NULL, processed_bar_count INTEGER NOT NULL, position_status TEXT NOT NULL, record_json TEXT NOT NULL, record_sha256 TEXT NOT NULL)"
            )
            self.db.execute(
                "INSERT INTO run_store_meta(key, value) VALUES ('store_kind', 'historical-run-snapshot-v1')"
            )
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _validate_existing_store(self) -> None:
        application_id = self.db.execute("PRAGMA application_id").fetchone()[0]
        schema_version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if application_id != RUN_STORE_APPLICATION_ID or schema_version != RUN_STORE_SCHEMA_VERSION:
            raise HistoricalRunStoreError("RUN_STORE_UNSUPPORTED", "Dosya desteklenen historical run store değil.")
        try:
            kind = self.db.execute("SELECT value FROM run_store_meta WHERE key='store_kind'").fetchone()
            self.db.execute("SELECT 1 FROM historical_runs LIMIT 1")
        except sqlite3.Error as exc:
            raise HistoricalRunStoreError("RUN_STORE_UNSUPPORTED", "Historical run store şeması desteklenmiyor.") from exc
        if kind != ("historical-run-snapshot-v1",):
            raise HistoricalRunStoreError("RUN_STORE_UNSUPPORTED", "Historical run store sahipliği doğrulanamadı.")

    def _close_after_open_failure(self) -> None:
        if hasattr(self, "db"):
            self.db.close()


def _build_record(capture: HistoricalRunCapture, *, created_at: str, run_id: str) -> tuple[str, dict[str, object]]:
    try:
        input_snapshot = json.loads(capture.input_snapshot_json)
        config_snapshot = json.loads(capture.config_json)
        instrument_risk_snapshot = json.loads(capture.instrument_risk_json)
        execution = json.loads(capture.execution_identity_json)
        result_snapshot = json.loads(capture.result_json)
    except json.JSONDecodeError as exc:
        raise HistoricalRunStoreError("RUN_CAPTURE_INVALID", "Historical run capture JSON geçersiz.") from exc
    if not all(isinstance(value, dict) for value in (input_snapshot, config_snapshot, instrument_risk_snapshot, execution, result_snapshot)):
        raise HistoricalRunStoreError("RUN_CAPTURE_INVALID", "Historical run capture nesne sözleşmesi geçersiz.")
    evaluation_lineage = _evaluation_lineage_from_capture(capture)
    record: dict[str, object] = {
        "schema_version": RUN_STORE_SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": created_at,
        "storage_state": "STORED",
        "execution_status": result_snapshot["execution_status"],
        "reproduces_run_id": None,
        "dataset": {
            "dataset_id": input_snapshot["dataset_id"],
            "artifact_sha256": execution["artifact_sha256"],
            "canonical_input_sha256": capture.canonical_input_sha256,
            "period_start": input_snapshot["period_start"],
            "period_end": input_snapshot["period_end"],
            "processed_bar_count": result_snapshot["processed_bar_count"],
            "symbol": input_snapshot["symbol"],
            "interval": input_snapshot["interval"],
            "monetary_unit": input_snapshot["monetary_unit"],
        },
        "input_snapshot": input_snapshot,
        "config": {
            "schema_version": config_snapshot["schema_version"],
            "config_hash": capture.config_hash,
            "snapshot": config_snapshot,
        },
        "instrument_risk": {
            "schema_version": 1,
            "snapshot": instrument_risk_snapshot,
            "snapshot_sha256": capture.instrument_risk_snapshot_sha256,
        },
        "execution": {
            **execution,
            "execution_identity_sha256": capture.execution.identity_sha256,
        },
        "result_snapshot": result_snapshot,
        "result_sha256": capture.result_sha256,
        "evaluation_lineage": evaluation_lineage,
    }
    record_body_json = canonical_json(record)
    record["record_sha256"] = _sha256(record_body_json)
    return canonical_json(record), record


def _decode_record(record_json: str, record_sha256: str, *, expected_run_id: str) -> dict[str, object]:
    if len(record_json.encode("utf-8")) > MAX_RUN_RECORD_BYTES:
        raise HistoricalRunStoreError("RUN_CORRUPT", "Historical run kaydı byte sınırını aşıyor.")
    try:
        record = json.loads(record_json)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise HistoricalRunStoreError("RUN_CORRUPT", "Historical run kaydı okunamıyor.") from exc
    if not isinstance(record, dict) or record.get("record_sha256") != record_sha256 or record.get("run_id") != expected_run_id:
        raise HistoricalRunStoreError("RUN_CORRUPT", "Historical run kayıt bütünlüğü doğrulanamadı.")
    stored_hash = record.pop("record_sha256", None)
    if not isinstance(stored_hash, str) or _sha256(canonical_json(record)) != stored_hash:
        raise HistoricalRunStoreError("RUN_CORRUPT", "Historical run checksum doğrulanamadı.")
    record["record_sha256"] = stored_hash
    if record.get("schema_version") != RUN_STORE_SCHEMA_VERSION or record.get("storage_state") != "STORED":
        raise HistoricalRunStoreError("RUN_CORRUPT", "Historical run schema desteklenmiyor.")
    record.setdefault("evaluation_lineage", None)
    return record


def _evaluation_lineage_from_capture(capture: HistoricalRunCapture) -> dict[str, object] | None:
    if (capture.evaluation_binding_json is None) != (capture.evaluation_binding_sha256 is None):
        raise HistoricalRunStoreError(
            "RUN_CAPTURE_INVALID", "Evaluation lineage binding alanları birlikte bulunmalıdır."
        )
    if capture.evaluation_binding_json is None:
        if capture.evaluation_binding is not None:
            raise HistoricalRunStoreError(
                "RUN_CAPTURE_INVALID", "Evaluation lineage binding JSON alanı eksik."
            )
        return None
    try:
        lineage = json.loads(capture.evaluation_binding_json)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise HistoricalRunStoreError(
            "RUN_CAPTURE_INVALID", "Evaluation lineage binding JSON geçersiz."
        ) from exc
    if not isinstance(lineage, dict):
        raise HistoricalRunStoreError(
            "RUN_CAPTURE_INVALID", "Evaluation lineage binding nesne sözleşmesi geçersiz."
        )
    try:
        canonical_lineage = canonical_json(lineage)
    except (TypeError, ValueError) as exc:
        raise HistoricalRunStoreError(
            "RUN_CAPTURE_INVALID", "Evaluation lineage binding canonical değil."
        ) from exc
    if canonical_lineage != capture.evaluation_binding_json:
        raise HistoricalRunStoreError(
            "RUN_CAPTURE_INVALID", "Evaluation lineage binding canonical değil."
        )
    binding_hash = lineage.get("binding_sha256")
    if not isinstance(binding_hash, str) or capture.evaluation_binding_sha256 != binding_hash:
        raise HistoricalRunStoreError(
            "RUN_CAPTURE_INVALID", "Evaluation lineage binding checksum eşleşmiyor."
        )
    try:
        EvaluationRunBinding(**lineage)
        expected_hash = _sha256(
            canonical_json({key: value for key, value in lineage.items() if key != "binding_sha256"})
        )
    except (TypeError, ValueError) as exc:
        raise HistoricalRunStoreError(
            "RUN_CAPTURE_INVALID", "Evaluation lineage binding şeması geçersiz."
        ) from exc
    if expected_hash != binding_hash:
        raise HistoricalRunStoreError(
            "RUN_CAPTURE_INVALID", "Evaluation lineage binding canonical checksum geçersiz."
        )
    return lineage


def _list_item_from_record(record: dict[str, object], health: str) -> HistoricalRunListItem:
    dataset = record["dataset"]
    summary = record["result_snapshot"]["summary"]
    return HistoricalRunListItem(
        run_id=record["run_id"],
        created_at=record["created_at"],
        execution_status=record["execution_status"],
        record_health=health,
        symbol=dataset["symbol"],
        interval=dataset["interval"],
        period_start=dataset["period_start"],
        period_end=dataset["period_end"],
        processed_bar_count=dataset["processed_bar_count"],
        position_status=summary["position_status"],
    )


def _list_item_from_row(row: tuple[object, ...], health: str) -> HistoricalRunListItem:
    return HistoricalRunListItem(
        run_id=row[0],
        created_at=row[1],
        execution_status=row[4],
        record_health=health,
        symbol=row[6],
        interval=row[7],
        period_start=row[8],
        period_end=row[9],
        processed_bar_count=row[10],
        position_status=row[11],
    )


def _record_matches_row(record: dict[str, object], row: tuple[object, ...]) -> bool:
    try:
        dataset = record["dataset"]
        result_snapshot = record["result_snapshot"]
        if not isinstance(dataset, dict) or not isinstance(result_snapshot, dict):
            return False
        summary = result_snapshot["summary"]
        if not isinstance(summary, dict):
            return False
        return (
            record["run_id"],
            record["created_at"],
            record["execution_status"],
            dataset["dataset_id"],
            dataset["symbol"],
            dataset["interval"],
            dataset["period_start"],
            dataset["period_end"],
            dataset["processed_bar_count"],
            summary["position_status"],
        ) == (row[0], row[1], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11])
    except (KeyError, TypeError):
        return False


def _validate_store_path(path: Path) -> Path:
    candidate = Path(path)
    resolved = candidate.resolve()
    if "YEDEK_ESKI_PROJE" in resolved.parts or _is_linked(candidate) or _is_linked(resolved.parent):
        raise HistoricalRunStoreError("RUN_STORE_PATH_INVALID", "Historical run store linked/backup path üzerinde olamaz.")
    if not resolved.parent.is_dir() or candidate.exists() and not candidate.is_file():
        raise HistoricalRunStoreError("RUN_STORE_PATH_INVALID", "Historical run store yolu geçersiz.")
    return candidate


def _is_linked(path: Path) -> bool:
    return path.is_symlink() or bool(getattr(path, "is_junction", lambda: False)())


def _validate_source_execution_id(value: str) -> None:
    if not isinstance(value, str) or _SOURCE_EXECUTION_ID.fullmatch(value) is None:
        raise HistoricalRunStoreError("SOURCE_EXECUTION_ID_INVALID", "Source execution kimliği geçersiz.")


def _validate_created_at(value: str) -> None:
    if not isinstance(value, str) or len(value) > 32:
        raise HistoricalRunStoreError("CREATED_AT_INVALID", "Historical run zamanı geçersiz.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HistoricalRunStoreError("CREATED_AT_INVALID", "Historical run zamanı geçersiz.") from exc
    if parsed.tzinfo != timezone.utc:
        raise HistoricalRunStoreError("CREATED_AT_INVALID", "Historical run zamanı UTC olmalıdır.")


def _validate_uuid(value: str) -> None:
    try:
        parsed = UUID(value)
    except (AttributeError, ValueError) as exc:
        raise HistoricalRunStoreError("RUN_ID_INVALID", "Historical run kimliği geçersiz.") from exc
    if str(parsed) != value:
        raise HistoricalRunStoreError("RUN_ID_INVALID", "Historical run kimliği geçersiz.")


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
