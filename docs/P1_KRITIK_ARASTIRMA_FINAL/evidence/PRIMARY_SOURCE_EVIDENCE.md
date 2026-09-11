# PRIMARY_SOURCE_EVIDENCE

Short evidence summaries only; see SOURCE_CARDS for URL/version/scope.

## S01 — Order State Changes
- Evidence summary: General order state model; ExecType vs OrdStatus; leaves/cumulative concepts.
- Scope limit: Does not define LOCAL_SIMULATOR state names or chosen OHLC policy.
- URL: https://www.fixtrading.org/online-specification/order-state-changes/

## S02 — FIX Latest Specification — Order State Changes
- Evidence summary: Normative FIX order-state package/version anchor.
- Scope limit: Exchange-specific contracts can override/generalize differently.
- URL: https://www.fixtrading.org/packages/fix-latest-order-state-changes/

## S03 — FIX 5.0 SP2 Field 151 — LeavesQty
- Evidence summary: LeavesQty quantity remaining; relation to OrderQty/CumQty for active order.
- Scope limit: Does not define terminal remainder in LOCAL_SIMULATOR.
- URL: https://fiximate.fixtrading.org/legacy/en/FIX.5.0/tag151.html

## S05 — decimal — Decimal fixed-point and floating-point arithmetic
- Evidence summary: Exact decimal string conversion; contexts, traps, explicit rounding.
- Scope limit: Does not mandate Fraction internally or venue rounding mode.
- URL: https://docs.python.org/3/library/decimal.html

## S06 — RFC 8785 — JSON Canonicalization Scheme (JCS)
- Evidence summary: Deterministic JSON representation suitable for repeatable hashing/signatures.
- Scope limit: Does not select application schema or Decimal encoding.
- URL: https://www.rfc-editor.org/rfc/rfc8785.html

## S07 — Secure Hash Standard (SHS), FIPS 180-4
- Evidence summary: SHA-2 including SHA-256.
- Scope limit: Hash equality does not prove economic correctness.
- URL: https://www.nist.gov/publications/secure-hash-standard

## S10 — Advanced Trade — Order management
- Evidence summary: Spot order holds, partial fill/cancel product behavior.
- Scope limit: Not a universal reserve definition.
- URL: https://help.coinbase.com/en/coinbase/trading-and-funding/advanced-trade/order-management

## S11 — Equity Fill Model
- Evidence summary: Concrete historical fill policy; same/stale bar guards; limit/stop behavior.
- Scope limit: Not venue truth; not the only valid simulator model.
- URL: https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/trade-fills/supported-models/equity-model

## S12 — Latest Price Fill Model
- Evidence summary: Alternative concrete fill/equality/price policy.
- Scope limit: Not universal; differs from S11.
- URL: https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/trade-fills/supported-models/latest-price-model

## S15 — P&L Calculations (USDT Perpetual and Expiry Contracts)
- Evidence summary: AEP, long/short UPL, realized/closed PnL and fee/funding distinction.
- Scope limit: Does not apply to inverse contracts or other venues.
- URL: https://www.bybit.com/en/help-center/article/Profit-Loss-calculations-USDT-Contract

## S16 — Funding Fee Calculation
- Evidence summary: Funding time/sign; USDT position value × rate; mark-price basis.
- Scope limit: Does not define all venues or future interval changes.
- URL: https://www.bybit.com/en/help-center/article/Funding-fee-calculation

## S17 — Mark Price (Perpetual and Expiry Contracts)
- Evidence summary: Mark/index/last distinction and current mark-price mechanism.
- Scope limit: Venue/product/version-specific.
- URL: https://www.bybit.com/en/help-center/article/Mark-Price-Calculation-Perpetual-Expiry-Contracts

## S18 — Mark Price Calculation Update Announcement
- Evidence summary: Documents Sep 2–7 2026 transition timing.
- Scope limit: Announcement alone is not permanent formula authority after transition.
- URL: https://announcements.bybit.com/en/article/updates-to-mark-price-calculation-for-perpetual-contracts--artd86c87b8f55a/

## S19 — Unified Trading Account
- Evidence summary: Account-level margin/equity concepts and isolated/cross scope.
- Scope limit: Not a generic futures account model.
- URL: https://www.bybit.com/en/help-center/article/Unified-Trading-Account-Asset-Page

