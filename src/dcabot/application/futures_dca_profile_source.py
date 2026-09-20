"""Explicit offline source contract for a Futures DCA journal profile revision."""

from dataclasses import dataclass
import re

from dcabot.application.futures_dca_plan import FuturesDcaProfile
from dcabot.domain.numbers import exact_text, positive
from dcabot.persistence.futures_dca_journal_schema import FuturesDcaProfileRevision


_IDENTIFIER = re.compile(r"[A-Za-z0-9:_-]{1,128}\Z", re.ASCII)


class FuturesDcaProfileSourceError(ValueError):
    """Raised when an explicit profile source cannot form a journal revision."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class FuturesDcaProfileRevisionSource:
    """Caller-supplied immutable fields; no venue lookup or default is implied."""

    revision_id: str
    symbol: str
    effective_time_us: int
    contract_size: str
    fee_policy_revision: str
    slippage_policy_revision: str
    rounding_policy_revision: str


def build_futures_dca_profile_revision(
    profile: FuturesDcaProfile, source: FuturesDcaProfileRevisionSource
) -> FuturesDcaProfileRevision:
    """Project an explicit source into the journal profile contract."""

    if not isinstance(profile, FuturesDcaProfile) or not isinstance(source, FuturesDcaProfileRevisionSource):
        raise FuturesDcaProfileSourceError("FUTURES_DCA_PROFILE_SOURCE_INVALID", "Profile source güvenli tipte değil.")
    for value in (
        source.revision_id,
        source.symbol,
        source.fee_policy_revision,
        source.slippage_policy_revision,
        source.rounding_policy_revision,
    ):
        if _IDENTIFIER.fullmatch(value or "") is None:
            raise FuturesDcaProfileSourceError("FUTURES_DCA_PROFILE_SOURCE_INVALID", "Profile source identity geçersiz.")
    if type(source.effective_time_us) is not int or source.effective_time_us < 0:
        raise FuturesDcaProfileSourceError("FUTURES_DCA_PROFILE_SOURCE_INVALID", "Profile effective time geçersiz.")
    try:
        contract_size = exact_text(positive(source.contract_size))
    except (TypeError, ValueError) as exc:
        raise FuturesDcaProfileSourceError(
            "FUTURES_DCA_PROFILE_CONTRACT_SIZE_REQUIRED", "Contract-size source tarafından exact pozitif verilmelidir."
        ) from exc
    return FuturesDcaProfileRevision(
        revision_id=source.revision_id,
        venue=profile.venue,
        product=f"{profile.product_family}_{profile.contract_type}",
        symbol=source.symbol,
        settlement_asset=profile.settlement_asset,
        margin_mode=profile.margin_mode,
        position_mode=profile.position_mode,
        effective_time_us=source.effective_time_us,
        contract_size=contract_size,
        fee_policy_revision=source.fee_policy_revision,
        slippage_policy_revision=source.slippage_policy_revision,
        rounding_policy_revision=source.rounding_policy_revision,
    )
