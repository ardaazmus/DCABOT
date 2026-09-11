# CLAIM_REGISTER

Access date: 2026-09-09. Local code inspected: NO. Local tests executed: 0.

## CLM-G01
CLAIM_ID: CLM-G01
PHASE: GLOBAL
TOPIC: Authority
CLAIM: ExecType/event purpose and current order status are distinct concepts; economic FILL should not be conflated with terminal status.
TYPE: DOMAIN
STATUS: VERIFIED
SOURCES: S01, S02
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: ExecType/event purpose and current order status are distinct concepts; economic FILL should not be conflated with terminal status.
SOURCE_SCOPE_LIMIT: FIX supports separation; exact LOCAL_SIMULATOR event names remain local policy
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: fill then final-status fixture
NEGATIVE_EXPECTATION: ORDER_FINAL must not add a second economic fill
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-G02
CLAIM_ID: CLM-G02
PHASE: GLOBAL
TOPIC: Exact numeric
CLAIM: Decimal strings can be represented exactly with explicit rounding/traps; binary float is not suitable as default economic authority.
TYPE: MATHEMATICAL
STATUS: VERIFIED
SOURCES: S05
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Decimal strings can be represented exactly with explicit rounding/traps; binary float is not suitable as default economic authority.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: 0.1+0.2 exact Decimal fixture
NEGATIVE_EXPECTATION: no epsilon equality in economic core
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-G03
CLAIM_ID: CLM-G03
PHASE: GLOBAL
TOPIC: Canonicalization
CLAIM: A canonical serialization plus SHA-256 can produce deterministic content identity.
TYPE: PERSISTENCE
STATUS: VERIFIED
SOURCES: S06, S07
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: A canonical serialization plus SHA-256 can produce deterministic content identity.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: same semantic object/order-normalized -> same digest
NEGATIVE_EXPECTATION: hash mismatch alone must not be labeled economic mismatch
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-G04
CLAIM_ID: CLM-G04
PHASE: GLOBAL
TOPIC: Atomicity
CLAIM: Accepted FILL economic mutations should commit as one semantic transaction.
TYPE: PERSISTENCE
STATUS: LOCAL_CODE_REQUIRED
SOURCES: S08, S09
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Accepted FILL economic mutations should commit as one semantic transaction.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: fault injection at each sub-mutation
NEGATIVE_EXPECTATION: no half-updated fee/position/reserve
REQUIRED_CODE_OR_FIXTURE: LCR-06 transaction boundary required

## CLM-G05
CLAIM_ID: CLM-G05
PHASE: GLOBAL
TOPIC: Feed ordering
CLAIM: Public market feeds can contain sequence gaps/out-of-order messages; receive order alone is not reliable economic order.
TYPE: DATA
STATUS: VERIFIED
SOURCES: S38, S40
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Public market feeds can contain sequence gaps/out-of-order messages; receive order alone is not reliable economic order.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: gap/reorder fixture
NEGATIVE_EXPECTATION: no silent contiguous assumption
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-G06
CLAIM_ID: CLM-G06
PHASE: GLOBAL
TOPIC: UI authority
CLAIM: UI formatting/markers must not be economic authority.
TYPE: UI
STATUS: CONDITIONAL
SOURCES: S05
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: UI formatting/markers must not be economic authority.
SOURCE_SCOPE_LIMIT: Project design rule; source only supports numeric-boundary rationale
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: API exact string vs formatted UI fixture
NEGATIVE_EXPECTATION: UI recomputation cannot change persisted number
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-056-01
CLAIM_ID: CLM-056-01
PHASE: P1.05/P1.06
TOPIC: Metrics
CLAIM: Unrealized PnL excludes trading/funding fees in the cited futures product while closed/realized PnL includes fee/funding components; metrics must not be collapsed.
TYPE: MATHEMATICAL
STATUS: VERIFIED
SOURCES: S15
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Unrealized PnL excludes trading/funding fees in the cited futures product while closed/realized PnL includes fee/funding components; metrics must not be collapsed.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: open vs closed position fixture
NEGATIVE_EXPECTATION: no single PnL scalar with hidden inclusion rules
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-056-02
CLAIM_ID: CLM-056-02
PHASE: P1.05/P1.06
TOPIC: Drawdown
CLAIM: Drawdown must be defined against a peak equity/value series and stored with its sampling convention.
TYPE: MATHEMATICAL
STATUS: CONDITIONAL
SOURCES: S48
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Drawdown must be defined against a peak equity/value series and stored with its sampling convention.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: 1000 peak -> 850 -> 15% drawdown fixture
NEGATIVE_EXPECTATION: do not compare drawdowns with different sampling conventions
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-056-03
CLAIM_ID: CLM-056-03
PHASE: P1.05/P1.06
TOPIC: Run identity
CLAIM: dataset/config/model/kernel/seed/canonicalization versions belong in immutable run identity.
TYPE: PERSISTENCE
STATUS: CONDITIONAL
SOURCES: S06, S07
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: dataset/config/model/kernel/seed/canonicalization versions belong in immutable run identity.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: mutate one identity component -> different run digest
NEGATIVE_EXPECTATION: do not reuse same run id
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-056-04
CLAIM_ID: CLM-056-04
PHASE: P1.05/P1.06
TOPIC: Incomplete result
CLAIM: OPEN_AT_END may report committed realized/unrealized components but must not be presented as fully closed result.
TYPE: DOMAIN
STATUS: CONDITIONAL
SOURCES: S01
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: OPEN_AT_END may report committed realized/unrealized components but must not be presented as fully closed result.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: pending/open position at EOF
NEGATIVE_EXPECTATION: no forced close for convenience
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-056-05
CLAIM_ID: CLM-056-05
PHASE: P1.05/P1.06
TOPIC: Replay
CLAIM: Saved and recomputed results must compare via independent field oracle, not only stored hash.
TYPE: PERSISTENCE
STATUS: LOCAL_CODE_REQUIRED
SOURCES: S06, S07
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Saved and recomputed results must compare via independent field oracle, not only stored hash.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: save/reopen/recompute fixture
NEGATIVE_EXPECTATION: no hash-only proof
REQUIRED_CODE_OR_FIXTURE: LCR-10 serializer/persistence fixture

