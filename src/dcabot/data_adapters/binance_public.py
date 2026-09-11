"""Network-free Binance Spot public payload normalization.

This module accepts already decoded public payloads only. It never opens a
socket, performs an HTTP request, reads credentials, or creates economic state.
"""

from enum import Enum
import hashlib
import json

from dcabot.data_adapters.public_feed import (
    FeedCursor,
    PublicFeedContractError,
    PublicObservation,
    ReplayResult,
    new_public_observation,
    replay_observations,
)
from dcabot.domain.numbers import exact_text, number


SOURCE_ID = "binance-spot-public-v3"
_MIN_TIMESTAMP_MS = 946_684_800_000  # 2000-01-01 UTC, local plausibility bound
_MAX_TIMESTAMP_MS = 7_258_118_400_000  # 2200-01-01 UTC, local plausibility bound


class BinanceTimeUnit(Enum):
    """Explicit timestamp unit selected by the transport configuration."""

    MILLISECONDS = "MILLISECONDS"
    MICROSECONDS = "MICROSECONDS"


def normalize_binance_trade_payload(
    payload: dict,
    *,
    allowed_symbols: frozenset[str],
    receive_time_us: int,
    processing_time_us: int,
    time_unit: BinanceTimeUnit,
) -> PublicObservation:
    """Normalize one Binance ``@trade`` payload without network side effects."""

    return _normalize(
        payload,
        stream_type="TRADE",
        expected_event_type="trade",
        event_key="t",
        required_fields=frozenset({"e", "E", "s", "t", "p", "q", "T", "m"}),
        allowed_symbols=allowed_symbols,
        receive_time_us=receive_time_us,
        processing_time_us=processing_time_us,
        time_unit=time_unit,
    )


def normalize_binance_agg_trade_payload(
    payload: dict,
    *,
    allowed_symbols: frozenset[str],
    receive_time_us: int,
    processing_time_us: int,
    time_unit: BinanceTimeUnit,
) -> PublicObservation:
    """Normalize one Binance ``@aggTrade`` payload without splitting it."""

    return _normalize(
        payload,
        stream_type="AGG_TRADE",
        expected_event_type="aggTrade",
        event_key="a",
        required_fields=frozenset(
            {"e", "E", "s", "a", "p", "q", "f", "l", "T", "m", "M"}
        ),
        allowed_symbols=allowed_symbols,
        receive_time_us=receive_time_us,
        processing_time_us=processing_time_us,
        time_unit=time_unit,
    )


def normalize_binance_rest_trade_payload(
    payload: dict,
    *,
    symbol: str,
    allowed_symbols: frozenset[str],
    receive_time_us: int,
    processing_time_us: int,
    time_unit: BinanceTimeUnit,
) -> PublicObservation:
    """Normalize one decoded ``/api/v3/trades`` record without networking."""

    return _normalize_rest(
        payload,
        symbol=symbol,
        stream_type="TRADE",
        event_key="id",
        time_key="time",
        required_fields=frozenset(
            {"id", "price", "qty", "quoteQty", "time", "isBuyerMaker", "isBestMatch"}
        ),
        allowed_symbols=allowed_symbols,
        receive_time_us=receive_time_us,
        processing_time_us=processing_time_us,
        time_unit=time_unit,
    )


def normalize_binance_rest_agg_trade_payload(
    payload: dict,
    *,
    symbol: str,
    allowed_symbols: frozenset[str],
    receive_time_us: int,
    processing_time_us: int,
    time_unit: BinanceTimeUnit,
) -> PublicObservation:
    """Normalize one decoded ``/api/v3/aggTrades`` record without networking."""

    return _normalize_rest(
        payload,
        symbol=symbol,
        stream_type="AGG_TRADE",
        event_key="a",
        time_key="T",
        required_fields=frozenset({"a", "p", "q", "f", "l", "T", "m", "M"}),
        allowed_symbols=allowed_symbols,
        receive_time_us=receive_time_us,
        processing_time_us=processing_time_us,
        time_unit=time_unit,
    )


