"""Read-only preflight for the not-yet-implemented Futures DCA migration."""

from dataclasses import dataclass
import sqlite3
from typing import Literal

from dcabot.application.account_reservation_ledger import ReservationLedger
from dcabot.persistence.futures_dca_event_store import FuturesDcaEventStore


@dataclass(frozen=True, slots=True)
class FuturesDcaMigrationPreflight:
    """Describe whether the split local stores can satisfy the v1 journal contract."""

    status: Literal["READY", "NO_GO"]
    missing_fields: tuple[str, ...]
    observed_fields: tuple[str, ...]


_REQUIRED_FIELDS = frozenset(
    {
        "profile.venue",
        "profile.product",
        "profile.symbol",
        "profile.settlement_asset",
        "profile.margin_mode",
        "profile.position_mode",
        "profile.effective_time_us",
        "profile.revision_id",
        "profile.contract_size",
        "profile.fee_policy_revision",
        "profile.slippage_policy_revision",
        "profile.rounding_policy_revision",
        "event.event_id",
        "event.execution_id",
        "event.sequence_no",
        "event.order_id",
        "event.event_kind",
        "event.profile_revision_id",
        "event.observed_time_us",
        "event.execution_time_us",
        "execution.fill_quantity",
        "execution.effective_price",
        "execution.gross_commitment",
        "event.payload_hash",
        "execution.fee_amount",
        "execution.fee_asset",
        "execution.slippage_reference",
        "execution.rounding_policy_revision",
        "event.payload",
        "event.event_state",
        "reservation.reservation_id",
        "reservation.owner_scope",
        "reservation.asset",
        "reservation.reserved_amount",
        "reservation.consumed_amount",
        "reservation.releasable_amount",
        "reservation.release_identity",
        "reservation.terminal_state",
        "reservation.version",
        "reservation.source_event_id",
        "posting.posting_id",
        "posting.source_event_id",
        "posting.posting_cursor",
        "posting.commitment",
        "posting.fee_amount",
        "posting.funding_amount",
        "posting.posting_state",
        "posting.checksum",
    }
)


def inspect_futures_dca_migration_sources(
    event_store: FuturesDcaEventStore, reservation_ledger: ReservationLedger
) -> FuturesDcaMigrationPreflight:
    """Inspect existing stores without writing or opening a migration target."""

    if not isinstance(event_store, FuturesDcaEventStore):
        raise TypeError("event_store must be FuturesDcaEventStore")
    if not isinstance(reservation_ledger, ReservationLedger):
        raise TypeError("reservation_ledger must be ReservationLedger")

    observed = set()
    event_columns = _columns(event_store.db, "futures_dca_events")
    reservation_columns = _columns(reservation_ledger.db, "account_reservations")
    metadata_keys = {row[0] for row in event_store.db.execute("SELECT key FROM metadata")}

    observed.update(
        field
        for column, field in {
            "event_id": "event.event_id",
            "sequence_no": "event.sequence_no",
            "event_hash": "event.payload_hash",
        }.items()
        if column in event_columns
    )
    observed.update(
        field
        for key, field in {
            "venue": "profile.venue",
            "symbol": "profile.symbol",
            "effective_time_us": "profile.effective_time_us",
            "profile_revision_id": "profile.revision_id",
            "contract_size": "profile.contract_size",
        }.items()
        if key in metadata_keys
    )
    observed.update(
        field
        for column, field in {
            "reservation_id": "reservation.reservation_id",
            "account_id": "reservation.owner_scope",
            "amount": "reservation.reserved_amount",
        }.items()
        if column in reservation_columns
    )

    missing_fields = tuple(sorted(_REQUIRED_FIELDS - observed))
    return FuturesDcaMigrationPreflight(
        status="READY" if not missing_fields else "NO_GO",
        missing_fields=missing_fields,
        observed_fields=tuple(sorted(observed)),
    )


def _columns(db: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in db.execute(f"PRAGMA table_info({table})")}
