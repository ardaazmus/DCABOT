"""Faz 17 G.4 (RG-09): a thin registry+protocol layer over this phase's
indicator functions -- additive, does not modify `signal_native_indicators.py`
or any of the individual indicator modules. Its only job is letting a caller
look an indicator up by name instead of importing every module directly;
it computes nothing itself and applies no new math or validation.
"""

from typing import Callable, Protocol


class IndicatorRegistryError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class IndicatorFunction(Protocol):
    def __call__(self, closes: tuple[str, ...], **kwargs: object) -> object: ...


def _sma(closes: tuple[str, ...], **kwargs: object) -> object:
    from dcabot.application.signal_native_indicators import sma_series

    return sma_series(closes, **kwargs)


def _ema(closes: tuple[str, ...], **kwargs: object) -> object:
    from dcabot.application.signal_native_indicators import ema_series

    return ema_series(closes, **kwargs)


def _macd(closes: tuple[str, ...], **kwargs: object) -> object:
    from dcabot.application.momentum_oscillators import macd_series

    return macd_series(closes, **kwargs)


def _stoch_rsi(closes: tuple[str, ...], **kwargs: object) -> object:
    from dcabot.application.momentum_oscillators import stoch_rsi_series

    return stoch_rsi_series(closes, **kwargs)


def _bollinger(closes: tuple[str, ...], **kwargs: object) -> object:
    from dcabot.application.bollinger_bands import bollinger_bands_series

    return bollinger_bands_series(closes, **kwargs)


_REGISTRY: dict[str, IndicatorFunction] = {
    "SMA": _sma,
    "EMA": _ema,
    "MACD": _macd,
    "STOCH_RSI": _stoch_rsi,
    "BOLLINGER": _bollinger,
}


def available_indicators() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY))


def compute_indicator(name: str, closes: tuple[str, ...], **kwargs: object) -> object:
    fn = _REGISTRY.get(name)
    if fn is None:
        raise IndicatorRegistryError(
            "INDICATOR_UNKNOWN", f"Bilinmeyen indikatör: {name!r}. Mevcut: {available_indicators()}."
        )
    return fn(closes, **kwargs)
