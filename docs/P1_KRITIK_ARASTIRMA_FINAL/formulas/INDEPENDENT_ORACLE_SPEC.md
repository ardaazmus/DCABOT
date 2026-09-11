# INDEPENDENT_ORACLE_SPEC

ORACLE_STATUS: SPECIFIED_AND_RESEARCH_FIXTURES_EXECUTED; PRODUCTION_COMPARISON_NOT_EXECUTED.

The oracle must not import production reducer/helper/formula utilities. It parses literal decimal strings independently and compares field-by-field before comparing hashes.

## Executed arithmetic fixtures
- Linear long: Q=1.25, entry=40000, mark=42000 -> `2500.00` QUOTE_ASSET.
- Linear short with same prices -> `-2500.00` QUOTE_ASSET.
- Funding magnitude at rate 0.0001 and mark value Q×mark -> `5.250000` QUOTE_ASSET.
- Weighted AEP: 0.5@5000 + 0.3@6000 -> `5375`.
- Arithmetic grid: 1000..2000, N=10 -> step `100`.
- Drawdown: peak 1000, current 850 -> `15.00%`.

## State-oracle pattern
1. Literal fixture events with ids/times/units.
2. Independent transition table, not production class methods.
3. Exact quantity/ledger conservation checks.
4. Canonical output written using oracle-owned serializer/version.
5. Production output compared field-by-field: qty, cost, fee, reserve, state, identities, timestamps.
6. Hash equality is supplementary, not sole proof.

## Negative oracles
- same execution id + different payload -> CONFLICT and no economic delta;
- missing venue profile for liquidation -> BLOCKED, no numeric threshold;
- unknown reserve -> tagged NONE/UNKNOWN, not 0;
- stale/gap public feed -> no simulated FILL before resync policy.
