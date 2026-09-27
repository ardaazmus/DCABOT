"""Faz 17 G.1 (RG-06): Margin Mode pre-flight -- LOCAL state machine only.

Binance's marginType is symbol-level venue configuration, not an order
parameter (`POST /fapi/v1/marginType`; no `marginType` field on `New
Order`). No futures credential exists yet (open question), so this module
never calls a real venue -- callers inject a `MarginTypeVenuePort`
implementation (a fake in tests today, a real HTTP adapter later, unchanged
interface). LCR-12 is untouched by construction: this module manages the
margin-type SETTING only and never computes or estimates a liquidation
price.

State machine is read -> (change) -> read-to-confirm, matching the sector
research (Faz 17 konu 6/12): a mode already matching the request is a no-op,
a change is attempted only when needed, and the post-change read is the
proof the venue actually applied it -- never assumed from a 2xx response
alone.
"""

from dataclasses import dataclass
from typing import Protocol

MARGIN_MODES = ("ISOLATED", "CROSS")

# Faz 17 konu 6/12 (3 independent research reports, M/F/B PASS, KARARLAR.md
# 2026-09-22): Binance futures marginType error codes.
_VENUE_ERROR_MAP: dict[int, tuple[str, str]] = {
    -4046: ("MARGIN_TYPE_ALREADY_SET", "Hesap zaten istenen marjin modunda."),
    -4047: ("MARGIN_TYPE_OPEN_ORDERS", "Açık emir varken marjin modu değiştirilemez."),
    -4048: ("MARGIN_TYPE_OPEN_POSITION", "Açık pozisyon varken marjin modu değiştirilemez."),
    -4049: ("MARGIN_TYPE_CROSS_ISOLATED_MARGIN_ADD", "Cross modda izole marjin eklenemez."),
    -4050: ("MARGIN_TYPE_INSUFFICIENT_BALANCE", "Marjin modu değişikliği için bakiye yetersiz."),
    -4051: ("MARGIN_TYPE_INSUFFICIENT_BALANCE", "Marjin modu değişikliği için bakiye yetersiz."),
}


class MarginModePreflightError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class VenueMarginTypeError(Exception):
    """Raised by a `MarginTypeVenuePort` implementation for a rejected
    `set_margin_type` call; `code` is the venue's raw numeric error code."""

    def __init__(self, code: int, raw_message: str = "") -> None:
        self.code = code
        self.raw_message = raw_message
        super().__init__(f"{code}: {raw_message}")


class MarginTypeVenuePort(Protocol):
    def read_margin_type(self, symbol: str) -> str: ...

    def set_margin_type(self, symbol: str, mode: str) -> None: ...


@dataclass(frozen=True, slots=True)
class MarginModePreflightResult:
    symbol: str
    requested_mode: str
    previous_mode: str
    changed: bool
    confirmed_mode: str


def map_venue_error(code: int) -> MarginModePreflightError:
    mapped = _VENUE_ERROR_MAP.get(code)
    if mapped is None:
        return MarginModePreflightError(
            "MARGIN_TYPE_UNKNOWN_VENUE_ERROR", f"Bilinmeyen venue hata kodu: {code}."
        )
    domain_code, message = mapped
    return MarginModePreflightError(domain_code, message)


def run_margin_mode_preflight(
    venue: MarginTypeVenuePort, *, symbol: str, requested_mode: str
) -> MarginModePreflightResult:
    if requested_mode not in MARGIN_MODES:
        raise MarginModePreflightError(
            "MARGIN_TYPE_INVALID_REQUEST", "requested_mode ISOLATED veya CROSS olmalıdır."
        )
    previous = venue.read_margin_type(symbol)
    if previous not in MARGIN_MODES:
        raise MarginModePreflightError(
            "MARGIN_TYPE_VENUE_RESPONSE_INVALID", "Venue geçersiz bir marjin modu döndürdü."
        )
    if previous == requested_mode:
        return MarginModePreflightResult(
            symbol=symbol,
            requested_mode=requested_mode,
            previous_mode=previous,
            changed=False,
            confirmed_mode=previous,
        )
    try:
        venue.set_margin_type(symbol, requested_mode)
    except VenueMarginTypeError as exc:
        if exc.code == -4046:
            # Race: another actor set it between our read and our write
            # (RG-06: "aynı paritede iki bağımsız bot" race is real). Only
            # trust a re-read, never the error message's implication alone.
            confirmed = venue.read_margin_type(symbol)
            if confirmed == requested_mode:
                return MarginModePreflightResult(
                    symbol=symbol,
                    requested_mode=requested_mode,
                    previous_mode=previous,
                    changed=False,
                    confirmed_mode=confirmed,
                )
        raise map_venue_error(exc.code) from exc
    confirmed = venue.read_margin_type(symbol)
    if confirmed != requested_mode:
        raise MarginModePreflightError(
            "MARGIN_TYPE_CONFIRMATION_MISMATCH",
            "Değişiklik sonrası doğrulama okuması istenen modla eşleşmiyor.",
        )
    return MarginModePreflightResult(
        symbol=symbol,
        requested_mode=requested_mode,
        previous_mode=previous,
        changed=True,
        confirmed_mode=confirmed,
    )
