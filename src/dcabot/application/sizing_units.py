"""Exact, pre-quantization sizing candidates for the offline application."""

from dataclasses import dataclass

from dcabot.domain.numbers import Q, bounded, exact_text, positive


class SizingContractError(ValueError):
    """Raised when a sizing input cannot produce an exact candidate."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class SizingCandidate:
    """Exact candidate values before venue quantity/tick quantization."""

    sizing_mode: str
    source_amount: str
    reference_price: str
    candidate_quantity: str
    candidate_notional: str


def build_sizing_candidate(
    *, sizing_mode: str, amount: str, reference_price: str
) -> SizingCandidate:
    """Convert one explicitly tagged BASE or QUOTE amount to a candidate.

    ``BASE_QTY`` is already a base quantity. ``QUOTE_NOTIONAL`` is converted
    using the explicit positive reference price. No venue rounding, minimum
    filter, balance lookup, risk acceptance, or economic posting occurs here.
    """

    if sizing_mode not in ("BASE_QTY", "QUOTE_NOTIONAL"):
        raise SizingContractError(
            "SIZING_MODE_UNSUPPORTED",
            "Yalnız BASE_QTY veya QUOTE_NOTIONAL sizing desteklenir.",
        )
    try:
        source_amount = positive(amount)
    except ValueError as error:
        raise SizingContractError(
            "SIZING_AMOUNT_INVALID", "Sizing amount pozitif decimal string olmalıdır."
        ) from error
    try:
        price = positive(reference_price)
    except ValueError as error:
        raise SizingContractError(
            "SIZING_PRICE_INVALID", "Reference price pozitif decimal string olmalıdır."
        ) from error

    quantity = source_amount if sizing_mode == "BASE_QTY" else source_amount / price
    notional = quantity * price
    try:
        bounded(quantity)
        bounded(notional)
        return SizingCandidate(
            sizing_mode=sizing_mode,
            source_amount=exact_text(source_amount),
            reference_price=exact_text(price),
            candidate_quantity=exact_text(quantity),
            candidate_notional=exact_text(notional),
        )
    except ValueError as error:
        raise SizingContractError(
            "SIZING_CANDIDATE_UNREPRESENTABLE",
            "Aday miktar mevcut exact decimal sözleşmesine sığmıyor.",
        ) from error