## CLM-107-01
CLAIM_ID: CLM-107-01
PHASE: P1.07
TOPIC: Order quantities
CLAIM: For active orders, leaves quantity is conceptually remaining quantity and can be checked against original minus cumulative fill.
TYPE: DOMAIN
STATUS: VERIFIED
SOURCES: S03
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: For active orders, leaves quantity is conceptually remaining quantity and can be checked against original minus cumulative fill.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: 1 original, .3 cum -> .7 leaves
NEGATIVE_EXPECTATION: negative leaves => CONFLICT
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-107-02
CLAIM_ID: CLM-107-02
PHASE: P1.07
TOPIC: Final coverage
CLAIM: Full cumulative quantity and lifecycle final coverage should be represented separately.
TYPE: DOMAIN
STATUS: VERIFIED
SOURCES: S01, S02
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Full cumulative quantity and lifecycle final coverage should be represented separately.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: cum reaches original before final coverage
NEGATIVE_EXPECTATION: must not fabricate second fill
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-107-03
CLAIM_ID: CLM-107-03
PHASE: P1.07
TOPIC: OHLC policy
CLAIM: Equality/strict-penetration/placement-bar/gap fill rules are simulator-model policies, not universal market truth.
TYPE: DOMAIN
STATUS: VERIFIED
SOURCES: S11, S12
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Equality/strict-penetration/placement-bar/gap fill rules are simulator-model policies, not universal market truth.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: run same bar under two versioned profiles
NEGATIVE_EXPECTATION: no hidden default presented as venue fact
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-107-04
CLAIM_ID: CLM-107-04
PHASE: P1.07
TOPIC: EOF
CLAIM: EOF must not silently fabricate fill/cancel/expiry; explicit profile may define run-only termination state.
TYPE: DOMAIN
STATUS: CONDITIONAL
SOURCES: S11, S12
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: EOF must not silently fabricate fill/cancel/expiry; explicit profile may define run-only termination state.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: pending order at dataset end
NEGATIVE_EXPECTATION: no synthetic economic fill
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-107-05
CLAIM_ID: CLM-107-05
PHASE: P1.07
TOPIC: Reserve product scope
CLAIM: Spot hold and derivatives order-cost/margin concepts are not one universal reserve scalar.
TYPE: DOMAIN
STATUS: VERIFIED
SOURCES: S10, S19, S20
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Spot hold and derivatives order-cost/margin concepts are not one universal reserve scalar.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: REJECT
EXPECTED_TEST: spot vs derivatives tagged-unit fixture
NEGATIVE_EXPECTATION: no cross-product scalar arithmetic
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-107-06
CLAIM_ID: CLM-107-06
PHASE: P1.07
TOPIC: Reserve owner
CLAIM: Whether local reserve is acquired at INTENT/ACTIVE/FILL is implementation-specific and cannot be proven externally.
TYPE: CODE_BEHAVIOR
STATUS: LOCAL_CODE_REQUIRED
SOURCES: S10, S19
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Whether local reserve is acquired at INTENT/ACTIVE/FILL is implementation-specific and cannot be proven externally.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: DEFER
EXPECTED_TEST: local reducer event fixture
NEGATIVE_EXPECTATION: candidate must not mutate unless local contract explicitly proves it
REQUIRED_CODE_OR_FIXTURE: LCR-01/LCR-02

## CLM-107-07
CLAIM_ID: CLM-107-07
PHASE: P1.07
TOPIC: Initial margin estimate
CLAIM: `initial_margin_estimate` cannot be equated with persistent reserve without local call-chain/schema evidence.
TYPE: CODE_BEHAVIOR
STATUS: LOCAL_CODE_REQUIRED
SOURCES: S19, S20
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: `initial_margin_estimate` cannot be equated with persistent reserve without local call-chain/schema evidence.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: REJECT
EXPECTED_TEST: estimate call-chain vs persisted reserve fixture
NEGATIVE_EXPECTATION: no name-based equivalence
REQUIRED_CODE_OR_FIXTURE: LCR-03

