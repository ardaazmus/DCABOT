"""Bounded, read-only quality checks for canonical CSV and ZIP datasets."""

import csv
import hashlib
import io
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath

from dcabot.domain.numbers import number


MAX_INPUT_BYTES = 20 * 1024 * 1024
MAX_EXPANDED_BYTES = 100 * 1024 * 1024
MAX_ZIP_MEMBERS = 20
MAX_ROWS = 100_000
MAX_ISSUE_SAMPLES = 200
MAX_ISSUE_MESSAGE_BYTES = 1_024

BAR_FIELDS = {
    "open_time_us",
    "close_time_us",
    "open",
    "high",
    "low",
    "close",
    "base_volume",
    "is_closed",
}
TRADE_FIELDS = {"exchange_time_us", "source_trade_id", "price", "base_qty"}
INTEGER_PATTERN = re.compile(r"[0-9]+\Z", re.ASCII)


class DataQualityError(ValueError):
    """Raised when a file cannot be safely inspected as one CSV dataset."""


def _issue(code: str, severity: str, message: str, row: int | None = None) -> dict[str, object]:
    result: dict[str, object] = {"code": code, "severity": severity, "message": message}
    if row is not None:
        result["row"] = row
    return result


class _IssueCollector(list[dict[str, object]]):
    """Keep a bounded issue sample while preserving complete severity counts."""

    def __init__(self) -> None:
        super().__init__()
        self.issue_count = 0
        self.error_count = 0
        self.warning_count = 0
        self.truncated = False

    def append(self, issue: dict[str, object]) -> None:
        self.issue_count += 1
        if issue["severity"] == "error":
            self.error_count += 1
        elif issue["severity"] == "warning":
            self.warning_count += 1
        if len(self) >= MAX_ISSUE_SAMPLES:
            self.truncated = True
            return
        bounded = dict(issue)
        message = bounded.get("message")
        if isinstance(message, str):
            encoded = message.encode("utf-8")
            if len(encoded) > MAX_ISSUE_MESSAGE_BYTES:
                bounded["message"] = encoded[: MAX_ISSUE_MESSAGE_BYTES - 3].decode("utf-8", "ignore") + "..."
        super().append(bounded)


def _safe_filename(filename: str) -> str:
    if not isinstance(filename, str) or not filename or len(filename) > 255:
        raise DataQualityError("Dosya adı geçersiz.")
    if any(separator in filename for separator in ("/", "\\")):
        raise DataQualityError("Dosya adı path içermemelidir.")
    suffix = Path(filename).suffix.lower()
    if suffix not in {".csv", ".zip"}:
        raise DataQualityError("Yalnız CSV veya ZIP dosyası kabul edilir.")
    return filename


