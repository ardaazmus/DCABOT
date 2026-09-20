import unittest
from copy import deepcopy
import json
from pathlib import Path

from dcabot.application.futures_dca_core_mapping import (
    FuturesDcaCoreAdmissionOracle,
    FuturesDcaCoreFillAdmission,
    FuturesDcaCoreFillProjection,
    FuturesDcaCoreFillReplayDecision,
    FuturesDcaCoreOrderMapping,
    FuturesDcaCoreReplayReceipt,
    FuturesDcaCoreReplayRetryDecision,
    assess_futures_dca_core_fill_replay,
    assess_futures_dca_core_fill_admission,
    assess_futures_dca_core_mapping_admission,
    build_futures_dca_core_mapping_candidate,
    build_futures_dca_core_replay_receipt,
    project_futures_dca_core_fill,
    assess_futures_dca_core_replay_retry,
)
from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply
from dcabot.domain.numbers import number
from dcabot.persistence.futures_dca_journal_schema import (
    FuturesDcaEconomicPosting,
    FuturesDcaEventEnvelope,
    FuturesDcaReservationProjection,
)
from dcabot.persistence.futures_dca_release_transition import FuturesDcaReleaseTransition


class FuturesDcaCoreMappingTests(unittest.TestCase):
    def setUp(self):
        config_path = Path(__file__).resolve().parents[1] / "config/paper.json"
        self.config = Config.parse(json.loads(config_path.read_text()))

    def event(self, *, state="ACCEPTED", price="100"):
        return FuturesDcaEventEnvelope(
            "event-2", 2, "execution-2", "venue-order-1", "FILL", "profile-1", 100, 101,
            "0.4", price, "40", "0", "USDT", "slippage-1", "rounding-1", '{"source":"offline"}', state,
        )

    def posting(self, *, event_id="event-2", commitment="40", fee="0"):
        return FuturesDcaEconomicPosting("posting-1", event_id, 1, commitment, fee, "0", "PROJECTED")

    def candidate(self, **kwargs):
        values = {
            "mapping_id": "mapping-1",
            "profile_revision_id": "profile-1",
            "core_order_id": "core-order-1",
            "core_order_intent_id": "core-intent-1",
            "role": "SAFETY:1",
            "side": "BUY",
            "limit_price": "100",
        }
        values.update(kwargs)
        return build_futures_dca_core_mapping_candidate(self.event(), self.posting(), **values)

    def replay_context(self):
        candidate = self.candidate(role="BASE")
        state = apply(State(), {"type": "MARK", "price": "100"}, self.config)
        state = apply(
            state,
            {
                "type": "INTENT",
                "order_id": "core-order-1",
                "intent_id": "core-intent-1",
                "role": "BASE",
                "qty": "1",
                "limit_price": "100",
            },
            self.config,
        )
        reservation = FuturesDcaReservationProjection(
            "reservation-1", "deal-1", "USDT", "40", "0", "40", None, "OPEN", 0, "event-1"
        )
        transition = FuturesDcaReleaseTransition(
            "reservation-1", "event-2", "release-1", 1, 0, "FULL_FILL", "40", "0"
        )
        admission = assess_futures_dca_core_fill_admission(
            self.event(), self.posting(), candidate, state, self.config
        )
        decision = assess_futures_dca_core_fill_replay(
            self.event(), self.posting(), transition, reservation, candidate, admission, state, self.config
        )
        return candidate, state, reservation, transition, admission, decision

    def test_explicit_mapping_candidate_is_exact_and_non_economic(self):
        self.assertEqual(
            self.candidate(),
            FuturesDcaCoreOrderMapping(
                "mapping-1", "event-2", "posting-1", "profile-1", "core-order-1", "core-intent-1",
                "SAFETY:1", "BUY", "100", "CANDIDATE",
            ),
        )

    def test_missing_or_mismatched_authority_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "FUTURES_DCA_CORE_MAPPING_SOURCE_MISMATCH"):
            build_futures_dca_core_mapping_candidate(
                self.event(), self.posting(event_id="other-event"), mapping_id="mapping-1",
                profile_revision_id="profile-1", core_order_id="core-order-1",
                core_order_intent_id="core-intent-1", role="BASE", side="BUY", limit_price="100",
            )
        with self.assertRaisesRegex(ValueError, "FUTURES_DCA_CORE_MAPPING_EVENT_NOT_ACCEPTED"):
            build_futures_dca_core_mapping_candidate(
                self.event(state="UNKNOWN"), self.posting(), mapping_id="mapping-1",
                profile_revision_id="profile-1",
                core_order_id="core-order-1", core_order_intent_id="core-intent-1", role="BASE",
                side="BUY", limit_price="100",
            )

    def test_side_role_and_limit_rules_match_core_contract(self):
        with self.assertRaisesRegex(ValueError, "FUTURES_DCA_CORE_MAPPING_SIDE_INVALID"):
            self.candidate(side="LONG")
        with self.assertRaisesRegex(ValueError, "FUTURES_DCA_CORE_MAPPING_ROLE_INVALID"):
            self.candidate(role="MARTINGALE")
        with self.assertRaisesRegex(ValueError, "FUTURES_DCA_CORE_MAPPING_LIMIT_VIOLATION"):
            self.candidate(limit_price="99")

    def test_economic_identity_is_required_before_mapping_candidate(self):
        with self.assertRaisesRegex(ValueError, "FUTURES_DCA_CORE_MAPPING_ECONOMIC_MISMATCH"):
            build_futures_dca_core_mapping_candidate(
                self.event(), self.posting(commitment="41"), mapping_id="mapping-1",
                profile_revision_id="profile-1",
                core_order_id="core-order-1", core_order_intent_id="core-intent-1", role="BASE",
                side="BUY", limit_price="100",
            )

    def test_mapping_object_cannot_claim_admitted_status(self):
        with self.assertRaisesRegex(ValueError, "FUTURES_DCA_CORE_MAPPING_STATUS_INVALID"):
            FuturesDcaCoreOrderMapping(
                "mapping-1", "event-2", "posting-1", "profile-1", "core-order-1", "core-intent-1",
                "BASE", "BUY", "100", "ACCEPTED",
            )

    def test_admission_oracle_matches_order_without_mutating_core_state(self):
        candidate = self.candidate(role="BASE")
        state = apply(State(), {"type": "MARK", "price": "100"}, self.config)
        state = apply(
            state,
            {"type": "INTENT", "order_id": "core-order-1", "role": "BASE", "qty": "1", "limit_price": "100"},
            self.config,
        )
        before = deepcopy(state)
        self.assertEqual(
            assess_futures_dca_core_mapping_admission(candidate, state),
            FuturesDcaCoreAdmissionOracle(
                "mapping-1", "BLOCKED", ("core_order_intent",),
                "FUTURES_DCA_CORE_INTENT_SCOPE_UNREPRESENTED",
            ),
        )
        self.assertEqual(state, before)

    def test_admission_oracle_requires_exact_core_intent_identity(self):
        candidate = self.candidate(role="BASE")
        state = apply(State(), {"type": "MARK", "price": "100"}, self.config)
        state = apply(
            state,
            {
                "type": "INTENT",
                "order_id": "core-order-1",
                "intent_id": "core-intent-1",
                "role": "BASE",
                "qty": "1",
                "limit_price": "100",
            },
            self.config,
        )
        self.assertEqual(
            assess_futures_dca_core_mapping_admission(candidate, state),
            FuturesDcaCoreAdmissionOracle(
                "mapping-1", "ADMISSIBLE", (), "FUTURES_DCA_CORE_ADMISSION_READY"
            ),
        )
        self.assertEqual(
            assess_futures_dca_core_mapping_admission(
                self.candidate(role="BASE", core_order_intent_id="other-intent"), state
            ),
            FuturesDcaCoreAdmissionOracle(
                "mapping-1", "BLOCKED", (), "FUTURES_DCA_CORE_INTENT_ID_CONFLICT"
            ),
        )

    def test_admission_oracle_rejects_missing_order_and_scope_conflict(self):
        candidate = self.candidate(role="BASE")
        self.assertEqual(
            assess_futures_dca_core_mapping_admission(candidate, State()),
            FuturesDcaCoreAdmissionOracle(
                "mapping-1", "BLOCKED", ("core_order",),
                "FUTURES_DCA_CORE_ORDER_NOT_FOUND",
            ),
        )
        state = apply(State(), {"type": "MARK", "price": "100"}, self.config)
        state = apply(
            state,
            {"type": "INTENT", "order_id": "core-order-1", "role": "BASE", "qty": "1", "limit_price": "99"},
            self.config,
        )
        self.assertEqual(
            assess_futures_dca_core_mapping_admission(candidate, state),
            FuturesDcaCoreAdmissionOracle(
                "mapping-1", "BLOCKED", (),
                "FUTURES_DCA_CORE_ORDER_SCOPE_CONFLICT",
            ),
        )

    def test_fill_admission_emits_immutable_core_event_without_mutation(self):
        candidate = self.candidate(role="BASE")
        state = apply(State(), {"type": "MARK", "price": "100"}, self.config)
        state = apply(
            state,
            {
                "type": "INTENT",
                "order_id": "core-order-1",
                "intent_id": "core-intent-1",
                "role": "BASE",
                "qty": "1",
                "limit_price": "100",
            },
            self.config,
        )
        before = deepcopy(state)
        self.assertEqual(
            assess_futures_dca_core_fill_admission(
                self.event(), self.posting(), candidate, state, self.config
            ),
            FuturesDcaCoreFillAdmission(
                "mapping-1",
                "ADMISSIBLE",
                (),
                "FUTURES_DCA_CORE_FILL_ADMISSION_READY",
                (
                    ("type", "FILL"),
                    ("execution_id", "execution-2"),
                    ("order_id", "core-order-1"),
                    ("side", "BUY"),
                    ("qty", "0.4"),
                    ("price", "100"),
                    ("fee", "0"),
                    ("fee_asset", "USDT"),
                ),
            ),
        )
        self.assertEqual(state, before)

    def test_fill_admission_blocks_unsupported_economic_or_core_authority(self):
        candidate = self.candidate(role="BASE")
        state = apply(State(), {"type": "MARK", "price": "100"}, self.config)
        state = apply(
            state,
            {
                "type": "INTENT",
                "order_id": "core-order-1",
                "intent_id": "core-intent-1",
                "role": "BASE",
                "qty": "1",
                "limit_price": "100",
            },
            self.config,
        )
        self.assertEqual(
            assess_futures_dca_core_fill_admission(
                self.event(), self.posting(fee="1"), candidate, state, self.config
            ),
            FuturesDcaCoreFillAdmission(
                "mapping-1", "BLOCKED", (), "FUTURES_DCA_CORE_FILL_FEE_CONFLICT"
            ),
        )
        self.assertEqual(
            assess_futures_dca_core_fill_admission(
                self.event(), self.posting(), self.candidate(role="BASE", core_order_intent_id="other-intent"), state, self.config
            ),
            FuturesDcaCoreFillAdmission(
                "mapping-1", "BLOCKED", (), "FUTURES_DCA_CORE_INTENT_ID_CONFLICT"
            ),
        )

    def test_admitted_fill_projects_exactly_on_copy_and_blocked_fill_does_not_project(self):
        candidate = self.candidate(role="BASE")
        state = apply(State(), {"type": "MARK", "price": "100"}, self.config)
        state = apply(
            state,
            {
                "type": "INTENT",
                "order_id": "core-order-1",
                "intent_id": "core-intent-1",
                "role": "BASE",
                "qty": "1",
                "limit_price": "100",
            },
            self.config,
        )
        before = deepcopy(state)
        admission = assess_futures_dca_core_fill_admission(
            self.event(), self.posting(), candidate, state, self.config
        )
        projection = project_futures_dca_core_fill(admission, state, self.config)
        expected = apply(
            state,
            {
                "type": "FILL",
                "execution_id": "execution-2",
                "order_id": "core-order-1",
                "side": "BUY",
                "qty": "0.4",
                "price": "100",
                "fee": "0",
                "fee_asset": "USDT",
            },
            self.config,
        )
        self.assertEqual(
            projection,
            FuturesDcaCoreFillProjection(
                "mapping-1", "PROJECTED", "FUTURES_DCA_CORE_FILL_REDUCER_PROJECTED", expected
            ),
        )
        self.assertEqual(state, before)
        blocked = assess_futures_dca_core_fill_admission(
            self.event(), self.posting(fee="1"), candidate, state, self.config
        )
        self.assertEqual(
            project_futures_dca_core_fill(blocked, state, self.config),
            FuturesDcaCoreFillProjection(
                "mapping-1", "BLOCKED", "FUTURES_DCA_CORE_FILL_FEE_CONFLICT"
            ),
        )

    def test_tampered_fill_proposal_is_rejected_before_reducer(self):
        admission = FuturesDcaCoreFillAdmission(
            "mapping-1",
            "ADMISSIBLE",
            (),
            "FUTURES_DCA_CORE_FILL_ADMISSION_READY",
            (("type", "FILL"),),
        )
        result = project_futures_dca_core_fill(admission, State(), self.config)
        self.assertEqual(
            result,
            FuturesDcaCoreFillProjection(
                "mapping-1", "BLOCKED", "FUTURES_DCA_CORE_FILL_PROPOSAL_INVALID"
            ),
        )

    def test_replay_decision_joins_exact_core_and_release_projections_read_only(self):
        candidate = self.candidate(role="BASE")
        state = apply(State(), {"type": "MARK", "price": "100"}, self.config)
        state = apply(
            state,
            {
                "type": "INTENT",
                "order_id": "core-order-1",
                "intent_id": "core-intent-1",
                "role": "BASE",
                "qty": "1",
                "limit_price": "100",
            },
            self.config,
        )
        reservation = FuturesDcaReservationProjection(
            "reservation-1", "deal-1", "USDT", "40", "0", "40", None, "OPEN", 0, "event-1"
        )
        transition = FuturesDcaReleaseTransition(
            "reservation-1", "event-2", "release-1", 1, 0, "FULL_FILL", "40", "0"
        )
        admission = assess_futures_dca_core_fill_admission(
            self.event(), self.posting(), candidate, state, self.config
        )
        before_state = deepcopy(state)
        before_reservation = reservation
        decision = assess_futures_dca_core_fill_replay(
            self.event(), self.posting(), transition, reservation, candidate, admission, state, self.config
        )
        self.assertEqual(decision.status, "ACCEPTED")
        self.assertEqual(decision.reason_code, "FUTURES_DCA_CORE_REPLAY_READY")
        self.assertEqual(decision.posting_id, "posting-1")
        self.assertEqual(decision.reservation.terminal_state, "RELEASED")
        self.assertEqual(decision.reservation.consumed_amount, "40")
        self.assertEqual(decision.core_state.orders["core-order-1"].filled, number("0.4"))
        self.assertEqual(state, before_state)
        self.assertEqual(reservation, before_reservation)

        duplicate = assess_futures_dca_core_fill_replay(
            self.event(), self.posting(), transition, decision.reservation, candidate, admission, state, self.config
        )
        self.assertEqual(
            duplicate,
            FuturesDcaCoreFillReplayDecision(
                "mapping-1", "DUPLICATE", "FUTURES_DCA_CORE_REPLAY_DUPLICATE"
            ),
        )

    def test_replay_decision_blocks_release_kind_or_amount_conflicts(self):
        candidate = self.candidate(role="BASE")
        state = apply(State(), {"type": "MARK", "price": "100"}, self.config)
        state = apply(
            state,
            {
                "type": "INTENT",
                "order_id": "core-order-1",
                "intent_id": "core-intent-1",
                "role": "BASE",
                "qty": "1",
                "limit_price": "100",
            },
            self.config,
        )
        reservation = FuturesDcaReservationProjection(
            "reservation-1", "deal-1", "USDT", "40", "0", "40", None, "OPEN", 0, "event-1"
        )
        admission = assess_futures_dca_core_fill_admission(
            self.event(), self.posting(), candidate, state, self.config
        )
        cancel = FuturesDcaReleaseTransition(
            "reservation-1", "event-2", "release-1", 1, 0, "CANCEL", "0", "40"
        )
        self.assertEqual(
            assess_futures_dca_core_fill_replay(
                self.event(), self.posting(), cancel, reservation, candidate, admission, state, self.config
            ),
            FuturesDcaCoreFillReplayDecision(
                "mapping-1", "BLOCKED", "FUTURES_DCA_CORE_REPLAY_TRANSITION_INVALID"
            ),
        )
        wrong_amount = FuturesDcaReleaseTransition(
            "reservation-1", "event-2", "release-1", 1, 0, "FULL_FILL", "39", "1"
        )
        self.assertEqual(
            assess_futures_dca_core_fill_replay(
                self.event(), self.posting(), wrong_amount, reservation, candidate, admission, state, self.config
            ),
            FuturesDcaCoreFillReplayDecision(
                "mapping-1", "BLOCKED", "FUTURES_DCA_CORE_REPLAY_RELEASE_REJECTED"
            ),
        )

    def test_replay_receipt_is_exactly_idempotent_without_replaying_economics(self):
        candidate, state, reservation, transition, _, decision = self.replay_context()
        self.assertEqual(decision.status, "ACCEPTED")
        before_state = deepcopy(state)
        receipt = build_futures_dca_core_replay_receipt(
            self.event(), self.posting(), transition, candidate, decision
        )
        self.assertIsInstance(receipt, FuturesDcaCoreReplayReceipt)
        self.assertEqual(receipt.mapping_id, "mapping-1")
        self.assertEqual(receipt.event_id, "event-2")
        self.assertEqual(receipt.posting_id, "posting-1")
        self.assertEqual(len(receipt.fingerprint), 64)
        self.assertEqual(
            assess_futures_dca_core_replay_retry(
                receipt, self.event(), self.posting(), transition, candidate
            ),
            FuturesDcaCoreReplayRetryDecision(
                "DUPLICATE", "FUTURES_DCA_CORE_REPLAY_DUPLICATE"
            ),
        )
        self.assertEqual(state, before_state)
        self.assertEqual(reservation.terminal_state, "OPEN")

    def test_replay_receipt_blocks_same_scope_conflict_and_other_scope(self):
        candidate, _, _, transition, _, decision = self.replay_context()
        receipt = build_futures_dca_core_replay_receipt(
            self.event(), self.posting(), transition, candidate, decision
        )
        self.assertEqual(
            assess_futures_dca_core_replay_retry(
                receipt, self.event(), self.posting(commitment="41"), transition, candidate
            ),
            FuturesDcaCoreReplayRetryDecision(
                "BLOCKED", "FUTURES_DCA_CORE_REPLAY_CONFLICT"
            ),
        )
        other_transition = FuturesDcaReleaseTransition(
            "reservation-1", "event-2", "release-2", 1, 0, "FULL_FILL", "40", "0"
        )
        self.assertEqual(
            assess_futures_dca_core_replay_retry(
                receipt, self.event(), self.posting(), other_transition, candidate
            ),
            FuturesDcaCoreReplayRetryDecision(
                "BLOCKED", "FUTURES_DCA_CORE_REPLAY_SCOPE_CONFLICT"
            ),
        )

    def test_replay_receipt_requires_an_accepted_decision(self):
        candidate, _, _, transition, _, _ = self.replay_context()
        with self.assertRaisesRegex(ValueError, "FUTURES_DCA_CORE_RECEIPT_NOT_ACCEPTED"):
            build_futures_dca_core_replay_receipt(
                self.event(),
                self.posting(),
                transition,
                candidate,
                FuturesDcaCoreFillReplayDecision(
                    "mapping-1", "BLOCKED", "FUTURES_DCA_CORE_REPLAY_RELEASE_REJECTED"
                ),
            )


if __name__ == "__main__":
    unittest.main()
