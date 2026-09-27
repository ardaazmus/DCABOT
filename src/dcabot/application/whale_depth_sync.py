"""Faz 17 E.3: official spot @depth local-order-book sync state machine.

Algorithm (verified 2026-09-22 against developers.binance.com; spot has
NO `pu` field, unlike futures -- see `data_adapters/binance_public_depth.py`
module docstring for the correction against the original brief):
  1. Buffer WS events while a REST snapshot is fetched.
  2. On snapshot arrival, discard buffered events with `u <= lastUpdateId`.
  3. The first surviving event must satisfy `U <= lastUpdateId+1 <= u`;
     otherwise a gap was already missed (GAP_DETECTED).
  4. Thereafter: `u < local_last_id` -> stale, ignore; `U > local_last_id+1`
     -> gap, GAP_DETECTED; else merge and advance `local_last_id = u`.
A GAP_DETECTED book requires a fresh `apply_snapshot()` to resync -- this
module never silently repairs a gap.
"""

from dataclasses import dataclass, field
from typing import Literal

from dcabot.data_adapters.binance_public_depth import DepthDiffEvent, DepthSnapshot
from dcabot.domain.numbers import number

SyncState = Literal["SYNCING", "IN_SYNC", "GAP_DETECTED"]


class WhaleDepthSyncError(ValueError):
    """Raised when depth events cannot be applied honestly."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(slots=True)
class DepthBookSync:
    """One symbol's local order book, synced per the official U/u algorithm."""

    symbol: str | None = None
    state: SyncState = field(default="SYNCING", init=False)
    bids: dict[str, str] = field(default_factory=dict, init=False)
    asks: dict[str, str] = field(default_factory=dict, init=False)
    _last_id: int | None = field(default=None, init=False)
    _snapshot_applied: bool = field(default=False, init=False)
    _buffer: list[DepthDiffEvent] = field(default_factory=list, init=False)

    def apply_snapshot(self, snapshot: DepthSnapshot) -> SyncState:
        """Adopt a fresh REST snapshot as the sync anchor; replays any
        events buffered before this call (or since the last gap)."""

        if not isinstance(snapshot, DepthSnapshot):
            raise WhaleDepthSyncError("WHALE_SYNC_SNAPSHOT_INVALID", "Snapshot geçersiz.")
        self.bids = {price: qty for price, qty in snapshot.bids}
        self.asks = {price: qty for price, qty in snapshot.asks}
        self._last_id = snapshot.last_update_id
        self._snapshot_applied = True
        self.state = "SYNCING"
        pending, self._buffer = self._buffer, []
        for event in pending:
            if self.state == "GAP_DETECTED":
                break
            self._apply(event)
        return self.state

    def apply_event(self, event: DepthDiffEvent) -> SyncState:
        """Feed one WS diff event; buffers it if no snapshot has landed yet."""

        if not isinstance(event, DepthDiffEvent):
            raise WhaleDepthSyncError("WHALE_SYNC_EVENT_INVALID", "Event geçersiz.")
        if self.symbol is not None and event.symbol != self.symbol:
            raise WhaleDepthSyncError(
                "WHALE_SYNC_SYMBOL_MISMATCH", "Event başka bir symbol'e ait."
            )
        if not self._snapshot_applied:
            self._buffer.append(event)
            return self.state
        if self.state == "GAP_DETECTED":
            # A gapped book only recovers via a fresh apply_snapshot(); until
            # then, further events are noise, not silently re-applied.
            return self.state
        self._apply(event)
        return self.state

    def _apply(self, event: DepthDiffEvent) -> None:
        assert self._last_id is not None
        if event.final_update_id <= self._last_id:
            return  # stale, already covered by the current anchor
        if self.state == "SYNCING":
            if not (event.first_update_id <= self._last_id + 1 <= event.final_update_id):
                self.state = "GAP_DETECTED"
                return
        else:
            if event.first_update_id > self._last_id + 1:
                self.state = "GAP_DETECTED"
                return
        self._merge(event)
        self._last_id = event.final_update_id
        self.state = "IN_SYNC"

    def _merge(self, event: DepthDiffEvent) -> None:
        for side_book, levels in ((self.bids, event.bids), (self.asks, event.asks)):
            for price, qty in levels:
                if number(qty) == 0:
                    side_book.pop(price, None)
                else:
                    side_book[price] = qty
