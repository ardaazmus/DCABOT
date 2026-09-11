"""Canonical inert strategy-template data before activation authority."""

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Final


_IDENTIFIER = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)
_SHA256 = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_SCHEMA: Final = "strategy-template-v1"
_MAX_PAYLOAD_BYTES: Final = 65_536
_FORBIDDEN_KEYS: Final = frozenset(
    {
        "api_key",
        "apikey",
        "command",
        "code",
        "credential",
        "credentials",
        "exec",
        "executable",
        "script",
        "secret",
        "token",
    }
)


class StrategyTemplateError(ValueError):
    """Raised when an imported template is invalid or unsafe."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class StrategyTemplate:
    """Immutable configuration artifact with no activation or order method."""

    template_id: str
    schema_version: str
    payload_json: str
    payload_sha256: str
    declared_capabilities: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_identifier(self.template_id, "TEMPLATE_ID_INVALID")
        if self.schema_version != _SCHEMA:
            raise StrategyTemplateError(
                "TEMPLATE_SCHEMA_INVALID",
                "Yalnız strategy-template-v1 şeması kabul edilir.",
            )
        payload = _decode_payload(self.payload_json)
        if not isinstance(self.payload_sha256, str) or _SHA256.fullmatch(
            self.payload_sha256
        ) is None:
            raise StrategyTemplateError(
                "TEMPLATE_HASH_INVALID", "Payload hash lowercase SHA-256 hex olmalıdır."
            )
        if _sha256(self.payload_json) != self.payload_sha256:
            raise StrategyTemplateError(
                "TEMPLATE_HASH_MISMATCH", "Payload hash snapshot ile eşleşmiyor."
            )
        _validate_capabilities(self.declared_capabilities)
        if tuple(sorted(self.declared_capabilities)) != self.declared_capabilities:
            raise StrategyTemplateError(
                "TEMPLATE_CAPABILITIES_NOT_CANONICAL",
                "Declared capabilities canonical sırada olmalıdır.",
            )
        _validate_payload_value(payload)


def new_strategy_template(
    *,
    template_id: str,
    schema_version: str,
    payload: dict[str, object],
    declared_capabilities: tuple[str, ...],
) -> StrategyTemplate:
    """Create a canonical inert template from JSON-compatible data.

    The payload is configuration data only. Importing it cannot activate a
    strategy or create a candidate, order, reserve, or fill.
    """

    _validate_identifier(template_id, "TEMPLATE_ID_INVALID")
    if schema_version != _SCHEMA:
        raise StrategyTemplateError(
            "TEMPLATE_SCHEMA_INVALID",
            "Yalnız strategy-template-v1 şeması kabul edilir.",
        )
    if not isinstance(payload, dict):
        raise StrategyTemplateError(
            "TEMPLATE_PAYLOAD_INVALID", "Template payload JSON object olmalıdır."
        )
    _validate_payload_value(payload)
    _validate_capabilities(declared_capabilities)
    if len(set(declared_capabilities)) != len(declared_capabilities):
        raise StrategyTemplateError(
            "TEMPLATE_CAPABILITY_DUPLICATE",
            "Declared capability tekrar edemez.",
        )
    payload_json = _canonical_json(payload)
    if len(payload_json.encode("utf-8")) > _MAX_PAYLOAD_BYTES:
        raise StrategyTemplateError(
            "TEMPLATE_PAYLOAD_TOO_LARGE",
            "Template payload boyutu sınırı aşıyor.",
        )
    return StrategyTemplate(
        template_id=template_id,
        schema_version=schema_version,
        payload_json=payload_json,
        payload_sha256=_sha256(payload_json),
        declared_capabilities=tuple(sorted(declared_capabilities)),
    )


def _canonical_json(payload: dict[str, object]) -> str:
    try:
        return json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise StrategyTemplateError(
            "TEMPLATE_PAYLOAD_INVALID", "Template payload canonical JSON olmalıdır."
        ) from error


def _decode_payload(payload_json: str) -> dict[str, object]:
    if not isinstance(payload_json, str):
        raise StrategyTemplateError(
            "TEMPLATE_SNAPSHOT_INVALID", "Template snapshot metni geçersiz."
        )
    if len(payload_json.encode("utf-8")) > _MAX_PAYLOAD_BYTES:
        raise StrategyTemplateError(
            "TEMPLATE_PAYLOAD_TOO_LARGE", "Template payload boyutu sınırı aşıyor."
        )
    try:
        payload = json.loads(payload_json)
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise StrategyTemplateError(
            "TEMPLATE_SNAPSHOT_INVALID", "Template snapshot JSON olarak okunamadı."
        ) from error
    if not isinstance(payload, dict) or _canonical_json(payload) != payload_json:
        raise StrategyTemplateError(
            "TEMPLATE_SNAPSHOT_INVALID", "Template snapshot canonical değil."
        )
    return payload


def _validate_payload_value(value: object, *, depth: int = 0) -> None:
    if depth > 8:
        raise StrategyTemplateError(
            "TEMPLATE_PAYLOAD_INVALID", "Template payload nesting sınırı aşıyor."
        )
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise StrategyTemplateError(
                    "TEMPLATE_PAYLOAD_INVALID", "Template JSON key string olmalıdır."
                )
            if key.lower().replace("-", "_") in _FORBIDDEN_KEYS:
                raise StrategyTemplateError(
                    "TEMPLATE_FORBIDDEN_FIELD",
                    "Template executable veya secret alan taşıyamaz.",
                )
            _validate_payload_value(child, depth=depth + 1)
        return
    if isinstance(value, list):
        for child in value:
            _validate_payload_value(child, depth=depth + 1)
        return
    if isinstance(value, float) or not isinstance(value, (str, int, bool, type(None))):
        raise StrategyTemplateError(
            "TEMPLATE_PAYLOAD_INVALID",
            "Template payload yalnız JSON-safe string/integer/bool/null değer taşıyabilir.",
        )


def _validate_capabilities(capabilities: tuple[str, ...]) -> None:
    if not isinstance(capabilities, tuple):
        raise StrategyTemplateError(
            "TEMPLATE_CAPABILITIES_INVALID", "Capabilities tuple olmalıdır."
        )
    for capability in capabilities:
        _validate_identifier(capability, "TEMPLATE_CAPABILITY_INVALID")


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_identifier(value: str, code: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise StrategyTemplateError(code, "Template kimliği geçersiz.")