## CLM-107-08
CLAIM_ID: CLM-107-08
PHASE: P1.07
TOPIC: NONE vs zero
CLAIM: `reserve_model=NONE` and explicit numeric zero must be distinct tagged states.
TYPE: API
STATUS: CONDITIONAL
SOURCES: S05, S06
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: `reserve_model=NONE` and explicit numeric zero must be distinct tagged states.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: canonical serialize both
NEGATIVE_EXPECTATION: NONE cannot deserialize to 0
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-107-09
CLAIM_ID: CLM-107-09
PHASE: P1.07
TOPIC: Duplicate
CLAIM: Known duplicate should be idempotent; conflicting duplicate should become CONFLICT without second mutation.
TYPE: PERSISTENCE
STATUS: CONDITIONAL
SOURCES: S04, S38
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Known duplicate should be idempotent; conflicting duplicate should become CONFLICT without second mutation.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: same execution id same/different payload
NEGATIVE_EXPECTATION: no double fee/fill
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-107-10
CLAIM_ID: CLM-107-10
PHASE: P1.07
TOPIC: Atomic fill
CLAIM: position, fee, cum/leaves, reserve, dedupe identity and state version require one semantic commit.
TYPE: PERSISTENCE
STATUS: LOCAL_CODE_REQUIRED
SOURCES: S08, S09
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: position, fee, cum/leaves, reserve, dedupe identity and state version require one semantic commit.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: fault-injection crash/retry
NEGATIVE_EXPECTATION: no partial commit
REQUIRED_CODE_OR_FIXTURE: LCR-06/LCR-07

## CLM-108-01
CLAIM_ID: CLM-108-01
PHASE: P1.08
TOPIC: Deal lifecycle
CLAIM: Active config revision should be immutable for a running deal; copy creates a new revision rather than mutating history.
TYPE: PERSISTENCE
STATUS: CONDITIONAL
SOURCES: S06
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Active config revision should be immutable for a running deal; copy creates a new revision rather than mutating history.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: copy/modify active config fixture
NEGATIVE_EXPECTATION: no retroactive config mutation
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-108-02
CLAIM_ID: CLM-108-02
PHASE: P1.08
TOPIC: Isolation
CLAIM: Each deal must own its order/risk state; shared account effects are explicit account events, not hidden deal mutation.
TYPE: DOMAIN
STATUS: CONDITIONAL
SOURCES: S08
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Each deal must own its order/risk state; shared account effects are explicit account events, not hidden deal mutation.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: two deals same instrument fixture
NEGATIVE_EXPECTATION: no cross-deal order mutation
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-108-03
CLAIM_ID: CLM-108-03
PHASE: P1.08
TOPIC: Lifecycle replay
CLAIM: start/pause/resume/finish/abort events need dedupe and deterministic replay.
TYPE: PERSISTENCE
STATUS: LOCAL_CODE_REQUIRED
SOURCES: S06, S08
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: start/pause/resume/finish/abort events need dedupe and deterministic replay.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: duplicate pause and replay fixture
NEGATIVE_EXPECTATION: no duplicate lifecycle side effect
REQUIRED_CODE_OR_FIXTURE: LCR-02/LCR-07

