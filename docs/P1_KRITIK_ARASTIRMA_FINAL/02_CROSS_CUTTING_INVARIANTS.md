# 02_CROSS_CUTTING_INVARIANTS

## Authority invariant
`Observation != Candidate != Accepted Economic FILL != ORDER_FINAL != Persisted Result`. FIX separates execution-report purpose/current order status, supporting a non-collapsed event model [S01/S02]. UI/chart/preview are never economic authority.

## Event-time taxonomy
| Field | Meaning | Economic use |
|---|---|---|
| event_time | source economic event time | primary when source contract defines it |
| receive_time | adapter arrival | latency/audit, not economic substitution |
| processing_time | reducer processing | performance/audit |
| bar_open_time/bar_close_time | historical bar bounds | closed-bar/look-ahead gates |
| effective_time | event applies to economics | funding/expiry/etc. when defined |
| persistence_time | commit time | audit/recovery |
| display_time | localized UI time | presentation only |

Public sequence gaps/out-of-order must be explicit [S38/S40].

## Execution identity
Canonical identity is a typed tuple such as `{venue_scope, product_scope, order_id, execution_id}` plus local event id/sequence/payload hash for conflict evidence. FIX ExecID supports execution-message identity [S04], but exact local key is `LOCAL_CODE_REQUIRED`. Known duplicate, conflicting duplicate, and new late event are separate states.

## Atomic economic transition
Accepted FILL should atomically cover position/cost, fee, cum/leaves, reserve if enabled, dedupe identity, and resulting version. Transaction technology can support all-or-none commit [S08/S09], but local transaction boundary remains LCR-06.

## Canonical serialization/hash
Use versioned canonical representation; RFC 8785 provides deterministic JSON canonicalization principles [S06]; SHA-256 is defined by FIPS 180-4 [S07]. Include schema/canonicalization version, null-vs-absent policy, Decimal string policy, timezone/encoding normalization.

## Numeric boundary
`parse -> exact internal -> economic calculation -> venue quantization -> persistence -> API exact string -> UI formatting`. Python Decimal supplies exact decimal-string semantics and explicit rounding/traps [S05]. Unknown must never become 0. UI rounding is not economic rounding.

## Result taxonomy
VALID may mutate and summarize. INVALID_INPUT/UNSUPPORTED/STALE/CONFLICT/CORRUPT block economic mutation. AMBIGUOUS/INDETERMINATE may preserve only committed prefix. OPEN_AT_END preserves accepted economics but remains open. LOCAL_CODE_REQUIRED/BLOCKED are research/gate states, not numeric values.

## Global property tests
Known duplicate is idempotent; replay count invariant; export/import canonical state invariant; exact remainder quantity conservation; ambiguity suffix cannot erase committed prefix; venue-specific formula cannot activate in another venue profile; fee equality on split fills remains CONDITIONAL until rounding policy is known.
