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


def trade_payload(**overrides) -> dict:
    payload = {
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
    payload.update(overrides)
    return payload


def aggregate_payload(**overrides) -> dict:
    payload = {
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
    payload.update(overrides)
    return payload


def normalize_trade(payload=None, *, time_unit=BinanceTimeUnit.MILLISECONDS):
    return normalize_binance_trade_payload(
        trade_payload() if payload is None else payload,
        allowed_symbols=ALLOWLIST,
        receive_time_us=RECEIVE_US,
        processing_time_us=PROCESSING_US,
        time_unit=time_unit,
    )


class BinancePublicAcceptanceMatrixTests(unittest.TestCase):
    def test_bounded_acceptance_matrix(self):
        micro_payload = trade_payload(
            T=1_700_000_000_000_000,
            E=1_700_000_000_001_000,
        )
        parser_cases = (
            ("valid_trade", lambda: normalize_trade(), False),
            (
                "valid_agg_trade",
                lambda: normalize_binance_agg_trade_payload(
                    aggregate_payload(),
                    allowed_symbols=ALLOWLIST,
                    receive_time_us=RECEIVE_US,
                    processing_time_us=PROCESSING_US,
                    time_unit=BinanceTimeUnit.MILLISECONDS,
                ),
                False,
            ),
            (
                "valid_microseconds",
                lambda: normalize_trade(
                    micro_payload, time_unit=BinanceTimeUnit.MICROSECONDS
                ),
                False,
            ),
            ("wrong_event_type", lambda: normalize_trade(trade_payload(e="kline")), True),
            ("wrong_symbol", lambda: normalize_trade(trade_payload(s="ETHUSDT")), True),
            ("float_price", lambda: normalize_trade(trade_payload(p=50000.0)), True),
            ("missing_event_id", lambda: normalize_trade(trade_payload(t=None)), True),
            (
                "timestamp_unit_mismatch",
                lambda: normalize_trade(
                    micro_payload, time_unit=BinanceTimeUnit.MILLISECONDS
                ),
                True,
            ),
        )
        for name, call, must_fail in parser_cases:
            with self.subTest(name=name):
                if must_fail:
                    with self.assertRaises(ValueError):
                        call()
                else:
                    observation = call()
                    self.assertEqual(observation.source_id, "binance-spot-public-v3")
                    self.assertEqual(observation.transport, "WEBSOCKET")
                    self.assertIsNone(observation.source_sequence)
                    self.assertFalse(
                        any(hasattr(observation, field) for field in ("order", "fill", "pnl", "reserve"))
                    )

        first = normalize_trade()
        next_observation = normalize_trade(
            trade_payload(t=5002, T=1_700_000_000_002)
        )
        conflict = normalize_trade(trade_payload(p="50001.00"))
        older = replace(first, event_id="4999", event_time_us=first.event_time_us - 1)
        aggregate = normalize_binance_agg_trade_payload(
            aggregate_payload(),
            allowed_symbols=ALLOWLIST,
            receive_time_us=RECEIVE_US,
            processing_time_us=PROCESSING_US,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )
        replay_cases = (
            (
                "duplicate_then_noncontiguous_id",
                (first, first, next_observation),
                (ObservationOutcome.ACCEPTED, ObservationOutcome.DUPLICATE, ObservationOutcome.ACCEPTED),
                FeedState.SYNCED,
            ),
            (
                "conflicting_duplicate",
                (first, conflict),
                (ObservationOutcome.ACCEPTED, ObservationOutcome.CONFLICT),
                FeedState.FAILED,
            ),
            (
                "event_time_out_of_order",
                (first, older),
                (ObservationOutcome.ACCEPTED, ObservationOutcome.OUT_OF_ORDER),
                FeedState.GAP,
            ),
            (
                "mixed_stream_scope",
                (first, aggregate),
                (ObservationOutcome.ACCEPTED, ObservationOutcome.WRONG_SCOPE),
                FeedState.FAILED,
            ),
        )
        for name, observations, expected_outcomes, expected_state in replay_cases:
            with self.subTest(name=name):
                result = replay_binance_observations(
                    observations,
                    now_times_us=(RECEIVE_US + 100,) * len(observations),
                    max_staleness_us=1_000,
                )
                self.assertEqual(result.outcomes, expected_outcomes)
                self.assertEqual(result.cursor.state, expected_state)


if __name__ == "__main__":
    unittest.main()