def replay_binance_observations(
    observations: tuple[PublicObservation, ...],
    *,
    now_times_us: tuple[int, ...],
    max_staleness_us: int,
    cursor: FeedCursor | None = None,
    resync_indexes: frozenset[int] = frozenset(),
) -> ReplayResult:
    """Replay Binance observations through the existing bounded feed cursor."""

    if not isinstance(observations, tuple) or any(
        not isinstance(item, PublicObservation) for item in observations
    ):
        raise PublicFeedContractError(
            "BINANCE_REPLAY_INPUT_INVALID", "Replay observation tuple olmalıdır."
        )
    if cursor is not None and not isinstance(cursor, FeedCursor):
        raise PublicFeedContractError("BINANCE_CURSOR_INVALID", "Feed cursor geçersiz.")
    for item in observations:
        if (
            item.source_id != SOURCE_ID
            or item.transport != "WEBSOCKET"
            or item.product != "SPOT"
        ):
            raise PublicFeedContractError(
                "BINANCE_REPLAY_SCOPE_INVALID", "Observation Binance Spot WS scope dışında."
            )
        if item.source_sequence is not None:
            raise PublicFeedContractError(
                "BINANCE_SEQUENCE_UNSUPPORTED", "Binance t/a alanı source sequence değildir."
            )
    if cursor is not None and cursor.last_source_sequence is not None:
        raise PublicFeedContractError(
            "BINANCE_CURSOR_SEQUENCE_INVALID", "Binance cursor source sequence taşıyamaz."
        )
    return replay_observations(
        observations,
        now_times_us=now_times_us,
        max_staleness_us=max_staleness_us,
        cursor=cursor,
        resync_indexes=resync_indexes,
    )


def _normalize(
    payload: dict,
    *,
    stream_type: str,
    expected_event_type: str,
    event_key: str,
    required_fields: frozenset[str],
    allowed_symbols: frozenset[str],
    receive_time_us: int,
    processing_time_us: int,
    time_unit: BinanceTimeUnit,
) -> PublicObservation:
    if type(payload) is not dict:
        raise PublicFeedContractError("BINANCE_PAYLOAD_INVALID", "Payload dict olmalıdır.")
    if not isinstance(allowed_symbols, frozenset) or not allowed_symbols or any(
        type(symbol) is not str or not symbol for symbol in allowed_symbols
    ):
        raise PublicFeedContractError(
            "BINANCE_ALLOWLIST_INVALID", "Açık ve boş olmayan symbol allowlist gerekir."
        )
    if not isinstance(time_unit, BinanceTimeUnit):
        raise PublicFeedContractError(
            "BINANCE_TIME_UNIT_INVALID", "Timestamp unit açıkça seçilmelidir."
        )
    if not required_fields.issubset(payload):
        missing = sorted(required_fields - payload.keys())
        raise PublicFeedContractError(
            "BINANCE_PAYLOAD_MISSING", f"Gerekli alanlar eksik: {missing}."
        )
    if payload["e"] != expected_event_type:
        raise PublicFeedContractError(
            "BINANCE_EVENT_TYPE_INVALID", f"Beklenen event type {expected_event_type!r}."
        )

    symbol = payload["s"]
    if type(symbol) is not str or symbol not in allowed_symbols:
        raise PublicFeedContractError(
            "BINANCE_SYMBOL_INVALID", "Symbol allowlist kapsamında değil."
        )

    event_id = str(_required_integer(payload[event_key], event_key))
    event_time_us = _timestamp_us(payload["T"], "T", time_unit)
    exchange_time_us = _timestamp_us(payload["E"], "E", time_unit)
    if type(receive_time_us) is not int or receive_time_us < 0:
        raise PublicFeedContractError(
            "BINANCE_RECEIVE_TIME_INVALID", "receive_time_us non-negative integer olmalıdır."
        )
    if type(processing_time_us) is not int or processing_time_us < receive_time_us:
        raise PublicFeedContractError(
            "BINANCE_PROCESSING_TIME_INVALID",
            "processing_time_us receive_time_us değerinden küçük olamaz.",
        )

    price = _canonical_decimal(payload["p"], "p", positive=True)
    quantity = _canonical_decimal(payload["q"], "q", positive=True)
    is_buyer_maker = _required_bool(payload["m"], "m")
    payload_hash = _payload_hash(payload)

    common = {
        "source_id": SOURCE_ID,
        "transport": "WEBSOCKET",
        "symbol": symbol,
        "product": "SPOT",
        "event_id": event_id,
        "event_time_us": event_time_us,
        "receive_time_us": receive_time_us,
        "processing_time_us": processing_time_us,
        "price": price,
        "quantity": quantity,
        "payload_hash": payload_hash,
        "source_sequence": None,
        "stream_type": stream_type,
        "exchange_time_us": exchange_time_us,
        "is_buyer_maker": is_buyer_maker,
    }
    if stream_type == "TRADE":
        common["buyer_order_id"] = _optional_integer(payload.get("b"), "b")
        common["seller_order_id"] = _optional_integer(payload.get("a"), "a")
    else:
        common["first_trade_id"] = _required_integer(payload["f"], "f")
        common["last_trade_id"] = _required_integer(payload["l"], "l")
        if common["last_trade_id"] < common["first_trade_id"]:
            raise PublicFeedContractError(
                "BINANCE_TRADE_RANGE_INVALID", "Aggregate trade ID aralığı geriye gidemez."
            )
    return new_public_observation(**common)


