import unittest

from dcabot.application.order_list_contract import (
    OrderListLegIdentity,
    OrderListLegRole,
)
from dcabot.application.order_list_reconciliation import (
    CancelReplaceDisposition,
    CancelReplaceIdentity,
    OrderListEventOutcome,
    OrderListVenueEvent,
    reconcile_order_list_event,
)
from dcabot.application.order_list_contract import create_oco_identity


def oco_identity():
    return create_oco_identity(
        order_list_id=42,
        list_client_order_id="list-42",
        symbol="BTCUSDT",
        working=OrderListLegIdentity(
            leg_id="working",
            order_id=101,
            client_order_id="working-101",
            role=OrderListLegRole.WORKING,
            order_type="LIMIT",
        ),
        pending=OrderListLegIdentity(
            leg_id="pending",
            order_id=102,
            client_order_id="pending-102",
            role=OrderListLegRole.PENDING,
            order_type="STOP_LOSS_LIMIT",
        ),
    )


def event(**overrides):
    values = {
        "event_id": "event-1",
        "event_time_ms": 100,
        "order_list_id": 42,
        "list_client_order_id": "list-42",
        "order_id": 101,
        "client_order_id": "working-101",
        "list_status": "EXECUTING",
        "list_order_status": "EXECUTING",
        "leg_status": "NEW",
    }
    values.update(overrides)
    return OrderListVenueEvent(**values)


class OrderListReconciliationTests(unittest.TestCase):
    def test_exact_list_and_leg_identity_is_matched_without_fill_data(self):
        result = reconcile_order_list_event(oco_identity(), event())

        self.assertEqual(result.outcome, OrderListEventOutcome.MATCHED)
        self.assertEqual(result.matched_leg_id, "working")
        self.assertFalse(hasattr(result, "raw_payload"))

    def test_list_or_leg_identity_mismatch_is_conflict(self):
        identity = oco_identity()

        list_conflict = reconcile_order_list_event(identity, event(order_list_id=43))
        leg_conflict = reconcile_order_list_event(identity, event(client_order_id="other"))

        self.assertEqual(list_conflict.outcome, OrderListEventOutcome.CONFLICT)
        self.assertEqual(leg_conflict.outcome, OrderListEventOutcome.CONFLICT)
        self.assertIsNone(leg_conflict.matched_leg_id)

    def test_cancel_replace_both_success_requires_replacement_identity(self):
        result = CancelReplaceIdentity(
            operation_id="replace-1",
            prior_order_id=101,
            prior_client_order_id="working-101",
            cancel_result="SUCCESS",
            new_order_result="SUCCESS",
            replacement_order_id=103,
            replacement_client_order_id="working-103",
            observed_at_ms=100,
        )

        self.assertEqual(result.disposition, CancelReplaceDisposition.CONFIRMED)
        self.assertEqual(result.replacement_order_id, 103)

    def test_partial_cancel_replace_results_are_explicit_and_fail_closed(self):
        cancel_only = CancelReplaceIdentity(
            operation_id="replace-2",
            prior_order_id=101,
            prior_client_order_id="working-101",
            cancel_result="SUCCESS",
            new_order_result="FAILURE",
            replacement_order_id=None,
            replacement_client_order_id=None,
            observed_at_ms=100,
        )
        new_only = CancelReplaceIdentity(
            operation_id="replace-3",
            prior_order_id=101,
            prior_client_order_id="working-101",
            cancel_result="FAILURE",
            new_order_result="SUCCESS",
            replacement_order_id=103,
            replacement_client_order_id="working-103",
            observed_at_ms=100,
        )

        self.assertEqual(
            cancel_only.disposition,
            CancelReplaceDisposition.CANCEL_CONFIRMED_NEW_REJECTED,
        )
        self.assertEqual(
            new_only.disposition,
            CancelReplaceDisposition.CANCEL_REJECTED_NEW_CONFIRMED,
        )

    def test_missing_or_unexpected_result_is_unknown(self):
        result = CancelReplaceIdentity(
            operation_id="replace-4",
            prior_order_id=101,
            prior_client_order_id="working-101",
            cancel_result=None,
            new_order_result="SUCCESS",
            replacement_order_id=None,
            replacement_client_order_id=None,
            observed_at_ms=100,
        )

        self.assertEqual(result.disposition, CancelReplaceDisposition.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
