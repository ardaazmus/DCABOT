"""Faz 17 E.3 (Whale Wall Detection Faz-0): spot @depth REST snapshot +
WS diff-depth event normalization (public, keyless, bounded)."""
import json
import unittest

from dcabot.data_adapters.binance_public_depth import (
    BINANCE_SPOT_PUBLIC_DEPTH_URL,
    BinancePublicDepthError,
    DepthDiffEvent,
    DepthSnapshot,
    fetch_binance_public_depth_snapshot,
    normalize_depth_diff_event,
)


class FakeResponse:
    status = 200

    def __init__(self, payload, *, used_weight_1m=None):
        body = json.dumps(payload).encode("utf-8")
        self.headers = {"Content-Length": str(len(body))}
        if used_weight_1m is not None:
            self.headers["X-MBX-USED-WEIGHT-1M"] = str(used_weight_1m)
        self._body = body
        self.closed = False

    def read(self, _size: int = -1) -> bytes:
        return self._body

    def close(self) -> None:
        self.closed = True


class FakeOpener:
    def __init__(self, response: FakeResponse):
        self.response = response
        self.request = None

    def open(self, request, timeout: int):
        self.request = request
        self.timeout = timeout
        return self.response


class FetchDepthSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "lastUpdateId": 1_027_024,
            "bids": [["4.00000000", "431.00000000"], ["3.99000000", "9.00000000"]],
            "asks": [["4.00000200", "12.00000000"]],
        }

    def test_signed_free_request_hits_depth_endpoint_and_normalizes(self):
        opener = FakeOpener(FakeResponse(self.payload, used_weight_1m=42))
        snapshot = fetch_binance_public_depth_snapshot("BTCUSDT", limit=100, opener=opener)
        self.assertIsInstance(snapshot, DepthSnapshot)
        self.assertEqual(snapshot.last_update_id, 1_027_024)
        self.assertEqual(snapshot.bids, (("4.00000000", "431.00000000"), ("3.99000000", "9.00000000")))
        self.assertEqual(snapshot.asks, (("4.00000200", "12.00000000"),))
        self.assertEqual(snapshot.used_weight_1m, 42)
        self.assertTrue(opener.request.full_url.startswith(BINANCE_SPOT_PUBLIC_DEPTH_URL))

    def test_missing_weight_header_is_none(self):
        opener = FakeOpener(FakeResponse(self.payload))
        snapshot = fetch_binance_public_depth_snapshot("BTCUSDT", limit=100, opener=opener)
        self.assertIsNone(snapshot.used_weight_1m)

    def test_invalid_symbol_fails_closed(self):
        with self.assertRaises(BinancePublicDepthError):
            fetch_binance_public_depth_snapshot("btc usdt", limit=100, opener=FakeOpener(FakeResponse(self.payload)))

    def test_invalid_limit_fails_closed(self):
        with self.assertRaises(BinancePublicDepthError):
            fetch_binance_public_depth_snapshot("BTCUSDT", limit=0, opener=FakeOpener(FakeResponse(self.payload)))
        with self.assertRaises(BinancePublicDepthError):
            fetch_binance_public_depth_snapshot("BTCUSDT", limit=5001, opener=FakeOpener(FakeResponse(self.payload)))

    def test_malformed_level_fails_closed(self):
        payload = dict(self.payload, bids=[["4.0"]])
        opener = FakeOpener(FakeResponse(payload))
        with self.assertRaises(BinancePublicDepthError):
            fetch_binance_public_depth_snapshot("BTCUSDT", limit=100, opener=opener)

    def test_negative_last_update_id_fails_closed(self):
        payload = dict(self.payload, lastUpdateId=-1)
        opener = FakeOpener(FakeResponse(payload))
        with self.assertRaises(BinancePublicDepthError):
            fetch_binance_public_depth_snapshot("BTCUSDT", limit=100, opener=opener)


class NormalizeDepthDiffEventTests(unittest.TestCase):
    def setUp(self):
        self.frame = {
            "e": "depthUpdate",
            "E": 1_700_000_000_123,
            "s": "BTCUSDT",
            "U": 157,
            "u": 160,
            "b": [["0.0024", "10"]],
            "a": [["0.0026", "100"]],
        }

    def test_normalizes_a_well_formed_frame(self):
        event = normalize_depth_diff_event(json.dumps(self.frame))
        self.assertIsInstance(event, DepthDiffEvent)
        self.assertEqual(event.symbol, "BTCUSDT")
        self.assertEqual(event.first_update_id, 157)
        self.assertEqual(event.final_update_id, 160)
        self.assertEqual(event.bids, (("0.0024", "10"),))
        self.assertEqual(event.asks, (("0.0026", "100"),))

    def test_wrong_event_type_fails_closed(self):
        frame = dict(self.frame, e="trade")
        with self.assertRaises(BinancePublicDepthError):
            normalize_depth_diff_event(json.dumps(frame))

    def test_u_less_than_capital_u_fails_closed(self):
        frame = dict(self.frame, U=161, u=160)
        with self.assertRaises(BinancePublicDepthError):
            normalize_depth_diff_event(json.dumps(frame))

    def test_no_pu_field_required_spot_has_none(self):
        # Binding correction (verified 2026-09-22 against developers.binance.com):
        # spot diff-depth frames carry NO "pu" field (that's futures-only).
        # A frame without "pu" must normalize cleanly.
        self.assertNotIn("pu", self.frame)
        normalize_depth_diff_event(json.dumps(self.frame))  # does not raise

    def test_malformed_json_fails_closed(self):
        with self.assertRaises(BinancePublicDepthError):
            normalize_depth_diff_event("{not json")

    def test_oversized_frame_fails_closed(self):
        huge = dict(self.frame, b=[["0.01", "1"]] * 20000)
        with self.assertRaises(BinancePublicDepthError):
            normalize_depth_diff_event(json.dumps(huge))


if __name__ == "__main__":
    unittest.main()
