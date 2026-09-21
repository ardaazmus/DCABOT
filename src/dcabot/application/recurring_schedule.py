"""Recurring-buy schedule projection (F16).

Projects planned purchase slots from explicit timestamps. It is not a
safety/DCA strategy, not an order, and not an execution: slots carry no
price and no fill. All time comes from the caller; there is no clock.
"""
import re
from typing import Final

from dcabot.domain.numbers import exact_text, number


_SYMBOL = re.compile(r"[A-Z0-9]{3,20}\Z", re.ASCII)
_MAX_SLOTS: Final = 365


class RecurringScheduleError(ValueError):
    """Raised when a recurring schedule cannot be projected safely."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def project_recurring_schedule(
    *,
    symbol: str,
    quote_amount: str,
    start_us: int,
    interval_us: int,
    count: int,
) -> dict[str, object]:
    """Project evenly spaced purchase slots with an exact total."""
    if type(symbol) is not str or _SYMBOL.fullmatch(symbol) is None:
        raise RecurringScheduleError("RECURRING_SYMBOL_INVALID", "Sembol geçersiz.")
    if not isinstance(quote_amount, str):
        raise RecurringScheduleError(
            "RECURRING_AMOUNT_INVALID", "Tutar exact decimal metni olmalıdır."
        )
    try:
        amount = number(quote_amount)
    except ValueError as error:
        raise RecurringScheduleError(
            "RECURRING_AMOUNT_INVALID", "Tutar exact decimal metni olmalıdır."
        ) from error
    if amount <= 0:
        raise RecurringScheduleError("RECURRING_AMOUNT_INVALID", "Tutar pozitif olmalıdır.")
    for name, value in (("start_us", start_us), ("interval_us", interval_us)):
        if type(value) is not int or value < 0:
            raise RecurringScheduleError(
                "RECURRING_TIME_INVALID", f"{name} negatif olmayan integer olmalıdır."
            )
    if interval_us == 0:
        raise RecurringScheduleError(
            "RECURRING_TIME_INVALID", "Aralık pozitif olmalıdır."
        )
    if type(count) is not int or not 1 <= count <= _MAX_SLOTS:
        raise RecurringScheduleError(
            "RECURRING_COUNT_INVALID", "Slot sayısı 1-365 arası olmalıdır."
        )
    slots = [
        {"index": index, "slot_us": start_us + index * interval_us}
        for index in range(count)
    ]
    return {
        "symbol": symbol,
        "quote_amount": exact_text(amount),
        "start_us": start_us,
        "interval_us": interval_us,
        "count": count,
        "slots": slots,
        "total_quote": exact_text(amount * count),
        "order_authority": "NONE",
    }
