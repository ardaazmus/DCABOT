"""Read-only canonical bars from a catalog-selected verified public artifact."""

import csv
from dataclasses import dataclass
from datetime import date, datetime, timezone
from io import TextIOWrapper
from pathlib import Path
import re
from zipfile import BadZipFile, ZipFile

from dcabot.data_adapters.catalog import PublicDatasetSelection
from dcabot.domain.numbers import Q, exact_text, number


RAW_KLINE_FIELD_COUNT = 12
MAX_BARS = 100_000
INTEGER_PATTERN = re.compile(r"[0-9]+\Z", re.ASCII)


class HistoricalInputError(ValueError):
    """Raised when a verified artifact cannot become a safe canonical input."""


@dataclass(frozen=True, slots=True)
class CanonicalBar:
    """One closed bar with exact decimal strings at the application boundary."""

    open_time_us: int
    close_time_us: int
    open: str
    high: str
    low: str
    close: str
    base_volume: str
    is_closed: bool


@dataclass(frozen=True, slots=True)
class HistoricalDatasetMetadata:
    """Source and time identity that accompanies canonical bars without a path or URL."""

    dataset_id: str
    source_id: str
    symbol: str
    interval: str
    period_start: str
    period_end: str
    artifact_sha256: str
    artifact_bytes: int
    timestamp_unit: str
    timezone: str


@dataclass(frozen=True, slots=True)
class HistoricalDatasetInput:
    """Bounded, immutable parser/application input for one verified dataset."""

    metadata: HistoricalDatasetMetadata
    bars: tuple[CanonicalBar, ...]


def parse_verified_dataset(selection: PublicDatasetSelection) -> HistoricalDatasetInput:
    """Parse one catalog capability without network access, writes, or arbitrary file input."""

    if not isinstance(selection, PublicDatasetSelection) or selection.entry.quality_status != "VERIFIED":
        raise HistoricalInputError("Yalnız VERIFIED dataset seçimi okunabilir.")
    if selection.entry.byte_count is None:
        raise HistoricalInputError("Verified dataset byte bilgisi eksik.")
    if selection.inner_filename is None:
        raise HistoricalInputError("Verified dataset iç CSV tanımı eksik.")
    if selection.path.is_symlink() or not selection.path.is_file():
        raise HistoricalInputError("Verified dataset artifact’ı okunabilir değil.")
    try:
        with ZipFile(selection.path) as archive:
            info = archive.getinfo(selection.inner_filename)
            if info.is_dir():
                raise HistoricalInputError("Verified dataset CSV üyesi dosya olmalıdır.")
            with archive.open(info, "r") as member:
                with TextIOWrapper(member, encoding="utf-8-sig", newline="") as text:
                    bars = _read_raw_klines(text, selection)
    except (BadZipFile, KeyError, OSError, UnicodeError, csv.Error) as exc:
        raise HistoricalInputError("Verified dataset CSV okunamadı.") from exc
    return HistoricalDatasetInput(
        metadata=HistoricalDatasetMetadata(
            dataset_id=selection.entry.dataset_id,
            source_id=selection.entry.source_id,
            symbol=selection.entry.symbol,
            interval=selection.entry.interval,
            period_start=selection.entry.period_start,
            period_end=selection.entry.period_end,
            artifact_sha256=selection.entry.sha256,
            artifact_bytes=selection.entry.byte_count,
            timestamp_unit="microseconds",
            timezone="UTC",
        ),
        bars=tuple(bars),
    )


def _read_raw_klines(reader: TextIOWrapper, selection: PublicDatasetSelection) -> list[CanonicalBar]:
    rows: list[CanonicalBar] = []
    for row_number, fields in enumerate(csv.reader(reader, strict=True), start=1):
        if len(rows) >= MAX_BARS:
            raise HistoricalInputError(f"Dataset {MAX_BARS} bar sınırını aşıyor.")
        if len(fields) != RAW_KLINE_FIELD_COUNT:
            raise HistoricalInputError(f"Dataset satırı {row_number} Binance kline şemasıyla eşleşmiyor.")
        rows.append(_parse_raw_kline(fields, row_number, selection))
    if not rows:
        raise HistoricalInputError("Dataset içinde bar bulunamadı.")
    _validate_time_sequence(rows, selection)
    return rows


