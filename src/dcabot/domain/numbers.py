"""Strict Decimal boundary, exact rational economics, rounded display only."""

from decimal import Decimal, Context, localcontext, ROUND_HALF_EVEN
from fractions import Fraction
import re

Q = Fraction
_PATTERN = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z", re.ASCII)


def number(value: object) -> Q:
    if not isinstance(value, str) or len(value) > 50 or not _PATTERN.fullmatch(value):
        raise ValueError("Financial values must be plain decimal strings (no exponent)")
    if "." in value and len(value.split(".")[1]) > 24:
        raise ValueError("At most 24 fractional digits are supported")
    result = Q(Decimal(value))
    if abs(result) > 10**12:
        raise ValueError("Input magnitude exceeds 10^12")
    return result


def positive(value: object) -> Q:
    result = number(value)
    if result <= 0:
        raise ValueError("Expected positive value")
    return result


def bounded(value: Q) -> Q:
    if value.numerator.bit_length() > 4096 or value.denominator.bit_length() > 4096:
        raise ValueError("Exact arithmetic resource bound exceeded")
    return value


def text(value: Q | None, places: int = 12) -> str | None:
    if value is None:
        return None
    bounded(value)
    with localcontext(Context(prec=1400, rounding=ROUND_HALF_EVEN)):
        result = (Decimal(value.numerator) / Decimal(value.denominator)).quantize(
            Decimal(1).scaleb(-places)
        )
        if not result:
            return "0"
        return (
            format(result, "f").rstrip("0").rstrip(".")
            if places
            else format(result, "f")
        )


def exact_text(value: Q) -> str:
    result = text(value, 24)
    if number(result) != value:
        raise ValueError("Value cannot be represented in the external decimal contract")
    return result


def align(value: Q, step: Q, *, up: bool, origin: Q = Q(0)) -> Q:
    if step <= 0:
        raise ValueError("Step must be positive")
    ratio = (value - origin) / step
    units = (
        -((-ratio.numerator) // ratio.denominator)
        if up
        else ratio.numerator // ratio.denominator
    )
    return bounded(origin + units * step)


def round_quantum(value: Q, quantum: Q) -> Q:
    if quantum <= 0:
        raise ValueError("Quantum must be positive")
    return round(value / quantum) * quantum  # Fraction round: exact ties to even.


def ratio(value: Q) -> list[str]:
    bounded(value)
    return [str(value.numerator), str(value.denominator)]
