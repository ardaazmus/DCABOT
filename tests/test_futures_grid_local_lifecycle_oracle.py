import unittest

from dcabot.application.futures_grid_local_lifecycle import (
    FuturesGridLocalEventType,
    FuturesGridLocalLifecycleError,
    FuturesGridLocalLifecycleStatus,
    apply_futures_grid_local_event,
    new_futures_grid_local_event,
    new_futures_grid_local_lifecycle,
    replay_futures_grid_local_events,
)


def _event(
    event_id: str,
    event_type: FuturesGridLocalEventType,
    sequence: int,
    fill_id: str | None = None,
):
    return new_futures_grid_local_event(event_id, event_type, sequence, fill_id)


class FuturesGridLocalLifecycleOracleTests(unittest.TestCase):
    def test_literal_transition_matrix(self):
        cases = (
            (
                (
                    _event("event-1", FuturesGridLocalEventType.CANCEL_REQUESTED, 1),
                ),
                FuturesGridLocalLifecycleStatus.CANCEL_PENDING,
                ("ACCEPTED",),
            ),
            (
                (
                    _event("event-1", FuturesGridLocalEventType.CANCEL_REQUESTED, 1),
                    _event("event-2", FuturesGridLocalEventType.CANCEL_CONFIRMED, 2),
                ),
                FuturesGridLocalLifecycleStatus.CANCELED,
                ("ACCEPTED", "ACCEPTED"),
            ),
            (
                (
                    _event("event-1", FuturesGridLocalEventType.CANCEL_REQUESTED, 1),
                    _event("event-2", FuturesGridLocalEventType.CANCEL_CONFIRMED, 2),
                    _event("event-3", FuturesGridLocalEventType.FILL_ACCEPTED, 3, "trade-1"),
                ),
                FuturesGridLocalLifecycleStatus.FILLED,
                ("ACCEPTED", "ACCEPTED", "ACCEPTED"),
            ),
            (
                (
                    _event("event-1", FuturesGridLocalEventType.CANCEL_REQUESTED, 1),
                    _event("event-2", FuturesGridLocalEventType.CANCEL_CONFIRMED, 2),
                    _event("event-3", FuturesGridLocalEventType.REPLACEMENT_REQUESTED, 3),
                ),
                FuturesGridLocalLifecycleStatus.REPLACEMENT_READY,
                ("ACCEPTED", "ACCEPTED", "ACCEPTED"),
            ),
            (
                (
                    _event("event-1", FuturesGridLocalEventType.REPLACEMENT_REQUESTED, 1),
                ),
                FuturesGridLocalLifecycleStatus.QUARANTINED,
                ("QUARANTINED",),
            ),
        )

        for events, expected_status, expected_outcomes in cases:
            with self.subTest(expected_status=expected_status):
                state, outcomes = replay_futures_grid_local_events(events)
                self.assertEqual(
                    (state.status, outcomes), (expected_status, expected_outcomes)
                )

    def test_conflicting_event_identity_quarantines_without_appending(self):
        state, _ = apply_futures_grid_local_event(
            new_futures_grid_local_lifecycle(),
            _event("event-1", FuturesGridLocalEventType.CANCEL_REQUESTED, 1),
        )

        quarantined, outcome = apply_futures_grid_local_event(
            state,
            _event("event-1", FuturesGridLocalEventType.CANCEL_CONFIRMED, 2),
        )

        self.assertEqual(
            (quarantined.status, quarantined.events, outcome),
            (
                FuturesGridLocalLifecycleStatus.QUARANTINED,
                state.events,
                "QUARANTINED",
            ),
        )

    def test_invalid_sequence_is_rejected_before_transition(self):
        with self.assertRaisesRegex(
            FuturesGridLocalLifecycleError,
            "FUTURES_GRID_LOCAL_EVENT_SEQUENCE_INVALID",
        ):
            apply_futures_grid_local_event(
                new_futures_grid_local_lifecycle(),
                _event("event-2", FuturesGridLocalEventType.CANCEL_REQUESTED, 2),
            )

    def test_replay_has_literal_stable_result(self):
        events = (
            _event("event-1", FuturesGridLocalEventType.CANCEL_REQUESTED, 1),
            _event("event-2", FuturesGridLocalEventType.CANCEL_CONFIRMED, 2),
            _event("event-3", FuturesGridLocalEventType.REPLACEMENT_REQUESTED, 3),
        )

        state, outcomes = replay_futures_grid_local_events(events)

        self.assertEqual(state.status, FuturesGridLocalLifecycleStatus.REPLACEMENT_READY)
        self.assertEqual(state.events, events)
        self.assertEqual(state.fill_ids, ())
        self.assertTrue(state.replacement_admitted)
        self.assertEqual(outcomes, ("ACCEPTED", "ACCEPTED", "ACCEPTED"))


if __name__ == "__main__":
    unittest.main()