## CLM-109-01
CLAIM_ID: CLM-109-01
PHASE: P1.09
TOPIC: Sizing units
CLAIM: BASE quantity, QUOTE notional and balance-percent are different input units and require explicit conversion before order quantity.
TYPE: MATHEMATICAL
STATUS: CONDITIONAL
SOURCES: S05, S47
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: BASE quantity, QUOTE notional and balance-percent are different input units and require explicit conversion before order quantity.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: same economic size via tagged inputs
NEGATIVE_EXPECTATION: no scalar addition across units
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-109-02
CLAIM_ID: CLM-109-02
PHASE: P1.09
TOPIC: Venue filters
CLAIM: Tick/step/notional filters are instrument metadata and rounding/validation must be owned by a declared boundary.
TYPE: API
STATUS: VERIFIED
SOURCES: S27, S47
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Tick/step/notional filters are instrument metadata and rounding/validation must be owned by a declared boundary.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: boundary just below/at minimum notional
NEGATIVE_EXPECTATION: UI rounding cannot create accepted order
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-109-03
CLAIM_ID: CLM-109-03
PHASE: P1.09
TOPIC: Ladder conservation
CLAIM: Custom ladder total must equal exact sum of generated order quantities/notionals after declared rounding policy.
TYPE: MATHEMATICAL
STATUS: CONDITIONAL
SOURCES: S05
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Custom ladder total must equal exact sum of generated order quantities/notionals after declared rounding policy.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: sum generated ladder vs budget
NEGATIVE_EXPECTATION: no hidden remainder loss
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-109-04
CLAIM_ID: CLM-109-04
PHASE: P1.09
TOPIC: Reinvestment
CLAIM: Reinvestment should use a specified realized-profit pool; unrealized PnL must not silently increase realized budget.
TYPE: DOMAIN
STATUS: CONDITIONAL
SOURCES: S15
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Reinvestment should use a specified realized-profit pool; unrealized PnL must not silently increase realized budget.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: realized vs unrealized split fixture
NEGATIVE_EXPECTATION: no unrealized-to-budget promotion
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-110-01
CLAIM_ID: CLM-110-01
PHASE: P1.10
TOPIC: Trigger/execution
CLAIM: TP/SL trigger and resulting execution are separate events and may use different reference/price semantics.
TYPE: DOMAIN
STATUS: VERIFIED
SOURCES: S25
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: TP/SL trigger and resulting execution are separate events and may use different reference/price semantics.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: trigger fires but execution price gaps
NEGATIVE_EXPECTATION: trigger price not booked as guaranteed fill
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-110-02
CLAIM_ID: CLM-110-02
PHASE: P1.10
TOPIC: Trailing ratchet
CLAIM: Trailing stop reference should ratchet only in favorable direction after activation for the cited profile.
TYPE: DOMAIN
STATUS: VERIFIED
SOURCES: S26
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Trailing stop reference should ratchet only in favorable direction after activation for the cited profile.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: high-water/low-water monotonic fixture
NEGATIVE_EXPECTATION: reference must not move backward
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-110-03
CLAIM_ID: CLM-110-03
PHASE: P1.10
TOPIC: Multi-TP conservation
CLAIM: Sum of accepted TP exit quantities cannot exceed currently closable position; partial exits must recompute remaining gate.
TYPE: MATHEMATICAL
STATUS: CONDITIONAL
SOURCES: S25
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Sum of accepted TP exit quantities cannot exceed currently closable position; partial exits must recompute remaining gate.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: three TP slices sum exactly position
NEGATIVE_EXPECTATION: no negative remaining qty
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-110-04
CLAIM_ID: CLM-110-04
PHASE: P1.10
TOPIC: Cancel-replace
CLAIM: Late fill during cancel/replace must be reconciled by execution identity, not assumed impossible.
TYPE: PERSISTENCE
STATUS: LOCAL_CODE_REQUIRED
SOURCES: S01, S04
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Late fill during cancel/replace must be reconciled by execution identity, not assumed impossible.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: cancel then new late execution fixture
NEGATIVE_EXPECTATION: no double replacement/over-close
REQUIRED_CODE_OR_FIXTURE: LCR-07

## CLM-111-01
CLAIM_ID: CLM-111-01
PHASE: P1.11
TOPIC: Account scope
CLAIM: Shared account balance/exposure is account-level state; pair/deal position ownership remains separately attributable.
TYPE: DOMAIN
STATUS: CONDITIONAL
SOURCES: S19, S20
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Shared account balance/exposure is account-level state; pair/deal position ownership remains separately attributable.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: two deals reserve from same account
NEGATIVE_EXPECTATION: no duplicate counting of same collateral
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-111-02
CLAIM_ID: CLM-111-02
PHASE: P1.11
TOPIC: Concurrent reservation
CLAIM: Concurrent order reservations must serialize/compare version so both cannot spend the same available capacity.
TYPE: PERSISTENCE
STATUS: LOCAL_CODE_REQUIRED
SOURCES: S08, S09
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Concurrent order reservations must serialize/compare version so both cannot spend the same available capacity.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: two writers race fixture
NEGATIVE_EXPECTATION: no oversubscription
REQUIRED_CODE_OR_FIXTURE: LCR-06

## CLM-111-03
CLAIM_ID: CLM-111-03
PHASE: P1.11
TOPIC: Replay
CLAIM: Account reservation/fill/release replay must be idempotent across restart.
TYPE: PERSISTENCE
STATUS: LOCAL_CODE_REQUIRED
SOURCES: S08
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Account reservation/fill/release replay must be idempotent across restart.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: restart between reserve and fill
NEGATIVE_EXPECTATION: no double reserve/release
REQUIRED_CODE_OR_FIXTURE: LCR-07

