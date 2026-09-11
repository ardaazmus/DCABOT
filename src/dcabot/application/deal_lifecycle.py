"""Pure, non-economic lifecycle states for one future offline deal."""

from dataclasses import dataclass, replace
import re
from typing import Final


_IDENTIFIER = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)
_TRANSITIONS: Final = {
    ("DRAFT", "START"): "RUNNING",
    ("DRAFT", "ABORT"): "ABORTED",
    ("DRAFT", "FAIL"): "FAILED",
    ("RUNNING", "PAUSE"): "PAUSED",
    ("RUNNING", "COMPLETE"): "COMPLETED",
    ("RUNNING", "ABORT"): "ABORTED",
    ("RUNNING", "FAIL"): "FAILED",
    ("PAUSED", "RESUME"): "RUNNING",
    ("PAUSED", "ABORT"): "ABORTED",
    ("PAUSED", "FAIL"): "FAILED",
}


class DealLifecycleError(ValueError):
    """Raised when a non-economic deal lifecycle event is not admissible."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class DealLifecycle:
    """Immutable lifecycle projection that never mutates economic state."""

    deal_id: str
    config_revision_id: str
    status: str
    event_sequence: int


def new_deal_lifecycle(deal_id: str, config_revision_id: str) -> DealLifecycle:
    """Create a DRAFT deal bound to one immutable future config revision."""

    _validate_identifier(deal_id, "DEAL_ID_INVALID")
    _validate_identifier(config_revision_id, "CONFIG_REVISION_ID_INVALID")
    return DealLifecycle(
        deal_id=deal_id,
        config_revision_id=config_revision_id,
        status="DRAFT",
        event_sequence=0,
    )


def transition_deal_lifecycle(lifecycle: DealLifecycle, event: str) -> DealLifecycle:
    """Return the next lifecycle projection without producing economic events.

    ``START`` is an event, not a separate durable state. This intentionally
    avoids treating the report's STARTED/STARTING/ACTIVE naming variants as
    independent economic authorities before a persisted lifecycle contract
    exists.
    """

    if not isinstance(lifecycle, DealLifecycle):
        raise DealLifecycleError("LIFECYCLE_INVALID", "Lifecycle projection geçersiz.")
    if not isinstance(event, str):
        raise DealLifecycleError("LIFECYCLE_EVENT_INVALID", "Lifecycle olayı geçersiz.")
    target = _TRANSITIONS.get((lifecycle.status, event))
    if target is None:
        raise DealLifecycleError(
            "LIFECYCLE_TRANSITION_INVALID",
            "Lifecycle olayı mevcut durum için kabul edilemez.",
        )
    return replace(lifecycle, status=target, event_sequence=lifecycle.event_sequence + 1)


def copy_deal_lifecycle(
    source: DealLifecycle,
    *,
    new_deal_id: str,
    new_config_revision_id: str,
) -> DealLifecycle:
    """Create a distinct DRAFT projection without mutating the source deal.

    The caller supplies a previously created config-revision identity. This
    projection layer neither persists nor manufactures a config snapshot.
    """

    if not isinstance(source, DealLifecycle):
        raise DealLifecycleError("LIFECYCLE_INVALID", "Kaynak lifecycle geçersiz.")
    _validate_identifier(new_deal_id, "DEAL_ID_INVALID")
    _validate_identifier(new_config_revision_id, "CONFIG_REVISION_ID_INVALID")
    if new_deal_id == source.deal_id:
        raise DealLifecycleError(
            "COPY_DEAL_ID_REUSED", "Kopya deal kimliği kaynak deal ile aynı olamaz."
        )
    if new_config_revision_id == source.config_revision_id:
        raise DealLifecycleError(
            "COPY_CONFIG_REVISION_ID_REUSED",
            "Kopya config revision kimliği kaynak revision ile aynı olamaz.",
        )
    return new_deal_lifecycle(new_deal_id, new_config_revision_id)


def _validate_identifier(value: str, code: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise DealLifecycleError(code, "Lifecycle kimliği geçersiz.")
