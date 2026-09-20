"""Immutable, non-authoritative acceptance snapshot for custom Futures DCA candidates."""

from dataclasses import dataclass
import hashlib
import json
import re

from dcabot.application.balance_percent_sizing import BalancePercentBudget
from dcabot.application.futures_dca_plan import (
    FuturesDcaCustomCandidateProjection,
    FuturesDcaPlanError,
    bind_futures_dca_custom_candidates,
)
from dcabot.application.ladder_binding import LadderBinding, LadderLevelCandidate
from dcabot.application.ladder_conservation import validate_ladder_allocations
from dcabot.application.sizing_pre_acceptance import (
    SizingPreAcceptance,
    SizingPreAcceptanceError,
    evaluate_sizing_pre_acceptance,
)
from dcabot.application.sizing_units import (
    SizingContractError,
    build_sizing_candidate,
)


_SHA256 = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)


@dataclass(frozen=True, slots=True)
class FuturesDcaCustomCandidateAcceptance:
    """Immutable candidate snapshot; acceptance never grants order authority."""

    candidate_id: str
    instrument_profile_id: str
    qty_step: str
    price_tick: str
    min_qty: str
    min_notional: str
    side: str
    allocation_unit: str
    level_count: int
    actual_total_allocation: str
    budget: str
    remaining_budget: str
    order_authority: str = "NONE"

    def __post_init__(self) -> None:
        if not isinstance(self.candidate_id, str) or _SHA256.fullmatch(self.candidate_id) is None:
            raise FuturesDcaPlanError(
                "FUTURES_DCA_CUSTOM_ACCEPTANCE_ID_INVALID",
                "Candidate identity küçük harfli SHA-256 olmalıdır.",
            )
        if self.order_authority != "NONE":
            raise FuturesDcaPlanError(
                "FUTURES_DCA_CUSTOM_ORDER_AUTHORITY_INVALID",
                "Custom candidate acceptance order authority taşıyamaz.",
            )
        if type(self.level_count) is not int or not 0 <= self.level_count <= 50:
            raise FuturesDcaPlanError(
                "FUTURES_DCA_CUSTOM_ACCEPTANCE_LEVEL_COUNT_INVALID",
                "Acceptance level count integer 0..50 olmalıdır.",
            )


@dataclass(frozen=True, slots=True)
class FuturesDcaCustomPreAcceptance:
    """Custom acceptance joined to the existing read-only sizing gate."""

    acceptance: FuturesDcaCustomCandidateAcceptance
    sizing: SizingPreAcceptance