## CLM-112-01
CLAIM_ID: CLM-112-01
PHASE: P1.12
TOPIC: Product separation
CLAIM: Spot inventory and linear futures position/margin are different economic states and should not share one untyped reserve/fee model.
TYPE: DOMAIN
STATUS: VERIFIED
SOURCES: S10, S15, S19
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Spot inventory and linear futures position/margin are different economic states and should not share one untyped reserve/fee model.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: REJECT
EXPECTED_TEST: spot buy vs futures long fixtures
NEGATIVE_EXPECTATION: no shared untagged ledger
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-112-02
CLAIM_ID: CLM-112-02
PHASE: P1.12
TOPIC: Linear PnL
CLAIM: For cited USDT linear contracts, long UPL is Q×(P−Entry) and short UPL Q×(Entry−P); leverage changes margin/ROI, not raw PnL.
TYPE: MATHEMATICAL
STATUS: VERIFIED
SOURCES: S15
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: For cited USDT linear contracts, long UPL is Q×(P−Entry) and short UPL Q×(Entry−P); leverage changes margin/ROI, not raw PnL.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: long/short up/down fixtures
NEGATIVE_EXPECTATION: do not multiply PnL by leverage
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-112-03
CLAIM_ID: CLM-112-03
PHASE: P1.12
TOPIC: Funding
CLAIM: For cited USDT perpetuals, funding fee is position value × funding rate at funding time, with position value quantity × mark price.
TYPE: MATHEMATICAL
STATUS: VERIFIED
SOURCES: S16
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: For cited USDT perpetuals, funding fee is position value × funding rate at funding time, with position value quantity × mark price.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: positive/negative funding fixtures
NEGATIVE_EXPECTATION: no funding outside effective timestamp
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-112-04
CLAIM_ID: CLM-112-04
PHASE: P1.12
TOPIC: Mark authority
CLAIM: Mark/index/last are distinct; mark price can be risk/liquidation authority while UI UPL may display last-price based value.
TYPE: DOMAIN
STATUS: VERIFIED
SOURCES: S15, S17
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Mark/index/last are distinct; mark price can be risk/liquidation authority while UI UPL may display last-price based value.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: mark/last divergence fixture
NEGATIVE_EXPECTATION: no silent last-price liquidation
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-112-05
CLAIM_ID: CLM-112-05
PHASE: P1.12
TOPIC: Margin scope
CLAIM: Cross/isolated account equations and risk tiers are venue/product/mode/version specific.
TYPE: MATHEMATICAL
STATUS: VERIFIED
SOURCES: S19, S20, S22
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Cross/isolated account equations and risk tiers are venue/product/mode/version specific.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: DEFER
EXPECTED_TEST: mode/risk-tier boundary fixtures
NEGATIVE_EXPECTATION: no universal margin formula
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-112-06
CLAIM_ID: CLM-112-06
PHASE: P1.12
TOPIC: Liquidation
CLAIM: Liquidation formula cannot be ACCEPTed until a venue/product/mode/version profile is selected and frozen.
TYPE: MATHEMATICAL
STATUS: BLOCKED
SOURCES: S21, S22
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Liquidation formula cannot be ACCEPTed until a venue/product/mode/version profile is selected and frozen.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: UNRESOLVED
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: DEFER
EXPECTED_TEST: selected-profile independent liquidation fixtures
NEGATIVE_EXPECTATION: no generic liquidation scalar
REQUIRED_CODE_OR_FIXTURE: LCR-05 + venue profile

