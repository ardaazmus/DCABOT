import unittest

from dcabot.application.paper_feed_binding import (
    PaperMarketState,
    apply_observations,
    new_market_state,
)
from dcabot.data_adapters.public_feed import ObservationOutcome, new_public_observation

HASH = "ab" * 32


def _obs(event_id, price, event_time_us, seq):
    return new_public_observation(
        source_id="binance-spot-public-v3",
        transport="REST",
        symbol="BTCUSDT",
        product="SPOT",
        event_id=event_id,
        event_time_us=event_time_us,
        receive_time_us=event_time_us + 100,
        processing_time_us=event_time_us + 200,
        price=price,
        quantity="1",
        payload_hash=HASH,
        source_sequence=seq,
    )


class ApplyObservationsTests(unittest.TestCase):
    def test_accepted_prints_update_last_price(self):
        state = new_market_state()
        state, outcomes = apply_observations(
            state,
            (_obs("e1", "50000", 1000, 1), _obs("e2", "50010", 2000, 2)),
            now_times_us=(3000, 3000),
            max_staleness_us=5000,
        )
        self.assertIsInstance(state, PaperMarketState)
        self.assertEqual(outcomes, (ObservationOutcome.ACCEPTED, ObservationOutcome.ACCEPTED))
        self.assertEqual(
            [(m.symbol, m.price, m.event_id) for m in state.marks],
            [("BTCUSDT", "50010", "e2")],
        )

    def test_stale_print_does_not_move_price(self):
        state = new_market_state()
        state, _ = apply_observations(
            state,
            (_obs("e1", "50000", 1000, 1),),
            now_times_us=(3000,),
            max_staleness_us=5000,
        )
        state, outcomes = apply_observations(
            state,
            (_obs("e9", "1", 1000, 2),),
            now_times_us=(999_999,),
            max_staleness_us=5000,
        )
        self.assertEqual(outcomes, (ObservationOutcome.STALE,))
        self.assertEqual(state.marks[0].price, "50000")

    def test_new_symbol_adds_new_mark(self):
        state = new_market_state()
        eth = new_public_observation(
            source_id="binance-spot-public-v3", transport="REST",
            symbol="ETHUSDT", product="SPOT", event_id="x1",
            event_time_us=1000, receive_time_us=1100,
            processing_time_us=1200, price="3000",
            quantity="1", payload_hash=HASH, source_sequence=None,
        )
        state, _ = apply_observations(
            state,
            (_obs("e1", "50000", 1000, 1), eth),
            now_times_us=(3000, 3000),
            max_staleness_us=5000,
        )
        self.assertEqual(
            [(m.symbol, m.price) for m in state.marks],
            [("BTCUSDT", "50000"), ("ETHUSDT", "3000")],
        )

    def test_mismatched_times_rejected(self):
        with self.assertRaises(ValueError):
            apply_observations(
                new_market_state(),
                (_obs("e1", "50000", 1000, 1), _obs("e2", "50010", 2000, 2)),
                now_times_us=(3000,),
                max_staleness_us=5000,
            )


if __name__ == "__main__":
    unittest.main()
