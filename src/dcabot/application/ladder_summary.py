"""Exact ladder (DCA averaging) summary for the Futures DCA form.

Pure read-only projection over hypothetical ladder legs: integer share
totals are always exact; the weighted average entry is reported with an
explicit exactness flag and never rounded. A non-terminating average is a
reported outcome (``weighted_average_exact=False``), not an error.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import re


from dcabot.domain.numbers import bounded, exact_text, positive


_SHARES = re.compile(r"(?:0|[1-9][0-9]*)\Z", re.ASCII)


class LadderSummaryError(ValueError):
    """Raised when a ladder summary cannot be validated."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class LadderLeg:
    """One hypothetical ladder row: level price plus integer shares."""

    price: str
    shares: str


@dataclass(frozen=True, slots=True)
class LadderSummary:
    """Exact totals plus a flagged weighted average entry."""

    direction: str
    leg_count: int
    total_shares: str
    weighted_average_entry: str | None
    weighted_average_exact: bool


def summarize_ladder(*, direction: str, legs: list[LadderLeg]) -> LadderSummary:
    """Summarize ladder legs with exact rational arithmetic."""

    if direction not in ("LONG", "SHORT"):
        raise LadderSummaryError(
            "LADDER_DIRECTION_UNSUPPORTED",
            "Merdiven özeti yalnız LONG veya SHORT yönünü destekler.",
        )
    if not isinstance(legs, list) or not 1 <= len(legs) <= 128:
        raise LadderSummaryError(
            "LADDER_LEGS_INVALID", "Merdiven 1-128 satır olmalıdır."
        )
    total = 0
    numerator = Fraction(0)
    for leg in legs:
        if not isinstance(leg, LadderLeg):
            raise LadderSummaryError(
                "LADDER_LEG_INVALID", "Merdiven satırı güvenli tipte olmalıdır."
            )
        try:
            price = positive(leg.price)
        except ValueError as error:
            raise LadderSummaryError(
                "LADDER_PRICE_INVALID", "Merdiven fiyatı pozitif ondalık olmalıdır."
            ) from error
        if not isinstance(leg.shares, str) or _SHARES.fullmatch(leg.shares) is None:
            raise LadderSummaryError(
                "LADDER_SHARES_INVALID",
                "Paylar negatif olmayan tam sayı metni olmalıdır.",
            )
        shares = int(leg.shares)
        total += shares
        numerator += bounded(price * shares)
    if total <= 0:
        raise LadderSummaryError(
            "LADDER_SHARES_ALL_ZERO", "En az bir satır pozitif pay içermelidir."
        )
    average = bounded(numerator / total)
    try:
        entry: str | None = exact_text(average)
        exact = True
    except ValueError:
        entry = None
        exact = False
    return LadderSummary(
        direction=direction,
        leg_count=len(legs),
        total_shares=str(total),
        weighted_average_entry=entry,
        weighted_average_exact=exact,
    )
