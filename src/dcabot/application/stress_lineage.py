"""Separate, deterministic identity for stress scenarios without economic authority."""

from dataclasses import dataclass
import hashlib
import re


_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,100}\Z", re.ASCII)
_PROFILE_HASH = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)


class StressLineageError(ValueError):
    """Raised when a stress result could be confused with its base result."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class StressLineage:
    """Immutable stress identity that cannot overwrite the normal result identity."""

    base_result_id: str
    stress_profile_id: str
    stress_profile_hash: str
    stress_result_id: str
    label: str = "STRESS"

    def __post_init__(self) -> None:
        _validate_identifier(self.base_result_id, "STRESS_BASE_RESULT_ID_INVALID")
        _validate_identifier(self.stress_profile_id, "STRESS_PROFILE_ID_INVALID")
        if _PROFILE_HASH.fullmatch(self.stress_profile_hash) is None:
            raise StressLineageError(
                "STRESS_PROFILE_HASH_INVALID",
                "Stress profile hash SHA-256 hexadecimal değer olmalıdır.",
            )
        _validate_identifier(self.stress_result_id, "STRESS_RESULT_ID_INVALID")
        if self.stress_result_id == self.base_result_id:
            raise StressLineageError(
                "STRESS_IDENTITY_CONFLICT",
                "Stress sonucu base result kimliğini kullanamaz.",
            )
        if self.label != "STRESS":
            raise StressLineageError("STRESS_LABEL_INVALID", "Stress etiketi sabittir.")


def new_stress_lineage(
    base_result_id: str,
    *,
    stress_profile_id: str,
    stress_profile_hash: str,
) -> StressLineage:
    """Derive a deterministic non-economic identity for a separate stress result."""

    _validate_identifier(base_result_id, "STRESS_BASE_RESULT_ID_INVALID")
    _validate_identifier(stress_profile_id, "STRESS_PROFILE_ID_INVALID")
    if _PROFILE_HASH.fullmatch(stress_profile_hash) is None:
        raise StressLineageError(
            "STRESS_PROFILE_HASH_INVALID",
            "Stress profile hash SHA-256 hexadecimal değer olmalıdır.",
        )

    canonical = "|".join(
        ("stress-lineage-v1", base_result_id, stress_profile_id, stress_profile_hash)
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    stress_result_id = f"stress-v1:{digest}"
    if stress_result_id == base_result_id:
        raise StressLineageError(
            "STRESS_IDENTITY_CONFLICT",
            "Stress sonucu base result kimliğini kullanamaz.",
        )
    return StressLineage(
        base_result_id=base_result_id,
        stress_profile_id=stress_profile_id,
        stress_profile_hash=stress_profile_hash,
        stress_result_id=stress_result_id,
    )


def _validate_identifier(value: object, code: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise StressLineageError(code, "Kimlik değeri geçersiz.")
