"""Profile-owned exact instrument filter validation before order authority."""

from dataclasses import dataclass
import re

from dcabot.domain.numbers import Q, align, exact_text, positive


_PROFILE_ID = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)


class InstrumentFilterError(ValueError):
    """Raised when a profile or candidate violates an instrument filter."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class InstrumentFilterProfile:
    """Exact instrument metadata owned by one explicit profile."""

    profile_id: str
    qty_step: str
    price_tick: str
    min_qty: str
    min_notional: str

    def __post_init__(self) -> None:
        if not isinstance(self.profile_id, str) or _PROFILE_ID.fullmatch(self.profile_id) is None:
            raise InstrumentFilterError(
                "FILTER_PROFILE_INVALID", "Instrument filter profile kimliği geçersiz."
            )
        try:
            values = tuple(
                positive(value)
                for value in (
                    self.qty_step,
                    self.price_tick,
                    self.min_qty,
                    self.min_notional,
                )
            )
        except ValueError as error:
            raise InstrumentFilterError(
                "FILTER_PROFILE_INVALID",
                "Instrument filter değerleri pozitif decimal string olmalıdır.",
            ) from error
        if any((value * 10**12).denominator != 1 for value in values):
            raise InstrumentFilterError(
                "FILTER_PROFILE_INVALID",
                "Instrument filter değerleri 12 decimal basamağı aşamaz.",
            )


@dataclass(frozen=True, slots=True)
class ValidatedOrderCandidate:
    """A candidate that passed profile filters, still without posting."""

    profile_id: str
    quantity: str
    price: str
    notional: str


def validate_order_candidate(
    profile: InstrumentFilterProfile, *, quantity: str, price: str
) -> ValidatedOrderCandidate:
    """Validate exact quantity/price against the explicit instrument profile."""

    if not isinstance(profile, InstrumentFilterProfile):
        raise InstrumentFilterError(
            "FILTER_PROFILE_INVALID", "Instrument filter profili geçersiz."
        )
    try:
        parsed_quantity = positive(quantity)
    except ValueError as error:
        raise InstrumentFilterError(
            "ORDER_QUANTITY_INVALID", "Order quantity pozitif decimal string olmalıdır."
        ) from error
    try:
        parsed_price = positive(price)
    except ValueError as error:
        raise InstrumentFilterError(
            "ORDER_PRICE_INVALID", "Order price pozitif decimal string olmalıdır."
        ) from error
    qty_step, price_tick, min_qty, min_notional = tuple(
        positive(value)
        for value in (
            profile.qty_step,
            profile.price_tick,
            profile.min_qty,
            profile.min_notional,
        )
    )
    if align(parsed_quantity, qty_step, up=False) != parsed_quantity:
        raise InstrumentFilterError(
            "ORDER_QUANTITY_OFF_GRID", "Order quantity profile step grid’inde değil."
        )
    if align(parsed_price, price_tick, up=False) != parsed_price:
        raise InstrumentFilterError(
            "ORDER_PRICE_OFF_GRID", "Order price profile tick grid’inde değil."
        )
    if parsed_quantity < min_qty:
        raise InstrumentFilterError(
            "ORDER_QUANTITY_BELOW_MINIMUM", "Order quantity profile minimumunun altında."
        )
    notional = parsed_quantity * parsed_price
    if notional < min_notional:
        raise InstrumentFilterError(
            "ORDER_NOTIONAL_BELOW_MINIMUM",
            "Order notional profile minimumunun altında.",
        )
    try:
        return ValidatedOrderCandidate(
            profile_id=profile.profile_id,
            quantity=exact_text(parsed_quantity),
            price=exact_text(parsed_price),
            notional=exact_text(notional),
        )
    except ValueError as error:
        raise InstrumentFilterError(
            "ORDER_CANDIDATE_UNREPRESENTABLE",
            "Order adayı exact decimal sözleşmesine sığmıyor.",
        ) from error
