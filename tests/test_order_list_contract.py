import unittest

from dcabot.application.order_list_contract import (
    OrderListError,
    OrderListLegIdentity,
    OrderListLegRole,
    OrderListLegStatus,
    OrderListObservation,
    OrderListObservationOutcome,
    OrderListStatus,
    admit_order_list_observation,
    create_oco_identity,
)


class OrderListContractTests(unittest.TestCase):
    def setUp(self):
        self.identity = create_oco_identity(
            order_list_id=7,
            list_client_order_id="list-7",
            symbol="BTCUSDT",
            working=OrderListLegIdentity(
                leg_id="working-7",
                order_id=70,
                client_order_id="working-client-7",
                role=OrderListLegRole.WORKING,
                order_type="LIMIT_MAKER",
            ),
            pending=OrderListLegIdentity(
                leg_id="pending-7",
                order_id=71,
                client_order_id="pending-client-7",
                role=OrderListLegRole.PENDING,
                order_type="STOP_LOSS_LIMIT",
            ),
        )

    def _observation(self, *, event_id="event-1", status="EXEC_STARTED", at=100, legs=None):
        return OrderListObservation(
            event_id=event_id,
            order_list_id=7,
            list_client_order_id="list-7",
            list_status=status,
            list_order_status="EXECUTING" if status != "ALL_DONE" else "ALL_DONE",
            leg_statuses=legs or ("NEW", "PENDING_NEW"),
            observed_at_ms=at,
        )

    def test_identity_requires_two_typed_working_pending_legs(self):
        self.assertEqual(self.identity.legs[0].role, OrderListLegRole.WORKING)
        self.assertEqual(self.identity.legs[1].role, OrderListLegRole.PENDING)
        with self.assertRaisesRegex(OrderListError, "ORDER_LIST_WORKING_TYPE_INVALID"):
            OrderListLegIdentity("bad-working", 72, "bad-client", "WORKING", "STOP_LOSS")
        with self.assertRaisesRegex(OrderListError, "ORDER_LIST_LEG_ROLES_INVALID"):
            create_oco_identity(
                order_list_id=8,
                list_client_order_id="list-8",
                symbol="BTCUSDT",
                working=self.identity.legs[1],
                pending=self.identity.legs[0],
            )

    def test_observation_replay_is_idempotent_and_conflict_safe(self):
        first = self._observation()
        snapshot = admit_order_list_observation(self.identity, first)
        duplicate = snapshot.apply(self._observation(event_id="event-1", at=100))
        self.assertEqual(duplicate.outcome, OrderListObservationOutcome.DUPLICATE)
        with self.assertRaisesRegex(OrderListError, "ORDER_LIST_EVENT_CONFLICT"):
            snapshot.apply(self._observation(event_id="event-1", at=101))

    def test_status_and_identity_mismatches_fail_closed(self):
        snapshot = admit_order_list_observation(self.identity, self._observation())
        with self.assertRaisesRegex(OrderListError, "ORDER_LIST_EVENT_OUT_OF_ORDER"):
            snapshot.apply(self._observation(event_id="event-0", at=99))
        wrong_identity = OrderListObservation(
            event_id="event-2",
            order_list_id=8,
            list_client_order_id="list-8",
            list_status="EXECUTING",
            list_order_status="EXECUTING",
            leg_statuses=("NEW", "PENDING_NEW"),
            observed_at_ms=101,
        )
        with self.assertRaisesRegex(OrderListError, "ORDER_LIST_IDENTITY_MISMATCH"):
            snapshot.apply(wrong_identity)

    def test_oco_terminal_coordination_does_not_create_fill_or_core_event(self):
        initial = admit_order_list_observation(self.identity, self._observation())
        terminal = initial.apply(
            self._observation(
                event_id="event-2",
                status="ALL_DONE",
                at=101,
                legs=(OrderListLegStatus.FILLED, OrderListLegStatus.EXPIRED),
            )
        )
        self.assertEqual(terminal.snapshot.list_status, OrderListStatus.ALL_DONE)
        self.assertFalse(hasattr(terminal.snapshot, "fills"))
        self.assertFalse(hasattr(terminal.snapshot, "core_events"))
        with self.assertRaisesRegex(OrderListError, "ORDER_LIST_OCO_COORDINATION_INVALID"):
            initial.apply(
                self._observation(
                    event_id="event-both-filled",
                    status="ALL_DONE",
                    at=101,
                    legs=("FILLED", "FILLED"),
                )
            )
        with self.assertRaisesRegex(OrderListError, "ORDER_LIST_TERMINAL_EVENT"):
            terminal.snapshot.apply(
                self._observation(
                    event_id="event-3",
                    status="ALL_DONE",
                    at=102,
                    legs=("FILLED", "EXPIRED"),
                )
            )


if __name__ == "__main__":
    unittest.main()
