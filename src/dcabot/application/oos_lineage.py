"""In-memory OOS inspection freeze boundary without run or economic authority."""

from dataclasses import dataclass
import re


_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z", re.ASCII)


class OosLineageError(ValueError):
    """Raised when an OOS lineage transition would hide evaluation reuse."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class OosStatus:
    """Stable labels for the minimal OOS inspection boundary."""

    OOS_UNTOUCHED = "OOS_UNTOUCHED"
    OOS_INSPECTED = "OOS_INSPECTED"
    TOUCHED = "TOUCHED"


_STATUSES = (
    OosStatus.OOS_UNTOUCHED,
    OosStatus.OOS_INSPECTED,
    OosStatus.TOUCHED,
)


@dataclass(frozen=True, slots=True)
class EvaluationLineage:
    """Immutable status for one experiment's OOS segment."""

    experiment_id: str
    status: str = OosStatus.OOS_UNTOUCHED

    def __post_init__(self) -> None:
        if not isinstance(self.experiment_id, str) or _IDENTIFIER.fullmatch(self.experiment_id) is None:
            raise OosLineageError(
                "OOS_EXPERIMENT_ID_INVALID", "Experiment identity geçersiz."
            )
        if self.status not in _STATUSES:
            raise OosLineageError("OOS_STATUS_INVALID", "OOS status geçersiz.")


@dataclass(frozen=True, slots=True)
class OosTuningDecision:
    """Decision and resulting old-lineage status after a tuning request."""

    lineage: EvaluationLineage
    outcome: str

    def __post_init__(self) -> None:
        if not isinstance(self.lineage, EvaluationLineage):
            raise OosLineageError("OOS_LINEAGE_INVALID", "Evaluation lineage geçersiz.")
        if self.outcome not in ("TUNING_ALLOWED", "NEW_EXPERIMENT_REQUIRED"):
            raise OosLineageError("OOS_OUTCOME_INVALID", "OOS tuning kararı geçersiz.")


def new_evaluation_lineage(experiment_id: str) -> EvaluationLineage:
    """Start a lineage before its OOS result has been inspected."""

    return EvaluationLineage(experiment_id=experiment_id)


def inspect_oos(lineage: EvaluationLineage) -> EvaluationLineage:
    """Mark OOS as inspected; a touched lineage can never become untouched."""

    _validate_lineage(lineage)
    if lineage.status == OosStatus.OOS_UNTOUCHED:
        return EvaluationLineage(lineage.experiment_id, OosStatus.OOS_INSPECTED)
    if lineage.status == OosStatus.OOS_INSPECTED:
        return lineage
    raise OosLineageError(
        "OOS_LINEAGE_TRANSITION_INVALID",
        "TOUCHED lineage yeniden untouched/inspected yapılamaz.",
    )


def request_tuning(lineage: EvaluationLineage) -> OosTuningDecision:
    """Allow pre-inspection tuning or mark inspected OOS as reused."""

    _validate_lineage(lineage)
    if lineage.status == OosStatus.OOS_UNTOUCHED:
        return OosTuningDecision(lineage=lineage, outcome="TUNING_ALLOWED")
    if lineage.status == OosStatus.OOS_INSPECTED:
        return OosTuningDecision(
            lineage=EvaluationLineage(lineage.experiment_id, OosStatus.TOUCHED),
            outcome="NEW_EXPERIMENT_REQUIRED",
        )
    return OosTuningDecision(lineage=lineage, outcome="NEW_EXPERIMENT_REQUIRED")


def _validate_lineage(lineage: EvaluationLineage) -> None:
    if not isinstance(lineage, EvaluationLineage):
        raise OosLineageError("OOS_LINEAGE_INVALID", "Evaluation lineage geçersiz.")