def _normalize_rest(
    payload: dict,
    *,
    symbol: str,
    stream_type: str,
    event_key: str,
    time_key: str,
    required_fields: frozenset[str],
    allowed_symbols: frozenset[str],
    receive_time_us: int,
    processing_time_us: int,
    time_unit: BinanceTimeUnit,
) -> PublicObservation:
    if type(payload) is not dict:
        raise PublicFeedContractError("BINANCE_PAYLOAD_INVALID", "Payload dict olmalıdır.")
    if not isinstance(allowed_symbols, frozenset) or not allowed_symbols or any(
        type(item) is not str or not item for item in allowed_symbols
    ):
        raise PublicFeedContractError(
            "BINANCE_ALLOWLIST_INVALID", "Açık ve boş olmayan symbol allowlist gerekir."
        )
    if type(symbol) is not str or symbol not in allowed_symbols:
        raise PublicFeedContractError(
            "BINANCE_SYMBOL_INVALID", "REST symbol allowlist kapsamında değil."
        )
    if not isinstance(time_unit, BinanceTimeUnit):
        raise PublicFeedContractError(
            "BINANCE_TIME_UNIT_INVALID", "Timestamp unit açıkça seçilmelidir."
        )
    if not required_fields.issubset(payload):
        missing = sorted(required_fields - payload.keys())
        raise PublicFeedContractError(
            "BINANCE_PAYLOAD_MISSING", f"Gerekli REST alanları eksik: {missing}."
        )
    event_id = str(_required_integer(payload[event_key], event_key))
    event_time_us = _timestamp_us(payload[time_key], time_key, time_unit)
    if type(receive_time_us) is not int or receive_time_us < 0:
        raise PublicFeedContractError(
            "BINANCE_RECEIVE_TIME_INVALID", "receive_time_us non-negative integer olmalıdır."
        )
    if type(processing_time_us) is not int or processing_time_us < receive_time_us:
        raise PublicFeedContractError(
            "BINANCE_PROCESSING_TIME_INVALID",
            "processing_time_us receive_time_us değerinden küçük olamaz.",
        )

    price_key = "price" if stream_type == "TRADE" else "p"
    quantity_key = "qty" if stream_type == "TRADE" else "q"
    maker_key = "isBuyerMaker" if stream_type == "TRADE" else "m"
    price = _canonical_decimal(payload[price_key], "price", positive=True)
    quantity = _canonical_decimal(payload[quantity_key], "quantity", positive=True)
    is_buyer_maker = _required_bool(payload[maker_key], maker_key)
    if stream_type == "TRADE":
        _canonical_decimal(payload["quoteQty"], "quoteQty", positive=True)
        _required_bool(payload["isBestMatch"], "isBestMatch")
    else:
        first_trade_id = _required_integer(payload["f"], "f")
        last_trade_id = _required_integer(payload["l"], "l")
        if last_trade_id < first_trade_id:
            raise PublicFeedContractError(
                "BINANCE_TRADE_RANGE_INVALID", "Aggregate trade ID aralığı geriye gidemez."
            )
        _required_bool(payload["M"], "M")
    payload_hash = _payload_hash(payload)
    common = {
        "source_id": SOURCE_ID,
        "transport": "REST",
        "symbol": symbol,
        "product": "SPOT",
        "event_id": event_id,
        "event_time_us": event_time_us,
        "receive_time_us": receive_time_us,
        "processing_time_us": processing_time_us,
        "price": price,
        "quantity": quantity,
        "payload_hash": payload_hash,
        "source_sequence": None,
        "stream_type": stream_type,
        "exchange_time_us": None,
        "is_buyer_maker": is_buyer_maker,
    }
    if stream_type == "AGG_TRADE":
        common["first_trade_id"] = first_trade_id
        common["last_trade_id"] = last_trade_id
    return new_public_observation(**common)


