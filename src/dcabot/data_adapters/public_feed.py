"""Bounded, read-only public observation and reconnect gate.

This module deliberately stops at source-observation acceptance. It does not
create candidates, orders, fills, balances, or economic results.
"""

from dataclasses import dataclass, replace
from enum import Enum
import re

from dcabot.domain.numbers import exact_text, number


_IDENTIFIER = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)
_SHA256 = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_MAX_ACCEPTED = 1_024
_MAX_REPLAY = 1_024


class PublicFeedContractError(ValueError):
    """Raised when a public observation cannot be trusted."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class FeedState(Enum):
    """Non-economic state of one bounded public feed cursor."""

    DISCONNECTED = "DISCONNECTED"
    SYNCED = "SYNCED"
    STALE = "STALE"
    GAP = "GAP"
    RECONNECTING = "RECONNECTING"
    FAILED = "FAILED"


class ObservationOutcome(Enum):
    """Result of attempting to accept one source observation."""

    ACCEPTED = "ACCEPTED"
    DUPLICATE = "DUPLICATE"
    CONFLICT = "CONFLICT"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    SEQUENCE_GAP = "SEQUENCE_GAP"
    STALE = "STALE"
    RESYNC_REQUIRED = "RESYNC_REQUIRED"
    WRONG_SCOPE = "WRONG_SCOPE"
    MISSING_SEQUENCE = "MISSING_SEQUENCE"
    CAPACITY_EXCEEDED = "CAPACITY_EXCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class PublicObservation:
    """One immutable read-only observation with explicit source and time data."""

    source_id: str
    transport: str
    symbol: str
    product: str
    event_id: str
    event_time_us: int
    receive_time_us: int
    processing_time_us: int
    price: str
    quantity: str
    payload_hash: str
    source_sequence: int | None
    stream_type: str = "TRADE"
    exchange_time_us: int | None = None
    is_buyer_maker: bool | None = None
    buyer_order_id: int | None = None
    seller_order_id: int | None = None
    first_trade_id: int | None = None
    last_trade_id: int | None = None

    def __post_init__(self) -> None:
        for value, code in (
            (self.source_id, "FEED_SOURCE_INVALID"),
            (self.symbol, "FEED_SYMBOL_INVALID"),
            (self.product, "FEED_PRODUCT_INVALID"),
            (self.event_id, "FEED_EVENT_ID_INVALID"),
        ):
            _validate_identifier(value, code)
        if self.transport not in {"REST", "WEBSOCKET"}:
            raise PublicFeedContractError(
                "FEED_TRANSPORT_INVALID", "Yalnız REST veya WEBSOCKET kabul edilir."
            )
        if self.stream_type not in {"TRADE", "AGG_TRADE"}:
            raise PublicFeedContractError(
                "FEED_STREAM_INVALID", "Yalnız TRADE veya AGG_TRADE kabul edilir."
            )
        for value, code in (
            (self.event_time_us, "FEED_EVENT_TIME_INVALID"),
            (self.receive_time_us, "FEED_RECEIVE_TIME_INVALID"),
            (self.processing_time_us, "FEED_PROCESSING_TIME_INVALID"),
        ):
            _validate_nonnegative_integer(value, code)
        if self.exchange_time_us is not None:
            _validate_nonnegative_integer(self.exchange_time_us, "FEED_EXCHANGE_TIME_INVALID")
        if self.is_buyer_maker is not None and type(self.is_buyer_maker) is not bool:
            raise PublicFeedContractError(
                "FEED_MAKER_FLAG_INVALID", "is_buyer_maker boolean olmalıdır."
            )
        for value, code in (
            (self.buyer_order_id, "FEED_BUYER_ORDER_ID_INVALID"),
            (self.seller_order_id, "FEED_SELLER_ORDER_ID_INVALID"),
            (self.first_trade_id, "FEED_FIRST_TRADE_ID_INVALID"),
            (self.last_trade_id, "FEED_LAST_TRADE_ID_INVALID"),
        ):
            if value is not None:
                _validate_nonnegative_integer(value, code)
        try:
            price = number(self.price)
            quantity = number(self.quantity)
        except ValueError as exc:
            raise PublicFeedContractError(
                "FEED_NUMERIC_INVALID", "Fiyat ve miktar exact decimal string olmalıdır."
            ) from exc
        if price <= 0 or quantity < 0:
            raise PublicFeedContractError(
                "FEED_NUMERIC_RANGE_INVALID", "Fiyat pozitif, miktar negatif olmayan olmalıdır."
            )
        try:
            if exact_text(price) != self.price or exact_text(quantity) != self.quantity:
                raise ValueError
        except ValueError as exc:
            raise PublicFeedContractError(
                "FEED_NUMERIC_CANONICAL_INVALID", "Numeric değer canonical decimal biçiminde olmalıdır."
            ) from exc
        if not isinstance(self.payload_hash, str) or _SHA256.fullmatch(self.payload_hash) is None:
            raise PublicFeedContractError(
                "FEED_PAYLOAD_HASH_INVALID", "Payload hash küçük harfli SHA-256 hex olmalıdır."
            )
        if self.source_sequence is not None:
            _validate_nonnegative_integer(self.source_sequence, "FEED_SEQUENCE_INVALID")

    def immutable_key(self) -> tuple[object, ...]:
        """Return fields that identify the source payload, excluding local receive times."""

        return (
            self.source_id,
            self.transport,
            self.symbol,
            self.product,
            self.event_id,
            self.event_time_us,
            self.price,
            self.quantity,
            self.payload_hash,
            self.source_sequence,
            self.stream_type,
            self.exchange_time_us,
            self.is_buyer_maker,
            self.buyer_order_id,
            self.seller_order_id,
            self.first_trade_id,
            self.last_trade_id,
        )


@dataclass(frozen=True, slots=True)
class FeedCursor:
    """Bounded accepted-observation history and its fail-closed feed state."""

    state: FeedState = FeedState.DISCONNECTED
    accepted: tuple[PublicObservation, ...] = ()
    last_event_time_us: int | None = None
    last_receive_time_us: int | None = None
    last_source_sequence: int | None = None


@dataclass(frozen=True, slots=True)
class ObservationResult:
    """Read-only observation decision; never contains an economic posting."""

    cursor: FeedCursor
    outcome: ObservationOutcome


@dataclass(frozen=True, slots=True)
class ReplayResult:
    """Bounded local replay output containing no run or economic identity."""

    cursor: FeedCursor
    outcomes: tuple[ObservationOutcome, ...]
    accepted_count: int


def new_feed_cursor() -> FeedCursor:
    """Create a disconnected cursor without contacting a network source."""

    return FeedCursor()


def new_public_observation(
    *,
    source_id: str,
    transport: str,
    symbol: str,
    product: str,
    event_id: str,
    event_time_us: int,
    receive_time_us: int,
    processing_time_us: int,
    price: str,
    quantity: str,
    payload_hash: str,
    source_sequence: int | None,
    stream_type: str = "TRADE",
    exchange_time_us: int | None = None,
    is_buyer_maker: bool | None = None,
    buyer_order_id: int | None = None,
    seller_order_id: int | None = None,
    first_trade_id: int | None = None,
    last_trade_id: int | None = None,
) -> PublicObservation:
    """Validate one already-normalized observation without creating economic state."""

    return PublicObservation(
        source_id=source_id,
        transport=transport,
        symbol=symbol,
        product=product,
        event_id=event_id,
        event_time_us=event_time_us,
        receive_time_us=receive_time_us,
        processing_time_us=processing_time_us,
        price=price,
        quantity=quantity,
        payload_hash=payload_hash,
        source_sequence=source_sequence,
        stream_type=stream_type,
        exchange_time_us=exchange_time_us,
        is_buyer_maker=is_buyer_maker,
        buyer_order_id=buyer_order_id,
        seller_order_id=seller_order_id,
        first_trade_id=first_trade_id,
        last_trade_id=last_trade_id,
    )


def replay_observations(
    observations: tuple[PublicObservation, ...],
    *,
    now_times_us: tuple[int, ...],
    max_staleness_us: int,
    cursor: FeedCursor | None = None,
    resync_indexes: frozenset[int] = frozenset(),
) -> ReplayResult:
    """Replay normalized observations locally without economic side effects.

    The caller supplies all replay times and explicit resync indexes. No wall
    clock, network, historical-run identity, candidate, order, or fill is
    created by this function.
    """

    if not isinstance(observations, tuple) or any(
        not isinstance(item, PublicObservation) for item in observations
    ):
        raise PublicFeedContractError(
            "FEED_REPLAY_INPUT_INVALID", "Replay yalnız PublicObservation tuple kabul eder."
        )
    if len(observations) > _MAX_REPLAY:
        raise PublicFeedContractError(
            "FEED_REPLAY_LIMIT_EXCEEDED", "Replay bounded observation sınırını aşıyor."
        )
    if not isinstance(now_times_us, tuple) or len(now_times_us) != len(observations):
        raise PublicFeedContractError(
            "FEED_REPLAY_TIME_INVALID", "Her observation için bir deterministic replay zamanı gerekir."
        )
    if not isinstance(resync_indexes, frozenset) or any(
        type(index) is not int or index < 0 or index >= len(observations)
        for index in resync_indexes
    ):
        raise PublicFeedContractError(
            "FEED_REPLAY_RESYNC_INVALID", "Resync indexleri replay sınırları içinde integer olmalıdır."
        )
    current = new_feed_cursor() if cursor is None else cursor
    if not isinstance(current, FeedCursor):
        raise PublicFeedContractError("FEED_CURSOR_INVALID", "Feed cursor geçersiz.")
    outcomes: list[ObservationOutcome] = []
    for index, (item, now_time_us) in enumerate(zip(observations, now_times_us)):
        decision = accept_observation(
            current,
            item,
            now_time_us=now_time_us,
            max_staleness_us=max_staleness_us,
            resync=index in resync_indexes,
        )
        current = decision.cursor
        outcomes.append(decision.outcome)
    return ReplayResult(
        cursor=current,
        outcomes=tuple(outcomes),
        accepted_count=outcomes.count(ObservationOutcome.ACCEPTED),
    )


def accept_observation(
    cursor: FeedCursor,
    observation: PublicObservation,
    *,
    now_time_us: int,
    max_staleness_us: int,
    resync: bool = False,
) -> ObservationResult:
    """Accept a contiguous observation or return a fail-closed gate outcome.

    ``now_time_us`` is supplied by the caller for deterministic replay. It is
    not read from the wall clock, and a source observation is never a fill.
    """

    if not isinstance(cursor, FeedCursor):
        raise PublicFeedContractError("FEED_CURSOR_INVALID", "Feed cursor geçersiz.")
    if not isinstance(observation, PublicObservation):
        raise PublicFeedContractError("FEED_OBSERVATION_INVALID", "Observation geçersiz.")
    _validate_nonnegative_integer(now_time_us, "FEED_NOW_TIME_INVALID")
    _validate_nonnegative_integer(max_staleness_us, "FEED_STALENESS_INVALID")
    prior = _find_event(cursor.accepted, observation.event_id)
    if prior is not None:
        if prior.immutable_key() == observation.immutable_key():
            return ObservationResult(cursor, ObservationOutcome.DUPLICATE)
        return ObservationResult(replace(cursor, state=FeedState.FAILED), ObservationOutcome.CONFLICT)
    if cursor.accepted and _scope(cursor.accepted[0]) != _scope(observation):
        return ObservationResult(replace(cursor, state=FeedState.FAILED), ObservationOutcome.WRONG_SCOPE)
    if cursor.state is FeedState.FAILED:
        return ObservationResult(cursor, ObservationOutcome.FAILED)
    if cursor.state in {FeedState.RECONNECTING, FeedState.GAP} and not resync:
        return ObservationResult(cursor, ObservationOutcome.RESYNC_REQUIRED)
    if now_time_us < observation.receive_time_us:
        return ObservationResult(replace(cursor, state=FeedState.FAILED), ObservationOutcome.STALE)
    if now_time_us - observation.receive_time_us > max_staleness_us:
        return ObservationResult(replace(cursor, state=FeedState.STALE), ObservationOutcome.STALE)
    if cursor.last_event_time_us is not None and observation.event_time_us < cursor.last_event_time_us:
        return ObservationResult(replace(cursor, state=FeedState.GAP), ObservationOutcome.OUT_OF_ORDER)
    if cursor.last_source_sequence is not None and not resync:
        if observation.source_sequence is None:
            return ObservationResult(replace(cursor, state=FeedState.GAP), ObservationOutcome.MISSING_SEQUENCE)
        if observation.source_sequence <= cursor.last_source_sequence:
            return ObservationResult(replace(cursor, state=FeedState.GAP), ObservationOutcome.OUT_OF_ORDER)
        if observation.source_sequence != cursor.last_source_sequence + 1:
            return ObservationResult(replace(cursor, state=FeedState.GAP), ObservationOutcome.SEQUENCE_GAP)
    if len(cursor.accepted) >= _MAX_ACCEPTED:
        return ObservationResult(replace(cursor, state=FeedState.FAILED), ObservationOutcome.CAPACITY_EXCEEDED)
    next_cursor = replace(
        cursor,
        state=FeedState.SYNCED,
        accepted=(*cursor.accepted, observation),
        last_event_time_us=observation.event_time_us,
        last_receive_time_us=observation.receive_time_us,
        last_source_sequence=observation.source_sequence,
    )
    return ObservationResult(next_cursor, ObservationOutcome.ACCEPTED)


def begin_reconnect(cursor: FeedCursor) -> FeedCursor:
    """Move a non-failed cursor to an explicit reconnect gate."""

    if not isinstance(cursor, FeedCursor):
        raise PublicFeedContractError("FEED_CURSOR_INVALID", "Feed cursor geçersiz.")
    if cursor.state is FeedState.FAILED:
        return cursor
    return replace(cursor, state=FeedState.RECONNECTING)


def assess_feed_state(cursor: FeedCursor, *, now_time_us: int, max_staleness_us: int) -> FeedState:
    """Classify an existing cursor using caller-provided deterministic time."""

    if not isinstance(cursor, FeedCursor):
        raise PublicFeedContractError("FEED_CURSOR_INVALID", "Feed cursor geçersiz.")
    _validate_nonnegative_integer(now_time_us, "FEED_NOW_TIME_INVALID")
    _validate_nonnegative_integer(max_staleness_us, "FEED_STALENESS_INVALID")
    if cursor.last_receive_time_us is None or cursor.state is not FeedState.SYNCED:
        return cursor.state
    if now_time_us - cursor.last_receive_time_us > max_staleness_us:
        return FeedState.STALE
    return FeedState.SYNCED


def _find_event(history: tuple[PublicObservation, ...], event_id: str) -> PublicObservation | None:
    return next((item for item in history if item.event_id == event_id), None)


def _scope(observation: PublicObservation) -> tuple[str, str, str, str, str]:
    return (
        observation.source_id,
        observation.transport,
        observation.symbol,
        observation.product,
        observation.stream_type,
    )


def _validate_identifier(value: str, code: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise PublicFeedContractError(code, "Feed kimlik alanı geçersiz.")


def _validate_nonnegative_integer(value: int, code: str) -> None:
    if type(value) is not int or value < 0:
        raise PublicFeedContractError(code, "Değer sıfır veya pozitif integer olmalıdır.")
