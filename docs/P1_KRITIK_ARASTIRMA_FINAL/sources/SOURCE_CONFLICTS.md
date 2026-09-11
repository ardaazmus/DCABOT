# SOURCE_CONFLICTS

## CONFLICT-01 — Historical OHLC equality/gap policy
SOURCE_A: S11 QuantConnect Equity Fill Model
SOURCE_B: S12 QuantConnect Latest Price Fill Model
CONFLICTING_PROPOSITIONS: order/data models use different inequalities and fill-price handling.
PRODUCT_MARKET_VERSION_SCOPE: historical simulation models, not a live venue contract.
PRECEDENCE_REASON: no source is universal; selected LOCAL_SIMULATOR execution profile must version its rule.
CONFLICT_STATUS: RESOLVED
SELECTED_RULE: policy is explicit/versioned; hidden universal equality rule rejected.
DO_NOT_IMPLEMENT_IF_UNRESOLVED: YES

## CONFLICT-02 — Bybit mark-price transition in September 2026
SOURCE_A: S17 current help article (last updated 2026-09-04)
SOURCE_B: S18 transition announcement (2026-09-01, transition Sep 2–7)
CONFLICTING_PROPOSITIONS: transition notice describes a temporary migration while current help describes active formula family.
PRODUCT_MARKET_VERSION_SCOPE: Bybit perpetual/expiry mark-price method around Sep 2026.
PRECEDENCE_REASON: after announced transition end, current product help page is the narrower ongoing contract; announcement remains historical evidence.
CONFLICT_STATUS: RESOLVED
SELECTED_RULE: freeze source/version/date in venue profile; never assume formula across versions.
DO_NOT_IMPLEMENT_IF_UNRESOLVED: YES

## CONFLICT-03 — UI UPL price vs risk price
SOURCE_A: S15 shows default displayed UPL can use Last Traded Price and exposes Mark-based alternative.
SOURCE_B: S17 uses Mark Price for risk/liquidation role in cited product.
CONFLICTING_PROPOSITIONS: one price can be display basis while another is risk authority.
PRODUCT_MARKET_VERSION_SCOPE: cited Bybit USDT derivatives.
PRECEDENCE_REASON: purpose-specific scope; display metric and risk engine are different contracts.
CONFLICT_STATUS: RESOLVED
SELECTED_RULE: store price authority per calculation; UI cannot substitute its display price for risk price.
DO_NOT_IMPLEMENT_IF_UNRESOLVED: YES

## CONFLICT-04 — Spot hold vs derivatives margin/order-cost semantics
SOURCE_A: S10
SOURCE_B: S19/S20
CONFLICTING_PROPOSITIONS: reserved resource can be spot-held asset or account margin requirement.
PRODUCT_MARKET_VERSION_SCOPE: different product families.
PRECEDENCE_REASON: product scope separation.
CONFLICT_STATUS: RESOLVED
SELECTED_RULE: typed reserve profiles; universal untyped scalar rejected.
DO_NOT_IMPLEMENT_IF_UNRESOLVED: YES

## CONFLICT-05 — Walk-forward vs alternative purged validation
SOURCE_A: S31/S32/S34 walk-forward/time split guidance
SOURCE_B: S37 purged/embargo financial-validation context
CONFLICTING_PROPOSITIONS: no single validation scheme is universally superior for all feature/label structures.
PRODUCT_MARKET_VERSION_SCOPE: research methodology.
PRECEDENCE_REASON: selection depends on label overlap, feature horizon and evaluation objective.
CONFLICT_STATUS: UNRESOLVED (method superiority), RESOLVED (minimum no-leakage requirement)
SELECTED_RULE: chronology + lineage + explicit gap/purge/embargo policy; do not claim universal best method.
DO_NOT_IMPLEMENT_IF_UNRESOLVED: NO, provided chosen policy is versioned and leakage-tested.

## CONFLICT-06 — Partial-fill splitting vs fee/rounding equality
SOURCE_A: exact quantity conservation invariant
SOURCE_B: venue fees/rounding can be charged/rounded per fill.
CONFLICTING_PROPOSITIONS: splitting one economic quantity into fills may alter rounded fees even when quantity/cost sum is conserved.
PRODUCT_MARKET_VERSION_SCOPE: fee policy dependent.
PRECEDENCE_REASON: venue fee event/rounding owner overrides generic metamorphic fee equality.
CONFLICT_STATUS: UNRESOLVED until fee policy selected
SELECTED_RULE: quantity/cost conservation mandatory; fee equality CONDITIONAL.
DO_NOT_IMPLEMENT_IF_UNRESOLVED: YES for exact fee-equivalence assertion.
