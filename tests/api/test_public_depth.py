"""AA.14 (2026-09-23): GET /api/public/depth -- real order-book depth,
replacing qwen's fabricated order-book. `binance_public_depth.py` (E.3's
whale-detection transport) was never wired to HTTP before this."""
import json
import unittest

from starlette.responses import Response

import dcabot.server.api as api
from dcabot.data_adapters.binance_public_depth import DepthSnapshot


def _snapshot() -> DepthSnapshot:
    return DepthSnapshot(
        last_update_id=123456,
        bids=(("50000.00", "1.5"), ("49999.00", "2.0")),
        asks=(("50001.00", "0.5"), ("50002.00", "3.0")),
        used_weight_1m=5,
    )


class PublicDepthApiTests(unittest.TestCase):
    def setUp(self):
        self._original = api.fetch_binance_public_depth_snapshot

    def tearDown(self):
        api.fetch_binance_public_depth_snapshot = self._original

    def test_passes_the_exact_levels_through(self):
        calls: list[tuple] = []

        def spy(symbol, *, limit):
            calls.append((symbol, limit))
            return _snapshot()

        api.fetch_binance_public_depth_snapshot = spy
        response = Response()

        result = api.get_binance_public_depth("BTCUSDT", response, limit=20)

        self.assertEqual(result["data"]["symbol"], "BTCUSDT")
        self.assertEqual(result["data"]["last_update_id"], 123456)
        self.assertEqual(result["data"]["bids"], [["50000.00", "1.5"], ["49999.00", "2.0"]])
        self.assertEqual(result["data"]["asks"], [["50001.00", "0.5"], ["50002.00", "3.0"]])
        self.assertEqual(result["data"]["read_only"], True)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(calls, [("BTCUSDT", 20)])

    def test_rejects_malformed_symbol_without_touching_transport(self):
        calls: list[tuple] = []

        def spy(*args, **kwargs):
            calls.append((args, kwargs))
            return _snapshot()

        api.fetch_binance_public_depth_snapshot = spy
        for bad in ("btcusdt", "BTC USDT", "BTCUSDT!", ""):
            with self.subTest(symbol=bad):
                response = Response()
                result = api.get_binance_public_depth(bad, response, limit=20)
                self.assertEqual(result.status_code, 422)
                body = json.loads(result.body)
                self.assertIn("symbol", body["error"]["fields"])
        self.assertEqual(calls, [])

    def test_rejects_a_limit_binance_does_not_support(self):
        response = Response()
        result = api.get_binance_public_depth("BTCUSDT", response, limit=17)
        self.assertEqual(result.status_code, 422)
        body = json.loads(result.body)
        self.assertIn("limit", body["error"]["fields"])

    def test_transport_failure_is_a_bounded_502(self):
        failure = api.BinancePublicDepthError("PUBLIC_DEPTH_UNAVAILABLE", "Depth yanıtı alınamadı.")

        def fail(*args, **kwargs):
            raise failure

        api.fetch_binance_public_depth_snapshot = fail
        response = Response()

        result = api.get_binance_public_depth("BTCUSDT", response, limit=20)

        self.assertEqual(result.status_code, 502)
        body = json.loads(result.body)
        self.assertIn("PUBLIC_DEPTH_UNAVAILABLE", body["error"]["fields"]["depth"])


if __name__ == "__main__":
    unittest.main()
