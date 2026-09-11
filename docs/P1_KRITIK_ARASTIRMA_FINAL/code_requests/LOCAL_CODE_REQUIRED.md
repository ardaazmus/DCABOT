# LOCAL_CODE_REQUIRED

No local code was inspected. Each request is deliberately narrow and contains no secrets/private paths.

## LCR-01
LOCAL_CODE_REQUEST_ID: LCR-01
PHASE: P1.07
UNKNOWN_QUESTION: Reserve schema/owner
WHY_EXTERNAL_SOURCES_CANNOT_ANSWER: reserve acquisition/reduction/release owner
EXACT_SYMBOL_OR_BRANCH: State/Order/Position ve reserve/commitment alanları
EXACT_TEST_OR_FIXTURE: matching smallest test body for the stated question
MAX_SNIPPET_SIZE: <=120 lines, redact paths/secrets
REDACTION_RULES: remove secrets, credentials, private URLs, DB names, user paths/data; placeholders allowed.
DECISION_AFTER_CODE: close only this claim/gate; do not infer unrelated implementation behavior.

## LCR-02
LOCAL_CODE_REQUEST_ID: LCR-02
PHASE: P1.07/P1.08
UNKNOWN_QUESTION: Reducer authority
WHY_EXTERNAL_SOURCES_CANNOT_ANSWER: economic vs lifecycle authority
EXACT_SYMBOL_OR_BRANCH: INTENT/FILL/ORDER_FINAL/UNKNOWN/MARK and deal lifecycle branches
EXACT_TEST_OR_FIXTURE: matching smallest test body for the stated question
MAX_SNIPPET_SIZE: <=120 lines per branch
REDACTION_RULES: remove secrets, credentials, private URLs, DB names, user paths/data; placeholders allowed.
DECISION_AFTER_CODE: close only this claim/gate; do not infer unrelated implementation behavior.

## LCR-03
LOCAL_CODE_REQUEST_ID: LCR-03
PHASE: P1.07
UNKNOWN_QUESTION: Initial margin call-chain
WHY_EXTERNAL_SOURCES_CANNOT_ANSWER: estimate vs persistent reserve relationship
EXACT_SYMBOL_OR_BRANCH: initial_margin_estimate function + acceptance caller
EXACT_TEST_OR_FIXTURE: matching smallest test body for the stated question
MAX_SNIPPET_SIZE: <=120 lines each
REDACTION_RULES: remove secrets, credentials, private URLs, DB names, user paths/data; placeholders allowed.
DECISION_AFTER_CODE: close only this claim/gate; do not infer unrelated implementation behavior.

## LCR-04
LOCAL_CODE_REQUEST_ID: LCR-04
PHASE: P1.07
UNKNOWN_QUESTION: Pending blocker
WHY_EXTERNAL_SOURCES_CANNOT_ANSWER: pending-state gate
EXACT_SYMBOL_OR_BRANCH: pending/unsettled BASE -> SAFETY/EXIT blocker
EXACT_TEST_OR_FIXTURE: matching smallest test body for the stated question
MAX_SNIPPET_SIZE: <=120 lines
REDACTION_RULES: remove secrets, credentials, private URLs, DB names, user paths/data; placeholders allowed.
DECISION_AFTER_CODE: close only this claim/gate; do not infer unrelated implementation behavior.

## LCR-05
LOCAL_CODE_REQUEST_ID: LCR-05
PHASE: P1.07
UNKNOWN_QUESTION: Historical adapter
WHY_EXTERNAL_SOURCES_CANNOT_ANSWER: adapter/core ownership
EXACT_SYMBOL_OR_BRANCH: candidate -> core FILL call chain
EXACT_TEST_OR_FIXTURE: matching smallest test body for the stated question
MAX_SNIPPET_SIZE: <=120 lines
REDACTION_RULES: remove secrets, credentials, private URLs, DB names, user paths/data; placeholders allowed.
DECISION_AFTER_CODE: close only this claim/gate; do not infer unrelated implementation behavior.

## LCR-06
LOCAL_CODE_REQUEST_ID: LCR-06
PHASE: P1.07/P1.11
UNKNOWN_QUESTION: Atomic transaction
WHY_EXTERNAL_SOURCES_CANNOT_ANSWER: all-or-none semantics
EXACT_SYMBOL_OR_BRANCH: reserve/fill/account commit transaction/version boundary
EXACT_TEST_OR_FIXTURE: matching smallest test body for the stated question
MAX_SNIPPET_SIZE: <=120 lines
REDACTION_RULES: remove secrets, credentials, private URLs, DB names, user paths/data; placeholders allowed.
DECISION_AFTER_CODE: close only this claim/gate; do not infer unrelated implementation behavior.