## CLM-112-07
CLAIM_ID: CLM-112-07
PHASE: P1.12
TOPIC: Partial close
CLAIM: Fee/funding allocation on partial close follows venue accounting policy and must be explicit.
TYPE: MATHEMATICAL
STATUS: VERIFIED
SOURCES: S15
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Fee/funding allocation on partial close follows venue accounting policy and must be explicit.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: partial-close prorating fixture for cited profile
NEGATIVE_EXPECTATION: no full-close fee allocation on partial close
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-113-01
CLAIM_ID: CLM-113-01
PHASE: P1.13
TOPIC: Grid levels
CLAIM: Arithmetic and geometric grid level generation are mathematically distinct.
TYPE: MATHEMATICAL
STATUS: VERIFIED
SOURCES: S28
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Arithmetic and geometric grid level generation are mathematically distinct.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: same bounds/count generate different levels
NEGATIVE_EXPECTATION: do not alias geometric to arithmetic
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-113-02
CLAIM_ID: CLM-113-02
PHASE: P1.13
TOPIC: Grid families
CLAIM: Trailing/reverse/infinity/leveraged grid must be separate profiles; names alone do not imply identical risk/state.
TYPE: DOMAIN
STATUS: CONDITIONAL
SOURCES: S28, S29
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Trailing/reverse/infinity/leveraged grid must be separate profiles; names alone do not imply identical risk/state.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: profile id changes state machine
NEGATIVE_EXPECTATION: no shared implicit behavior
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-113-03
CLAIM_ID: CLM-113-03
PHASE: P1.13
TOPIC: Inventory
CLAIM: Grid profit and total equity are not interchangeable because open inventory valuation/fees remain.
TYPE: MATHEMATICAL
STATUS: CONDITIONAL
SOURCES: S28, S15
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Grid profit and total equity are not interchangeable because open inventory valuation/fees remain.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: realized grid cycle + open inventory fixture
NEGATIVE_EXPECTATION: no realized-grid-profit==equity claim
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-113-04
CLAIM_ID: CLM-113-04
PHASE: P1.13
TOPIC: Reverse/infinity exact semantics
CLAIM: Exact reverse/infinity-grid semantics are product-specific and insufficiently standardized for a universal model.
TYPE: DOMAIN
STATUS: NOT_VERIFIED
SOURCES: S29
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Exact reverse/infinity-grid semantics are product-specific and insufficiently standardized for a universal model.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: DEFER
EXPECTED_TEST: product-specific fixture before implementation
NEGATIVE_EXPECTATION: no universal formula
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-114-01
CLAIM_ID: CLM-114-01
PHASE: P1.14
TOPIC: Rebalance triggers
CLAIM: Time-based and ratio/threshold rebalancing are distinct trigger policies.
TYPE: DOMAIN
STATUS: VERIFIED
SOURCES: S30
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Time-based and ratio/threshold rebalancing are distinct trigger policies.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: same portfolio under time vs threshold trigger
NEGATIVE_EXPECTATION: no trigger-policy merge
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-114-02
CLAIM_ID: CLM-114-02
PHASE: P1.14
TOPIC: Warmup
CLAIM: Indicators requiring history need warm-up/closed-bar policy; warm-up data must not cause normal economic orders.
TYPE: DATA
STATUS: VERIFIED
SOURCES: S33
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Indicators requiring history need warm-up/closed-bar policy; warm-up data must not cause normal economic orders.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: warm-up period with zero orders
NEGATIVE_EXPECTATION: no fill during warm-up
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-114-03
CLAIM_ID: CLM-114-03
PHASE: P1.14
TOPIC: Signal dedupe
CLAIM: External/webhook signal replay must have event identity and idempotence.
TYPE: SECURITY
STATUS: CONDITIONAL
SOURCES: S38
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: External/webhook signal replay must have event identity and idempotence.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: duplicate signal payload/id
NEGATIVE_EXPECTATION: no duplicate order intent
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-114-04
CLAIM_ID: CLM-114-04
PHASE: P1.14
TOPIC: Template authority
CLAIM: Imported templates are data/config only and cannot themselves bypass core acceptance authority.
TYPE: SECURITY
STATUS: CONDITIONAL
SOURCES: S06, S46
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Imported templates are data/config only and cannot themselves bypass core acceptance authority.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: malformed/untrusted template import
NEGATIVE_EXPECTATION: no executable code/order side effect
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-115-01
CLAIM_ID: CLM-115-01
PHASE: P1.15
TOPIC: Hedge/netting
CLAIM: One-way/net and hedge position modes have different long/short state semantics.
TYPE: DOMAIN
STATUS: VERIFIED
SOURCES: S23
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: One-way/net and hedge position modes have different long/short state semantics.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: opposite-side order in each mode
NEGATIVE_EXPECTATION: no silent mode conversion
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-115-02
CLAIM_ID: CLM-115-02
PHASE: P1.15
TOPIC: Reduce-only
CLAIM: Reduce-only intent must never intentionally increase opposite exposure.
TYPE: DOMAIN
STATUS: VERIFIED
SOURCES: S24
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Reduce-only intent must never intentionally increase opposite exposure.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: reduce-only qty > position
NEGATIVE_EXPECTATION: no position flip
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-115-03
CLAIM_ID: CLM-115-03
PHASE: P1.15
TOPIC: Cross account
CLAIM: Cross margin risk can be account-level rather than isolated position-level.
TYPE: DOMAIN
STATUS: VERIFIED
SOURCES: S19, S20
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Cross margin risk can be account-level rather than isolated position-level.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: shared loss affects account margin
NEGATIVE_EXPECTATION: no isolated-only risk check
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-115-04
CLAIM_ID: CLM-115-04
PHASE: P1.15
TOPIC: Two-leg lifecycle
CLAIM: One-leg-filled/other-leg-unfilled is a valid recoverable state; local simulator must not pretend multi-leg atomic market execution.
TYPE: DOMAIN
STATUS: CONDITIONAL
SOURCES: S01
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: One-leg-filled/other-leg-unfilled is a valid recoverable state; local simulator must not pretend multi-leg atomic market execution.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: leg A fill, leg B no fill
NEGATIVE_EXPECTATION: do not roll back real accepted A fill
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-115-05
CLAIM_ID: CLM-115-05
PHASE: P1.15
TOPIC: Two-leg recovery
CLAIM: Timeout/recovery/partial hedge ownership is local strategy policy and requires explicit reducer/persistence evidence.
TYPE: CODE_BEHAVIOR
STATUS: LOCAL_CODE_REQUIRED
SOURCES: S08
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Timeout/recovery/partial hedge ownership is local strategy policy and requires explicit reducer/persistence evidence.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: DEFER
EXPECTED_TEST: crash after leg A commit fixture
NEGATIVE_EXPECTATION: no synthetic hedge without policy
REQUIRED_CODE_OR_FIXTURE: LCR-09

