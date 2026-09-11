import unittest
from dataclasses import replace

from dcabot.data_adapters.binance_public import (
    BinanceTimeUnit,
    normalize_binance_agg_trade_payload,
    normalize_binance_trade_payload,
    replay_binance_observations,
)
from dcabot.data_adapters.public_feed import FeedState, ObservationOutcome


ALLOWLIST = frozenset({"BTCUSDT"})
RECEIVE_US = 1_700_000_000_000_100
PROCESSING_US = 1_700_000_000_000_200


def trade_payload() -> dict:
    return {
        "e": "trade",
        "E": 1_700_000_000_001,
        "s": "BTCUSDT",
        "t": 5000,
        "p": "50000.00",
        "q": "0.01000000",
        "b": 88,
        "a": 50,
        "T": 1_700_000_000_000,
        "m": False,
        "M": True,
    }


def agg_trade_payload() -> dict:
    return {
        "e": "aggTrade",
        "E": 1_700_000_000_001,
        "s": "BTCUSDT",
        "a": 7000,
        "p": "50000.00",
        "q": "0.01000000",
        "f": 5000,
        "l": 5002,
        "T": 1_700_000_000_000,
        "m": False,
        "M": True,
    }


class BinancePublicNormalizationTests(unittest.TestCase):
    def test_trade_payload_is_network_free_and_exactly_normalized(self):
        observation = normalize_binance_trade_payload(
            trade_payload(),
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )

        self.assertEqual(observation.source_id, "binance-spot-public-v3")
        self.assertEqual(observation.transport, "WEBSOCKET")
        self.assertEqual(observation.stream_type, "TRADE")
        self.assertEqual(observation.product, "SPOT")
        self.assertEqual(observation.event_id, "5000")
        self.assertEqual(observation.event_time_us, 1_700_000_000_000_000)
        self.assertEqual(observation.exchange_time_us, 1_700_000_000_001_000)
        self.assertEqual(observation.price, "50000")
        self.assertEqual(observation.quantity, "0.01")
        self.assertIsNone(observation.source_sequence)
        self.assertEqual(observation.buyer_order_id, 88)
        self.assertEqual(observation.seller_order_id, 50)

    def test_aggregate_trade_keeps_aggregate_identity_and_trade_range(self):
        observation = normalize_binance_agg_trade_payload(
            agg_trade_payload(),
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )

        self.assertEqual(observation.stream_type, "AGG_TRADE")
        self.assertEqual(observation.event_id, "7000")
        self.assertEqual(observation.first_trade_id, 5000)
        self.assertEqual(observation.last_trade_id, 5002)
        self.assertIsNone(observation.source_sequence)

    def test_explicit_microsecond_mode_does_not_multiply_twice(self):
        payload = trade_payload()
        payload["T"] = 1_700_000_000_000_000
        payload["E"] = 1_700_000_000_001_000

        observation = normalize_binance_trade_payload(
            payload,
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MICROSECONDS,
        )

        self.assertEqual(observation.event_time_us, payload["T"])
        self.assertEqual(observation.exchange_time_us, payload["E"])

    def test_invalid_scope_numeric_type_and_missing_event_are_fail_closed(self):
        cases = (
            (lambda: normalize_binance_trade_payload(
                {**trade_payload(), "s": "ETHUSDT"},
                allowed_symbols=ALLOWLIST,
                receive_time_us=RECEIVE_US,
                processing_time_us=PROCESSING_US,
                time_unit=BinanceTimeUnit.MILLISECONDS,
            )),
            (lambda: normalize_binance_trade_payload(
                {**trade_payload(), "p": 50000.0},
                allowed_symbols=ALLOWLIST,
                receive_time_us=RECEIVE_US,
                processing_time_us=PROCESSING_US,
                time_unit=BinanceTimeUnit.MILLISECONDS,
            )),
            (lambda: normalize_binance_trade_payload(
                {key: value for key, value in trade_payload().items() if key != "t"},
                allowed_symbols=ALLOWLIST,
                receive_time_us=RECEIVE_US,
                processing_time_us=PROCESSING_US,
                time_unit=BinanceTimeUnit.MILLISECONDS,
            )),
        )

        for call in cases:
            with self.subTest():
                with self.assertRaises(ValueError):
                    call()

    def test_binance_ids_are_not_bound_as_contiguous_source_sequence(self):
        first = normalize_binance_trade_payload(
            trade_payload(),
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )
        second_payload = {**trade_payload(), "t": 5002, "T": 1_700_000_000_002}
        second = normalize_binance_trade_payload(
            second_payload,
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )

        self.assertIsNone(first.source_sequence)
        self.assertIsNone(second.source_sequence)

    def test_replay_preserves_duplicate_idempotency_without_sequence_binding(self):
        first = normalize_binance_trade_payload(
            trade_payload(),
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )
        second_payload = {**trade_payload(), "t": 5002, "T": 1_700_000_000_002}
        second = normalize_binance_trade_payload(
            second_payload,
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )

        result = replay_binance_observations(
            (first, first, second),
            now_times_us=(RECEIVE_US + 100, RECEIVE_US + 100, RECEIVE_US + 100),
            max_staleness_us=1_000,
        )

        self.assertEqual(
            result.outcomes,
            (
                ObservationOutcome.ACCEPTED,
                ObservationOutcome.DUPLICATE,
                ObservationOutcome.ACCEPTED,
            ),
        )
        self.assertEqual(result.accepted_count, 2)
        self.assertEqual(result.cursor.state, FeedState.SYNCED)

    def test_mixed_trade_streams_fail_closed_at_scope_boundary(self):
        trade = normalize_binance_trade_payload(
            trade_payload(),
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )
        aggregate = normalize_binance_agg_trade_payload(
            agg_trade_payload(),
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )

        result = replay_binance_observations(
            (trade, aggregate),
            now_times_us=(RECEIVE_US + 100, RECEIVE_US + 100),
            max_staleness_us=1_000,
        )

        self.assertEqual(
            result.outcomes,
            (ObservationOutcome.ACCEPTED, ObservationOutcome.WRONG_SCOPE),
        )
        self.assertEqual(result.cursor.state, FeedState.FAILED)
        self.assertEqual(len(result.cursor.accepted), 1)

    def test_conflicting_duplicate_and_out_of_order_remain_fail_closed(self):
        first = normalize_binance_trade_payload(
            trade_payload(),
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )
        conflict = normalize_binance_trade_payload(
            {**trade_payload(), "p": "50001.00"},
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )

        conflict_result = replay_binance_observations(
            (first, conflict),
            now_times_us=(RECEIVE_US + 100, RECEIVE_US + 100),
            max_staleness_us=1_000,
        )

        self.assertEqual(
            conflict_result.outcomes,
            (ObservationOutcome.ACCEPTED, ObservationOutcome.CONFLICT),
        )
        self.assertEqual(conflict_result.cursor.state, FeedState.FAILED)

        older = replace(first, event_id="4999", event_time_us=first.event_time_us - 1)
        order_result = replay_binance_observations(
            (first, older),
            now_times_us=(RECEIVE_US + 100, RECEIVE_US + 100),
            max_staleness_us=1_000,
        )

        self.assertEqual(
            order_result.outcomes,
            (ObservationOutcome.ACCEPTED, ObservationOutcome.OUT_OF_ORDER),
        )
        self.assertEqual(order_result.cursor.state, FeedState.GAP)

    def test_replay_rejects_forged_binance_source_sequence(self):
        observation = normalize_binance_trade_payload(
            trade_payload(),
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )

        with self.assertRaises(ValueError):
            replay_binance_observations(
                (replace(observation, source_sequence=1),),
                now_times_us=(RECEIVE_US + 100,),
                max_staleness_us=1_000,
            )


if __name__ == "__main__":
    unittest.main()