def assess_futures_dca_custom_candidate_acceptance(
    candidate: FuturesDcaCustomCandidateProjection,
) -> FuturesDcaCustomCandidateAcceptance:
    """Revalidate and freeze one custom candidate without persistence or posting."""

    if not isinstance(candidate, FuturesDcaCustomCandidateProjection):
        raise FuturesDcaPlanError(
            "FUTURES_DCA_CUSTOM_ACCEPTANCE_INPUT_INVALID",
            "Custom candidate projection güvenli tipte olmalıdır.",
        )
    try:
        rebuilt = bind_futures_dca_custom_candidates(
            candidate.ladder, candidate.instrument
        )
    except FuturesDcaPlanError as error:
        raise FuturesDcaPlanError(
            "FUTURES_DCA_CUSTOM_ACCEPTANCE_INVALID", str(error)
        ) from error
    if rebuilt != candidate:
        raise FuturesDcaPlanError(
            "FUTURES_DCA_CUSTOM_ACCEPTANCE_CONFLICT",
            "Candidate projection immutable acceptance snapshot ile uyuşmuyor.",
        )
    ladder = candidate.ladder
    instrument = candidate.instrument
    payload = {
        "schema": "futures-dca-custom-candidate-v1",
        "futures_profile": {
            "venue": ladder.profile.venue,
            "product_family": ladder.profile.product_family,
            "settlement_asset": ladder.profile.settlement_asset,
            "margin_asset": ladder.profile.margin_asset,
            "contract_type": ladder.profile.contract_type,
            "position_mode": ladder.profile.position_mode,
            "margin_mode": ladder.profile.margin_mode,
            "leverage": ladder.profile.leverage,
        },
        "instrument": {
            "profile_id": instrument.profile_id,
            "qty_step": instrument.qty_step,
            "price_tick": instrument.price_tick,
            "min_qty": instrument.min_qty,
            "min_notional": instrument.min_notional,
        },
        "ladder": {
            "side": ladder.side,
            "anchor_price": ladder.anchor_price,
            "price_tick": ladder.price_tick,
            "allocation_unit": ladder.allocation_unit,
            "levels": [
                {
                    "index": level.index,
                    "price": level.price,
                    "requested_allocation": level.requested_allocation,
                    "quantity": level.quantity,
                    "actual_allocation": level.actual_allocation,
                    "quote_notional": level.quote_notional,
                }
                for level in candidate.levels
            ],
            "conservation": {
                "total_allocated": candidate.conservation.total_allocated,
                "budget": candidate.conservation.budget,
                "remaining_budget": candidate.conservation.remaining_budget,
            },
        },
    }
    encoded = json.dumps(
        payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    candidate_id = hashlib.sha256(encoded).hexdigest()
    return FuturesDcaCustomCandidateAcceptance(
        candidate_id=candidate_id,
        instrument_profile_id=instrument.profile_id,
        qty_step=instrument.qty_step,
        price_tick=instrument.price_tick,
        min_qty=instrument.min_qty,
        min_notional=instrument.min_notional,
        side=ladder.side,
        allocation_unit=ladder.allocation_unit,
        level_count=len(candidate.levels),
        actual_total_allocation=candidate.conservation.total_allocated,
        budget=candidate.conservation.budget,
        remaining_budget=candidate.conservation.remaining_budget,
    )


def evaluate_futures_dca_custom_pre_acceptance(
    *,
    candidate: FuturesDcaCustomCandidateProjection,
    acceptance: FuturesDcaCustomCandidateAcceptance,
    eligible_budget: BalancePercentBudget,
    quote_asset: str,
) -> FuturesDcaCustomPreAcceptance:
    """Join a custom candidate to the existing offline sizing gate.

    The bridge deliberately accepts only a quote-notional custom ladder. A
    BASE_QTY ladder has no explicit quote budget after quantization, so an
    implicit conversion would weaken the existing asset/unit boundary.
    """

    if not isinstance(candidate, FuturesDcaCustomCandidateProjection):
        raise FuturesDcaPlanError(
            "FUTURES_DCA_CUSTOM_PRE_ACCEPTANCE_INPUT_INVALID",
            "Custom candidate projection güvenli tipte olmalıdır.",
        )
    if not isinstance(acceptance, FuturesDcaCustomCandidateAcceptance):
        raise FuturesDcaPlanError(
            "FUTURES_DCA_CUSTOM_PRE_ACCEPTANCE_INPUT_INVALID",
            "Custom acceptance snapshot güvenli tipte olmalıdır.",
        )
    if not isinstance(eligible_budget, BalancePercentBudget):
        raise FuturesDcaPlanError(
            "FUTURES_DCA_CUSTOM_PRE_ACCEPTANCE_INPUT_INVALID",
            "Eligible budget güvenli tipte olmalıdır.",
        )
    expected = assess_futures_dca_custom_candidate_acceptance(candidate)
    if acceptance != expected:
        raise FuturesDcaPlanError(
            "FUTURES_DCA_CUSTOM_PRE_ACCEPTANCE_CONFLICT",
            "Acceptance snapshot candidate projection ile eşleşmiyor.",
        )
    if candidate.ladder.allocation_unit != "QUOTE_NOTIONAL":
        raise FuturesDcaPlanError(
            "FUTURES_DCA_CUSTOM_PRE_ACCEPTANCE_UNIT_UNSUPPORTED",
            "Pre-acceptance köprüsü yalnız açık quote-notional bütçeyi kabul eder.",
        )
    if not candidate.levels:
        raise FuturesDcaPlanError(
            "FUTURES_DCA_CUSTOM_PRE_ACCEPTANCE_EMPTY",
            "Pre-acceptance için en az bir custom candidate seviyesi gerekir.",
        )

    first, *remaining = candidate.levels
    try:
        sizing_candidate = build_sizing_candidate(
            sizing_mode="QUOTE_NOTIONAL",
            amount=first.quote_notional,
            reference_price=first.price,
        )
        if (
            sizing_candidate.candidate_quantity != first.quantity
            or sizing_candidate.candidate_notional != first.quote_notional
        ):
            raise FuturesDcaPlanError(
                "FUTURES_DCA_CUSTOM_PRE_ACCEPTANCE_CONFLICT",
                "İlk custom candidate quote/quantity projection ile eşleşmiyor.",
            )
        remaining_levels = tuple(
            LadderLevelCandidate(
                index=level.index,
                price=level.price,
                quantity=level.quantity,
                allocation=level.quote_notional,
            )
            for level in remaining
        )
        remaining_conservation = validate_ladder_allocations(
            allocation_unit="QUOTE_NOTIONAL",
            allocations=tuple(level.allocation for level in remaining_levels),
            budget=candidate.ladder.conservation.budget,
        )
        sizing = evaluate_sizing_pre_acceptance(
            candidate=sizing_candidate,
            ladder=LadderBinding(
                levels=remaining_levels,
                conservation=remaining_conservation,
            ),
            profile=candidate.instrument,
            eligible_budget=eligible_budget,
            quote_asset=quote_asset,
        )
    except FuturesDcaPlanError:
        raise
    except SizingPreAcceptanceError as error:
        raise FuturesDcaPlanError(error.code, str(error)) from error
    except SizingContractError as error:
        raise FuturesDcaPlanError(error.code, str(error)) from error
    except ValueError as error:
        raise FuturesDcaPlanError(
            "FUTURES_DCA_CUSTOM_PRE_ACCEPTANCE_INVALID",
            "Custom candidate pre-acceptance exact sözleşmesine sığmıyor.",
        ) from error
    return FuturesDcaCustomPreAcceptance(acceptance=acceptance, sizing=sizing)
