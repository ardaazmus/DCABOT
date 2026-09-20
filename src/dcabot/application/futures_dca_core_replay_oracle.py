"""Read-only restart oracle for the durable Futures DCA CORE01 binding."""

from dataclasses import dataclass, replace
from pathlib import Path

from dcabot.domain.config import Config
from dcabot.domain.engine import State
from dcabot.application.futures_dca_core_mapping import (
    FuturesDcaCoreFillAdmission,
    FuturesDcaCoreFillReplayDecision,
    FuturesDcaCoreOrderMapping,
    FuturesDcaCoreReplayReceipt,
    FuturesDcaCoreReplayRetryDecision,
    assess_futures_dca_core_fill_replay,
    assess_futures_dca_core_replay_retry,
    build_futures_dca_core_replay_receipt,
)
from dcabot.persistence.futures_dca_core_replay_store import (
    load_futures_dca_core_replay_receipts,
)
from dcabot.persistence.futures_dca_journal_schema import (
    FuturesDcaEconomicPosting,
    FuturesDcaEventEnvelope,
    FuturesDcaJournalSchemaError,
    FuturesDcaReservationProjection,
    _normalize_event,
    _normalize_posting,
    _normalize_reservation,
    load_economic_postings,
    load_journal_events,
    load_reservation_projections,
)
from dcabot.persistence.futures_dca_release_store import load_futures_dca_release_transitions
from dcabot.persistence.futures_dca_release_transition import FuturesDcaReleaseTransition


@dataclass(frozen=True, slots=True)
class FuturesDcaCoreReplayRestartOracle:
    """Read-only equality result between durable rows and pure CORE01 replay."""

    status: str
    reason_code: str
    decision: FuturesDcaCoreFillReplayDecision | None = None
    receipt: FuturesDcaCoreReplayReceipt | None = None

    def __post_init__(self) -> None:
        if self.status not in {"READY", "BLOCKED"}:
            raise ValueError("Replay restart oracle status yalnız READY veya BLOCKED olabilir.")
        if self.status == "READY" and (
            self.decision is None or self.decision.status != "ACCEPTED" or self.receipt is None
        ):
            raise ValueError("READY replay oracle accepted decision ve receipt taşımalıdır.")
        if self.status == "BLOCKED" and any(
            value is not None for value in (self.decision, self.receipt)
        ):
            raise ValueError("BLOCKED replay oracle ekonomik projection taşıyamaz.")


def assess_futures_dca_core_replay_restart_oracle(
    path: Path,
    event: FuturesDcaEventEnvelope,
    posting: FuturesDcaEconomicPosting,
    transition: FuturesDcaReleaseTransition,
    reservation: FuturesDcaReservationProjection,
    mapping: FuturesDcaCoreOrderMapping,
    admission: FuturesDcaCoreFillAdmission,
    core_state: State,
    config: Config,
) -> FuturesDcaCoreReplayRestartOracle:
    """Compare pure replay output with durable rows and fail closed on corruption."""

    try:
        return _assess_futures_dca_core_replay_restart_oracle(
            path,
            event,
            posting,
            transition,
            reservation,
            mapping,
            admission,
            core_state,
            config,
        )
    except FuturesDcaJournalSchemaError:
        return FuturesDcaCoreReplayRestartOracle(
            "BLOCKED", "FUTURES_DCA_CORE_REPLAY_ORACLE_DURABLE_CORRUPT"
        )