## S23 — Difference Between Position Modes: One-Way Mode and Hedge Mode
- Evidence summary: One-way/net vs hedge simultaneous long/short semantics.
- Scope limit: Venue-specific mode capabilities.
- URL: https://www.bybit.com/en/help-center/article/Difference-Between-Position-Modes-One-Way-Mode-and-Hedge-Mode

## S24 — Reduce-Only Order
- Evidence summary: Reduce-only cannot intentionally grow opposite exposure.
- Scope limit: Does not define LOCAL_SIMULATOR cancel/resize behavior.
- URL: https://www.bybit.com/en/help-center/article/Reduce-Only-Order

## S25 — Introduction to Take Profit / Stop Loss
- Evidence summary: Trigger reference vs resulting market/limit close; partial TP/SL behavior.
- Scope limit: Not universal execution semantics.
- URL: https://www.bybit.com/en/help-center/article/Introduction-to-Take-Profit-Stop-Loss-Perpetual-Futures-Contracts

## S26 — Trailing Stop Order
- Evidence summary: Activation + ratcheting high/low + retracement trigger.
- Scope limit: Not universal trailing policy.
- URL: https://www.bybit.com/en/help-center/article/Trailing-Stop-Order-Perpetual-and-Futures-Trading

## S31 — TimeSeriesSplit
- Evidence summary: Chronological CV and gap parameter; no future training for earlier test fold.
- Scope limit: Does not select financial purge/embargo horizon automatically.
- URL: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html

## S34 — Optimization Parameters
- Evidence summary: Optimized backtest period becomes in-sample; evaluate on newer history/walk-forward.
- Scope limit: Does not define exact untouched-holdout size.
- URL: https://www.quantconnect.com/docs/v2/writing-algorithms/optimization/parameters

## S35 — The Deflated Sharpe Ratio
- Evidence summary: Multiple-testing/selection-bias adjustment rationale.
- Scope limit: Does not mandate one simulator metric or threshold.
- URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551

## S36 — The Probability of Backtest Overfitting
- Evidence summary: Backtest-overfitting risk from repeated model selection.
- Scope limit: Does not define local tuning workflow.
- URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253

## S38 — Advanced Trade WebSocket Overview
- Evidence summary: Sequence gaps and out-of-order handling; public channel behavior.
- Scope limit: Not LOCAL_SIMULATOR adapter implementation.
- URL: https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-overview

## S40 — Public Trade WebSocket
- Evidence summary: Trade time/system time/sequence fields.
- Scope limit: Not a local identity schema.
- URL: https://bybit-exchange.github.io/docs/v5/websocket/public/trade

## S41 — Web Content Accessibility Guidelines (WCAG) 2.2
- Evidence summary: Keyboard/focus/contrast/reflow accessibility requirements.
- Scope limit: Does not choose application visual design.
- URL: https://www.w3.org/TR/WCAG22/

## S42 — Understanding Success Criterion 1.4.10 Reflow
- Evidence summary: 320 CSS px reflow interpretation.
- Scope limit: Not a screenshot/layout specification.
- URL: https://www.w3.org/WAI/WCAG22/Understanding/reflow.html

## S43 — Package and deploy Windows apps
- Evidence summary: Windows packaging/deployment options.
- Scope limit: Does not prove LOCAL_SIMULATOR installer works offline.
- URL: https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/

## S44 — MSIX Packaging Tool in a disconnected environment
- Evidence summary: Disconnected/offline packaging-tool workflow.
- Scope limit: Not application-specific E2E evidence.
- URL: https://learn.microsoft.com/en-us/windows/msix/packaging-tool/disconnected-environment

## S45 — CSV Injection
- Evidence summary: Spreadsheet formula injection risk in exported CSV.
- Scope limit: Does not prove a particular spreadsheet client behavior for every payload.
- URL: https://owasp.org/www-community/attacks/CSV_Injection

## S46 — zipfile — Work with ZIP archives
- Evidence summary: Warns to inspect untrusted archives before extraction; path safety considerations.
- Scope limit: Does not set application size/count limits.
- URL: https://docs.python.org/3/library/zipfile.html
