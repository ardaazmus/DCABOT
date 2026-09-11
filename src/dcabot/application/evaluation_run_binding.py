"""Bounded binding of P1.16 evaluation lineage to an existing run capture."""

from dataclasses import dataclass, replace
import hashlib
import re

from dcabot.application.historical_run_contract import (
    HistoricalRunCapture,
    canonical_json,
)
from dcabot.application.oos_lineage import EvaluationLineage, OosStatus
from dcabot.application.stress_lineage import StressLineage
from dcabot.application.trial_registry import TrialRecord, TrialStatus, TrialStudy


_HASH = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z", re.ASCII)
_SCHEMA_VERSION = 1


class EvaluationRunBindingError(ValueError):
    """Raised when evaluation lineage cannot be bound without ambiguity."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class EvaluationRunBinding:
    """Immutable non-economic identity joining a trial/OOS decision to one run."""

    schema_version: int
    run_identity_sha256: str
    result_sha256: str
    canonical_input_sha256: str
    config_hash: str
    study_id: str
    trial_id: str
    trial_status: str
    oos_experiment_id: str
    oos_status: str
    stress_profile_id: str | None
    stress_profile_hash: str | None
    stress_result_id: str | None
    binding_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != _SCHEMA_VERSION:
            raise EvaluationRunBindingError("RUN_BINDING_SCHEMA_INVALID", "Binding schema sürümü desteklenmiyor.")
        for value, code in (
            (self.run_identity_sha256, "RUN_IDENTITY_HASH_INVALID"),
            (self.result_sha256, "RUN_RESULT_HASH_INVALID"),
            (self.canonical_input_sha256, "RUN_INPUT_HASH_INVALID"),
            (self.config_hash, "RUN_CONFIG_HASH_INVALID"),
            (self.binding_sha256, "RUN_BINDING_HASH_INVALID"),
        ):
            _validate_hash(value, code)
        for value, code in (
            (self.study_id, "RUN_STUDY_ID_INVALID"),
            (self.trial_id, "RUN_TRIAL_ID_INVALID"),
            (self.oos_experiment_id, "RUN_OOS_EXPERIMENT_ID_INVALID"),
        ):
            _validate_identifier(value, code)
        if self.trial_status not in (
            TrialStatus.SUCCEEDED,
            TrialStatus.FAILED,
            TrialStatus.INVALID,
        ):
            raise EvaluationRunBindingError("RUN_TRIAL_STATUS_INVALID", "Trial status geçersiz.")
        if self.oos_status not in (
            OosStatus.OOS_UNTOUCHED,
            OosStatus.OOS_INSPECTED,
            OosStatus.TOUCHED,
        ):
            raise EvaluationRunBindingError("RUN_OOS_STATUS_INVALID", "OOS status geçersiz.")
        if self.stress_profile_id is None:
            if self.stress_profile_hash is not None or self.stress_result_id is not None:
                raise EvaluationRunBindingError(
                    "RUN_STRESS_FIELDS_INCOMPLETE",
                    "Stress alanları birlikte bulunmalıdır.",
                )
        else:
            _validate_identifier(self.stress_profile_id, "RUN_STRESS_PROFILE_ID_INVALID")
            if not isinstance(self.stress_profile_hash, str) or _HASH.fullmatch(self.stress_profile_hash) is None:
                raise EvaluationRunBindingError(
                    "RUN_STRESS_PROFILE_HASH_INVALID",
                    "Stress profile hash geçersiz.",
                )
            _validate_identifier(self.stress_result_id, "RUN_STRESS_RESULT_ID_INVALID")
        if _sha256(canonical_json(_binding_payload(self))) != self.binding_sha256:
            raise EvaluationRunBindingError(
                "RUN_BINDING_HASH_MISMATCH",
                "Binding checksum canonical payload ile eşleşmiyor.",
            )


def bind_historical_run(
    capture: HistoricalRunCapture,
    *,
    study: TrialStudy,
    trial: TrialRecord,
    oos_lineage: EvaluationLineage,
    stress_lineage: StressLineage | None,
) -> EvaluationRunBinding:
    """Bind existing capture identity to registered trial/OOS/stress metadata."""

    if not isinstance(capture, HistoricalRunCapture):
        raise EvaluationRunBindingError("RUN_CAPTURE_INVALID", "Historical run capture geçersiz.")
    if not isinstance(study, TrialStudy) or not isinstance(trial, TrialRecord):
        raise EvaluationRunBindingError("RUN_TRIAL_INPUT_INVALID", "Trial study veya kaydı geçersiz.")
    if not isinstance(oos_lineage, EvaluationLineage):
        raise EvaluationRunBindingError("RUN_OOS_INPUT_INVALID", "OOS lineage geçersiz.")
    if stress_lineage is not None and not isinstance(stress_lineage, StressLineage):
        raise EvaluationRunBindingError("RUN_STRESS_INPUT_INVALID", "Stress lineage geçersiz.")
    if trial not in study.trials:
        raise EvaluationRunBindingError(
            "TRIAL_NOT_REGISTERED",
            "Trial aynı study registry içinde kayıtlı değil.",
        )
    if stress_lineage is not None and stress_lineage.base_result_id != capture.result_sha256:
        raise EvaluationRunBindingError(
            "STRESS_BASE_RESULT_MISMATCH",
            "Stress lineage base result capture sonucu ile eşleşmiyor.",
        )

    stress_profile_id = stress_lineage.stress_profile_id if stress_lineage else None
    stress_profile_hash = stress_lineage.stress_profile_hash if stress_lineage else None
    stress_result_id = stress_lineage.stress_result_id if stress_lineage else None
    payload = {
        "schema_version": _SCHEMA_VERSION,
        "run_identity_sha256": capture.execution.identity_sha256,
        "result_sha256": capture.result_sha256,
        "canonical_input_sha256": capture.canonical_input_sha256,
        "config_hash": capture.config_hash,
        "study_id": study.study_id,
        "trial_id": trial.trial_id,
        "trial_status": trial.status,
        "oos_experiment_id": oos_lineage.experiment_id,
        "oos_status": oos_lineage.status,
        "stress_profile_id": stress_profile_id,
        "stress_profile_hash": stress_profile_hash,
        "stress_result_id": stress_result_id,
    }
    return EvaluationRunBinding(**payload, binding_sha256=_sha256(canonical_json(payload)))


def attach_run_binding(
    capture: HistoricalRunCapture, binding: EvaluationRunBinding
) -> HistoricalRunCapture:
    """Attach validated lineage JSON to a capture without changing economics."""

    if not isinstance(capture, HistoricalRunCapture):
        raise EvaluationRunBindingError("RUN_CAPTURE_INVALID", "Historical run capture geçersiz.")
    if not isinstance(binding, EvaluationRunBinding):
        raise EvaluationRunBindingError("RUN_BINDING_INVALID", "Evaluation run binding geçersiz.")
    if (
        binding.run_identity_sha256 != capture.execution.identity_sha256
        or binding.result_sha256 != capture.result_sha256
        or binding.canonical_input_sha256 != capture.canonical_input_sha256
        or binding.config_hash != capture.config_hash
    ):
        raise EvaluationRunBindingError(
            "RUN_BINDING_CAPTURE_MISMATCH",
            "Binding mevcut capture identity alanlarıyla eşleşmiyor.",
        )
    payload = _binding_payload(binding)
    serialized = canonical_json({**payload, "binding_sha256": binding.binding_sha256})
    return replace(
        capture,
        evaluation_binding_json=serialized,
        evaluation_binding_sha256=binding.binding_sha256,
        evaluation_binding=binding,
    )


def _binding_payload(binding: EvaluationRunBinding) -> dict[str, object]:
    return {
        "schema_version": _SCHEMA_VERSION,
        "run_identity_sha256": binding.run_identity_sha256,
        "result_sha256": binding.result_sha256,
        "canonical_input_sha256": binding.canonical_input_sha256,
        "config_hash": binding.config_hash,
        "study_id": binding.study_id,
        "trial_id": binding.trial_id,
        "trial_status": binding.trial_status,
        "oos_experiment_id": binding.oos_experiment_id,
        "oos_status": binding.oos_status,
        "stress_profile_id": binding.stress_profile_id,
        "stress_profile_hash": binding.stress_profile_hash,
        "stress_result_id": binding.stress_result_id,
    }


def _validate_hash(value: object, code: str) -> None:
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise EvaluationRunBindingError(code, "SHA-256 identity geçersiz.")


def _validate_identifier(value: object, code: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise EvaluationRunBindingError(code, "Kimlik değeri geçersiz.")


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