## CLM-115-06
CLAIM_ID: CLM-115-06
PHASE: P1.15
TOPIC: One-leg liquidation
CLAIM: If one leg is liquidated, survivor state and shared margin must be recomputed; automatic survivor closure is not universal.
TYPE: DOMAIN
STATUS: CONDITIONAL
SOURCES: S19, S21
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: If one leg is liquidated, survivor state and shared margin must be recomputed; automatic survivor closure is not universal.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: DEFER
EXPECTED_TEST: one-leg liquidation fixture under selected profile
NEGATIVE_EXPECTATION: no assumed atomic two-leg liquidation
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-116-01
CLAIM_ID: CLM-116-01
PHASE: P1.16
TOPIC: Chronological split
CLAIM: Time-series validation must preserve chronology; scikit-learn TimeSeriesSplit uses past folds to predict later test folds and offers a gap.
TYPE: DATA
STATUS: VERIFIED
SOURCES: S31
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Time-series validation must preserve chronology; scikit-learn TimeSeriesSplit uses past folds to predict later test folds and offers a gap.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: assert max(train_time)<min(test_time)
NEGATIVE_EXPECTATION: no future row in training
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-116-02
CLAIM_ID: CLM-116-02
PHASE: P1.16
TOPIC: OOS freeze
CLAIM: Once an OOS period is inspected and tuning is performed against it, it is no longer untouched evaluation; a new untouched holdout is required for fresh evaluation.
TYPE: DATA
STATUS: VERIFIED
SOURCES: S34, S35, S36
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Once an OOS period is inspected and tuning is performed against it, it is no longer untouched evaluation; a new untouched holdout is required for fresh evaluation.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: lineage flag after OOS inspection+tuning
NEGATIVE_EXPECTATION: do not retain untouched label
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-116-03
CLAIM_ID: CLM-116-03
PHASE: P1.16
TOPIC: Purge/embargo
CLAIM: Overlapping labels/serial dependence can require purge/embargo or gap; exact horizon depends on labeling/features.
TYPE: DATA
STATUS: CONDITIONAL
SOURCES: S31, S37
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Overlapping labels/serial dependence can require purge/embargo or gap; exact horizon depends on labeling/features.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: label overlap boundary fixture
NEGATIVE_EXPECTATION: no hard-coded universal gap
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-116-04
CLAIM_ID: CLM-116-04
PHASE: P1.16
TOPIC: Warmup leakage
CLAIM: Indicator warm-up belongs before evaluation decision and must not create trades.
TYPE: DATA
STATUS: VERIFIED
SOURCES: S33
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Indicator warm-up belongs before evaluation decision and must not create trades.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: warm-up event ledger empty
NEGATIVE_EXPECTATION: no warm-up fill
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-116-05
CLAIM_ID: CLM-116-05
PHASE: P1.16
TOPIC: Multiple testing
CLAIM: Repeated parameter/model trials increase selection/backtest-overfitting risk; trial count and selection protocol must be persisted.
TYPE: DATA
STATUS: VERIFIED
SOURCES: S35, S36
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Repeated parameter/model trials increase selection/backtest-overfitting risk; trial count and selection protocol must be persisted.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: 100 trials stored including failures
NEGATIVE_EXPECTATION: do not retain only winner
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-116-06
CLAIM_ID: CLM-116-06
PHASE: P1.16
TOPIC: Stress separation
CLAIM: Stress/slippage/latency/ambiguity scenarios must be separately identified from normal backtest.
TYPE: DATA
STATUS: CONDITIONAL
SOURCES: S13
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Stress/slippage/latency/ambiguity scenarios must be separately identified from normal backtest.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: base vs stress result ids differ
NEGATIVE_EXPECTATION: no overwrite normal result
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-117-01
CLAIM_ID: CLM-117-01
PHASE: P1.17
TOPIC: Public feed
CLAIM: Read-only/public feeds can be consumed without private credentials for supported public channels; local simulated execution id remains separate.
TYPE: API
STATUS: VERIFIED
SOURCES: S39, S40
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Read-only/public feeds can be consumed without private credentials for supported public channels; local simulated execution id remains separate.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: feed event -> local sim id fixture
NEGATIVE_EXPECTATION: no venue order id fabrication
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-117-02
CLAIM_ID: CLM-117-02
PHASE: P1.17
TOPIC: Gap/stale
CLAIM: Sequence gap/out-of-order/stale data requires explicit state/recovery rather than silent continuity.
TYPE: DATA
STATUS: VERIFIED
SOURCES: S38, S40
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Sequence gap/out-of-order/stale data requires explicit state/recovery rather than silent continuity.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: skip sequence and old timestamp
NEGATIVE_EXPECTATION: no economic event from stale/quarantined input
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-117-03
CLAIM_ID: CLM-117-03
PHASE: P1.17
TOPIC: Clock
CLAIM: source event time and receive/processing times are distinct and should all be retained where available.
TYPE: DATA
STATUS: VERIFIED
SOURCES: S40
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: source event time and receive/processing times are distinct and should all be retained where available.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: delayed message fixture
NEGATIVE_EXPECTATION: processing time cannot replace trade time
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-118-01
CLAIM_ID: CLM-118-01
PHASE: P1.18
TOPIC: Explanation authority
CLAIM: Rule-based or optional LLM explanations must be read-only projections of authoritative state.
TYPE: UI
STATUS: CONDITIONAL
SOURCES: S06
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Rule-based or optional LLM explanations must be read-only projections of authoritative state.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: same state -> explanation; attempted action rejected
NEGATIVE_EXPECTATION: LLM cannot emit economic FILL
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-118-02
CLAIM_ID: CLM-118-02
PHASE: P1.18
TOPIC: Notification dedupe
CLAIM: Notifications should be keyed to authoritative event identity/severity and deduped on replay.
TYPE: PERSISTENCE
STATUS: CONDITIONAL
SOURCES: S04
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Notifications should be keyed to authoritative event identity/severity and deduped on replay.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: replay same rejection event
NEGATIVE_EXPECTATION: no duplicate notification
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-118-03
CLAIM_ID: CLM-118-03
PHASE: P1.18
TOPIC: Template integrity
CLAIM: Shared template version/hash/integrity should be verified before import and must remain non-executable data.
TYPE: SECURITY
STATUS: CONDITIONAL
SOURCES: S06, S07, S46
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Shared template version/hash/integrity should be verified before import and must remain non-executable data.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: hash mismatch/malformed archive fixture
NEGATIVE_EXPECTATION: no import on mismatch
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-119-01
CLAIM_ID: CLM-119-01
PHASE: P1.19
TOPIC: 320px reflow
CLAIM: WCAG 2.2 reflow guidance includes 320 CSS px width behavior for content intended to reflow.
TYPE: UI
STATUS: VERIFIED
SOURCES: S41, S42
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: WCAG 2.2 reflow guidance includes 320 CSS px width behavior for content intended to reflow.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: 320px viewport no essential horizontal loss
NEGATIVE_EXPECTATION: do not hide risk state by clipping
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-119-02
CLAIM_ID: CLM-119-02
PHASE: P1.19
TOPIC: Keyboard/focus/contrast
CLAIM: Keyboard operability, focus visibility and contrast are accessibility gates.
TYPE: UI
STATUS: VERIFIED
SOURCES: S41
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Keyboard operability, focus visibility and contrast are accessibility gates.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: keyboard-only path + focus checks
NEGATIVE_EXPECTATION: no color-only risk meaning
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-119-03
CLAIM_ID: CLM-119-03
PHASE: P1.19
TOPIC: Windows offline
CLAIM: Windows/MSIX tooling supports disconnected packaging scenarios, but LOCAL_SIMULATOR offline install/startup needs E2E proof.
TYPE: SECURITY
STATUS: LOCAL_CODE_REQUIRED
SOURCES: S43, S44
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Windows/MSIX tooling supports disconnected packaging scenarios, but LOCAL_SIMULATOR offline install/startup needs E2E proof.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: clean offline VM install/startup/reopen
NEGATIVE_EXPECTATION: no network dependency hidden
REQUIRED_CODE_OR_FIXTURE: LCR-11

