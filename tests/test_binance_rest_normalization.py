import unittest

from dcabot.data_adapters.binance_public import (
    BinanceTimeUnit,
    normalize_binance_agg_trade_payload,
    normalize_binance_rest_agg_trade_payload,
    normalize_binance_rest_trade_payload,
    normalize_binance_trade_payload,
)
from dcabot.data_adapters.public_feed import ObservationOutcome, replay_observations


ALLOWLIST = frozenset({"BTCUSDT"})
RECEIVE_US = 1_700_000_000_000_100
PROCESSING_US = 1_700_000_000_000_200


def rest_trade_payload(**overrides) -> dict:
    payload = {
        "id": 28457,
        "price": "50000.00",
        "qty": "0.01000000",
        "quoteQty": "500.00000000",
        "time": 1_700_000_000_000,
        "isBuyerMaker": True,
        "isBestMatch": True,
    }
    payload.update(overrides)
    return payload


def rest_agg_trade_payload(**overrides) -> dict:
    payload = {
        "a": 26129,
        "p": "50000.00",
        "q": "0.01000000",
        "f": 27781,
        "l": 27781,
        "T": 1_700_000_000_000,
        "m": True,
        "M": True,
    }
    payload.update(overrides)
    return payload


class BinanceRestNormalizationTests(unittest.TestCase):
    def test_recent_trade_maps_to_rest_observation_without_exchange_event_time(self):
        observation = normalize_binance_rest_trade_payload(
            rest_trade_payload(),
            symbol="BTCUSDT",
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )

        self.assertEqual(observation.source_id, "binance-spot-public-v3")
        self.assertEqual(observation.transport, "REST")
        self.assertEqual(observation.stream_type, "TRADE")
        self.assertEqual(observation.symbol, "BTCUSDT")
        self.assertEqual(observation.product, "SPOT")
        self.assertEqual(observation.event_id, "28457")
        self.assertEqual(observation.event_time_us, 1_700_000_000_000_000)
        self.assertIsNone(observation.exchange_time_us)
        self.assertEqual(observation.price, "50000")
        self.assertEqual(observation.quantity, "0.01")
        self.assertEqual(observation.is_buyer_maker, True)
        self.assertIsNone(observation.source_sequence)

    def test_aggregate_trade_keeps_rest_identity_and_range(self):
        observation = normalize_binance_rest_agg_trade_payload(
            rest_agg_trade_payload(),
            symbol="BTCUSDT",
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )

        self.assertEqual(observation.transport, "REST")
        self.assertEqual(observation.stream_type, "AGG_TRADE")
        self.assertEqual(observation.event_id, "26129")
        self.assertEqual(observation.first_trade_id, 27781)
        self.assertEqual(observation.last_trade_id, 27781)
        self.assertIsNone(observation.exchange_time_us)
        self.assertIsNone(observation.source_sequence)

    def test_rest_microsecond_mode_does_not_multiply_timestamp_twice(self):
        payload = rest_trade_payload(time=1_700_000_000_000_000)

        observation = normalize_binance_rest_trade_payload(
            payload,
            symbol="BTCUSDT",
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MICROSECONDS,
        )

        self.assertEqual(observation.event_time_us, payload["time"])

    def test_rest_scope_and_payload_errors_fail_closed(self):
        cases = (
            lambda: normalize_binance_rest_trade_payload(
                rest_trade_payload(price=50000.0),
                symbol="BTCUSDT",
                allowed_symbols=ALLOWLIST,
                receive_time_us=RECEIVE_US,
                processing_time_us=PROCESSING_US,
                time_unit=BinanceTimeUnit.MILLISECONDS,
            ),
            lambda: normalize_binance_rest_trade_payload(
                rest_trade_payload(),
                symbol="ETHUSDT",
                allowed_symbols=ALLOWLIST,
                receive_time_us=RECEIVE_US,
                processing_time_us=PROCESSING_US,
                time_unit=BinanceTimeUnit.MILLISECONDS,
            ),
            lambda: normalize_binance_rest_agg_trade_payload(
                {key: value for key, value in rest_agg_trade_payload().items() if key != "a"},
                symbol="BTCUSDT",
                allowed_symbols=ALLOWLIST,
                receive_time_us=RECEIVE_US,
                processing_time_us=PROCESSING_US,
                time_unit=BinanceTimeUnit.MILLISECONDS,
            ),
            lambda: normalize_binance_rest_trade_payload(
                rest_trade_payload(time=1_700_000_000_000_000),
                symbol="BTCUSDT",
                allowed_symbols=ALLOWLIST,
                receive_time_us=RECEIVE_US,
                processing_time_us=PROCESSING_US,
                time_unit=BinanceTimeUnit.MILLISECONDS,
            ),
        )

        for call in cases:
            with self.subTest():
                with self.assertRaises(ValueError):
                    call()

    def test_rest_trade_and_ws_trade_keep_transport_scope_distinct(self):
        rest = normalize_binance_rest_trade_payload(
            rest_trade_payload(),
            symbol="BTCUSDT",
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )
        self.assertEqual(rest.transport, "REST")
        self.assertNotEqual(rest.immutable_key()[1], "WEBSOCKET")

    def test_rest_duplicate_is_idempotent_and_mixed_transport_fails_closed(self):
        rest = normalize_binance_rest_trade_payload(
            rest_trade_payload(),
            symbol="BTCUSDT",
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )
        rest_duplicate_result = replay_observations(
            (rest, rest),
            now_times_us=(RECEIVE_US + 100, RECEIVE_US + 100),
            max_staleness_us=1_000,
        )

        self.assertEqual(
            rest_duplicate_result.outcomes,
            (ObservationOutcome.ACCEPTED, ObservationOutcome.DUPLICATE),
        )

        ws = normalize_binance_trade_payload(
            {
                "e": "trade",
                "E": 1_700_000_000_001,
                "s": "BTCUSDT",
                "t": 28457,
                "p": "50000.00",
                "q": "0.01000000",
                "T": 1_700_000_000_000,
                "m": True,
            },
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )
        mixed_result = replay_observations(
            (rest, ws),
            now_times_us=(RECEIVE_US + 100, RECEIVE_US + 100),
            max_staleness_us=1_000,
        )

        self.assertEqual(
            mixed_result.outcomes,
            (ObservationOutcome.ACCEPTED, ObservationOutcome.CONFLICT),
        )

    def test_rest_trade_and_aggregate_stream_scope_cannot_mix(self):
        rest_trade = normalize_binance_rest_trade_payload(
            rest_trade_payload(),
            symbol="BTCUSDT",
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )
        rest_aggregate = normalize_binance_rest_agg_trade_payload(
            rest_agg_trade_payload(),
            symbol="BTCUSDT",
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )
        result = replay_observations(
            (rest_trade, rest_aggregate),
            now_times_us=(RECEIVE_US + 100, RECEIVE_US + 100),
            max_staleness_us=1_000,
        )

        self.assertEqual(
            result.outcomes,
            (ObservationOutcome.ACCEPTED, ObservationOutcome.WRONG_SCOPE),
        )


if __name__ == "__main__":
    unittest.main()
