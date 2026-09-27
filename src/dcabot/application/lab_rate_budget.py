"""Faz 17 E.1: Lab rate bütçesi — merkezi, izole ağırlık tavanı (§8.2).

Lab'daki her veri kaynağı REST ağırlığını bu modüle danışır; paylaşılan
tavan aşılamaz. Venue gerçeği (`X-MBX-USED-WEIGHT-1M` response header'ı)
yerel sayımdan büyükse yukarı yuvarlanır (fail-closed) — hesap genelindeki
(ana motor dahil) tüketim asla eksik sayılmaz. Yalnız tamsayı sayaçlar;
ekonomik hesap yok.
"""

from collections import deque

WINDOW_US = 60_000_000
# PROVISIONAL (E kapısında gözden geçirilir): spot 6000 + futures 2400
# ilan edilmiş limitlerinin altında muhafazakâr tavan; ana motorun ve
# diğer istemcilerin payına geniş headroom bırakır.
DEFAULT_LAB_CEILING_WEIGHT_1M = 600


class LabRateBudgetError(ValueError):
    """Raised when budget inputs or clock order cannot be honored."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class LabRateBudget:
    """Sliding-60s shared weight ceiling with venue-observed floor."""

    def __init__(self, *, ceiling_weight_1m: int = DEFAULT_LAB_CEILING_WEIGHT_1M) -> None:
        if type(ceiling_weight_1m) is not int or ceiling_weight_1m <= 0:
            raise LabRateBudgetError(
                "LAB_BUDGET_CEILING_INVALID", "Tavan pozitif integer olmalıdır."
            )
        self._ceiling = ceiling_weight_1m
        self._spends: deque[tuple[int, int]] = deque()
        self._floor_weight = 0
        self._floor_at_us: int | None = None
        self._last_seen_us: int | None = None

    def allow(self, feature: str, weight: int, *, now_us: int) -> bool:
        """True (and records the spend) only if the ceiling still holds."""
        self._check_clock(now_us)
        if not isinstance(feature, str) or not feature:
            raise LabRateBudgetError(
                "LAB_BUDGET_FEATURE_INVALID", "Özellik adı boş olmayan metin olmalıdır."
            )
        if type(weight) is not int or weight < 1:
            raise LabRateBudgetError(
                "LAB_BUDGET_WEIGHT_INVALID", "Ağırlık pozitif integer olmalıdır."
            )
        self._last_seen_us = now_us
        self._prune(now_us)
        if self._effective_usage(now_us) + weight > self._ceiling:
            return False
        self._spends.append((now_us, weight))
        return True

    def observe_used_weight_1m(self, used_weight: int, *, now_us: int) -> None:
        """Adopt the venue-reported 1m used weight as a floor (never lowers)."""
        self._check_clock(now_us)
        if type(used_weight) is not int or used_weight < 0:
            raise LabRateBudgetError(
                "LAB_BUDGET_OBSERVED_INVALID", "Gözlenen ağırlık negatif olamaz."
            )
        self._last_seen_us = now_us
        self._floor_weight = used_weight
        self._floor_at_us = now_us

    def usage_1m(self, *, now_us: int) -> int:
        """Effective 1m usage: local window sum raised by a fresh venue floor."""
        self._check_clock(now_us)
        self._last_seen_us = now_us
        self._prune(now_us)
        return self._effective_usage(now_us)

    def _check_clock(self, now_us: int) -> None:
        if type(now_us) is not int or now_us < 0:
            raise LabRateBudgetError(
                "LAB_BUDGET_NOW_INVALID", "now_us negatif olmayan integer olmalıdır."
            )
        if self._last_seen_us is not None and now_us < self._last_seen_us:
            raise LabRateBudgetError(
                "LAB_BUDGET_CLOCK_REGRESSED", "now_us önceki kayıttan geride olamaz."
            )

    def _prune(self, now_us: int) -> None:
        while self._spends and now_us - self._spends[0][0] >= WINDOW_US:
            self._spends.popleft()

    def _effective_usage(self, now_us: int) -> int:
        tracked = sum(weight for _, weight in self._spends)
        if (
            self._floor_at_us is not None
            and now_us - self._floor_at_us < WINDOW_US
            and self._floor_weight > tracked
        ):
            return self._floor_weight
        return tracked