def _parse_raw_kline(fields: list[str], row_number: int, selection: PublicDatasetSelection) -> CanonicalBar:
    open_time = _integer(fields[0], "open_time_us", row_number)
    close_time = _integer(fields[6], "close_time_us", row_number)
    open_value, open_text = _decimal(fields[1], "open", row_number, positive=True)
    high_value, high_text = _decimal(fields[2], "high", row_number, positive=True)
    low_value, low_text = _decimal(fields[3], "low", row_number, positive=True)
    close_value, close_text = _decimal(fields[4], "close", row_number, positive=True)
    _, volume_text = _decimal(fields[5], "base_volume", row_number)
    _decimal(fields[7], "quote_volume", row_number)
    _integer(fields[8], "trade_count", row_number)
    _decimal(fields[9], "taker_buy_base_volume", row_number)
    _decimal(fields[10], "taker_buy_quote_volume", row_number)
    if fields[11] != "0":
        raise HistoricalInputError(f"Dataset satırı {row_number} ignore alanı geçersiz.")
    if low_value > open_value or low_value > close_value or high_value < open_value or high_value < close_value or low_value > high_value:
        raise HistoricalInputError(f"Dataset satırı {row_number} OHLC sınırlarını sağlamıyor.")
    return CanonicalBar(
        open_time_us=open_time,
        close_time_us=close_time,
        open=open_text,
        high=high_text,
        low=low_text,
        close=close_text,
        base_volume=volume_text,
        is_closed=True,
    )


def _integer(value: str, field: str, row_number: int) -> int:
    if not INTEGER_PATTERN.fullmatch(value):
        raise HistoricalInputError(f"Dataset satırı {row_number} {field} tam sayı olmalıdır.")
    return int(value)


def _decimal(value: str, field: str, row_number: int, *, positive: bool = False) -> tuple[Q, str]:
    try:
        parsed = number(value)
    except ValueError as exc:
        raise HistoricalInputError(f"Dataset satırı {row_number} {field} ondalık değeri geçersiz.") from exc
    if (positive and parsed <= 0) or (not positive and parsed < 0):
        raise HistoricalInputError(f"Dataset satırı {row_number} {field} aralık dışında.")
    return parsed, exact_text(parsed)


def _validate_time_sequence(rows: list[CanonicalBar], selection: PublicDatasetSelection) -> None:
    period_start = _period_us(selection.entry.period_start)
    period_end = _period_us(selection.entry.period_end)
    previous_open: int | None = None
    for index, bar in enumerate(rows):
        if not period_start <= bar.open_time_us < period_end:
            raise HistoricalInputError("Dataset bar zamanı katalog döneminin dışında.")
        if bar.close_time_us <= bar.open_time_us or bar.close_time_us >= period_end:
            raise HistoricalInputError("Dataset bar zaman aralığı geçersiz.")
        if previous_open is not None and bar.open_time_us <= previous_open:
            raise HistoricalInputError("Dataset bar zaman sırası benzersiz ve artan olmalıdır.")
        if index and rows[index - 1].close_time_us >= bar.open_time_us:
            raise HistoricalInputError("Dataset bar zaman aralıkları çakışıyor.")
        previous_open = bar.open_time_us


def _period_us(value: str) -> int:
    try:
        instant = datetime.combine(date.fromisoformat(value), datetime.min.time(), tzinfo=timezone.utc)
    except (TypeError, ValueError) as exc:
        raise HistoricalInputError("Dataset dönemi geçersiz.") from exc
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    delta = instant - epoch
    return (delta.days * 86_400 + delta.seconds) * 1_000_000 + delta.microseconds
