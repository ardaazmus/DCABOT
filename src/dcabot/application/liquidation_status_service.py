"""Faz 17 D.2: liquidation-status servisi — D.1 parçalarını okuma akışına bağlar.

Credential yoksa ağa hiç dokunmadan SIMULATED_ONLY döner; bütçe reddinde
son bilinen okumayı (yaşıyla STALE/DATA_OK işaretli) sunar; okuma
başarısız olur ve önbellek yoksa typed hata verir. Hiçbir ekonomik hesap
yapmaz — oran/hız matematiği D.1'de, bu modül yalnız orkestrasyon.
"""

from dataclasses import dataclass

from dcabot.application.alc_rate_budget import AlcPollBudget, AlcRateBudgetError
from dcabot.application.anti_liquidation_status import (
    LiquidationStatus,
    evaluate_liquidation_status,
    select_position_row,
)
from dcabot.application.credential_boundary import CredentialProvider
from dcabot.application.signed_request import SignedRequestError
from dcabot.data_adapters.binance_futures_testnet_position_risk import (
    BinanceFuturesPositionRiskError,
    FuturesAccountMargin,
    FuturesPositionRisk,
    fetch_binance_futures_account_margin,
    fetch_binance_futures_position_risk,
)

VENUE = "binance_futures"

DEFAULT_MIN_INTERVAL_US = 30_000_000
DEFAULT_STALE_AFTER_US = 120_000_000
# PROVISIONAL (D kapısında canlı veriyle kalibre edilecek, Arda kararı):
# BTC-ölçeği |Δprice/Δt| eşiği, fiyat-birimi/sn. Sıfır olamaz (o zaman
# DATA_OK hiç üretilmez, her ikinci okuma WATCH olurdu).
DEFAULT_FAST_MOVE_THRESHOLD_PER_SECOND = "50"


class LiquidationStatusServiceError(ValueError):
    """Typed service failure; api maps codes to HTTP statuses."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(slots=True)
class _CachedReading:
    selected_row: FuturesPositionRisk | None
    margin: FuturesAccountMargin | None
    observed_at_us: int
    prev_mark_price: str | None
    prev_observed_at_us: int | None


class LiquidationStatusService:
    """In-memory last-known cache + rate budget around the D.1 fetchers."""

    def __init__(
        self,
        *,
        min_interval_us: int = DEFAULT_MIN_INTERVAL_US,
        stale_after_us: int = DEFAULT_STALE_AFTER_US,
        fast_move_threshold_per_second: str = DEFAULT_FAST_MOVE_THRESHOLD_PER_SECOND,
        clock=None,
        opener=None,
    ) -> None:
        if type(stale_after_us) is not int or stale_after_us <= 0:
            raise LiquidationStatusServiceError(
                "ALC_STALE_AFTER_INVALID", "stale_after_us pozitif integer olmalıdır."
            )
        if not isinstance(fast_move_threshold_per_second, str) or not fast_move_threshold_per_second:
            raise LiquidationStatusServiceError(
                "ALC_THRESHOLD_INVALID", "Hız eşiği boş olmayan metin olmalıdır."
            )
        self._budget = AlcPollBudget(min_interval_us=min_interval_us)
        self._stale_after_us = stale_after_us
        self._threshold = fast_move_threshold_per_second
        self._clock = clock
        self.opener = opener
        self._cache: dict[str, _CachedReading] = {}

    def get_status(
        self,
        symbol: str,
        *,
        credential_id: str | None,
        provider: CredentialProvider | None,
        now_us: int,
    ) -> LiquidationStatus:
        self._check_symbol(symbol)
        if type(now_us) is not int or now_us < 0:
            raise LiquidationStatusServiceError("ALC_NOW_INVALID", "now_us negatif olmayan integer olmalıdır.")
        if credential_id is None:
            return evaluate_liquidation_status(
                venue_supports_position_risk=False,
                position_risk=None,
                account_margin=None,
                observed_at_us=now_us,
                now_us=now_us,
                stale_after_us=self._stale_after_us,
            )
        if provider is None:
            raise LiquidationStatusServiceError(
                "ALC_PROVIDER_MISSING", "Credential varken provider gerekir."
            )
        try:
            allowed = self._budget.allow(VENUE, symbol, now_us=now_us)
        except AlcRateBudgetError as exc:
            raise LiquidationStatusServiceError(exc.code, str(exc)) from exc
        if not allowed:
            cached = self._cache.get(symbol)
            if cached is None:
                raise LiquidationStatusServiceError(
                    "ALC_UPSTREAM_UNAVAILABLE", "Bütçe reddedildi ve önbellek yok."
                )
            return self._evaluate_cached(symbol, cached, now_us)
        try:
            rows = fetch_binance_futures_position_risk(
                credential_id, symbol, provider=provider, clock=self._clock, opener=self.opener
            )
        except (BinanceFuturesPositionRiskError, SignedRequestError, OSError) as exc:
            return self._serve_cache_or_raise(symbol, exc, now_us)
        try:
            selected = select_position_row(rows)
        except ValueError as exc:
            code = getattr(exc, "code", None)
            raise LiquidationStatusServiceError(
                code if isinstance(code, str) else "ALC_ROW_SELECTION_FAILED",
                "Pozisyon satırı seçilemedi.",
            ) from exc
        try:
            margin = fetch_binance_futures_account_margin(
                credential_id, provider=provider, clock=self._clock, opener=self.opener
            )
        except (BinanceFuturesPositionRiskError, SignedRequestError, OSError):
            margin = None
        previous = self._cache.get(symbol)
        prev_mark = previous.selected_row.mark_price if previous and previous.selected_row else None
        prev_t = previous.observed_at_us if previous and previous.selected_row else None
        self._cache[symbol] = _CachedReading(
            selected_row=selected,
            margin=margin,
            observed_at_us=now_us,
            prev_mark_price=prev_mark,
            prev_observed_at_us=prev_t,
        )
        return evaluate_liquidation_status(
            venue_supports_position_risk=True,
            position_risk=selected,
            account_margin=margin,
            observed_at_us=now_us,
            now_us=now_us,
            stale_after_us=self._stale_after_us,
            previous_mark_price=prev_mark,
            previous_observed_at_us=prev_t,
            fast_move_threshold_per_second=self._threshold,
        )

    def _evaluate_cached(self, symbol: str, cached: _CachedReading, now_us: int) -> LiquidationStatus:
        return evaluate_liquidation_status(
            venue_supports_position_risk=True,
            position_risk=cached.selected_row,
            account_margin=cached.margin,
            observed_at_us=cached.observed_at_us,
            now_us=now_us,
            stale_after_us=self._stale_after_us,
            previous_mark_price=cached.prev_mark_price,
            previous_observed_at_us=cached.prev_observed_at_us,
            fast_move_threshold_per_second=self._threshold,
        )

    def _serve_cache_or_raise(self, symbol: str, exc: Exception, now_us: int) -> LiquidationStatus:
        cached = self._cache.get(symbol)
        if cached is None:
            raise LiquidationStatusServiceError(
                "ALC_UPSTREAM_UNAVAILABLE", "Upstream okunamadı ve önbellek yok."
            ) from exc
        return self._evaluate_cached(symbol, cached, now_us)

    @staticmethod
    def _check_symbol(symbol: str) -> None:
        if (
            not isinstance(symbol, str)
            or not 1 <= len(symbol) <= 32
            or symbol != symbol.strip()
            or any(ord(char) < 0x20 or ord(char) == 0x7F for char in symbol)
        ):
            raise LiquidationStatusServiceError("ALC_SYMBOL_INVALID", "Symbol değeri geçersiz.")