def _timestamp_us(raw: object, field_name: str, time_unit: BinanceTimeUnit) -> int:
    value = _required_integer(raw, field_name)
    if value <= 0:
        raise PublicFeedContractError(
            "BINANCE_TIMESTAMP_INVALID", f"{field_name} pozitif integer olmalıdır."
        )
    if time_unit is BinanceTimeUnit.MILLISECONDS:
        valid = _MIN_TIMESTAMP_MS <= value <= _MAX_TIMESTAMP_MS
        converted = value * 1000
    else:
        valid = _MIN_TIMESTAMP_MS * 1000 <= value <= _MAX_TIMESTAMP_MS * 1000
        converted = value
    if not valid:
        raise PublicFeedContractError(
            "BINANCE_TIMESTAMP_UNIT_MISMATCH",
            f"{field_name} seçilen timestamp unit ile plausibility sınırında değil.",
        )
    return converted


def _canonical_decimal(raw: object, field_name: str, *, positive: bool) -> str:
    if type(raw) is not str:
        raise PublicFeedContractError(
            "BINANCE_NUMERIC_TYPE_INVALID", f"{field_name} decimal string olmalıdır."
        )
    try:
        value = number(raw)
        if positive and value <= 0:
            raise ValueError
        return exact_text(value)
    except ValueError as exc:
        raise PublicFeedContractError(
            "BINANCE_NUMERIC_INVALID", f"{field_name} exact canonical decimal değil."
        ) from exc


def _payload_hash(payload: dict) -> str:
    if any(type(key) is not str for key in payload):
        raise PublicFeedContractError(
            "BINANCE_PAYLOAD_KEYS_INVALID", "Payload anahtarları string olmalıdır."
        )
    try:
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise PublicFeedContractError(
            "BINANCE_PAYLOAD_CANONICAL_INVALID", "Payload canonical JSON olarak yazılamadı."
        ) from exc
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _required_integer(raw: object, field_name: str) -> int:
    if type(raw) is not int or raw < 0:
        raise PublicFeedContractError(
            "BINANCE_INTEGER_INVALID", f"{field_name} non-negative integer olmalıdır."
        )
    return raw


def _optional_integer(raw: object, field_name: str) -> int | None:
    return None if raw is None else _required_integer(raw, field_name)


def _required_bool(raw: object, field_name: str) -> bool:
    if type(raw) is not bool:
        raise PublicFeedContractError(
            "BINANCE_BOOLEAN_INVALID", f"{field_name} boolean olmalıdır."
        )
    return raw
