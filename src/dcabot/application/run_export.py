"""Pure serializers for stored historical-run exports (F22).

JSON carries the complete record; CSV carries the flat summary row.
Both are deterministic so exports can be hashed and compared.
"""
import csv
import io
import json
from typing import Final


_CSV_COLUMNS: Final = (
    "run_id",
    "created_at",
    "storage_state",
    "execution_status",
    "symbol",
    "interval",
    "period_start",
    "period_end",
    "processed_bar_count",
    "position_status",
    "result_sha256",
    "record_sha256",
)


class RunExportError(ValueError):
    """Raised when a run record cannot be exported exactly."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def export_run_json(detail: dict[str, object]) -> str:
    """Serialize the complete record canonically."""
    _require_detail(detail)
    return json.dumps(detail, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def export_run_csv(detail: dict[str, object]) -> str:
    """Serialize the flat summary row with a header line."""
    _require_detail(detail)
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(_CSV_COLUMNS)
    writer.writerow([_cell(detail, column) for column in _CSV_COLUMNS])
    return buffer.getvalue()


def _require_detail(detail: object) -> None:
    if not isinstance(detail, dict):
        raise RunExportError("RUN_EXPORT_DETAIL_INVALID", "Run kaydı nesne olmalıdır.")
    for name in ("run_id", "created_at", "execution_status"):
        if not isinstance(detail.get(name), str):
            raise RunExportError(
                "RUN_EXPORT_DETAIL_INVALID", f"Run kaydı {name} taşımalıdır."
            )


def _cell(detail: dict[str, object], column: str) -> str:
    value: object = detail.get(column)
    if value is None and column in (
        "symbol",
        "interval",
        "period_start",
        "period_end",
        "processed_bar_count",
        "position_status",
    ):
        dataset = detail.get("dataset")
        if isinstance(dataset, dict):
            value = dataset.get(column)
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int)):
        return str(value)
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
