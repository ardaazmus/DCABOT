"""Credential and signed-account boundaries without an OS or network adapter."""

from dataclasses import dataclass
from enum import StrEnum
import re
from typing import Mapping, Protocol

from dcabot.application.signed_request import ApiKeyType, MAX_SECRET_BYTES, SignedRequestError


class CapabilitySource(StrEnum):
    """Authority source for capability evidence."""

    PUBLIC_VENUE_METADATA = "PUBLIC_VENUE_METADATA"
    SIGNED_ACCOUNT_CONTEXT = "SIGNED_ACCOUNT_CONTEXT"


class CredentialProvider(Protocol):
    """Load ephemeral credential material without defining OS storage."""

    def load(self, credential_id: str) -> "CredentialMaterial": ...


@dataclass(frozen=True, slots=True, repr=False)
class CredentialMaterial:
    """Short-lived signing material; it is never a response or durable record."""

    credential_id: str
    api_key: str
    key_type: ApiKeyType
    secret: bytes

    def __post_init__(self) -> None:
        if (
            not isinstance(self.credential_id, str)
            or not 1 <= len(self.credential_id) <= 128
            or _has_control_character(self.credential_id)
            or not re.fullmatch(r"[A-Za-z0-9_.:-]+", self.credential_id)
        ):
            raise SignedRequestError("CREDENTIAL_ID_INVALID", "Credential az ve güvenli bir kimlik olmalıdır.")
        if (
            not isinstance(self.api_key, str)
            or not 1 <= len(self.api_key) <= 256
            or _has_control_character(self.api_key)
        ):
            raise SignedRequestError("CREDENTIAL_API_KEY_INVALID", "API key bounded metin olmalıdır.")
        try:
            key_type = ApiKeyType(self.key_type)
        except (TypeError, ValueError) as exc:
            raise SignedRequestError("CREDENTIAL_KEY_TYPE_INVALID", "Credential key türü geçersiz.") from exc
        if key_type is ApiKeyType.UNKNOWN:
            raise SignedRequestError("CREDENTIAL_KEY_TYPE_INVALID", "Bilinmeyen credential key türü reddedildi.")
        object.__setattr__(self, "key_type", key_type)
        if not isinstance(self.secret, bytes) or not self.secret:
            raise SignedRequestError("CREDENTIAL_SECRET_INVALID", "Credential secret bytes ve boş olmayan değer olmalıdır.")
        if len(self.secret) > MAX_SECRET_BYTES:
            raise SignedRequestError("CREDENTIAL_SECRET_TOO_LARGE", "Credential secret sınırı aşıyor.")

    def __repr__(self) -> str:
        return f"CredentialMaterial(credential_id={self.credential_id!r}, key_type={self.key_type!r}, <redacted>)"


class EphemeralCredentialProvider:
    """In-memory fake provider for offline tests; no file or OS vault access."""

    __slots__ = ("_items",)

    def __init__(self) -> None:
        self._items: dict[str, CredentialMaterial] = {}

    def put(self, material: CredentialMaterial) -> None:
        if not isinstance(material, CredentialMaterial):
            raise SignedRequestError("CREDENTIAL_MATERIAL_INVALID", "Credential material geçersiz.")
        prior = self._items.get(material.credential_id)
        if prior is not None and prior != material:
            raise SignedRequestError(
                "CREDENTIAL_DUPLICATE_CONFLICT", "Aynı credential kimliği farklı material ile kullanılamaz."
            )
        self._items[material.credential_id] = material

    def load(self, credential_id: str) -> CredentialMaterial:
        material = self._items.get(credential_id)
        if material is None:
            raise SignedRequestError("CREDENTIAL_NOT_FOUND", "Credential bulunamadı.")
        return material

    def __repr__(self) -> str:
        return "EphemeralCredentialProvider(<redacted>)"


@dataclass(frozen=True, slots=True)
class AccountCapability:
    """Explicit signed-account evidence; it contains no credential material."""

    source: CapabilitySource
    signed_request_verified: bool
    can_trade: bool | None
    trade_scope_verified: bool | None

    def __post_init__(self) -> None:
        try:
            source = CapabilitySource(self.source)
        except (TypeError, ValueError) as exc:
            raise SignedRequestError(
                "ACCOUNT_CAPABILITY_SOURCE_INVALID", "Capability source tanınmıyor."
            ) from exc
        object.__setattr__(self, "source", source)
        _validate_optional_bool(self.signed_request_verified, "ACCOUNT_SIGNATURE_STATE_INVALID")
        _validate_optional_bool(self.can_trade, "ACCOUNT_TRADE_STATE_INVALID")
        _validate_optional_bool(self.trade_scope_verified, "ACCOUNT_SCOPE_STATE_INVALID")
        if source is CapabilitySource.PUBLIC_VENUE_METADATA:
            if self.signed_request_verified or self.can_trade is not None or self.trade_scope_verified is not None:
                raise SignedRequestError(
                    "ACCOUNT_CAPABILITY_SOURCE_INVALID",
                    "Public venue metadata account capability değildir.",
                )
        elif not self.signed_request_verified:
            raise SignedRequestError(
                "ACCOUNT_SIGNATURE_UNVERIFIED", "Signed account capability doğrulanmadı."
            )

    @classmethod
    def from_evidence(
        cls,
        *,
        source: CapabilitySource,
        signed_request_verified: bool,
        can_trade: bool | None,
        trade_scope_verified: bool | None,
    ) -> "AccountCapability":
        try:
            source = CapabilitySource(source)
        except (TypeError, ValueError) as exc:
            raise SignedRequestError(
                "ACCOUNT_CAPABILITY_SOURCE_INVALID", "Capability source tanınmıyor."
            ) from exc
        _validate_optional_bool(signed_request_verified, "ACCOUNT_SIGNATURE_STATE_INVALID")
        _validate_optional_bool(can_trade, "ACCOUNT_TRADE_STATE_INVALID")
        _validate_optional_bool(trade_scope_verified, "ACCOUNT_SCOPE_STATE_INVALID")
        if source is CapabilitySource.PUBLIC_VENUE_METADATA:
            if signed_request_verified or can_trade is not None or trade_scope_verified is not None:
                raise SignedRequestError(
                    "ACCOUNT_CAPABILITY_SOURCE_INVALID",
                    "Public venue metadata account capability değildir.",
                )
            return cls(source, False, None, None)
        if not signed_request_verified:
            raise SignedRequestError(
                "ACCOUNT_SIGNATURE_UNVERIFIED", "Signed account capability doğrulanmadı."
            )
        return cls(source, True, can_trade, trade_scope_verified)


def credential_public_metadata(material: CredentialMaterial) -> Mapping[str, str]:
    """Return display-safe identity metadata without API key or secret values."""

    if not isinstance(material, CredentialMaterial):
        raise SignedRequestError("CREDENTIAL_MATERIAL_INVALID", "Credential material geçersiz.")
    return {
        "credential_id": material.credential_id,
        "key_type": material.key_type.value,
    }


def _has_control_character(value: str) -> bool:
    return any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)


def _validate_optional_bool(value: object, code: str) -> None:
    if value is not None and type(value) is not bool:
        raise SignedRequestError(code, "Capability alanı boolean veya null olmalıdır.")