def _read_csv(content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DataQualityError("CSV UTF-8 olarak okunamadı.") from exc
    if "\x00" in text:
        raise DataQualityError("CSV içinde binary içerik bulundu.")
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        raw_headers = reader.fieldnames
        if not raw_headers:
            raise DataQualityError("CSV header satırı bulunamadı.")
        headers = [header.strip() for header in raw_headers]
        if any(not header for header in headers) or len(set(headers)) != len(headers):
            raise DataQualityError("CSV header alanları boş veya yinelenmiş.")
        rows: list[dict[str, str]] = []
        for row_number, raw_row in enumerate(reader, start=2):
            if len(rows) >= MAX_ROWS:
                raise DataQualityError(f"CSV {MAX_ROWS} satır sınırını aşıyor.")
            if None in raw_row:
                raise DataQualityError(f"CSV satırında beklenmeyen fazla kolon var: {row_number}.")
            rows.append({header: (raw_row.get(raw_header) or "").strip() for header, raw_header in zip(headers, raw_headers)})
    except csv.Error as exc:
        raise DataQualityError(f"CSV biçimi bozuk: {exc}") from exc
    return headers, rows


def _extract_csv(filename: str, content: bytes) -> tuple[str, bytes]:
    if not filename.lower().endswith(".zip"):
        return filename, content
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_ZIP_MEMBERS:
                raise DataQualityError(f"ZIP en fazla {MAX_ZIP_MEMBERS} dosya içerebilir.")
            candidates: list[zipfile.ZipInfo] = []
            expanded_size = 0
            for info in infos:
                if info.is_dir():
                    continue
                normalized = info.filename.replace("\\", "/")
                parts = PurePosixPath(normalized).parts
                if normalized.startswith("/") or ".." in parts:
                    raise DataQualityError("ZIP path traversal içeriyor.")
                mode = (info.external_attr >> 16) & 0xF000
                if mode == stat.S_IFLNK:
                    raise DataQualityError("ZIP symbolic link içeriyor.")
                expanded_size += info.file_size
                if expanded_size > MAX_EXPANDED_BYTES:
                    raise DataQualityError("ZIP açılım boyutu sınırı aşıyor.")
                if normalized.lower().endswith(".csv"):
                    candidates.append(info)
            if len(candidates) != 1:
                raise DataQualityError("ZIP içinde tam olarak bir CSV veri dosyası olmalıdır.")
            selected = candidates[0]
            return Path(selected.filename).name, archive.read(selected)
    except zipfile.BadZipFile as exc:
        raise DataQualityError("ZIP biçimi bozuk.") from exc


def _parse_integer(value: str, field: str, row: int, issues: list[dict[str, object]]) -> int | None:
    if not INTEGER_PATTERN.fullmatch(value):
        issues.append(_issue("invalid_integer", "error", f"{field} tam sayı olmalıdır.", row))
        return None
    return int(value)


def _parse_number(value: str, field: str, row: int, issues: list[dict[str, object]], *, positive: bool = False):
    try:
        result = number(value)
    except ValueError:
        issues.append(_issue("invalid_decimal", "error", f"{field} noktasız ondalık string olmalıdır.", row))
        return None
    if (positive and result <= 0) or (not positive and result < 0):
        issues.append(_issue("invalid_range", "error", f"{field} aralık dışında.", row))
        return None
    return result


def _quality_report(filename: str, content: bytes) -> dict[str, object]:
    headers, rows = _read_csv(content)
    header_set = set(headers)
    if BAR_FIELDS <= header_set:
        kind = "bar"
        required = BAR_FIELDS
        timestamp_field = "open_time_us"
    elif TRADE_FIELDS <= header_set:
        kind = "trade"
        required = TRADE_FIELDS
        timestamp_field = "exchange_time_us"
    else:
        kind = None
        required = BAR_FIELDS | TRADE_FIELDS
        timestamp_field = None
    issues = _IssueCollector()
    if kind is None:
        missing_bar = ", ".join(sorted(BAR_FIELDS - header_set))
        missing_trade = ", ".join(sorted(TRADE_FIELDS - header_set))
        issues.append(_issue(
            "unsupported_schema",
            "error",
            f"Canonical bar alanları eksik: {missing_bar}; trade alanları eksik: {missing_trade}.",
        ))
    else:
        missing = sorted(required - header_set)
        if missing:
            issues.append(_issue("missing_required_fields", "error", ", ".join(missing)))
    timestamps: list[tuple[int, int]] = []
    duplicate_same = 0
    duplicate_conflicts = 0
    seen: dict[object, dict[str, str]] = {}
    previous_timestamp: int | None = None
    symbols = sorted({row["symbol"] for row in rows if row.get("symbol")})
    if len(symbols) > 1:
        issues.append(_issue("mixed_symbol", "error", "Tek veri kümesinde birden fazla symbol bulundu."))
    for row_number, row in enumerate(rows, start=2):
        if kind is None or timestamp_field is None:
            continue
        timestamp = _parse_integer(row[timestamp_field], timestamp_field, row_number, issues)
        if timestamp is not None:
            timestamps.append((timestamp, row_number))
            if previous_timestamp is not None and timestamp < previous_timestamp:
                issues.append(_issue("out_of_order", "warning", "Zaman sırası geriye gidiyor.", row_number))
            previous_timestamp = timestamp
        if kind == "bar":
            close_time = _parse_integer(row["close_time_us"], "close_time_us", row_number, issues)
            open_time = timestamp
            if open_time is not None and close_time is not None and open_time >= close_time:
                issues.append(_issue("invalid_time_range", "error", "open_time_us close_time_us'den küçük olmalıdır.", row_number))
            values = {
                field: _parse_number(row[field], field, row_number, issues, positive=field not in {"base_volume", "quote_volume", "trade_count"})
                for field in ("open", "high", "low", "close", "base_volume")
            }
            if all(values[field] is not None for field in ("open", "high", "low", "close")):
                if values["low"] > values["open"] or values["low"] > values["close"] or values["high"] < values["open"] or values["high"] < values["close"] or values["low"] > values["high"]:
                    issues.append(_issue("ohlc_bounds", "error", "low ≤ open/close ≤ high koşulu sağlanmıyor.", row_number))
            closed = row["is_closed"].lower()
            if closed not in {"true", "false", "1", "0"}:
                issues.append(_issue("invalid_closed_flag", "error", "is_closed boolean olmalıdır.", row_number))
            elif closed in {"false", "0"}:
                issues.append(_issue("bar_not_closed", "error", "Kalite kontrolü yalnız kapalı bar kabul eder.", row_number))
            key = timestamp
        else:
            _parse_number(row["price"], "price", row_number, issues, positive=True)
            _parse_number(row["base_qty"], "base_qty", row_number, issues, positive=True)
            if not row["source_trade_id"]:
                issues.append(_issue("missing_trade_id", "error", "source_trade_id boş olamaz.", row_number))
            key = (timestamp, row["source_trade_id"])
        if key in seen:
            if seen[key] == row:
                duplicate_same += 1
            else:
                duplicate_conflicts += 1
                issues.append(_issue("duplicate_conflict", "error", "Aynı key farklı veri taşıyor.", row_number))
        else:
            seen[key] = row
    if duplicate_same:
        issues.append(_issue("duplicate_same", "warning", f"Aynı veriyle yinelenen kayıt: {duplicate_same}."))
    unique_timestamps = sorted({timestamp for timestamp, _ in timestamps})
    deltas = [right - left for left, right in zip(unique_timestamps, unique_timestamps[1:]) if right > left]
    inferred_interval = sorted(deltas)[(len(deltas) - 1) // 2] if deltas else None
    gap_count = 0
    largest_gap = None
    if inferred_interval is not None:
        large_gaps = [delta for delta in deltas if delta > inferred_interval * 3 // 2]
        gap_count = len(large_gaps)
        largest_gap = max(large_gaps, default=None)
        if gap_count:
            issues.append(_issue("gap_observed", "warning", f"Gözlenen zaman aralığı boşluğu: {gap_count}."))
    error_count = issues.error_count
    warning_count = issues.warning_count
    status = "REJECTED" if error_count else "PASS_WITH_WARNINGS" if warning_count else "PASS"
    return {
        "status": status,
        "source_filename": filename,
        "source_sha256": hashlib.sha256(content).hexdigest(),
        "source_bytes": len(content),
        "kind": kind,
        "symbol": symbols[0] if len(symbols) == 1 else None,
        "symbols": symbols,
        "schema_version": "canonical-v1",
        "headers": headers,
        "row_count": len(rows),
        "timestamp": {
            "field": timestamp_field,
            "unit": "microseconds" if timestamp_field else None,
            "timezone": "UTC" if timestamp_field else None,
            "start": str(unique_timestamps[0]) if unique_timestamps else None,
            "end": str(unique_timestamps[-1]) if unique_timestamps else None,
            "out_of_order": sum(issue["code"] == "out_of_order" for issue in issues),
        },
        "duplicates": {"same": duplicate_same, "conflicts": duplicate_conflicts},
        "gaps": {
            "interval_us": str(inferred_interval) if inferred_interval is not None else None,
            "basis": "median_observed_delta" if inferred_interval is not None else None,
            "count": gap_count,
            "largest_us": str(largest_gap) if largest_gap is not None else None,
        },
        "issues": list(issues),
        "issue_count": issues.issue_count,
        "issues_truncated": issues.truncated,
        "error_count": error_count,
        "warning_count": warning_count,
    }


def quality_from_bytes(filename: str, content: bytes) -> dict[str, object]:
    """Inspect one bounded CSV/ZIP payload without writing or executing its contents."""

    filename = _safe_filename(filename)
    if not isinstance(content, bytes):
        raise DataQualityError("Dosya içeriği bytes olmalıdır.")
    if len(content) > MAX_INPUT_BYTES:
        raise DataQualityError(f"Dosya {MAX_INPUT_BYTES} byte sınırını aşıyor.")
    selected_filename, csv_content = _extract_csv(filename, content)
    if len(csv_content) > MAX_EXPANDED_BYTES:
        raise DataQualityError("CSV açılım boyutu sınırı aşıyor.")
    return _quality_report(selected_filename, csv_content)


def quality_from_path(path: Path) -> dict[str, object]:
    """Inspect a local file without extracting it to disk or executing archive members."""

    resolved = path.resolve()
    if "YEDEK_ESKI_PROJE" in resolved.parts or path.is_symlink() or not path.is_file():
        raise DataQualityError("Local veri yolu geçersiz veya yedek alanında.")
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise DataQualityError(f"Dosya {MAX_INPUT_BYTES} byte sınırını aşıyor.")
    return quality_from_bytes(path.name, path.read_bytes())