## LCR-07
LOCAL_CODE_REQUEST_ID: LCR-07
PHASE: P1.07/P1.10/P1.11
UNKNOWN_QUESTION: Dedupe/late persistence
WHY_EXTERNAL_SOURCES_CANNOT_ANSWER: idempotence/conflict/replay
EXACT_SYMBOL_OR_BRANCH: duplicate/late execution tests + persisted identity schema
EXACT_TEST_OR_FIXTURE: matching smallest test body for the stated question
MAX_SNIPPET_SIZE: <=120 lines per test
REDACTION_RULES: remove secrets, credentials, private URLs, DB names, user paths/data; placeholders allowed.
DECISION_AFTER_CODE: close only this claim/gate; do not infer unrelated implementation behavior.

## LCR-08
LOCAL_CODE_REQUEST_ID: LCR-08
PHASE: P1.07
UNKNOWN_QUESTION: Fixtures
WHY_EXTERNAL_SOURCES_CANNOT_ANSWER: model policy and committed-prefix behavior
EXACT_SYMBOL_OR_BRANCH: partial fill/EOF/ambiguity/cancel fixtures
EXACT_TEST_OR_FIXTURE: matching smallest test body for the stated question
MAX_SNIPPET_SIZE: <=120 lines each
REDACTION_RULES: remove secrets, credentials, private URLs, DB names, user paths/data; placeholders allowed.
DECISION_AFTER_CODE: close only this claim/gate; do not infer unrelated implementation behavior.

## LCR-09
LOCAL_CODE_REQUEST_ID: LCR-09
PHASE: P1.15
UNKNOWN_QUESTION: Two-leg reducer
WHY_EXTERNAL_SOURCES_CANNOT_ANSWER: one-leg-filled recovery
EXACT_SYMBOL_OR_BRANCH: leg state schema + recovery/timeout branch
EXACT_TEST_OR_FIXTURE: matching smallest test body for the stated question
MAX_SNIPPET_SIZE: <=120 lines per branch
REDACTION_RULES: remove secrets, credentials, private URLs, DB names, user paths/data; placeholders allowed.
DECISION_AFTER_CODE: close only this claim/gate; do not infer unrelated implementation behavior.

## LCR-10
LOCAL_CODE_REQUEST_ID: LCR-10
PHASE: P1.05/P1.06/P1.19
UNKNOWN_QUESTION: DTO/serializer
WHY_EXTERNAL_SOURCES_CANNOT_ANSWER: exact numeric strings and canonical replay
EXACT_SYMBOL_OR_BRANCH: public DTO/serializer + legacy/reopen test
EXACT_TEST_OR_FIXTURE: matching smallest test body for the stated question
MAX_SNIPPET_SIZE: <=120 lines
REDACTION_RULES: remove secrets, credentials, private URLs, DB names, user paths/data; placeholders allowed.
DECISION_AFTER_CODE: close only this claim/gate; do not infer unrelated implementation behavior.

## LCR-11
LOCAL_CODE_REQUEST_ID: LCR-11
PHASE: P1.19
UNKNOWN_QUESTION: Windows E2E
WHY_EXTERNAL_SOURCES_CANNOT_ANSWER: offline install acceptance
EXACT_SYMBOL_OR_BRANCH: installer/startup/offline dependency test script/log excerpt
EXACT_TEST_OR_FIXTURE: matching smallest test body for the stated question
MAX_SNIPPET_SIZE: <=120 lines, no user path
REDACTION_RULES: remove secrets, credentials, private URLs, DB names, user paths/data; placeholders allowed.
DECISION_AFTER_CODE: close only this claim/gate; do not infer unrelated implementation behavior.

## LCR-12
LOCAL_CODE_REQUEST_ID: LCR-12
PHASE: P1.12
UNKNOWN_QUESTION: Futures state/profile
WHY_EXTERNAL_SOURCES_CANNOT_ANSWER: selected venue-profile mapping
EXACT_SYMBOL_OR_BRANCH: Position/Margin fields + fee/funding/mark/liquidation owner
EXACT_TEST_OR_FIXTURE: matching smallest test body for the stated question
MAX_SNIPPET_SIZE: <=120 lines each
REDACTION_RULES: remove secrets, credentials, private URLs, DB names, user paths/data; placeholders allowed.
DECISION_AFTER_CODE: close only this claim/gate; do not infer unrelated implementation behavior.
