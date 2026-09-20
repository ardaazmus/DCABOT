"""Offline identity and late-fill observation boundary for Futures DCA exits."""

from dataclasses import dataclass
import hashlib
import json
import re

from dcabot.application.futures_dca_exit_candidate import FuturesDcaExitCandidate
from dcabot.application.futures_dca_exit_priority import FuturesDcaExitTrigger
from dcabot.domain.numbers import exact_text, number, positive


class FuturesDcaExitIdentityError(ValueError):
    """Raised when a candidate identity or late-fill observation is unsafe."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class FuturesDcaExitCandidateIdentity:
    """Immutable candidate snapshot identity without execution authority."""

    selected_trigger: FuturesDcaExitTrigger
    trigger_price: str
    requested_qty: str
    remaining_capacity: str
    open_qty: str
    candidate_observed_at_ms: int
    candidate_identity_sha256: str
    order_authority: str = "NONE"

    def __post_init__(self) -> None:
        try:
            trigger = FuturesDcaExitTrigger(self.selected_trigger)
        except (TypeError, ValueError) as error:
            raise FuturesDcaExitIdentityError(
                "FUTURES_DCA_EXIT_IDENTITY_TRIGGER_INVALID",
                "Candidate identity geçerli exit trigger taşımalıdır.",
            ) from error
        if trigger is FuturesDcaExitTrigger.BREAKEVEN_ADJUSTMENT:
            raise FuturesDcaExitIdentityError(
                "FUTURES_DCA_EXIT_IDENTITY_TRIGGER_INVALID",
                "Breakeven adjustment close candidate identity’sine bağlanamaz.",
            )
        try:
            object.__setattr__(self, "selected_trigger", trigger)
            object.__setattr__(self, "trigger_price", exact_text(positive(self.trigger_price)))
            object.__setattr__(self, "requested_qty", exact_text(positive(self.requested_qty)))
            remaining_capacity = number(self.remaining_capacity)
            if remaining_capacity < 0:
                raise ValueError("Remaining capacity cannot be negative")
            object.__setattr__(self, "remaining_capacity", exact_text(remaining_capacity))
            object.__setattr__(self, "open_qty", exact_text(positive(self.open_qty)))
        except ValueError as error:
            raise FuturesDcaExitIdentityError(
                "FUTURES_DCA_EXIT_IDENTITY_NUMERIC_INVALID",
                "Candidate identity exact positive decimal alanlar taşımalıdır.",
            ) from error
        if type(self.candidate_observed_at_ms) is not int or self.candidate_observed_at_ms < 0:
            raise FuturesDcaExitIdentityError(
                "FUTURES_DCA_EXIT_IDENTITY_TIME_INVALID",
                "Candidate gözlem zamanı negatif olmayan integer olmalıdır.",
            )
        if not _HASH.fullmatch(self.candidate_identity_sha256):
            raise FuturesDcaExitIdentityError(
                "FUTURES_DCA_EXIT_IDENTITY_HASH_INVALID",
                "Candidate identity SHA-256 olmalıdır.",
            )
        if self.order_authority != "NONE":
            raise FuturesDcaExitIdentityError(
                "FUTURES_DCA_EXIT_IDENTITY_AUTHORITY_INVALID",
                "Candidate identity order authority taşıyamaz.",
            )
        if _identity_hash(self) != self.candidate_identity_sha256:
            raise FuturesDcaExitIdentityError(
                "FUTURES_DCA_EXIT_IDENTITY_TAMPERED",
                "Candidate identity payload hash ile eşleşmiyor.",
            )


@dataclass(frozen=True, slots=True)
class FuturesDcaLateFillObservation:
    """Observed late-fill evidence; it is not conditional execution or a fill post."""

    candidate_identity_sha256: str
    fill_event_id: str
    filled_qty: str
    fill_price: str
    observed_at_ms: int
    order_authority: str = "NONE"

    def __post_init__(self) -> None:
        if not _HASH.fullmatch(self.candidate_identity_sha256):
            raise FuturesDcaExitIdentityError(
                "FUTURES_DCA_LATE_FILL_IDENTITY_INVALID",
                "Late fill candidate identity geçersiz.",
            )
        if _IDENTIFIER.fullmatch(self.fill_event_id or "") is None:
            raise FuturesDcaExitIdentityError(
                "FUTURES_DCA_LATE_FILL_EVENT_INVALID",
                "Late fill event kimliği geçersiz.",
            )
        try:
            object.__setattr__(self, "filled_qty", exact_text(positive(self.filled_qty)))
            object.__setattr__(self, "fill_price", exact_text(positive(self.fill_price)))
        except ValueError as error:
            raise FuturesDcaExitIdentityError(
                "FUTURES_DCA_LATE_FILL_NUMERIC_INVALID",
                "Late fill miktarı ve fiyatı exact positive decimal olmalıdır.",
            ) from error
        if type(self.observed_at_ms) is not int or self.observed_at_ms < 0:
            raise FuturesDcaExitIdentityError(
                "FUTURES_DCA_LATE_FILL_TIME_INVALID",
                "Late fill gözlem zamanı negatif olmayan integer olmalıdır.",
            )
        if self.order_authority != "NONE":
            raise FuturesDcaExitIdentityError(
                "FUTURES_DCA_LATE_FILL_AUTHORITY_INVALID",
                "Late fill gözlemi order authority taşıyamaz.",
            )


def identify_futures_dca_exit_candidate(
    candidate: FuturesDcaExitCandidate,
    *,
    open_qty: str,
    candidate_observed_at_ms: int,
) -> FuturesDcaExitCandidateIdentity:
    """Create a deterministic identity for one immutable candidate snapshot."""

    if not isinstance(candidate, FuturesDcaExitCandidate):
        raise FuturesDcaExitIdentityError(
            "FUTURES_DCA_EXIT_IDENTITY_CANDIDATE_INVALID",
            "Candidate güvenli Futures DCA tipinde olmalıdır.",
        )
    try:
        normalized_open_qty = exact_text(positive(open_qty))
    except ValueError as error:
        raise FuturesDcaExitIdentityError(
            "FUTURES_DCA_EXIT_IDENTITY_OPEN_QTY_INVALID",
            "Candidate identity için açık miktar exact positive decimal olmalıdır.",
        ) from error
    if type(candidate_observed_at_ms) is not int or candidate_observed_at_ms < 0:
        raise FuturesDcaExitIdentityError(
            "FUTURES_DCA_EXIT_IDENTITY_TIME_INVALID",
            "Candidate gözlem zamanı negatif olmayan integer olmalıdır.",
        )
    payload = {
        "selected_trigger": candidate.selected_trigger.value,
        "trigger_price": candidate.trigger_price,
        "requested_qty": candidate.requested_qty,
        "remaining_capacity": candidate.remaining_capacity,
        "open_qty": normalized_open_qty,
        "candidate_observed_at_ms": candidate_observed_at_ms,
    }
    return FuturesDcaExitCandidateIdentity(
        selected_trigger=candidate.selected_trigger,
        trigger_price=candidate.trigger_price,
        requested_qty=candidate.requested_qty,
        remaining_capacity=candidate.remaining_capacity,
        open_qty=normalized_open_qty,
        candidate_observed_at_ms=candidate_observed_at_ms,
        candidate_identity_sha256=_sha256(_canonical(payload)),
    )


def observe_futures_dca_late_fill(
    identity: FuturesDcaExitCandidateIdentity,
    *,
    fill_event_id: str,
    filled_qty: str,
    fill_price: str,
    observed_at_ms: int,
) -> FuturesDcaLateFillObservation:
    """Record late-fill evidence without binding execution or economic posting."""

    if not isinstance(identity, FuturesDcaExitCandidateIdentity):
        raise FuturesDcaExitIdentityError(
            "FUTURES_DCA_LATE_FILL_IDENTITY_INVALID",
            "Late fill gözlemi candidate identity gerektirir.",
        )
    if type(observed_at_ms) is not int or observed_at_ms < identity.candidate_observed_at_ms:
        raise FuturesDcaExitIdentityError(
            "FUTURES_DCA_LATE_FILL_OUT_OF_ORDER",
            "Late fill gözlemi candidate snapshot’tan önce olamaz.",
        )
    try:
        quantity = positive(filled_qty)
        requested = positive(identity.requested_qty)
    except ValueError as error:
        raise FuturesDcaExitIdentityError(
            "FUTURES_DCA_LATE_FILL_NUMERIC_INVALID",
            "Late fill miktarı exact positive decimal olmalıdır.",
        ) from error
    if quantity > requested:
        raise FuturesDcaExitIdentityError(
            "FUTURES_DCA_LATE_FILL_OVER_REQUESTED",
            "Late fill miktarı candidate requested miktarını aşamaz.",
        )
    return FuturesDcaLateFillObservation(
        candidate_identity_sha256=identity.candidate_identity_sha256,
        fill_event_id=fill_event_id,
        filled_qty=exact_text(quantity),
        fill_price=fill_price,
        observed_at_ms=observed_at_ms,
    )


def _identity_hash(identity: FuturesDcaExitCandidateIdentity) -> str:
    return _sha256(
        _canonical(
            {
                "selected_trigger": identity.selected_trigger.value,
                "trigger_price": identity.trigger_price,
                "requested_qty": identity.requested_qty,
                "remaining_capacity": identity.remaining_capacity,
                "open_qty": identity.open_qty,
                "candidate_observed_at_ms": identity.candidate_observed_at_ms,
            }
        )
    )


def _canonical(value: dict[str, object]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


_HASH = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_IDENTIFIER = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)
