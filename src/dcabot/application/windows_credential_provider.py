"""Windows Credential Manager boundary for short-lived venue credentials."""

import ctypes
from ctypes import POINTER, Structure, addressof, byref, c_uint32, c_void_p, create_string_buffer
from ctypes import wintypes
import re
import sys
from typing import Any

from dcabot.application.credential_boundary import CredentialMaterial, CredentialProvider
from dcabot.application.signed_request import ApiKeyType, SignedRequestError


_CRED_TYPE_GENERIC = 1
_CRED_PERSIST_LOCAL = 2
_TARGET_PREFIX = "DCABOT:BINANCE_SPOT_TESTNET:"
_CREDENTIAL_ID_PATTERN = re.compile(r"[A-Za-z0-9_.:-]+\Z")


class _Credential(Structure):
    _fields_ = [
        ("flags", c_uint32),
        ("credential_type", c_uint32),
        ("target_name", wintypes.LPWSTR),
        ("comment", wintypes.LPWSTR),
        ("last_written", wintypes.FILETIME),
        ("credential_blob_size", c_uint32),
        ("credential_blob", c_void_p),
        ("persist", c_uint32),
        ("attribute_count", c_uint32),
        ("attributes", c_void_p),
        ("target_alias", wintypes.LPWSTR),
        ("user_name", wintypes.LPWSTR),
    ]


class WindowsCredentialManagerProvider(CredentialProvider):
    """Load and store HMAC material in the current Windows user vault."""

    __slots__ = ("_key_type",)

    def __init__(self, *, key_type: ApiKeyType = ApiKeyType.HMAC) -> None:
        if sys.platform != "win32":
            raise SignedRequestError("WINDOWS_CREDENTIALS_UNSUPPORTED", "Windows Credential Manager yalnız Windows’ta kullanılabilir.")
        try:
            parsed_key_type = ApiKeyType(key_type)
        except (TypeError, ValueError) as exc:
            raise SignedRequestError("CREDENTIAL_KEY_TYPE_INVALID", "Credential key türü geçersiz.") from exc
        if parsed_key_type is ApiKeyType.UNKNOWN:
            raise SignedRequestError("CREDENTIAL_KEY_TYPE_INVALID", "Bilinmeyen credential key türü reddedildi.")
        if parsed_key_type is not ApiKeyType.HMAC:
            raise SignedRequestError("CREDENTIAL_KEY_TYPE_UNSUPPORTED", "Windows sağlayıcı bu dilimde yalnız HMAC destekler.")
        self._key_type = parsed_key_type

    def put(self, material: CredentialMaterial) -> None:
        """Persist material as a user-scoped generic credential."""

        if not isinstance(material, CredentialMaterial):
            raise SignedRequestError("CREDENTIAL_MATERIAL_INVALID", "Credential material geçersiz.")
        if material.key_type is not self._key_type:
            raise SignedRequestError("CREDENTIAL_KEY_TYPE_CONFLICT", "Credential key türü sağlayıcıyla eşleşmiyor.")
        wincred = _wincred()
        blob = create_string_buffer(material.secret)
        credential = _Credential(
            credential_type=_CRED_TYPE_GENERIC,
            target_name=_target_name(material.credential_id),
            credential_blob_size=len(material.secret),
            credential_blob=c_void_p(addressof(blob)),
            persist=_CRED_PERSIST_LOCAL,
            user_name=material.api_key,
        )
        if not wincred.CredWriteW(byref(credential), 0):
            _raise_last_error("CREDENTIAL_WRITE_FAILED", "Windows Credential Manager yazma işlemi başarısız.")

    def load(self, credential_id: str) -> CredentialMaterial:
        """Read one user-scoped credential and copy its blob before freeing it."""

        target = _target_name(credential_id)
        wincred = _wincred()
        credential_pointer = POINTER(_Credential)()
        if not wincred.CredReadW(target, _CRED_TYPE_GENERIC, 0, byref(credential_pointer)):
            _raise_last_error("CREDENTIAL_NOT_FOUND", "Credential bulunamadı.")
        try:
            credential = credential_pointer.contents
            if credential.target_name != target or not credential.user_name:
                raise SignedRequestError("CREDENTIAL_DATA_INVALID", "Windows credential kimliği veya API key geçersiz.")
            if not credential.credential_blob or not credential.credential_blob_size:
                raise SignedRequestError("CREDENTIAL_DATA_INVALID", "Windows credential secret boş olamaz.")
            secret = _copy_blob(credential.credential_blob, credential.credential_blob_size)
            return CredentialMaterial(
                credential_id=credential_id,
                api_key=credential.user_name,
                key_type=self._key_type,
                secret=secret,
            )
        finally:
            wincred.CredFree(credential_pointer)

    def delete(self, credential_id: str) -> None:
        """Delete one credential target for local setup cleanup."""

        wincred = _wincred()
        if not wincred.CredDeleteW(_target_name(credential_id), _CRED_TYPE_GENERIC, 0):
            _raise_last_error("CREDENTIAL_DELETE_FAILED", "Windows credential silme işlemi başarısız.")

    def __repr__(self) -> str:
        return "WindowsCredentialManagerProvider(<redacted>)"


def _target_name(credential_id: str) -> str:
    if (
        not isinstance(credential_id, str)
        or not 1 <= len(credential_id) <= 128
        or not _CREDENTIAL_ID_PATTERN.fullmatch(credential_id)
        or any(ord(char) < 0x20 or ord(char) == 0x7F for char in credential_id)
    ):
        raise SignedRequestError("CREDENTIAL_ID_INVALID", "Credential az ve güvenli bir kimlik olmalıdır.")
    return f"{_TARGET_PREFIX}{credential_id}"


def _copy_blob(pointer: c_void_p, size: int) -> bytes:
    return ctypes.string_at(pointer, size)


def _wincred() -> Any:
    if sys.platform != "win32":
        raise SignedRequestError("WINDOWS_CREDENTIALS_UNSUPPORTED", "Windows Credential Manager yalnız Windows’ta kullanılabilir.")
    advapi32 = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
    advapi32.CredWriteW.argtypes = [POINTER(_Credential), wintypes.DWORD]
    advapi32.CredWriteW.restype = wintypes.BOOL
    advapi32.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, POINTER(POINTER(_Credential))]
    advapi32.CredReadW.restype = wintypes.BOOL
    advapi32.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    advapi32.CredDeleteW.restype = wintypes.BOOL
    advapi32.CredFree.argtypes = [c_void_p]
    advapi32.CredFree.restype = None
    return advapi32


def _raise_last_error(code: str, message: str) -> None:
    error = ctypes.get_last_error()
    if error in (1168, 2):
        raise SignedRequestError("CREDENTIAL_NOT_FOUND", "Credential bulunamadı.")
    raise SignedRequestError(code, f"{message} (Windows error {error}).")
