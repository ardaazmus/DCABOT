import unittest

from dcabot.application.futures_grid_local_lifecycle import (
    FuturesGridLocalEventType,
    FuturesGridLocalLifecycleStatus,
    apply_futures_grid_local_event,
    new_futures_grid_local_event,
    new_futures_grid_local_lifecycle,
    replay_futures_grid_local_events,
)


class FuturesGridLocalLifecycleTests(unittest.TestCase):
    def test_fill_wins_over_cancel_in_the_local_simulation(self):
        events = (
            new_futures_grid_local_event(
                "event-1", FuturesGridLocalEventType.CANCEL_REQUESTED, 1
            ),
            new_futures_grid_local_event(
                "event-2", FuturesGridLocalEventType.CANCEL_CONFIRMED, 2
            ),
            new_futures_grid_local_event(
                "event-3", FuturesGridLocalEventType.FILL_ACCEPTED, 3, "trade-1"
            ),
        )

        state, outcomes = replay_futures_grid_local_events(events)

        self.assertEqual(
            (state.status, state.fill_ids, outcomes),
            (
                FuturesGridLocalLifecycleStatus.FILLED,
                ("trade-1",),
                ("ACCEPTED", "ACCEPTED", "ACCEPTED"),
            ),
        )

    def test_replacement_requires_cancel_confirmation(self):
        state, outcome = apply_futures_grid_local_event(
            new_futures_grid_local_lifecycle(),
            new_futures_grid_local_event(
                "event-1", FuturesGridLocalEventType.CANCEL_REQUESTED, 1
            ),
        )
        quarantined, outcome = apply_futures_grid_local_event(
            state,
            new_futures_grid_local_event(
                "event-2", FuturesGridLocalEventType.REPLACEMENT_REQUESTED, 2
            ),
        )

        self.assertEqual(
            (quarantined.status, outcome),
            (FuturesGridLocalLifecycleStatus.QUARANTINED, "QUARANTINED"),
        )

    def test_exact_duplicate_trade_is_ignored(self):
        state, _ = apply_futures_grid_local_event(
            new_futures_grid_local_lifecycle(),
            new_futures_grid_local_event(
                "event-1", FuturesGridLocalEventType.FILL_ACCEPTED, 1, "trade-1"
            ),
        )
        duplicate, outcome = apply_futures_grid_local_event(
            state,
            new_futures_grid_local_event(
                "event-2", FuturesGridLocalEventType.FILL_ACCEPTED, 2, "trade-1"
            ),
        )

        self.assertEqual((duplicate, outcome), (state, "DUPLICATE"))

    def test_unknown_observation_quarantines_and_blocks_follow_up(self):
        state, outcome = apply_futures_grid_local_event(
            new_futures_grid_local_lifecycle(),
            new_futures_grid_local_event(
                "event-1", FuturesGridLocalEventType.UNKNOWN_OBSERVATION, 1
            ),
        )
        blocked, blocked_outcome = apply_futures_grid_local_event(
            state,
            new_futures_grid_local_event(
                "event-2", FuturesGridLocalEventType.FILL_ACCEPTED, 2, "trade-1"
            ),
        )

        self.assertEqual(
            (state.status, outcome, blocked, blocked_outcome),
            (
                FuturesGridLocalLifecycleStatus.QUARANTINED,
                "QUARANTINED",
                state,
                "BLOCKED_QUARANTINED",
            ),
        )

    def test_replay_is_deterministic_and_has_no_external_authority(self):
        events = (
            new_futures_grid_local_event(
                "event-1", FuturesGridLocalEventType.CANCEL_REQUESTED, 1
            ),
            new_futures_grid_local_event(
                "event-2", FuturesGridLocalEventType.CANCEL_CONFIRMED, 2
            ),
            new_futures_grid_local_event(
                "event-3", FuturesGridLocalEventType.REPLACEMENT_REQUESTED, 3
            ),
        )

        first = replay_futures_grid_local_events(events)
        second = replay_futures_grid_local_events(events)

        self.assertEqual(first, second)
        for field in (
            "order_id",
            "replacement_id",
            "reserve",
            "economic_posting",
            "store",
            "venue",
        ):
            self.assertFalse(hasattr(first[0], field))


if __name__ == "__main__":
    unittest.main()