## CLM-119-04
CLAIM_ID: CLM-119-04
PHASE: P1.19
TOPIC: Archive/export security
CLAIM: Untrusted ZIP extraction and spreadsheet CSV formula interpretation are security risks requiring import/export validation.
TYPE: SECURITY
STATUS: VERIFIED
SOURCES: S45, S46
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Untrusted ZIP extraction and spreadsheet CSV formula interpretation are security risks requiring import/export validation.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: path traversal, oversized archive policy, CSV formula prefix fixtures
NEGATIVE_EXPECTATION: no raw dangerous cell/archive extraction
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-120-01
CLAIM_ID: CLM-120-01
PHASE: P1.20
TOPIC: Acceptance
CLAIM: Menu/feature visibility is not evidence of economic implementation; acceptance requires data/math/core/persistence/UI/security/E2E evidence.
TYPE: DOMAIN
STATUS: CONDITIONAL
SOURCES: S08, S41, S43
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Menu/feature visibility is not evidence of economic implementation; acceptance requires data/math/core/persistence/UI/security/E2E evidence.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: feature matrix links to test/evidence ids
NEGATIVE_EXPECTATION: no menu-only PASS
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.

## CLM-120-02
CLAIM_ID: CLM-120-02
PHASE: P1.20
TOPIC: Independent review
CLAIM: Final acceptance must include an oracle/replay path independent from production helpers for critical math/state.
TYPE: DOMAIN
STATUS: CONDITIONAL
SOURCES: S05, S06
SOURCE_SECTIONS: exact source heading(s) are enumerated per source ID in `sources/SOURCE_CARDS.md`; only those scoped sections support this claim
EVIDENCE_SUMMARY: Final acceptance must include an oracle/replay path independent from production helpers for critical math/state.
SOURCE_SCOPE_LIMIT: Source scope is limited to the cited standard/product/method; no local implementation claim is inferred.
CONFLICT_STATUS: NONE/SEE_SOURCE_CONFLICTS_WHERE_APPLICABLE
LOCAL_APPLICABILITY: Research design only until local code/test gates pass.
IMPLEMENTATION_DECISION: ACCEPT
EXPECTED_TEST: oracle vs production fixture
NEGATIVE_EXPECTATION: no same-helper self-verification
REQUIRED_CODE_OR_FIXTURE: No local code required for the external-domain claim; implementation still requires its phase acceptance tests.
