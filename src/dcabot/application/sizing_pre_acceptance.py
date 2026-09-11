"""Pure pre-acceptance gate joining the bounded sizing contracts."""

from dataclasses import dataclass
import re

from dcabot.application.balance_percent_sizing import BalancePercentBudget
from dcabot.application.instrument_filters import (
    InstrumentFilterError,
    InstrumentFilterProfile,
    validate_order_candidate,
)
from dcabot.application.ladder_binding import LadderBinding
from dcabot.domain.numbers import bounded, exact_text, number
from dcabot.application.sizing_units import SizingCandidate


_ASSET = re.compile(r"[A-Z0-9]{2,12}\Z", re.ASCII)


class SizingPreAcceptanceError(ValueError):
    """Raised when a sizing bundle cannot pass its non-economic gate."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class SizingPreAcceptance:
    """Exact gate output with order authority intentionally disabled."""

    profile_id: str
    quote_asset: str
    candidate_notional: str
    ladder_notional: str
    eligible_budget: str
    total_commitment: str
    order_authority: str


def evaluate_sizing_pre_acceptance(
    *,
    candidate: SizingCandidate,
    ladder: LadderBinding,
    profile: InstrumentFilterProfile,
    eligible_budget: BalancePercentBudget,
    quote_asset: str,
) -> SizingPreAcceptance:
    """Join tagged sizing, quote-unit ladder, profile filters and budget.

    BASE_QTY and QUOTE_NOTIONAL candidates are both accepted when their exact
    quote notional is internally consistent with the explicit reference price.
    The ladder and eligible budget remain in one explicit quote unit. Passing
    this gate never posts an order.
    """

    if not isinstance(candidate, SizingCandidate) or not isinstance(
        ladder, LadderBinding
    ) or not isinstance(profile, InstrumentFilterProfile) or not isinstance(
        eligible_budget, BalancePercentBudget
    ):
        raise SizingPreAcceptanceError(
            "PRE_ACCEPTANCE_INPUT_INVALID", "Sizing gate girdileri geçersiz."
        )
    if not isinstance(quote_asset, str) or _ASSET.fullmatch(quote_asset) is None:
        raise SizingPreAcceptanceError(
            "PRE_ACCEPTANCE_ASSET_CONFLICT", "Quote asset açık kod olmalıdır."
        )
    if candidate.sizing_mode not in ("BASE_QTY", "QUOTE_NOTIONAL") or (
        ladder.conservation.allocation_unit != "QUOTE_NOTIONAL"
    ):
        raise SizingPreAcceptanceError(
            "PRE_ACCEPTANCE_UNIT_CONFLICT",
            "Candidate desteklenen BASE/QUOTE sizing ve quote-unit ladder ile uyumlu olmalıdır.",
        )
    if eligible_budget.asset != quote_asset:
        raise SizingPreAcceptanceError(
            "PRE_ACCEPTANCE_ASSET_CONFLICT",
            "Eligible budget asset quote asset ile aynı olmalıdır.",
        )
    try:
        validated_candidate = validate_order_candidate(
            profile,
            quantity=candidate.candidate_quantity,
            price=candidate.reference_price,
        )
        candidate_notional = number(candidate.candidate_notional)
        if number(validated_candidate.notional) != candidate_notional:
            raise SizingPreAcceptanceError(
                "PRE_ACCEPTANCE_CANDIDATE_CONFLICT",
                "Candidate notional quantity ve price ile uyumlu değil.",
            )
        ladder_allocations = tuple(number(level.allocation) for level in ladder.levels)
        ladder_notional = bounded(sum(ladder_allocations, number("0")))
        if ladder_notional != number(ladder.conservation.total_allocated):
            raise SizingPreAcceptanceError(
                "PRE_ACCEPTANCE_LADDER_CONFLICT",
                "Ladder allocation toplamı conservation kaydıyla uyumlu değil.",
            )
        budget = number(eligible_budget.budget)
    except InstrumentFilterError as error:
        raise SizingPreAcceptanceError(error.code, str(error)) from error
    except ValueError as error:
        if isinstance(error, SizingPreAcceptanceError):
            raise
        raise SizingPreAcceptanceError(
            "PRE_ACCEPTANCE_NUMERIC_INVALID", "Sizing gate numeric alanı geçersiz."
        ) from error
    total_commitment = bounded(candidate_notional + ladder_notional)
    if total_commitment > budget:
        raise SizingPreAcceptanceError(
            "PRE_ACCEPTANCE_BUDGET_EXCEEDED",
            "Candidate ve ladder toplam commitment eligible budget’ı aşamaz.",
        )
    try:
        return SizingPreAcceptance(
            profile_id=profile.profile_id,
            quote_asset=quote_asset,
            candidate_notional=exact_text(candidate_notional),
            ladder_notional=exact_text(ladder_notional),
            eligible_budget=exact_text(budget),
            total_commitment=exact_text(total_commitment),
            order_authority="NONE",
        )
    except ValueError as error:
        raise SizingPreAcceptanceError(
            "PRE_ACCEPTANCE_UNREPRESENTABLE",
            "Sizing gate sonucu exact decimal sözleşmesine sığmıyor.",
        ) from error
