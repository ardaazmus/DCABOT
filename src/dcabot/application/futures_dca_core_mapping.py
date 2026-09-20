"""Explicit, non-economic Futures DCA to CORE01 mapping contract."""

from dataclasses import dataclass
import hashlib
import json
import re

from dcabot.domain.numbers import align, exact_text, number, positive
from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply
from dcabot.persistence.futures_dca_journal_schema import (
    FuturesDcaEconomicPosting,
    FuturesDcaEventEnvelope,
    FuturesDcaReservationProjection,
    _normalize_event,
    _normalize_posting,
    _normalize_reservation,
)
from dcabot.persistence.futures_dca_release_transition import (
    FuturesDcaReleaseTransition,
    FuturesDcaReleaseTransitionError,
    apply_futures_dca_release_transition,
)


_IDENTIFIER = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)
_ROLE = re.compile(r"(?:BASE|EXIT|STOP|SAFETY:[1-9][0-9]*)\Z", re.ASCII)


class FuturesDcaCoreMappingError(ValueError):
    """Raised when an explicit Futures DCA to CORE01 mapping is unsafe."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class FuturesDcaCoreOrderMapping:
    """Immutable candidate; it carries no CORE01 mutation or order authority."""

    mapping_id: str
    event_id: str
    posting_id: str
    profile_revision_id: str
    core_order_id: str
    core_order_intent_id: str
    role: str
    side: str
    limit_price: str
    status: str = "CANDIDATE"

    def __post_init__(self) -> None:
        for value, code in (
            (self.mapping_id, "FUTURES_DCA_CORE_MAPPING_ID_INVALID"),
            (self.event_id, "FUTURES_DCA_CORE_MAPPING_EVENT_ID_INVALID"),
            (self.posting_id, "FUTURES_DCA_CORE_MAPPING_POSTING_ID_INVALID"),
            (self.profile_revision_id, "FUTURES_DCA_CORE_MAPPING_PROFILE_INVALID"),
            (self.core_order_id, "FUTURES_DCA_CORE_ORDER_ID_INVALID"),
            (self.core_order_intent_id, "FUTURES_DCA_CORE_INTENT_ID_INVALID"),
        ):
            if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
                raise FuturesDcaCoreMappingError(code, "CORE mapping kimliği güvenli biçimde saklanamaz.")
        if self.status != "CANDIDATE":
            raise FuturesDcaCoreMappingError(
                "FUTURES_DCA_CORE_MAPPING_STATUS_INVALID", "Mapping yalnız CANDIDATE olabilir."
            )
        if self.side not in {"BUY", "SELL"} or not isinstance(self.role, str) or _ROLE.fullmatch(self.role) is None:
            raise FuturesDcaCoreMappingError(
                "FUTURES_DCA_CORE_MAPPING_SCOPE_INVALID", "CORE mapping side veya role geçersiz."
            )
        try:
            if exact_text(positive(self.limit_price)) != self.limit_price:
                raise ValueError
        except (TypeError, ValueError) as exc:
            raise FuturesDcaCoreMappingError(
                "FUTURES_DCA_CORE_MAPPING_PRICE_INVALID", "CORE mapping limit exact olmalıdır."
            ) from exc


@dataclass(frozen=True, slots=True)
class FuturesDcaCoreAdmissionOracle:
    """Read-only admission result; it never promotes a mapping candidate."""

    mapping_id: str
    status: str
    missing_authority: tuple[str, ...]
    reason_code: str

    def __post_init__(self) -> None:
        if self.status not in {"ADMISSIBLE", "BLOCKED"}:
            raise FuturesDcaCoreMappingError(
                "FUTURES_DCA_CORE_ADMISSION_STATUS_INVALID",
                "Admission oracle yalnız ADMISSIBLE veya BLOCKED döndürebilir.",
            )
        if not isinstance(self.missing_authority, tuple) or any(
            not isinstance(item, str) for item in self.missing_authority
        ):
            raise FuturesDcaCoreMappingError(
                "FUTURES_DCA_CORE_ADMISSION_AUTHORITY_INVALID",
                "Admission eksik authority tuple olmalıdır.",
            )


@dataclass(frozen=True, slots=True)
class FuturesDcaCoreFillAdmission:
    """Read-only CORE01 FILL boundary decision and immutable event proposal."""

    mapping_id: str
    status: str
    missing_authority: tuple[str, ...]
    reason_code: str
    core_fill_event: tuple[tuple[str, str], ...] | None = None

    def __post_init__(self) -> None:
        if self.status not in {"ADMISSIBLE", "BLOCKED"}:
            raise FuturesDcaCoreMappingError(
                "FUTURES_DCA_CORE_FILL_STATUS_INVALID",
                "Fill admission yalnız ADMISSIBLE veya BLOCKED döndürebilir.",
            )
        if not isinstance(self.missing_authority, tuple) or any(
            not isinstance(item, str) for item in self.missing_authority
        ):
            raise FuturesDcaCoreMappingError(
                "FUTURES_DCA_CORE_FILL_AUTHORITY_INVALID",
                "Fill admission eksik authority tuple olmalıdır.",
            )
        if self.status == "ADMISSIBLE" and self.core_fill_event is None:
            raise FuturesDcaCoreMappingError(
                "FUTURES_DCA_CORE_FILL_EVENT_MISSING",
                "Admissible fill kararı immutable CORE event taşımalıdır.",
            )
        if self.status == "BLOCKED" and self.core_fill_event is not None:
            raise FuturesDcaCoreMappingError(
                "FUTURES_DCA_CORE_FILL_EVENT_UNEXPECTED",
                "Blocked fill kararı CORE event taşıyamaz.",
            )


@dataclass(frozen=True, slots=True)
class FuturesDcaCoreFillProjection:
    """Offline reducer projection; it carries no durable or venue authority."""

    mapping_id: str
    status: str
    reason_code: str
    projected_state: State | None = None

    def __post_init__(self) -> None:
        if self.status not in {"PROJECTED", "BLOCKED"}:
            raise FuturesDcaCoreMappingError(
                "FUTURES_DCA_CORE_PROJECTION_STATUS_INVALID",
                "Projection yalnız PROJECTED veya BLOCKED döndürebilir.",
            )
        if self.status == "PROJECTED" and self.projected_state is None:
            raise FuturesDcaCoreMappingError(
                "FUTURES_DCA_CORE_PROJECTION_STATE_MISSING",
                "Projected sonuç CORE01 state taşımalıdır.",
            )
        if self.status == "BLOCKED" and self.projected_state is not None:
            raise FuturesDcaCoreMappingError(
                "FUTURES_DCA_CORE_PROJECTION_STATE_UNEXPECTED",
                "Blocked projection CORE01 state taşıyamaz.",
            )


@dataclass(frozen=True, slots=True)
class FuturesDcaCoreFillReplayDecision:
    """Read-only decision joining CORE01, release, and posting identities."""

    mapping_id: str
    status: str
    reason_code: str
    core_state: State | None = None
    reservation: FuturesDcaReservationProjection | None = None
    posting_id: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"ACCEPTED", "DUPLICATE", "BLOCKED"}:
            raise FuturesDcaCoreMappingError(
                "FUTURES_DCA_CORE_REPLAY_STATUS_INVALID",
                "Replay kararı yalnız ACCEPTED, DUPLICATE veya BLOCKED olabilir.",
            )
        if self.status == "ACCEPTED" and (
            self.core_state is None or self.reservation is None or self.posting_id is None
        ):
            raise FuturesDcaCoreMappingError(
                "FUTURES_DCA_CORE_REPLAY_RESULT_MISSING",
                "Accepted replay kararı CORE state, reservation ve posting taşımalıdır.",
            )
        if self.status != "ACCEPTED" and any(
            value is not None for value in (self.core_state, self.reservation, self.posting_id)
        ):
            raise FuturesDcaCoreMappingError(
                "FUTURES_DCA_CORE_REPLAY_RESULT_UNEXPECTED",
                "Accepted olmayan replay kararı ekonomik projection taşıyamaz.",
            )


@dataclass(frozen=True, slots=True)
class FuturesDcaCoreReplayReceipt:
    """Bounded in-memory replay identity; it is not a durable Store record."""

    mapping_id: str
    event_id: str
    posting_id: str
    transition_event_id: str
    release_identity: str
    release_cursor: int
    fingerprint: str

    def __post_init__(self) -> None:
        for value, code in (
            (self.mapping_id, "FUTURES_DCA_CORE_RECEIPT_MAPPING_INVALID"),
            (self.event_id, "FUTURES_DCA_CORE_RECEIPT_EVENT_INVALID"),
            (self.posting_id, "FUTURES_DCA_CORE_RECEIPT_POSTING_INVALID"),
            (self.transition_event_id, "FUTURES_DCA_CORE_RECEIPT_TRANSITION_INVALID"),
            (self.release_identity, "FUTURES_DCA_CORE_RECEIPT_RELEASE_INVALID"),
        ):
            if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
                raise FuturesDcaCoreMappingError(code, "Replay receipt identity geçersiz.")
        if type(self.release_cursor) is not int or self.release_cursor < 1:
            raise FuturesDcaCoreMappingError(
                "FUTURES_DCA_CORE_RECEIPT_CURSOR_INVALID", "Replay receipt cursor pozitif olmalıdır."
            )
        if not isinstance(self.fingerprint, str) or re.fullmatch(r"[0-9a-f]{64}", self.fingerprint) is None:
            raise FuturesDcaCoreMappingError(
                "FUTURES_DCA_CORE_RECEIPT_FINGERPRINT_INVALID", "Replay receipt fingerprint geçersiz."
            )


@dataclass(frozen=True, slots=True)
class FuturesDcaCoreReplayRetryDecision:
    """Pure retry result for exact duplicate or conflicting replay input."""

    status: str
    reason_code: str

    def __post_init__(self) -> None:
        if self.status not in {"DUPLICATE", "BLOCKED"}:
            raise FuturesDcaCoreMappingError(
                "FUTURES_DCA_CORE_RETRY_STATUS_INVALID",
                "Retry kararı yalnız DUPLICATE veya BLOCKED olabilir.",
            )


def assess_futures_dca_core_mapping_admission(
    candidate: FuturesDcaCoreOrderMapping, core_state: State
) -> FuturesDcaCoreAdmissionOracle:
    """Check current CORE01 order scope without applying an event or mutation."""

    if not isinstance(candidate, FuturesDcaCoreOrderMapping):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_ADMISSION_MAPPING_INVALID", "Mapping candidate güvenli tipte olmalıdır."
        )
    if not isinstance(core_state, State):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_ADMISSION_STATE_INVALID", "CORE01 state güvenli tipte olmalıdır."
        )
    order = core_state.orders.get(candidate.core_order_id)
    if order is None:
        return FuturesDcaCoreAdmissionOracle(
            candidate.mapping_id,
            "BLOCKED",
            ("core_order",),
            "FUTURES_DCA_CORE_ORDER_NOT_FOUND",
        )
    if (
        order.order_id != candidate.core_order_id
        or order.role != candidate.role
        or order.side != candidate.side
        or order.limit != number(candidate.limit_price)
    ):
        return FuturesDcaCoreAdmissionOracle(
            candidate.mapping_id,
            "BLOCKED",
            (),
            "FUTURES_DCA_CORE_ORDER_SCOPE_CONFLICT",
        )
    if order.intent_id is None:
        return FuturesDcaCoreAdmissionOracle(
            candidate.mapping_id,
            "BLOCKED",
            ("core_order_intent",),
            "FUTURES_DCA_CORE_INTENT_SCOPE_UNREPRESENTED",
        )
    if order.intent_id != candidate.core_order_intent_id:
        return FuturesDcaCoreAdmissionOracle(
            candidate.mapping_id,
            "BLOCKED",
            (),
            "FUTURES_DCA_CORE_INTENT_ID_CONFLICT",
        )
    return FuturesDcaCoreAdmissionOracle(
        candidate.mapping_id, "ADMISSIBLE", (), "FUTURES_DCA_CORE_ADMISSION_READY"
    )


def assess_futures_dca_core_fill_admission(
    event: FuturesDcaEventEnvelope,
    posting: FuturesDcaEconomicPosting,
    mapping: FuturesDcaCoreOrderMapping,
    core_state: State,
    config: Config,
) -> FuturesDcaCoreFillAdmission:
    """Prepare a CORE01 FILL proposal without applying economics or persistence."""

    if not isinstance(event, FuturesDcaEventEnvelope) or not isinstance(
        posting, FuturesDcaEconomicPosting
    ):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_FILL_INPUT_INVALID", "Event ve posting güvenli tipte olmalıdır."
        )
    if not isinstance(mapping, FuturesDcaCoreOrderMapping):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_FILL_MAPPING_INVALID", "Mapping candidate güvenli tipte olmalıdır."
        )
    if not isinstance(core_state, State):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_FILL_STATE_INVALID", "CORE01 state güvenli tipte olmalıdır."
        )
    if not isinstance(config, Config):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_FILL_CONFIG_INVALID", "CORE01 config güvenli tipte olmalıdır."
        )
    event = _normalize_event(event)
    posting = _normalize_posting(posting)

    checks = (
        (mapping.event_id == event.event_id, "FUTURES_DCA_CORE_FILL_EVENT_ID_CONFLICT"),
        (mapping.posting_id == posting.posting_id, "FUTURES_DCA_CORE_FILL_POSTING_ID_CONFLICT"),
        (mapping.profile_revision_id == event.profile_revision_id, "FUTURES_DCA_CORE_FILL_PROFILE_CONFLICT"),
        (event.event_state == "ACCEPTED", "FUTURES_DCA_CORE_FILL_EVENT_NOT_ACCEPTED"),
        (event.event_kind == "FILL", "FUTURES_DCA_CORE_FILL_KIND_UNSUPPORTED"),
        (posting.source_event_id == event.event_id, "FUTURES_DCA_CORE_FILL_SOURCE_CONFLICT"),
        (posting.commitment == event.gross_commitment, "FUTURES_DCA_CORE_FILL_COMMITMENT_CONFLICT"),
        (posting.fee_amount == event.fee_amount, "FUTURES_DCA_CORE_FILL_FEE_CONFLICT"),
        (posting.funding_amount == "0", "FUTURES_DCA_CORE_FILL_FUNDING_UNREPRESENTED"),
        (posting.posting_state == "PROJECTED", "FUTURES_DCA_CORE_FILL_POSTING_NOT_PROJECTED"),
        (event.fee_asset == config.quote_asset, "FUTURES_DCA_CORE_FILL_FEE_ASSET_CONFLICT"),
        (
            number(event.gross_commitment)
            == number(event.fill_quantity) * number(event.effective_price),
            "FUTURES_DCA_CORE_FILL_COMMITMENT_UNREPRESENTED",
        ),
    )
    for valid, reason_code in checks:
        if not valid:
            return FuturesDcaCoreFillAdmission(mapping.mapping_id, "BLOCKED", (), reason_code)

    mapping_admission = assess_futures_dca_core_mapping_admission(mapping, core_state)
    if mapping_admission.status == "BLOCKED":
        return FuturesDcaCoreFillAdmission(
            mapping.mapping_id,
            "BLOCKED",
            mapping_admission.missing_authority,
            mapping_admission.reason_code,
        )
    order = core_state.orders[mapping.core_order_id]
    quantity = number(event.fill_quantity)
    price = number(event.effective_price)
    if order.complete:
        return FuturesDcaCoreFillAdmission(
            mapping.mapping_id, "BLOCKED", (), "FUTURES_DCA_CORE_ORDER_TERMINAL"
        )
    if order.status == "UNKNOWN":
        return FuturesDcaCoreFillAdmission(
            mapping.mapping_id, "BLOCKED", (), "FUTURES_DCA_CORE_ORDER_STATUS_UNSAFE"
        )
    if order.filled + quantity > order.qty:
        return FuturesDcaCoreFillAdmission(
            mapping.mapping_id, "BLOCKED", (), "FUTURES_DCA_CORE_FILL_OVERFILL"
        )
    if (
        align(quantity, config.qty_step, up=False) != quantity
        or align(price, config.tick, up=False) != price
    ):
        return FuturesDcaCoreFillAdmission(
            mapping.mapping_id, "BLOCKED", (), "FUTURES_DCA_CORE_FILL_OFF_GRID"
        )
    core_fill_event = (
        ("type", "FILL"),
        ("execution_id", event.execution_id),
        ("order_id", mapping.core_order_id),
        ("side", mapping.side),
        ("qty", event.fill_quantity),
        ("price", event.effective_price),
        ("fee", event.fee_amount),
        ("fee_asset", event.fee_asset),
    )
    return FuturesDcaCoreFillAdmission(
        mapping.mapping_id,
        "ADMISSIBLE",
        (),
        "FUTURES_DCA_CORE_FILL_ADMISSION_READY",
        core_fill_event,
    )


def project_futures_dca_core_fill(
    admission: FuturesDcaCoreFillAdmission, core_state: State, config: Config
) -> FuturesDcaCoreFillProjection:
    """Apply an admitted FILL only to a copied CORE01 state for offline proof."""

    if not isinstance(admission, FuturesDcaCoreFillAdmission):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_PROJECTION_ADMISSION_INVALID",
            "Fill admission güvenli tipte olmalıdır.",
        )
    if not isinstance(core_state, State):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_PROJECTION_STATE_INVALID", "CORE01 state güvenli tipte olmalıdır."
        )
    if not isinstance(config, Config):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_PROJECTION_CONFIG_INVALID", "CORE01 config güvenli tipte olmalıdır."
        )
    if admission.status == "BLOCKED":
        return FuturesDcaCoreFillProjection(
            admission.mapping_id, "BLOCKED", admission.reason_code
        )
    proposal = admission.core_fill_event
    if proposal is None or len(proposal) != 8 or any(
        not isinstance(pair, tuple) or len(pair) != 2 or any(not isinstance(value, str) for value in pair)
        for pair in proposal
    ) or len({pair[0] for pair in proposal}) != len(proposal):
        return FuturesDcaCoreFillProjection(
            admission.mapping_id, "BLOCKED", "FUTURES_DCA_CORE_FILL_PROPOSAL_INVALID"
        )
    event = dict(proposal)
    if set(event) != {
        "type", "execution_id", "order_id", "side", "qty", "price", "fee", "fee_asset"
    }:
        return FuturesDcaCoreFillProjection(
            admission.mapping_id, "BLOCKED", "FUTURES_DCA_CORE_FILL_PROPOSAL_INVALID"
        )
    try:
        projected_state = apply(core_state, event, config)
    except (TypeError, ValueError):
        return FuturesDcaCoreFillProjection(
            admission.mapping_id, "BLOCKED", "FUTURES_DCA_CORE_FILL_REDUCER_REJECTED"
        )
    return FuturesDcaCoreFillProjection(
        admission.mapping_id,
        "PROJECTED",
        "FUTURES_DCA_CORE_FILL_REDUCER_PROJECTED",
        projected_state,
    )


def assess_futures_dca_core_fill_replay(
    event: FuturesDcaEventEnvelope,
    posting: FuturesDcaEconomicPosting,
    transition: FuturesDcaReleaseTransition,
    reservation: FuturesDcaReservationProjection,
    mapping: FuturesDcaCoreOrderMapping,
    admission: FuturesDcaCoreFillAdmission,
    core_state: State,
    config: Config,
) -> FuturesDcaCoreFillReplayDecision:
    """Join pure CORE01 and release projections without durable mutation."""

    if not isinstance(transition, FuturesDcaReleaseTransition):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_REPLAY_TRANSITION_INVALID", "Release transition güvenli tipte olmalıdır."
        )
    if not isinstance(reservation, FuturesDcaReservationProjection):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_REPLAY_RESERVATION_INVALID", "Reservation projection güvenli tipte olmalıdır."
        )
    if not isinstance(mapping, FuturesDcaCoreOrderMapping):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_REPLAY_MAPPING_INVALID", "Mapping candidate güvenli tipte olmalıdır."
        )
    if not isinstance(admission, FuturesDcaCoreFillAdmission):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_REPLAY_ADMISSION_INVALID", "Fill admission güvenli tipte olmalıdır."
        )
    normalized_event = _normalize_event(event)
    normalized_posting = _normalize_posting(posting)
    normalized_reservation = _normalize_reservation(reservation)
    checks = (
        (normalized_event.event_state == "ACCEPTED", "FUTURES_DCA_CORE_REPLAY_EVENT_NOT_ACCEPTED"),
        (normalized_event.event_kind == "FILL", "FUTURES_DCA_CORE_REPLAY_KIND_UNSUPPORTED"),
        (transition.transition_event_id == normalized_event.event_id, "FUTURES_DCA_CORE_REPLAY_EVENT_CONFLICT"),
        (transition.transition_kind in {"PARTIAL_FILL", "FULL_FILL"}, "FUTURES_DCA_CORE_REPLAY_TRANSITION_INVALID"),
        (transition.reservation_id == normalized_reservation.reservation_id, "FUTURES_DCA_CORE_REPLAY_RESERVATION_CONFLICT"),
        (normalized_posting.source_event_id == normalized_event.event_id, "FUTURES_DCA_CORE_REPLAY_POSTING_SOURCE_CONFLICT"),
        (normalized_posting.commitment == normalized_event.gross_commitment, "FUTURES_DCA_CORE_REPLAY_COMMITMENT_CONFLICT"),
        (normalized_posting.fee_amount == normalized_event.fee_amount, "FUTURES_DCA_CORE_REPLAY_FEE_CONFLICT"),
    )
    for valid, reason_code in checks:
        if not valid:
            return FuturesDcaCoreFillReplayDecision(mapping.mapping_id, "BLOCKED", reason_code)
    current_admission = assess_futures_dca_core_fill_admission(
        normalized_event, normalized_posting, mapping, core_state, config
    )
    if current_admission != admission:
        return FuturesDcaCoreFillReplayDecision(
            mapping.mapping_id, "BLOCKED", "FUTURES_DCA_CORE_REPLAY_ADMISSION_STALE"
        )
    if admission.status == "BLOCKED":
        return FuturesDcaCoreFillReplayDecision(
            mapping.mapping_id, "BLOCKED", admission.reason_code
        )
    try:
        projected_reservation, release_result = apply_futures_dca_release_transition(
            normalized_reservation, transition
        )
    except FuturesDcaReleaseTransitionError:
        return FuturesDcaCoreFillReplayDecision(
            mapping.mapping_id, "BLOCKED", "FUTURES_DCA_CORE_REPLAY_RELEASE_REJECTED"
        )
    if release_result == "DUPLICATE":
        return FuturesDcaCoreFillReplayDecision(
            mapping.mapping_id, "DUPLICATE", "FUTURES_DCA_CORE_REPLAY_DUPLICATE"
        )
    if number(projected_reservation.consumed_amount) - number(
        normalized_reservation.consumed_amount
    ) != number(normalized_event.gross_commitment):
        return FuturesDcaCoreFillReplayDecision(
            mapping.mapping_id, "BLOCKED", "FUTURES_DCA_CORE_REPLAY_AMOUNT_CONFLICT"
        )
    core_projection = project_futures_dca_core_fill(admission, core_state, config)
    if core_projection.status == "BLOCKED":
        return FuturesDcaCoreFillReplayDecision(
            mapping.mapping_id, "BLOCKED", core_projection.reason_code
        )
    return FuturesDcaCoreFillReplayDecision(
        mapping.mapping_id,
        "ACCEPTED",
        "FUTURES_DCA_CORE_REPLAY_READY",
        core_projection.projected_state,
        projected_reservation,
        normalized_posting.posting_id,
    )


def build_futures_dca_core_replay_receipt(
    event: FuturesDcaEventEnvelope,
    posting: FuturesDcaEconomicPosting,
    transition: FuturesDcaReleaseTransition,
    mapping: FuturesDcaCoreOrderMapping,
    decision: FuturesDcaCoreFillReplayDecision,
) -> FuturesDcaCoreReplayReceipt:
    """Create a bounded in-memory identity for one accepted replay decision."""

    if not isinstance(mapping, FuturesDcaCoreOrderMapping):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_RECEIPT_MAPPING_INVALID", "Mapping candidate güvenli tipte olmalıdır."
        )
    if not isinstance(decision, FuturesDcaCoreFillReplayDecision):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_RECEIPT_DECISION_INVALID", "Replay kararı güvenli tipte olmalıdır."
        )
    normalized_event = _normalize_event(event)
    normalized_posting = _normalize_posting(posting)
    normalized_transition = transition
    if not isinstance(normalized_transition, FuturesDcaReleaseTransition):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_RECEIPT_TRANSITION_INVALID", "Release transition güvenli tipte olmalıdır."
        )
    if decision.status != "ACCEPTED" or decision.mapping_id != mapping.mapping_id:
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_RECEIPT_NOT_ACCEPTED", "Receipt yalnız accepted replay kararıyla üretilebilir."
        )
    if (
        mapping.event_id != normalized_event.event_id
        or mapping.posting_id != normalized_posting.posting_id
        or normalized_transition.transition_event_id != normalized_event.event_id
    ):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_RECEIPT_SCOPE_CONFLICT", "Receipt identity bileşenleri eşleşmiyor."
        )
    fingerprint = _futures_dca_core_replay_fingerprint(
        normalized_event, normalized_posting, normalized_transition, mapping
    )
    return FuturesDcaCoreReplayReceipt(
        mapping.mapping_id,
        normalized_event.event_id,
        normalized_posting.posting_id,
        normalized_transition.transition_event_id,
        normalized_transition.release_identity,
        normalized_transition.release_cursor,
        fingerprint,
    )


def assess_futures_dca_core_replay_retry(
    receipt: FuturesDcaCoreReplayReceipt,
    event: FuturesDcaEventEnvelope,
    posting: FuturesDcaEconomicPosting,
    transition: FuturesDcaReleaseTransition,
    mapping: FuturesDcaCoreOrderMapping,
) -> FuturesDcaCoreReplayRetryDecision:
    """Compare a retry with one accepted receipt without replaying economics."""

    if not isinstance(receipt, FuturesDcaCoreReplayReceipt):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_RETRY_RECEIPT_INVALID", "Replay receipt güvenli tipte olmalıdır."
        )
    if not isinstance(mapping, FuturesDcaCoreOrderMapping):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_RETRY_MAPPING_INVALID", "Mapping candidate güvenli tipte olmalıdır."
        )
    normalized_event = _normalize_event(event)
    normalized_posting = _normalize_posting(posting)
    if not isinstance(transition, FuturesDcaReleaseTransition):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_RETRY_TRANSITION_INVALID", "Release transition güvenli tipte olmalıdır."
        )
    same_scope = (
        receipt.mapping_id == mapping.mapping_id
        and receipt.event_id == normalized_event.event_id
        and receipt.posting_id == normalized_posting.posting_id
        and receipt.transition_event_id == transition.transition_event_id
        and receipt.release_identity == transition.release_identity
        and receipt.release_cursor == transition.release_cursor
    )
    if not same_scope:
        return FuturesDcaCoreReplayRetryDecision(
            "BLOCKED", "FUTURES_DCA_CORE_REPLAY_SCOPE_CONFLICT"
        )
    fingerprint = _futures_dca_core_replay_fingerprint(
        normalized_event, normalized_posting, transition, mapping
    )
    if fingerprint == receipt.fingerprint:
        return FuturesDcaCoreReplayRetryDecision(
            "DUPLICATE", "FUTURES_DCA_CORE_REPLAY_DUPLICATE"
        )
    return FuturesDcaCoreReplayRetryDecision(
        "BLOCKED", "FUTURES_DCA_CORE_REPLAY_CONFLICT"
    )


def _futures_dca_core_replay_fingerprint(
    event: FuturesDcaEventEnvelope,
    posting: FuturesDcaEconomicPosting,
    transition: FuturesDcaReleaseTransition,
    mapping: FuturesDcaCoreOrderMapping,
) -> str:
    payload = {
        "event": {
            "event_id": event.event_id,
            "sequence_no": event.sequence_no,
            "execution_id": event.execution_id,
            "order_id": event.order_id,
            "event_kind": event.event_kind,
            "profile_revision_id": event.profile_revision_id,
            "observed_time_us": event.observed_time_us,
            "execution_time_us": event.execution_time_us,
            "fill_quantity": event.fill_quantity,
            "effective_price": event.effective_price,
            "gross_commitment": event.gross_commitment,
            "fee_amount": event.fee_amount,
            "fee_asset": event.fee_asset,
            "slippage_reference": event.slippage_reference,
            "rounding_policy_revision": event.rounding_policy_revision,
            "payload": event.payload,
            "event_state": event.event_state,
        },
        "posting": {
            "posting_id": posting.posting_id,
            "source_event_id": posting.source_event_id,
            "posting_cursor": posting.posting_cursor,
            "commitment": posting.commitment,
            "fee_amount": posting.fee_amount,
            "funding_amount": posting.funding_amount,
            "posting_state": posting.posting_state,
        },
        "transition": {
            "reservation_id": transition.reservation_id,
            "transition_event_id": transition.transition_event_id,
            "release_identity": transition.release_identity,
            "release_cursor": transition.release_cursor,
            "expected_version": transition.expected_version,
            "transition_kind": transition.transition_kind,
            "consumed_amount": transition.consumed_amount,
            "releasable_amount": transition.releasable_amount,
        },
        "mapping": {
            "mapping_id": mapping.mapping_id,
            "event_id": mapping.event_id,
            "posting_id": mapping.posting_id,
            "profile_revision_id": mapping.profile_revision_id,
            "core_order_id": mapping.core_order_id,
            "core_order_intent_id": mapping.core_order_intent_id,
            "role": mapping.role,
            "side": mapping.side,
            "limit_price": mapping.limit_price,
            "status": mapping.status,
        },
    }
    canonical = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_futures_dca_core_mapping_candidate(
    event: FuturesDcaEventEnvelope,
    posting: FuturesDcaEconomicPosting,
    *,
    mapping_id: str,
    profile_revision_id: str,
    core_order_id: str,
    core_order_intent_id: str,
    role: str,
    side: str,
    limit_price: str,
) -> FuturesDcaCoreOrderMapping:
    """Validate explicit mapping facts without applying a CORE01 event."""

    if not isinstance(event, FuturesDcaEventEnvelope) or not isinstance(
        posting, FuturesDcaEconomicPosting
    ):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_MAPPING_INVALID", "Event ve posting güvenli tipte olmalıdır."
        )
    event = _normalize_event(event)
    posting = _normalize_posting(posting)
    for value, code in (
        (mapping_id, "FUTURES_DCA_CORE_MAPPING_ID_INVALID"),
        (profile_revision_id, "FUTURES_DCA_CORE_MAPPING_PROFILE_INVALID"),
        (core_order_id, "FUTURES_DCA_CORE_ORDER_ID_INVALID"),
        (core_order_intent_id, "FUTURES_DCA_CORE_INTENT_ID_INVALID"),
    ):
        if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
            raise FuturesDcaCoreMappingError(code, "CORE mapping kimliği güvenli biçimde saklanamaz.")
    if event.event_state != "ACCEPTED":
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_MAPPING_EVENT_NOT_ACCEPTED", "Mapping yalnız ACCEPTED event ile oluşturulabilir."
        )
    if posting.source_event_id != event.event_id:
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_MAPPING_SOURCE_MISMATCH", "Posting source event ile mapping event eşleşmelidir."
        )
    if posting.commitment != event.gross_commitment or posting.fee_amount != event.fee_amount:
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_MAPPING_ECONOMIC_MISMATCH", "Posting commitment ve fee event ile eşleşmelidir."
        )
    if profile_revision_id != event.profile_revision_id:
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_MAPPING_PROFILE_MISMATCH", "Mapping profile revision event kapsamıyla eşleşmelidir."
        )
    if side not in {"BUY", "SELL"}:
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_MAPPING_SIDE_INVALID", "CORE mapping side BUY veya SELL olmalıdır."
        )
    if not isinstance(role, str) or _ROLE.fullmatch(role) is None:
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_MAPPING_ROLE_INVALID", "CORE mapping role desteklenen bir order rolü olmalıdır."
        )
    try:
        canonical_limit = exact_text(positive(limit_price))
        execution_price = number(event.effective_price)
    except (TypeError, ValueError) as exc:
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_MAPPING_PRICE_INVALID", "CORE mapping limit ve execution fiyatı exact olmalıdır."
        ) from exc
    if (side == "BUY" and execution_price > number(canonical_limit)) or (
        side == "SELL" and execution_price < number(canonical_limit)
    ):
        raise FuturesDcaCoreMappingError(
            "FUTURES_DCA_CORE_MAPPING_LIMIT_VIOLATION", "Execution fiyatı CORE order limit kuralını ihlal ediyor."
        )
    return FuturesDcaCoreOrderMapping(
        mapping_id,
        event.event_id,
        posting.posting_id,
        profile_revision_id,
        core_order_id,
        core_order_intent_id,
        role,
        side,
        canonical_limit,
    )
