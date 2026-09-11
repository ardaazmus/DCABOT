import hashlib
import json
from io import BytesIO
import unittest

from dcabot.data_adapters.binance_testnet_public import (
    BINANCE_SPOT_TESTNET_EXCHANGE_INFO_URL,
    BinanceTestnetPublicError,
    fetch_binance_testnet_exchange_info,
)


def _exchange_info_payload() -> dict[str, object]:
    return {
        "timezone": "UTC",
        "serverTime": 1_700_000_000_000,
        "rateLimits": [
            {"rateLimitType": "REQUEST_WEIGHT", "interval": "MINUTE", "intervalNum": 1, "limit": 6000}
        ],
        "exchangeFilters": [],
        "symbols": [
            {
                "symbol": "BTCUSDT",
                "status": "TRADING",
                "baseAsset": "BTC",
                "quoteAsset": "USDT",
                "permissions": ["SPOT"],
                "permissionSets": [["SPOT"]],
                "orderTypes": ["LIMIT", "MARKET"],
                "filters": [
                    {"filterType": "PRICE_FILTER", "minPrice": "0.01000000", "tickSize": "0.01000000"}
                ],
            }
        ],
    }


class _FakeResponse:
    status = 200

    def __init__(self, payload: bytes):
        self.headers = {"Content-Length": str(len(payload)), "Content-Encoding": "identity"}
        self._payload = BytesIO(payload)

    def read(self, size: int = -1) -> bytes:
        return self._payload.read(size)

    def close(self) -> None:
        pass


class _FakeOpener:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.request = None
        self.timeout = None

    def open(self, request, timeout: int):
        self.request = request
        self.timeout = timeout
        return _FakeResponse(self.payload)


class BinanceTestnetPublicTests(unittest.TestCase):
    def test_fetches_only_public_exchange_info_and_normalizes_symbol(self):
        raw = _exchange_info_payload()
        payload = json.dumps(raw, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        opener = _FakeOpener(payload)

        snapshot = fetch_binance_testnet_exchange_info("BTCUSDT", opener=opener, timeout_seconds=7)

        self.assertEqual(snapshot.environment, "BINANCE_SPOT_TESTNET")
        self.assertEqual(snapshot.symbol, "BTCUSDT")
        self.assertEqual(snapshot.status, "TRADING")
        self.assertEqual(snapshot.permissions, ("SPOT",))
        self.assertEqual(snapshot.permission_sets, (("SPOT",),))
        self.assertEqual(snapshot.order_types, ("LIMIT", "MARKET"))
        self.assertEqual(snapshot.filters[0]["minPrice"], "0.01000000")
        self.assertEqual(snapshot.rate_limits[0]["limit"], "6000")
        self.assertEqual(snapshot.response_sha256, hashlib.sha256(payload).hexdigest())
        self.assertIsNotNone(opener.request)
        self.assertEqual(opener.request.full_url, BINANCE_SPOT_TESTNET_EXCHANGE_INFO_URL + "?symbol=BTCUSDT")
        self.assertEqual(opener.request.get_method(), "GET")
        self.assertEqual(opener.timeout, 7)
        self.assertNotIn("api-key", {key.lower() for key in opener.request.headers})
        self.assertNotIn("authorization", {key.lower() for key in opener.request.headers})

    def test_unknown_symbol_is_fail_closed(self):
        payload = _exchange_info_payload()
        payload["symbols"] = []
        encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")

        with self.assertRaisesRegex(BinanceTestnetPublicError, "TESTNET_SYMBOL_NOT_FOUND"):
            fetch_binance_testnet_exchange_info("BTCUSDT", opener=_FakeOpener(encoded))

    def test_response_size_limit_is_enforced(self):
        oversized = b"{" + b"x" * (256 * 1024) + b"}"

        with self.assertRaisesRegex(BinanceTestnetPublicError, "TESTNET_RESPONSE_TOO_LARGE"):
            fetch_binance_testnet_exchange_info("BTCUSDT", opener=_FakeOpener(oversized))

    def test_malformed_json_is_not_accepted_as_a_snapshot(self):
        with self.assertRaisesRegex(BinanceTestnetPublicError, "TESTNET_RESPONSE_INVALID"):
            fetch_binance_testnet_exchange_info("BTCUSDT", opener=_FakeOpener(b"not-json"))

    def test_unknown_venue_status_is_preserved_for_fail_closed_ui_handling(self):
        raw = _exchange_info_payload()
        raw["symbols"][0]["status"] = "FUTURE_STATUS"
        encoded = json.dumps(raw, separators=(",", ":"), ensure_ascii=True).encode("utf-8")

        snapshot = fetch_binance_testnet_exchange_info("BTCUSDT", opener=_FakeOpener(encoded))

        self.assertEqual(snapshot.status, "FUTURE_STATUS")

    def test_symbol_rejects_whitespace_and_control_characters(self):
        with self.assertRaisesRegex(BinanceTestnetPublicError, "TESTNET_SYMBOL_INVALID"):
            fetch_binance_testnet_exchange_info("BTC USDT", opener=_FakeOpener(b"{}"))
        with self.assertRaisesRegex(BinanceTestnetPublicError, "TESTNET_SYMBOL_INVALID"):
            fetch_binance_testnet_exchange_info("BTC\nUSDT", opener=_FakeOpener(b"{}"))
        with self.assertRaisesRegex(BinanceTestnetPublicError, "TESTNET_SYMBOL_INVALID"):
            fetch_binance_testnet_exchange_info("", opener=_FakeOpener(b"{}"))

    def test_symbol_is_utf8_encoded_and_query_delimiters_cannot_escape(self):
        raw = _exchange_info_payload()
        raw["symbols"][0]["symbol"] = "这是测试币456"
        payload = json.dumps(raw, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        opener = _FakeOpener(payload)

        snapshot = fetch_binance_testnet_exchange_info("这是测试币456", opener=opener)

        self.assertEqual(snapshot.symbol, "这是测试币456")
        self.assertIn("symbol=%E8%BF%99%E6%98%AF%E6%B5%8B%E8%AF%95%E5%B8%81456", opener.request.full_url)
        self.assertNotIn("&", opener.request.full_url.split("?", 1)[1])

    def test_permissions_can_be_omitted_without_inventing_account_capability(self):
        raw = _exchange_info_payload()
        del raw["symbols"][0]["permissions"]
        payload = json.dumps(raw, separators=(",", ":"), ensure_ascii=True).encode("utf-8")

        snapshot = fetch_binance_testnet_exchange_info("BTCUSDT", opener=_FakeOpener(payload))

        self.assertEqual(snapshot.permissions, ())
