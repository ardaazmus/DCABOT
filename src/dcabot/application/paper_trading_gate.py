"""Explicit activation gate for credential-free paper trading sessions."""

from dataclasses import dataclass
import hashlib
import json
import re

from dcabot.domain.numbers import exact_text, positive


_SYMBOL = re.compile(r"[A-Za-z0-9:_-]{1,32}\Z", re.ASCII)
_SCHEMA = "paper-session-v1"
_MAX_SYMBOLS = 16


class PaperTradingGateError(ValueError):
    """Raised when a paper session cannot be activated safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class PaperSession:
    """Immutable credential-free session; virtual cash only, never a venue order."""

    session_id: str
    schema_version: str
    status: str
    session_time_us: int
    symbols: tuple[str, ...]
    max_staleness_us: int
    cash: str
    positions: tuple[object, ...]
    orders: tuple[object, ...]
    fills: tuple[object, ...]


def activate_paper_session(
    *,
    confirmed: bool,
    session_time_us: int,
    symbols: tuple[str, ...],
    max_staleness_us: int,
    starting_cash: str,
    credential_present: bool,
) -> PaperSession:
    """Activate one paper session after explicit confirmation without credentials.

    ``confirmed`` is the execution-time user approval (same discipline as the
    testnet mutation gate: silent/auto activation never happens).
    ``credential_present`` must be False: paper trading is defined as the
    credential-free path, and any credential in scope fails the activation
    closed instead of leaking into a simulated session.
    """

    if type(confirmed) is not bool or not confirmed:
        raise PaperTradingGateError(
            "PAPER_ACTIVATION_NOT_CONFIRMED",
            "Paper session yalnız açık onayla açılır.",
        )
    if type(credential_present) is not bool or credential_present:
        raise PaperTradingGateError(
            "PAPER_CREDENTIAL_FORBIDDEN",
            "Paper session credential taşıyamaz.",
        )
    if type(session_time_us) is not int or session_time_us < 0:
        raise PaperTradingGateError(
            "PAPER_TIME_INVALID",
            "Session zamanı sıfır veya pozitif integer microseconds olmalıdır.",
        )
    if type(max_staleness_us) is not int or max_staleness_us < 0:
        raise PaperTradingGateError(
            "PAPER_STALENESS_INVALID",
            "Staleness negatif olmayan integer microseconds olmalıdır.",
        )
    if not isinstance(symbols, tuple) or not 1 <= len(symbols) <= _MAX_SYMBOLS:
        raise PaperTradingGateError(
            "PAPER_SYMBOLS_INVALID",
            "En az 1, en fazla 16 symbol gereklidir.",
        )
    for symbol in symbols:
        if not isinstance(symbol, str) or _SYMBOL.fullmatch(symbol) is None:
            raise PaperTradingGateError(
                "PAPER_SYMBOLS_INVALID", "Symbol kimliği geçersiz."
            )
    if len(set(symbols)) != len(symbols):
        raise PaperTradingGateError(
            "PAPER_SYMBOLS_DUPLICATE", "Aynı symbol iki kez verilemez."
        )
    try:
        cash = positive(starting_cash)
    except ValueError as error:
        raise PaperTradingGateError(
            "PAPER_CASH_INVALID",
            "Başlangıç nakdi pozitif decimal string olmalıdır.",
        ) from error

    ordered = tuple(sorted(symbols))
    try:
        cash_text = exact_text(cash)
    except ValueError as error:
        raise PaperTradingGateError(
            "PAPER_CASH_INVALID",
            "Başlangıç nakdi exact decimal sözleşmesine sığmıyor.",
        ) from error
    canonical = json.dumps(
        {
            "max_staleness_us": max_staleness_us,
            "schema": _SCHEMA,
            "session_time_us": session_time_us,
            "starting_cash": cash_text,
            "symbols": list(ordered),
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return PaperSession(
        session_id=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        schema_version=_SCHEMA,
        status="PAPER_ACTIVE",
        session_time_us=session_time_us,
        symbols=ordered,
        max_staleness_us=max_staleness_us,
        cash=cash_text,
        positions=(),
        orders=(),
        fills=(),
    )
