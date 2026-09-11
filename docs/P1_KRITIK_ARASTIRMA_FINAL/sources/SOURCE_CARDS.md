# SOURCE_CARDS

ACCESS_DATE for all cards: 2026-09-09.

## S01 — Order State Changes
SOURCE_ID: S01
PUBLISHER: FIX Trading Community
TITLE: Order State Changes
URL: https://www.fixtrading.org/online-specification/order-state-changes/
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: FIX Latest
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: FIX Latest
EXACT_SECTION_OR_HEADING: Order State Changes; ExecutionReport / OrdStatus / ExecType discussion
SUPPORTED_CLAIMS: General order state model; ExecType vs OrdStatus; leaves/cumulative concepts
UNSUPPORTED_CLAIMS: Does not define LOCAL_SIMULATOR state names or chosen OHLC policy
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S02 — FIX Latest Specification — Order State Changes
SOURCE_ID: S02
PUBLISHER: FIX Trading Community
TITLE: FIX Latest Specification — Order State Changes
URL: https://www.fixtrading.org/packages/fix-latest-order-state-changes/
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: EP284
DOC_LAST_UPDATED: 2023-11-19
PRODUCT_VERSION_APPLICABILITY: EP284
EXACT_SECTION_OR_HEADING: FIX Latest Order State Changes package; Version EP284 metadata
SUPPORTED_CLAIMS: Normative FIX order-state package/version anchor
UNSUPPORTED_CLAIMS: Exchange-specific contracts can override/generalize differently
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S03 — FIX 5.0 SP2 Field 151 — LeavesQty
SOURCE_ID: S03
PUBLISHER: FIX Trading Community
TITLE: FIX 5.0 SP2 Field 151 — LeavesQty
URL: https://fiximate.fixtrading.org/legacy/en/FIX.5.0/tag151.html
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: FIX 5.0 SP2
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: FIX 5.0 SP2
EXACT_SECTION_OR_HEADING: Field 151 (LeavesQty) description / quantity-remaining semantics
SUPPORTED_CLAIMS: LeavesQty quantity remaining; relation to OrderQty/CumQty for active order
UNSUPPORTED_CLAIMS: Does not define terminal remainder in LOCAL_SIMULATOR
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S04 — FIX 5.0 SP2 Field 17 — ExecID
SOURCE_ID: S04
PUBLISHER: FIX Trading Community
TITLE: FIX 5.0 SP2 Field 17 — ExecID
URL: https://fiximate.fixtrading.org/legacy/en/FIX.5.0SP2/tag17.html
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: FIX 5.0 SP2
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: FIX 5.0 SP2
EXACT_SECTION_OR_HEADING: Field 17 (ExecID) description
SUPPORTED_CLAIMS: Execution-report identity field semantics
UNSUPPORTED_CLAIMS: Does not prove local dedupe key composition
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S05 — decimal — Decimal fixed-point and floating-point arithmetic
SOURCE_ID: S05
PUBLISHER: Python Software Foundation
TITLE: decimal — Decimal fixed-point and floating-point arithmetic
URL: https://docs.python.org/3/library/decimal.html
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Python 3.14.7 docs observed
DOC_LAST_UPDATED: 2026-09-06 observed in search index
PRODUCT_VERSION_APPLICABILITY: Python 3.14.7 docs observed
EXACT_SECTION_OR_HEADING: Quick-start tutorial; Contexts; Signals; FloatOperation; quantize()
SUPPORTED_CLAIMS: Exact decimal string conversion; contexts, traps, explicit rounding
UNSUPPORTED_CLAIMS: Does not mandate Fraction internally or venue rounding mode
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S06 — RFC 8785 — JSON Canonicalization Scheme (JCS)
SOURCE_ID: S06
PUBLISHER: RFC Editor / IETF
TITLE: RFC 8785 — JSON Canonicalization Scheme (JCS)
URL: https://www.rfc-editor.org/rfc/rfc8785.html
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: RFC 8785
DOC_LAST_UPDATED: 2020-06
PRODUCT_VERSION_APPLICABILITY: RFC 8785
EXACT_SECTION_OR_HEADING: Section 3 — Generation of Canonical JSON Data
SUPPORTED_CLAIMS: Deterministic JSON representation suitable for repeatable hashing/signatures
UNSUPPORTED_CLAIMS: Does not select application schema or Decimal encoding
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S07 — Secure Hash Standard (SHS), FIPS 180-4
SOURCE_ID: S07
PUBLISHER: NIST
TITLE: Secure Hash Standard (SHS), FIPS 180-4
URL: https://www.nist.gov/publications/secure-hash-standard
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: FIPS 180-4
DOC_LAST_UPDATED: 2024-07-25 page update
PRODUCT_VERSION_APPLICABILITY: FIPS 180-4
EXACT_SECTION_OR_HEADING: Secure Hash Standard; SHA-256 family definition
SUPPORTED_CLAIMS: SHA-2 including SHA-256
UNSUPPORTED_CLAIMS: Hash equality does not prove economic correctness
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S08 — SQLite Is Transactional
SOURCE_ID: S08
PUBLISHER: SQLite
TITLE: SQLite Is Transactional
URL: https://www.sqlite.org/transactional.html
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Current documentation
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: Current documentation
EXACT_SECTION_OR_HEADING: Transactions are atomic / ACID transactional behavior
SUPPORTED_CLAIMS: ACID/atomic transaction behavior
UNSUPPORTED_CLAIMS: Does not prove LOCAL_SIMULATOR uses SQLite or correct transaction boundary
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S09 — Write-Ahead Logging
SOURCE_ID: S09
PUBLISHER: SQLite
TITLE: Write-Ahead Logging
URL: https://www.sqlite.org/wal.html
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Current documentation
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: Current documentation
EXACT_SECTION_OR_HEADING: How WAL Works; Concurrency; Checkpointing
SUPPORTED_CLAIMS: WAL transaction/recovery/concurrency characteristics
UNSUPPORTED_CLAIMS: Does not prove application durability settings
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S10 — Advanced Trade — Order management
SOURCE_ID: S10
PUBLISHER: Coinbase
TITLE: Advanced Trade — Order management
URL: https://help.coinbase.com/en/coinbase/trading-and-funding/advanced-trade/order-management
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Current help article
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: Current help article
EXACT_SECTION_OR_HEADING: Order management; open orders / holds / partial fills / cancellation
SUPPORTED_CLAIMS: Spot order holds, partial fill/cancel product behavior
UNSUPPORTED_CLAIMS: Not a universal reserve definition
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S11 — Equity Fill Model
SOURCE_ID: S11
PUBLISHER: QuantConnect
TITLE: Equity Fill Model
URL: https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/trade-fills/supported-models/equity-model
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: LEAN docs v2
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: LEAN docs v2
EXACT_SECTION_OR_HEADING: Limit Orders; Stop Market Orders; stale/same-timestamp guard
SUPPORTED_CLAIMS: Concrete historical fill policy; same/stale bar guards; limit/stop behavior
UNSUPPORTED_CLAIMS: Not venue truth; not the only valid simulator model
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S12 — Latest Price Fill Model
SOURCE_ID: S12
PUBLISHER: QuantConnect
TITLE: Latest Price Fill Model
URL: https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/trade-fills/supported-models/latest-price-model
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: LEAN docs v2
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: LEAN docs v2
EXACT_SECTION_OR_HEADING: Limit Orders / latest-price fill semantics
SUPPORTED_CLAIMS: Alternative concrete fill/equality/price policy
UNSUPPORTED_CLAIMS: Not universal; differs from S11
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S13 — Supported Slippage Models
SOURCE_ID: S13
PUBLISHER: QuantConnect
TITLE: Supported Slippage Models
URL: https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/slippage/supported-models
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: LEAN docs v2
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: LEAN docs v2
EXACT_SECTION_OR_HEADING: Null Slippage; Constant Slippage; Volume Share Slippage
SUPPORTED_CLAIMS: Null/constant/volume-share slippage model examples
UNSUPPORTED_CLAIMS: Does not prove dataset volume quality or chosen model
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S14 — Spot Trading: Fees Explained
SOURCE_ID: S14
PUBLISHER: Bybit
TITLE: Spot Trading: Fees Explained
URL: https://www.bybit.com/en/help-center/article/Bybit-Spot-Fees-Explained
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Current help article
DOC_LAST_UPDATED: 2026-06-24
PRODUCT_VERSION_APPLICABILITY: Current help article
EXACT_SECTION_OR_HEADING: Spot Trading Fees / fee calculation
SUPPORTED_CLAIMS: Spot fee basis/fee asset behavior for cited product
UNSUPPORTED_CLAIMS: Not universal spot fee policy
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S15 — P&L Calculations (USDT Perpetual and Expiry Contracts)
SOURCE_ID: S15
PUBLISHER: Bybit
TITLE: P&L Calculations (USDT Perpetual and Expiry Contracts)
URL: https://www.bybit.com/en/help-center/article/Profit-Loss-calculations-USDT-Contract
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: USDT Perpetual/Expiry
DOC_LAST_UPDATED: 2026-03-19
PRODUCT_VERSION_APPLICABILITY: USDT Perpetual/Expiry
EXACT_SECTION_OR_HEADING: Average Entry Price; Unrealized P&L; Closed P&L; Realized P&L
SUPPORTED_CLAIMS: AEP, long/short UPL, realized/closed PnL and fee/funding distinction
UNSUPPORTED_CLAIMS: Does not apply to inverse contracts or other venues
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S16 — Funding Fee Calculation
SOURCE_ID: S16
PUBLISHER: Bybit
TITLE: Funding Fee Calculation
URL: https://www.bybit.com/en/help-center/article/Funding-fee-calculation
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Perpetual contracts
DOC_LAST_UPDATED: 2026-05-12
PRODUCT_VERSION_APPLICABILITY: Perpetual contracts
EXACT_SECTION_OR_HEADING: When Is Funding Fee Charged; How Is Funding Fee Calculated; USDT Perpetual
SUPPORTED_CLAIMS: Funding time/sign; USDT position value × rate; mark-price basis
UNSUPPORTED_CLAIMS: Does not define all venues or future interval changes
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S17 — Mark Price (Perpetual and Expiry Contracts)
SOURCE_ID: S17
PUBLISHER: Bybit
TITLE: Mark Price (Perpetual and Expiry Contracts)
URL: https://www.bybit.com/en/help-center/article/Mark-Price-Calculation-Perpetual-Expiry-Contracts
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Current perpetual/expiry help
DOC_LAST_UPDATED: 2026-09-04
PRODUCT_VERSION_APPLICABILITY: Current perpetual/expiry help
EXACT_SECTION_OR_HEADING: Mark Price; Mark Price Calculation / risk role
SUPPORTED_CLAIMS: Mark/index/last distinction and current mark-price mechanism
UNSUPPORTED_CLAIMS: Venue/product/version-specific
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S18 — Mark Price Calculation Update Announcement
SOURCE_ID: S18
PUBLISHER: Bybit
TITLE: Mark Price Calculation Update Announcement
URL: https://announcements.bybit.com/en/article/updates-to-mark-price-calculation-for-perpetual-contracts--artd86c87b8f55a/
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Transition notice
DOC_LAST_UPDATED: 2026-09-01
PRODUCT_VERSION_APPLICABILITY: Transition notice
EXACT_SECTION_OR_HEADING: Updates to Mark Price Calculation; transition dates
SUPPORTED_CLAIMS: Documents Sep 2–7 2026 transition timing
UNSUPPORTED_CLAIMS: Announcement alone is not permanent formula authority after transition
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S19 — Unified Trading Account
SOURCE_ID: S19
PUBLISHER: Bybit
TITLE: Unified Trading Account
URL: https://www.bybit.com/en/help-center/article/Unified-Trading-Account-Asset-Page
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: UTA
DOC_LAST_UPDATED: 2026-07-19
PRODUCT_VERSION_APPLICABILITY: UTA
EXACT_SECTION_OR_HEADING: Unified Trading Account Overview; IM/MM concepts
SUPPORTED_CLAIMS: Account-level margin/equity concepts and isolated/cross scope
UNSUPPORTED_CLAIMS: Not a generic futures account model
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S20 — Key Terms and Formulas in Unified Trading Account
SOURCE_ID: S20
PUBLISHER: Bybit
TITLE: Key Terms and Formulas in Unified Trading Account
URL: https://www.bybit.com/en/help-center/article/?id=000001912
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: UTA
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: UTA
EXACT_SECTION_OR_HEADING: Margin Balance; Available Balance; Unrealized P&L formulas
SUPPORTED_CLAIMS: Margin balance/available balance/UPL terminology
UNSUPPORTED_CLAIMS: May change with UTA revisions; verify version when implementing
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S21 — Liquidation Price Calculation under Isolated Mode — UTA
SOURCE_ID: S21
PUBLISHER: Bybit
TITLE: Liquidation Price Calculation under Isolated Mode — UTA
URL: https://www.bybit.com/en/help-center/article/Liquidation-Price-Calculation-under-Isolated-Mode-Unified-Trading-Account
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: UTA isolated
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: UTA isolated
EXACT_SECTION_OR_HEADING: Liquidation Price Calculation under Isolated Mode
SUPPORTED_CLAIMS: Venue-specific isolated liquidation formula family
UNSUPPORTED_CLAIMS: Not universal and page rendering did not expose reliable update date
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S22 — The New Margin Calculation: Adjustments and Implications
SOURCE_ID: S22
PUBLISHER: Bybit
TITLE: The New Margin Calculation: Adjustments and Implications
URL: https://www.bybit.com/en/help-center/article/Understanding-the-Adjustment-and-Impact-of-the-New-Margin-Calculation
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: UTA margin model
DOC_LAST_UPDATED: 2026-06-18
PRODUCT_VERSION_APPLICABILITY: UTA margin model
EXACT_SECTION_OR_HEADING: New Margin Calculation; Mark Price / IM / MM / risk-tier implications
SUPPORTED_CLAIMS: Mode/risk-tier/mark-price dependencies in margin calculation
UNSUPPORTED_CLAIMS: Not universal or proof of local implementation
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S23 — Difference Between Position Modes: One-Way Mode and Hedge Mode
SOURCE_ID: S23
PUBLISHER: Bybit
TITLE: Difference Between Position Modes: One-Way Mode and Hedge Mode
URL: https://www.bybit.com/en/help-center/article/Difference-Between-Position-Modes-One-Way-Mode-and-Hedge-Mode
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Derivatives
DOC_LAST_UPDATED: 2026-08-07
PRODUCT_VERSION_APPLICABILITY: Derivatives
EXACT_SECTION_OR_HEADING: One-Way Mode; Hedge Mode
SUPPORTED_CLAIMS: One-way/net vs hedge simultaneous long/short semantics
UNSUPPORTED_CLAIMS: Venue-specific mode capabilities
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S24 — Reduce-Only Order
SOURCE_ID: S24
PUBLISHER: Bybit
TITLE: Reduce-Only Order
URL: https://www.bybit.com/en/help-center/article/Reduce-Only-Order
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Derivatives
DOC_LAST_UPDATED: 2026-06-29
PRODUCT_VERSION_APPLICABILITY: Derivatives
EXACT_SECTION_OR_HEADING: Reduce-Only Order behavior
SUPPORTED_CLAIMS: Reduce-only cannot intentionally grow opposite exposure
UNSUPPORTED_CLAIMS: Does not define LOCAL_SIMULATOR cancel/resize behavior
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S25 — Introduction to Take Profit / Stop Loss
SOURCE_ID: S25
PUBLISHER: Bybit
TITLE: Introduction to Take Profit / Stop Loss
URL: https://www.bybit.com/en/help-center/article/Introduction-to-Take-Profit-Stop-Loss-Perpetual-Futures-Contracts
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Perpetual/Futures
DOC_LAST_UPDATED: 2025-11-25
PRODUCT_VERSION_APPLICABILITY: Perpetual/Futures
EXACT_SECTION_OR_HEADING: Take Profit / Stop Loss; Entire and Partial Position TP/SL
SUPPORTED_CLAIMS: Trigger reference vs resulting market/limit close; partial TP/SL behavior
UNSUPPORTED_CLAIMS: Not universal execution semantics
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S26 — Trailing Stop Order
SOURCE_ID: S26
PUBLISHER: Bybit
TITLE: Trailing Stop Order
URL: https://www.bybit.com/en/help-center/article/Trailing-Stop-Order-Perpetual-and-Futures-Trading
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Perpetual/Futures
DOC_LAST_UPDATED: 2026-02-05
PRODUCT_VERSION_APPLICABILITY: Perpetual/Futures
EXACT_SECTION_OR_HEADING: How Trailing Stop Works; Activation Price; distance/percentage formulas
SUPPORTED_CLAIMS: Activation + ratcheting high/low + retracement trigger
UNSUPPORTED_CLAIMS: Not universal trailing policy
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S27 — Futures Trading Rules
SOURCE_ID: S27
PUBLISHER: Bybit
TITLE: Futures Trading Rules
URL: https://www.bybit.com/en/help-center/article/Futures-Trading-Rules
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Futures
DOC_LAST_UPDATED: 2026-07-03
PRODUCT_VERSION_APPLICABILITY: Futures
EXACT_SECTION_OR_HEADING: Futures Trading Rules; tick size / quantity / notional protections
SUPPORTED_CLAIMS: Tick-size/min-max notional/rules and protection notes
UNSUPPORTED_CLAIMS: Not other venue instrument filters
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S28 — Futures Grid Trading FAQ
SOURCE_ID: S28
PUBLISHER: Binance
TITLE: Futures Grid Trading FAQ
URL: https://www.binance.com/en/support/faq/detail/f4c453bab89648beb722aa26634120c3
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Product documentation
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: Product documentation
EXACT_SECTION_OR_HEADING: Arithmetic Grid; Geometric Grid
SUPPORTED_CLAIMS: Arithmetic/geometric grid formulas and leveraged-grid feature behavior
UNSUPPORTED_CLAIMS: Feature discovery, not universal mathematical correctness beyond formulas
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S29 — Spot Grid — Trailing Up
SOURCE_ID: S29
PUBLISHER: Binance
TITLE: Spot Grid — Trailing Up
URL: https://www.binance.com/en/support/faq/detail/3d987afd7906495cb4d997eccb8515bf
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Product documentation
DOC_LAST_UPDATED: 2026-01-08
PRODUCT_VERSION_APPLICABILITY: Product documentation
EXACT_SECTION_OR_HEADING: Trailing Up behavior
SUPPORTED_CLAIMS: Trailing-up grid feature behavior
UNSUPPORTED_CLAIMS: Does not define all grid families
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S30 — Rebalancing Bot FAQ
SOURCE_ID: S30
PUBLISHER: Binance
TITLE: Rebalancing Bot FAQ
URL: https://www.binance.com/en-IA/support/faq/detail/29bbbd2e7fc24085be7a8a7d02779457
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Product documentation
DOC_LAST_UPDATED: 2026-07-17
PRODUCT_VERSION_APPLICABILITY: Product documentation
EXACT_SECTION_OR_HEADING: Rebalancing by Coin Ratio; Rebalancing by Time
SUPPORTED_CLAIMS: Threshold/time rebalancing examples and execution constraints
UNSUPPORTED_CLAIMS: Feature discovery only; not universal portfolio theory
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S31 — TimeSeriesSplit
SOURCE_ID: S31
PUBLISHER: scikit-learn
TITLE: TimeSeriesSplit
URL: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: scikit-learn 1.9.0
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: scikit-learn 1.9.0
EXACT_SECTION_OR_HEADING: TimeSeriesSplit; gap parameter; Notes
SUPPORTED_CLAIMS: Chronological CV and gap parameter; no future training for earlier test fold
UNSUPPORTED_CLAIMS: Does not select financial purge/embargo horizon automatically
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S32 — Research Guide
SOURCE_ID: S32
PUBLISHER: QuantConnect
TITLE: Research Guide
URL: https://www.quantconnect.com/docs/v2/writing-algorithms/key-concepts/research-guide
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: LEAN docs v2
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: LEAN docs v2
EXACT_SECTION_OR_HEADING: Research Guide; look-ahead bias / point-in-time data / walk-forward
SUPPORTED_CLAIMS: Look-ahead bias, point-in-time data, walk-forward guidance
UNSUPPORTED_CLAIMS: Does not prove one walk-forward design is universally best
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S33 — Warm Up Periods
SOURCE_ID: S33
PUBLISHER: QuantConnect
TITLE: Warm Up Periods
URL: https://www.quantconnect.com/docs/v2/writing-algorithms/historical-data/warm-up-periods
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: LEAN docs v2
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: LEAN docs v2
EXACT_SECTION_OR_HEADING: Warm Up Status; Trailing Data Samples; Missing Data Points
SUPPORTED_CLAIMS: Warm-up before algorithm start and no normal trading during warm-up
UNSUPPORTED_CLAIMS: Does not solve all indicator leakage
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S34 — Optimization Parameters
SOURCE_ID: S34
PUBLISHER: QuantConnect
TITLE: Optimization Parameters
URL: https://www.quantconnect.com/docs/v2/writing-algorithms/optimization/parameters
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: LEAN docs v2
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: LEAN docs v2
EXACT_SECTION_OR_HEADING: Optimization Parameters; in-sample/out-of-sample guidance
SUPPORTED_CLAIMS: Optimized backtest period becomes in-sample; evaluate on newer history/walk-forward
UNSUPPORTED_CLAIMS: Does not define exact untouched-holdout size
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S35 — The Deflated Sharpe Ratio
SOURCE_ID: S35
PUBLISHER: Bailey & López de Prado
TITLE: The Deflated Sharpe Ratio
URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Journal of Portfolio Management / 2014
DOC_LAST_UPDATED: 2014
PRODUCT_VERSION_APPLICABILITY: Journal of Portfolio Management / 2014
EXACT_SECTION_OR_HEADING: Deflated Sharpe Ratio; multiple-testing / selection-bias rationale
SUPPORTED_CLAIMS: Multiple-testing/selection-bias adjustment rationale
UNSUPPORTED_CLAIMS: Does not mandate one simulator metric or threshold
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S36 — The Probability of Backtest Overfitting
SOURCE_ID: S36
PUBLISHER: Bailey et al.
TITLE: The Probability of Backtest Overfitting
URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Research paper
DOC_LAST_UPDATED: 2013/2014
PRODUCT_VERSION_APPLICABILITY: Research paper
EXACT_SECTION_OR_HEADING: Probability of Backtest Overfitting methodology
SUPPORTED_CLAIMS: Backtest-overfitting risk from repeated model selection
UNSUPPORTED_CLAIMS: Does not define local tuning workflow
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S37 — Purged K-fold / embargo discussion
SOURCE_ID: S37
PUBLISHER: Peer-reviewed financial ML study
TITLE: Purged K-fold / embargo discussion
URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC9521884/
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Peer-reviewed article
DOC_LAST_UPDATED: 2022
PRODUCT_VERSION_APPLICABILITY: Peer-reviewed article
EXACT_SECTION_OR_HEADING: Purged k-fold and embargo discussion
SUPPORTED_CLAIMS: Purging overlapping labels and embargo handling in a financial time-series context
UNSUPPORTED_CLAIMS: Not universal horizon value
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S38 — Advanced Trade WebSocket Overview
SOURCE_ID: S38
PUBLISHER: Coinbase Developer Platform
TITLE: Advanced Trade WebSocket Overview
URL: https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-overview
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Current API docs
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: Current API docs
EXACT_SECTION_OR_HEADING: WebSocket Overview; sequence numbers / dropped and out-of-order messages
SUPPORTED_CLAIMS: Sequence gaps and out-of-order handling; public channel behavior
UNSUPPORTED_CLAIMS: Not LOCAL_SIMULATOR adapter implementation
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S39 — Advanced Trade WebSocket Guide
SOURCE_ID: S39
PUBLISHER: Coinbase Developer Platform
TITLE: Advanced Trade WebSocket Guide
URL: https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/guides/websocket
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Current API docs
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: Current API docs
EXACT_SECTION_OR_HEADING: WebSocket Guide; public vs authenticated channels
SUPPORTED_CLAIMS: Public vs authenticated channel separation
UNSUPPORTED_CLAIMS: Not other venues
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S40 — Public Trade WebSocket
SOURCE_ID: S40
PUBLISHER: Bybit API Documentation
TITLE: Public Trade WebSocket
URL: https://bybit-exchange.github.io/docs/v5/websocket/public/trade
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: V5
DOC_LAST_UPDATED: 2026-09-09 observed
PRODUCT_VERSION_APPLICABILITY: V5
EXACT_SECTION_OR_HEADING: publicTrade parameters: ts, T, i, seq
SUPPORTED_CLAIMS: Trade time/system time/sequence fields
UNSUPPORTED_CLAIMS: Not a local identity schema
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S41 — Web Content Accessibility Guidelines (WCAG) 2.2
SOURCE_ID: S41
PUBLISHER: W3C
TITLE: Web Content Accessibility Guidelines (WCAG) 2.2
URL: https://www.w3.org/TR/WCAG22/
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: WCAG 2.2
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: WCAG 2.2
EXACT_SECTION_OR_HEADING: WCAG 2.2: Keyboard; Focus; Contrast; Reflow
SUPPORTED_CLAIMS: Keyboard/focus/contrast/reflow accessibility requirements
UNSUPPORTED_CLAIMS: Does not choose application visual design
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S42 — Understanding Success Criterion 1.4.10 Reflow
SOURCE_ID: S42
PUBLISHER: W3C
TITLE: Understanding Success Criterion 1.4.10 Reflow
URL: https://www.w3.org/WAI/WCAG22/Understanding/reflow.html
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: WCAG 2.2 understanding doc
DOC_LAST_UPDATED: 2026 observed
PRODUCT_VERSION_APPLICABILITY: WCAG 2.2 understanding doc
EXACT_SECTION_OR_HEADING: Understanding SC 1.4.10 Reflow; 320 CSS pixel interpretation
SUPPORTED_CLAIMS: 320 CSS px reflow interpretation
UNSUPPORTED_CLAIMS: Not a screenshot/layout specification
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S43 — Package and deploy Windows apps
SOURCE_ID: S43
PUBLISHER: Microsoft
TITLE: Package and deploy Windows apps
URL: https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Windows app packaging docs
DOC_LAST_UPDATED: 2026-08-17
PRODUCT_VERSION_APPLICABILITY: Windows app packaging docs
EXACT_SECTION_OR_HEADING: Package and deploy Windows apps
SUPPORTED_CLAIMS: Windows packaging/deployment options
UNSUPPORTED_CLAIMS: Does not prove LOCAL_SIMULATOR installer works offline
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S44 — MSIX Packaging Tool in a disconnected environment
SOURCE_ID: S44
PUBLISHER: Microsoft
TITLE: MSIX Packaging Tool in a disconnected environment
URL: https://learn.microsoft.com/en-us/windows/msix/packaging-tool/disconnected-environment
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: MSIX docs
DOC_LAST_UPDATED: 2026-04-15
PRODUCT_VERSION_APPLICABILITY: MSIX docs
EXACT_SECTION_OR_HEADING: MSIX Packaging Tool in a disconnected environment
SUPPORTED_CLAIMS: Disconnected/offline packaging-tool workflow
UNSUPPORTED_CLAIMS: Not application-specific E2E evidence
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S45 — CSV Injection
SOURCE_ID: S45
PUBLISHER: OWASP
TITLE: CSV Injection
URL: https://owasp.org/www-community/attacks/CSV_Injection
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: OWASP community guidance
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: OWASP community guidance
EXACT_SECTION_OR_HEADING: CSV Injection; spreadsheet formula interpretation
SUPPORTED_CLAIMS: Spreadsheet formula injection risk in exported CSV
UNSUPPORTED_CLAIMS: Does not prove a particular spreadsheet client behavior for every payload
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S46 — zipfile — Work with ZIP archives
SOURCE_ID: S46
PUBLISHER: Python Software Foundation
TITLE: zipfile — Work with ZIP archives
URL: https://docs.python.org/3/library/zipfile.html
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Python 3.14.6 docs
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: Python 3.14.6 docs
EXACT_SECTION_OR_HEADING: ZipFile.extract()/extractall() warning and path safety
SUPPORTED_CLAIMS: Warns to inspect untrusted archives before extraction; path safety considerations
UNSUPPORTED_CLAIMS: Does not set application size/count limits
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S47 — Spot WebSocket / Exchange Information
SOURCE_ID: S47
PUBLISHER: Binance API Documentation
TITLE: Spot WebSocket / Exchange Information
URL: https://developers.binance.com/docs/binance-spot-api-docs/web-socket-api/general-requests
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: Spot API docs
DOC_LAST_UPDATED: 2026 observed
PRODUCT_VERSION_APPLICABILITY: Spot API docs
EXACT_SECTION_OR_HEADING: Exchange information; symbol price/quantity/notional filters
SUPPORTED_CLAIMS: Instrument filters/timing/data metadata examples
UNSUPPORTED_CLAIMS: Not universal tick/step/notional schema
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED

## S48 — Backtesting Report
SOURCE_ID: S48
PUBLISHER: QuantConnect
TITLE: Backtesting Report
URL: https://www.quantconnect.com/docs/v2/cloud-platform/backtesting/report
ACCESS_DATE: 2026-09-09
SOURCE_VERSION: LEAN docs v2
DOC_LAST_UPDATED: VERSION_UNAVAILABLE
PRODUCT_VERSION_APPLICABILITY: LEAN docs v2
EXACT_SECTION_OR_HEADING: Backtesting Report; Drawdown/performance reporting
SUPPORTED_CLAIMS: Drawdown/reporting definitions and report separation
UNSUPPORTED_CLAIMS: Not a universal accounting GAAP definition
ARCHIVE_REFERENCE_IF_AVAILABLE: NONE_RETAINED
