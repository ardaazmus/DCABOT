"""Bind accepted public observations to per-symbol market marks.

Each feed scope (source/transport/symbol/product/stream) replays through its
own bounded cursor, so one mixed batch can carry several symbols without
WRONG_SCOPE failures. Marks always come from ACCEPTED observations only.
"""

from dataclasses import dataclass

from dcabot.data_adapters.public_feed import (
    FeedCursor,
    ObservationOutcome,
    PublicObservation,
    new_feed_cursor,
    replay_observations,
)


@dataclass(frozen=True, slots=True)
class MarketMark:
    """Latest accepted print for one symbol; display and fill reference only."""

    symbol: str
    price: str
    event_id: str
    event_time_us: int


@dataclass(frozen=True, slots=True)
class PaperMarketState:
    """Immutable per-scope cursors plus canonical per-symbol marks."""

    cursors: tuple[tuple[str, FeedCursor], ...]
    marks: tuple[MarketMark, ...]


def new_market_state() -> PaperMarketState:
    """Create an empty market state without contacting any source."""

    return PaperMarketState(cursors=(), marks=())


def apply_observations(
    state: PaperMarketState,
    observations: tuple[PublicObservation, ...],
    *,
    now_times_us: tuple[int, ...],
    max_staleness_us: int,
) -> tuple[PaperMarketState, tuple[ObservationOutcome, ...]]:
    """Replay one mixed batch and refresh marks from ACCEPTED prints only."""

    if not isinstance(state, PaperMarketState):
        raise ValueError("PAPER_BINDING_STATE_INVALID: Market state geçersiz.")
    if not isinstance(observations, tuple) or any(
        not isinstance(item, PublicObservation) for item in observations
    ):
        raise ValueError("PAPER_BINDING_INPUT_INVALID: Observation tuple geçersiz.")
    if not isinstance(now_times_us, tuple) or len(now_times_us) != len(observations):
        raise ValueError(
            "PAPER_BINDING_TIME_INVALID: Her observation için bir replay zamanı gerekir."
        )

    cursors = dict(state.cursors)
    marks = {mark.symbol: mark for mark in state.marks}
    outcomes: list[ObservationOutcome | None] = [None] * len(observations)
    by_scope: dict[str, list[int]] = {}
    for index, item in enumerate(observations):
        by_scope.setdefault(_scope_key(item), []).append(index)
    for key in sorted(by_scope):
        indexes = by_scope[key]
        result = replay_observations(
            tuple(observations[i] for i in indexes),
            now_times_us=tuple(now_times_us[i] for i in indexes),
            max_staleness_us=max_staleness_us,
            cursor=cursors.get(key, new_feed_cursor()),
        )
        cursors[key] = result.cursor
        for position, index in enumerate(indexes):
            outcomes[index] = result.outcomes[position]
            if result.outcomes[position] is ObservationOutcome.ACCEPTED:
                item = observations[index]
                prior = marks.get(item.symbol)
                if prior is None or item.event_time_us >= prior.event_time_us:
                    marks[item.symbol] = MarketMark(
                        symbol=item.symbol,
                        price=item.price,
                        event_id=item.event_id,
                        event_time_us=item.event_time_us,
                    )
    final = tuple(outcome for outcome in outcomes if outcome is not None)
    assert len(final) == len(observations)
    return (
        PaperMarketState(
            cursors=tuple(sorted(cursors.items())),
            marks=tuple(marks[symbol] for symbol in sorted(marks)),
        ),
        final,
    )


def _scope_key(item: PublicObservation) -> str:
    return "|".join(
        (item.source_id, item.transport, item.symbol, item.product, item.stream_type)
    )
