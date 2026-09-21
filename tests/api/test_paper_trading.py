import unittest

from dcabot.data_adapters.binance_public import BinanceTimeUnit
from dcabot.data_adapters.public_feed import new_public_observation
from dcabot.server.api import (
    _paper_activate,
    _paper_fill,
    _paper_place,
    _paper_refresh,
    _new_paper_store,
    _validate_paper_activation_payload,
)

HASH = "ab" * 32


def _activation():
    return {
        "confirmed": True,
        "symbols": ["BTCUSDT"],
        "max_staleness_us": 5_000_000,
        "starting_cash": "10000",
    }


def _obs(symbol, event_id, price, event_time_us=1700000001000000):
    return new_public_observation(
        source_id="binance-spot-public-v3",
        transport="REST",
        symbol=symbol,
        product="SPOT",
        event_id=event_id,
        event_time_us=event_time_us,
        receive_time_us=event_time_us + 100,
        processing_time_us=event_time_us + 200,
        price=price,
        quantity="1",
        payload_hash=HASH,
        source_sequence=1,
    )


class PaperActivationTests(unittest.TestCase):
    def test_valid_activation_snapshot(self):
        validated, fields = _validate_paper_activation_payload(_activation())
        self.assertEqual(fields, {})
        snapshot = _paper_activate(_new_paper_store(), validated, 1700000000000000)
        self.assertEqual(snapshot["status"], "PAPER_ACTIVE")
        self.assertEqual(snapshot["cash"], "10000")
        self.assertEqual(snapshot["orders"], [])
        self.assertRegex(snapshot["session_id"], r"\A[0-9a-f]{64}\Z")

    def test_unconfirmed_is_field_error(self):
        body = _activation()
        body["confirmed"] = False
        validated, fields = _validate_paper_activation_payload(body)
        self.assertIsNone(validated)
        self.assertIn("confirmed", fields)


class PaperOrderFillTests(unittest.TestCase):
    def _active(self, store):
        validated, _ = _validate_paper_activation_payload(_activation())
        return _paper_activate(store, validated, 1700000000000000)

    def test_place_then_fill_at_cached_print_moves_cash(self):
        store = _new_paper_store()
        session_id = self._active(store)["session_id"]
        placed = _paper_place(
            store,
            session_id,
            {
                "symbol": "BTCUSDT", "side": "BUY", "order_type": "MARKET",
                "qty": "0.01", "limit_price": None, "client_order_id": "c1",
            },
            1700000000000000,
        )
        self.assertEqual(placed["outcome"], "NEW")
        refreshed = _paper_refresh(
            store, session_id,
            fetch=lambda symbol: (_obs(symbol, "e1", "50000"),),
            now_us=1700000002000000,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )
        self.assertEqual(
            [(p["event_id"], p["price"]) for p in refreshed["prints"]],
            [("e1", "50000")],
        )
        filled = _paper_fill(
            store, session_id,
            {"client_order_id": "c1", "event_id": "e1", "fill_qty": "0.01"},
            1700000003000000,
        )
        self.assertEqual(filled["outcome"], "FILLED")
        self.assertEqual(filled["snapshot"]["cash"], "9500")
        self.assertEqual(
            filled["snapshot"]["positions"], [{"symbol": "BTCUSDT", "qty": "0.01"}]
        )

    def test_duplicate_place_is_duplicate(self):
        store = _new_paper_store()
        session_id = self._active(store)["session_id"]
        order = {
            "symbol": "BTCUSDT", "side": "BUY", "order_type": "MARKET",
            "qty": "0.01", "limit_price": None, "client_order_id": "c1",
        }
        _paper_place(store, session_id, order, 1700000000000000)
        again = _paper_place(store, session_id, order, 1700000000000000)
        self.assertEqual(again["outcome"], "DUPLICATE")

    def test_fill_at_unknown_event_fails(self):
        store = _new_paper_store()
        session_id = self._active(store)["session_id"]
        _paper_place(
            store, session_id,
            {
                "symbol": "BTCUSDT", "side": "BUY", "order_type": "MARKET",
                "qty": "0.01", "limit_price": None, "client_order_id": "c1",
            },
            1700000000000000,
        )
        with self.assertRaises(ValueError) as ctx:
            _paper_fill(
                store, session_id,
                {"client_order_id": "c1", "event_id": "nope", "fill_qty": "0.01"},
                1700000003000000,
            )
        self.assertIn("PAPER_EVENT_UNKNOWN", str(ctx.exception))

    def test_omitted_fill_qty_fills_remaining(self):
        store = _new_paper_store()
        session_id = self._active(store)["session_id"]
        _paper_place(
            store, session_id,
            {
                "symbol": "BTCUSDT", "side": "BUY", "order_type": "MARKET",
                "qty": "0.01", "limit_price": None, "client_order_id": "c1",
            },
            1700000000000000,
        )
        _paper_refresh(
            store, session_id,
            fetch=lambda symbol: (_obs(symbol, "e1", "50000"),),
            now_us=1700000002000000,
            time_unit=BinanceTimeUnit.MILLISECONDS,
        )
        filled = _paper_fill(
            store, session_id,
            {"client_order_id": "c1", "event_id": "e1"},
            1700000003000000,
        )
        self.assertEqual(filled["outcome"], "FILLED")
        self.assertEqual(filled["snapshot"]["cash"], "9500")
        self.assertEqual(
            filled["snapshot"]["orders"][0]["status"], "SIMULATED_FILLED"
        )

    def test_unknown_session_fails(self):
        store = _new_paper_store()
        with self.assertRaises(ValueError) as ctx:
            _paper_place(
                store, "0" * 64,
                {
                    "symbol": "BTCUSDT", "side": "BUY", "order_type": "MARKET",
                    "qty": "0.01", "limit_price": None, "client_order_id": "c1",
                },
                1700000000000000,
            )
        self.assertIn("PAPER_SESSION_UNKNOWN", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