def _assess_futures_dca_core_replay_restart_oracle(
    path: Path,
    event: FuturesDcaEventEnvelope,
    posting: FuturesDcaEconomicPosting,
    transition: FuturesDcaReleaseTransition,
    reservation: FuturesDcaReservationProjection,
    mapping: FuturesDcaCoreOrderMapping,
    admission: FuturesDcaCoreFillAdmission,
    core_state: State,
    config: Config,
) -> FuturesDcaCoreReplayRestartOracle:
    normalized_event = _normalize_event(event)
    normalized_posting = _normalize_posting(posting)
    normalized_reservation = _normalize_reservation(reservation)
    durable_event = next(
        (item for item in load_journal_events(path) if item.event_id == normalized_event.event_id),
        None,
    )
    if durable_event is None:
        return FuturesDcaCoreReplayRestartOracle(
            "BLOCKED", "FUTURES_DCA_CORE_REPLAY_ORACLE_EVENT_MISSING"
        )
    if durable_event != normalized_event:
        return FuturesDcaCoreReplayRestartOracle(
            "BLOCKED", "FUTURES_DCA_CORE_REPLAY_ORACLE_EVENT_CONFLICT"
        )
    durable_posting = next(
        (item for item in load_economic_postings(path) if item.posting_id == normalized_posting.posting_id),
        None,
    )
    if durable_posting is None:
        return FuturesDcaCoreReplayRestartOracle(
            "BLOCKED", "FUTURES_DCA_CORE_REPLAY_ORACLE_POSTING_MISSING"
        )
    if durable_posting != normalized_posting:
        return FuturesDcaCoreReplayRestartOracle(
            "BLOCKED", "FUTURES_DCA_CORE_REPLAY_ORACLE_POSTING_CONFLICT"
        )
    durable_release = next(
        (
            item.transition
            for item in load_futures_dca_release_transitions(path)
            if item.transition.release_identity == transition.release_identity
        ),
        None,
    )
    if durable_release is None:
        return FuturesDcaCoreReplayRestartOracle(
            "BLOCKED", "FUTURES_DCA_CORE_REPLAY_ORACLE_RELEASE_MISSING"
        )
    if durable_release != transition:
        return FuturesDcaCoreReplayRestartOracle(
            "BLOCKED", "FUTURES_DCA_CORE_REPLAY_ORACLE_RELEASE_CONFLICT"
        )

    decision = assess_futures_dca_core_fill_replay(
        normalized_event,
        normalized_posting,
        transition,
        normalized_reservation,
        mapping,
        admission,
        core_state,
        config,
    )
    if decision.status != "ACCEPTED":
        return FuturesDcaCoreReplayRestartOracle(
            "BLOCKED", decision.reason_code
        )
    durable_reservation = next(
        (
            item
            for item in load_reservation_projections(path)
            if item.reservation_id == normalized_reservation.reservation_id
        ),
        None,
    )
    if durable_reservation is None:
        return FuturesDcaCoreReplayRestartOracle(
            "BLOCKED", "FUTURES_DCA_CORE_REPLAY_ORACLE_RESERVATION_MISSING"
        )
    if durable_reservation != decision.reservation:
        return FuturesDcaCoreReplayRestartOracle(
            "BLOCKED", "FUTURES_DCA_CORE_REPLAY_ORACLE_RESERVATION_CONFLICT"
        )
    expected_receipt = build_futures_dca_core_replay_receipt(
        normalized_event,
        normalized_posting,
        transition,
        mapping,
        decision,
    )
    duplicate_decision = assess_futures_dca_core_fill_replay(
        normalized_event,
        normalized_posting,
        transition,
        decision.reservation,
        mapping,
        admission,
        core_state,
        config,
    )
    if duplicate_decision != FuturesDcaCoreFillReplayDecision(
        mapping.mapping_id,
        "DUPLICATE",
        "FUTURES_DCA_CORE_REPLAY_DUPLICATE",
    ):
        return FuturesDcaCoreReplayRestartOracle(
            "BLOCKED", "FUTURES_DCA_CORE_REPLAY_ORACLE_DUPLICATE_BOUNDARY"
        )
    retry_decision = assess_futures_dca_core_replay_retry(
        expected_receipt,
        normalized_event,
        normalized_posting,
        transition,
        mapping,
    )
    if retry_decision != FuturesDcaCoreReplayRetryDecision(
        "DUPLICATE", "FUTURES_DCA_CORE_REPLAY_DUPLICATE"
    ):
        return FuturesDcaCoreReplayRestartOracle(
            "BLOCKED", "FUTURES_DCA_CORE_REPLAY_ORACLE_DUPLICATE_BOUNDARY"
        )
    conflict_decision = assess_futures_dca_core_replay_retry(
        expected_receipt,
        normalized_event,
        replace(normalized_posting, commitment="41"),
        transition,
        mapping,
    )
    if conflict_decision != FuturesDcaCoreReplayRetryDecision(
        "BLOCKED", "FUTURES_DCA_CORE_REPLAY_CONFLICT"
    ):
        return FuturesDcaCoreReplayRestartOracle(
            "BLOCKED", "FUTURES_DCA_CORE_REPLAY_ORACLE_CONFLICT_BOUNDARY"
        )
    durable_receipts = load_futures_dca_core_replay_receipts(path)
    if expected_receipt in durable_receipts:
        return FuturesDcaCoreReplayRestartOracle(
            "READY",
            "FUTURES_DCA_CORE_REPLAY_ORACLE_READY",
            decision,
            expected_receipt,
        )
    same_scope = tuple(
        item
        for item in durable_receipts
        if (
            item.mapping_id,
            item.event_id,
            item.posting_id,
            item.transition_event_id,
            item.release_identity,
            item.release_cursor,
        )
        == (
            expected_receipt.mapping_id,
            expected_receipt.event_id,
            expected_receipt.posting_id,
            expected_receipt.transition_event_id,
            expected_receipt.release_identity,
            expected_receipt.release_cursor,
        )
    )
    if same_scope:
        return FuturesDcaCoreReplayRestartOracle(
            "BLOCKED", "FUTURES_DCA_CORE_REPLAY_ORACLE_RECEIPT_CONFLICT"
        )
    return FuturesDcaCoreReplayRestartOracle(
        "BLOCKED", "FUTURES_DCA_CORE_REPLAY_ORACLE_RECEIPT_MISSING"
    )
