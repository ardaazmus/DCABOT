"""Bounded in-memory trial registry that preserves failed and invalid attempts."""

from dataclasses import dataclass
import re


_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z", re.ASCII)
_STATUSES = ("SUCCEEDED", "FAILED", "INVALID")
_MAX_TRIALS = 1_000


class TrialRegistryError(ValueError):
    """Raised when a study or trial would lose evaluation lineage."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class TrialStatus:
    """Stable outcomes counted by a study, including non-winning attempts."""

    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    INVALID = "INVALID"


@dataclass(frozen=True, slots=True)
class TrialRecord:
    """One bounded trial outcome without parameters or economic result data."""

    trial_id: str
    status: str

    def __post_init__(self) -> None:
        _validate_identifier(self.trial_id, "TRIAL_ID_INVALID")
        if type(self.status) is not str or self.status not in _STATUSES:
            raise TrialRegistryError("TRIAL_STATUS_INVALID", "Trial status geçersiz.")


@dataclass(frozen=True, slots=True)
class TrialStudy:
    """Immutable study manifest whose count includes failed and invalid trials."""

    study_id: str
    parameter_space_id: str
    objective_id: str
    selection_rule_id: str
    max_trials: int = _MAX_TRIALS
    trials: tuple[TrialRecord, ...] = ()

    def __post_init__(self) -> None:
        _validate_identifier(self.study_id, "TRIAL_STUDY_ID_INVALID")
        _validate_identifier(self.parameter_space_id, "TRIAL_PARAMETER_SPACE_INVALID")
        _validate_identifier(self.objective_id, "TRIAL_OBJECTIVE_INVALID")
        _validate_identifier(self.selection_rule_id, "TRIAL_SELECTION_RULE_INVALID")
        if type(self.max_trials) is not int or not 1 <= self.max_trials <= _MAX_TRIALS:
            raise TrialRegistryError(
                "TRIAL_LIMIT_INVALID", "max_trials 1 ile 1000 arasında integer olmalıdır."
            )
        if type(self.trials) is not tuple or not all(
            type(trial) is TrialRecord for trial in self.trials
        ):
            raise TrialRegistryError("TRIAL_HISTORY_INVALID", "Trial history geçersiz.")
        if len(self.trials) > self.max_trials:
            raise TrialRegistryError("TRIAL_LIMIT_EXCEEDED", "Trial limiti aşılmış.")
        ids = tuple(trial.trial_id for trial in self.trials)
        if len(set(ids)) != len(ids):
            raise TrialRegistryError("TRIAL_ID_DUPLICATE", "Trial identity tekrar edemez.")

    @property
    def trial_count(self) -> int:
        """Return every recorded attempt count, not only successful attempts."""

        return len(self.trials)


@dataclass(frozen=True, slots=True)
class TrialRegistration:
    """Registration outcome that exposes no winner-selection authority."""

    study: TrialStudy
    outcome: str


def new_trial_study(
    study_id: str,
    *,
    parameter_space_id: str,
    objective_id: str,
    selection_rule_id: str,
    max_trials: int = _MAX_TRIALS,
) -> TrialStudy:
    """Create a bounded manifest without running or selecting a trial."""

    return TrialStudy(
        study_id=study_id,
        parameter_space_id=parameter_space_id,
        objective_id=objective_id,
        selection_rule_id=selection_rule_id,
        max_trials=max_trials,
    )


def register_trial(
    study: TrialStudy, trial: TrialRecord
) -> tuple[TrialStudy, str]:
    """Append one attempt or return DUPLICATE; never drops failed attempts."""

    if type(study) is not TrialStudy:
        raise TrialRegistryError("TRIAL_STUDY_INVALID", "Trial study geçersiz.")
    if type(trial) is not TrialRecord:
        raise TrialRegistryError("TRIAL_INVALID", "Trial kaydı geçersiz.")
    for prior in study.trials:
        if prior.trial_id == trial.trial_id:
            if prior == trial:
                return study, "DUPLICATE"
            raise TrialRegistryError(
                "TRIAL_ID_CONFLICT", "Aynı trial identity farklı status ile kullanılamaz."
            )
    if study.trial_count >= study.max_trials:
        raise TrialRegistryError("TRIAL_LIMIT_EXCEEDED", "Trial limiti dolu.")
    return (
        TrialStudy(
            study_id=study.study_id,
            parameter_space_id=study.parameter_space_id,
            objective_id=study.objective_id,
            selection_rule_id=study.selection_rule_id,
            max_trials=study.max_trials,
            trials=(*study.trials, trial),
        ),
        "ACCEPTED",
    )


def _validate_identifier(value: object, code: str) -> None:
    if type(value) is not str or _IDENTIFIER.fullmatch(value) is None:
        raise TrialRegistryError(code, "Kimlik değeri geçersiz.")
