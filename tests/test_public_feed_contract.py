import unittest

from dcabot.data_adapters.public_feed import (
    FeedState,
    ObservationOutcome,
    accept_observation,
    assess_feed_state,
    begin_reconnect,
    new_public_observation,
    new_feed_cursor,
    replay_observations,
)


def observation(*, event_id="evt-1", sequence=1, event_time_us=1_000, receive_time_us=1_100, payload_hash=None):
    return new_public_observation(
        source_id="public-fixture",
        transport="WEBSOCKET",
        symbol="BTCUSDT",
        product="SPOT",
        event_id=event_id,
        event_time_us=event_time_us,
        receive_time_us=receive_time_us,
        processing_time_us=1_200,
        price="100",
        quantity="0.1",
        payload_hash=payload_hash or "a" * 64,
        source_sequence=sequence,
    )


class PublicFeedContractTests(unittest.TestCase):
    def test_bounded_replay_returns_only_observation_outcomes(self):
        result = replay_observations(
            (observation(), observation(event_id="evt-1")),
            now_times_us=(1_200, 1_300),
            max_staleness_us=100,
        )

        self.assertEqual(
            result.outcomes,
            (ObservationOutcome.ACCEPTED, ObservationOutcome.DUPLICATE),
        )
        self.assertEqual(result.accepted_count, 1)
        self.assertEqual(len(result.cursor.accepted), 1)
        self.assertFalse(hasattr(result, "run_id"))
        self.assertFalse(hasattr(result, "result_id"))
        self.assertFalse(hasattr(result, "pnl"))

    def test_replay_gap_stops_acceptance_until_explicit_resync_index(self):
        result = replay_observations(
            (
                observation(),
                observation(event_id="evt-3", sequence=3, event_time_us=3_000, receive_time_us=3_100),
                observation(event_id="evt-4", sequence=4, event_time_us=4_000, receive_time_us=4_100),
                observation(event_id="evt-9", sequence=9, event_time_us=9_000, receive_time_us=9_100),
            ),
            now_times_us=(1_200, 3_200, 4_200, 9_200),
            max_staleness_us=100,
            resync_indexes=frozenset({3}),
        )

        self.assertEqual(
            result.outcomes,
            (
                ObservationOutcome.ACCEPTED,
                ObservationOutcome.SEQUENCE_GAP,
                ObservationOutcome.RESYNC_REQUIRED,
                ObservationOutcome.ACCEPTED,
            ),
        )
        self.assertEqual(result.accepted_count, 2)
        self.assertEqual(result.cursor.last_source_sequence, 9)

    def test_first_observation_is_synced_and_has_no_economic_fields(self):
        result = accept_observation(
            new_feed_cursor(), observation(), now_time_us=1_200, max_staleness_us=100
        )

        self.assertEqual(result.outcome, ObservationOutcome.ACCEPTED)
        self.assertEqual(result.cursor.state, FeedState.SYNCED)
        self.assertEqual(result.cursor.accepted, (observation(),))
        self.assertFalse(hasattr(result.cursor, "fill"))
        self.assertFalse(hasattr(result.cursor, "order"))

    def test_exact_duplicate_is_noop(self):
        cursor = new_feed_cursor()
        first = accept_observation(cursor, observation(), now_time_us=1_200, max_staleness_us=100)
        second = accept_observation(first.cursor, observation(), now_time_us=1_300, max_staleness_us=100)

        self.assertEqual(second.outcome, ObservationOutcome.DUPLICATE)
        self.assertEqual(second.cursor, first.cursor)

    def test_conflicting_duplicate_is_fail_closed(self):
        cursor = new_feed_cursor()
        first = accept_observation(cursor, observation(), now_time_us=1_200, max_staleness_us=100)
        conflicting = observation(payload_hash="b" * 64)
        second = accept_observation(first.cursor, conflicting, now_time_us=1_200, max_staleness_us=100)

        self.assertEqual(second.outcome, ObservationOutcome.CONFLICT)
        self.assertEqual(second.cursor.state, FeedState.FAILED)
        self.assertEqual(second.cursor.accepted, first.cursor.accepted)

    def test_sequence_gap_is_quarantined_without_accepting_the_event(self):
        cursor = new_feed_cursor()
        first = accept_observation(cursor, observation(), now_time_us=1_200, max_staleness_us=100)
        gap = accept_observation(
            first.cursor,
            observation(event_id="evt-3", sequence=3, event_time_us=3_000, receive_time_us=3_100),
            now_time_us=3_200,
            max_staleness_us=100,
        )

        self.assertEqual(gap.outcome, ObservationOutcome.SEQUENCE_GAP)
        self.assertEqual(gap.cursor.state, FeedState.GAP)
        self.assertEqual(gap.cursor.accepted, first.cursor.accepted)

    def test_out_of_order_event_is_quarantined(self):
        cursor = new_feed_cursor()
        first = accept_observation(cursor, observation(), now_time_us=1_200, max_staleness_us=100)
        late = accept_observation(
            first.cursor,
            observation(event_id="evt-0", sequence=0, event_time_us=900, receive_time_us=1_300),
            now_time_us=1_400,
            max_staleness_us=100,
        )

        self.assertEqual(late.outcome, ObservationOutcome.OUT_OF_ORDER)
        self.assertEqual(late.cursor.state, FeedState.GAP)
        self.assertEqual(late.cursor.accepted, first.cursor.accepted)

    def test_stale_observation_is_not_accepted(self):
        result = accept_observation(
            new_feed_cursor(), observation(receive_time_us=1_000), now_time_us=1_101, max_staleness_us=100
        )

        self.assertEqual(result.outcome, ObservationOutcome.STALE)
        self.assertEqual(result.cursor.state, FeedState.STALE)
        self.assertEqual(result.cursor.accepted, ())

    def test_reconnect_requires_explicit_resync_before_acceptance(self):
        cursor = new_feed_cursor()
        first = accept_observation(cursor, observation(), now_time_us=1_200, max_staleness_us=100)
        reconnecting = begin_reconnect(first.cursor)
        blocked = accept_observation(
            reconnecting, observation(event_id="evt-2", sequence=2, event_time_us=2_000, receive_time_us=2_100),
            now_time_us=2_200,
            max_staleness_us=100,
        )

        self.assertEqual(reconnecting.state, FeedState.RECONNECTING)
        self.assertEqual(blocked.outcome, ObservationOutcome.RESYNC_REQUIRED)
        self.assertEqual(blocked.cursor.state, FeedState.RECONNECTING)
        self.assertEqual(blocked.cursor.accepted, first.cursor.accepted)

    def test_resync_establishes_a_new_contiguous_segment(self):
        cursor = new_feed_cursor()
        first = accept_observation(cursor, observation(), now_time_us=1_200, max_staleness_us=100)
        reconnecting = begin_reconnect(first.cursor)
        resumed = accept_observation(
            reconnecting,
            observation(event_id="evt-9", sequence=9, event_time_us=9_000, receive_time_us=9_100),
            now_time_us=9_200,
            max_staleness_us=100,
            resync=True,
        )

        self.assertEqual(resumed.outcome, ObservationOutcome.ACCEPTED)
        self.assertEqual(resumed.cursor.state, FeedState.SYNCED)
        self.assertEqual(resumed.cursor.last_source_sequence, 9)

    def test_stale_boundary_is_inclusive_and_deterministic(self):
        first = accept_observation(
            new_feed_cursor(), observation(), now_time_us=1_200, max_staleness_us=100
        )

        self.assertEqual(
            assess_feed_state(first.cursor, now_time_us=1_200, max_staleness_us=100),
            FeedState.SYNCED,
        )
        self.assertEqual(
            assess_feed_state(first.cursor, now_time_us=1_301, max_staleness_us=100),
            FeedState.STALE,
        )


if __name__ == "__main__":
    unittest.main()
