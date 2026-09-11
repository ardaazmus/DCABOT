"""Immutable, exact config snapshot identity for lifecycle binding."""

from dataclasses import dataclass
import hashlib
import json
import re

from dcabot.domain.config import Config


_IDENTIFIER = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)


class ConfigRevisionError(ValueError):
    """Raised when a config revision snapshot or identity is invalid."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class ConfigRevision:
    """Validated config snapshot identified by its canonical SHA-256."""

    revision_id: str
    snapshot_json: str
    snapshot_sha256: str

    def __post_init__(self) -> None:
        _validate_identifier(self.revision_id, "CONFIG_REVISION_ID_INVALID")
        if not isinstance(self.snapshot_json, str):
            raise ConfigRevisionError(
                "CONFIG_SNAPSHOT_INVALID", "Config snapshot metni geçersiz."
            )
        try:
            raw = json.loads(self.snapshot_json)
            if not isinstance(raw, dict) or _canonical_json(raw) != self.snapshot_json:
                raise ValueError("Config snapshot canonical değil")
            Config.parse(raw)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ConfigRevisionError(
                "CONFIG_SNAPSHOT_INVALID", "Config snapshot doğrulanamadı."
            ) from exc
        if not re.fullmatch(r"[0-9a-f]{64}", self.snapshot_sha256 or ""):
            raise ConfigRevisionError(
                "CONFIG_SNAPSHOT_HASH_INVALID", "Config snapshot hash geçersiz."
            )
        if _sha256(self.snapshot_json) != self.snapshot_sha256:
            raise ConfigRevisionError(
                "CONFIG_SNAPSHOT_HASH_MISMATCH", "Config snapshot hash ile eşleşmiyor."
            )


def new_config_revision(revision_id: str, raw_config: dict[str, object]) -> ConfigRevision:
    """Validate config and create its deterministic immutable snapshot identity."""

    _validate_identifier(revision_id, "CONFIG_REVISION_ID_INVALID")
    try:
        Config.parse(raw_config)
        snapshot_json = _canonical_json(raw_config)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ConfigRevisionError(
            "CONFIG_SNAPSHOT_INVALID", "Config snapshot oluşturulamadı."
        ) from exc
    return ConfigRevision(
        revision_id=revision_id,
        snapshot_json=snapshot_json,
        snapshot_sha256=_sha256(snapshot_json),
    )


def _canonical_json(value: dict[str, object]) -> str:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_identifier(value: str, code: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise ConfigRevisionError(code, "Config revision kimliği geçersiz.")
