"""D.2: GET /api/risk/liquidation-status/{symbol} endpoint testleri."""

import asyncio
import json
import os
import unittest
from unittest.mock import patch

from dcabot.application.anti_liquidation_status import LiquidationStatus
from dcabot.application.liquidation_status_service import LiquidationStatusServiceError
from dcabot.server import api as api_module


def _asgi(path, method="GET", body=None):
    messages = [{"type": "http.request", "body": body or b"", "more_body": False}]
    sent = []

    async def receive():
        return messages.pop(0)

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http", "method": method, "path": path, "raw_path": path.encode(),
        "query_string": b"", "headers": [(b"content-type", b"application/json")],
        "scheme": "http", "server": ("testserver", 80), "client": ("testclient", 1),
    }
    asyncio.run(api_module.app(scope, receive, send))
    status = next(m["status"] for m in sent if m["type"] == "http.response.start")
    payload = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    return status, json.loads(payload.decode())


def _status(**overrides):
    base = {
        "state": "SIMULATED_ONLY",
        "liquidation_price": None,
        "margin_ratio": None,
        "is_fast_move": False,
        "reason": "VENUE_HAS_NO_POSITION_RISK_DATA",
        "observed_at_us": 1_700_000_000_000_000,
    }
    base.update(overrides)
    return LiquidationStatus(**base)


class FakeService:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls: list[tuple] = []

    def get_status(self, symbol, *, credential_id, provider, now_us):
        self.calls.append((symbol, credential_id, provider is not None, now_us))
        if self.error is not None:
            raise self.error
        return self.result


class LiquidationStatusEndpointTests(unittest.TestCase):
    def _no_credential_env(self):
        return patch.dict(os.environ, {}, clear=False)

    def test_too_long_symbol_is_422(self):
        status, body = _asgi("/api/risk/liquidation-status/" + "X" * 33)
        self.assertEqual(status, 422)
        self.assertEqual(body["error"]["fields"]["symbol"], "Symbol değeri geçersiz.")

    def test_unconfigured_credential_returns_simulated_only(self):
        with self._no_credential_env():
            os.environ.pop("DCABOT_FUTURES_TESTNET_CREDENTIAL_ID", None)
            status, body = _asgi("/api/risk/liquidation-status/BTCUSDT")
        self.assertEqual(status, 200)
        data = body["data"]
        self.assertEqual(data["environment"], "BINANCE_FUTURES_TESTNET")
        self.assertEqual(data["symbol"], "BTCUSDT")
        self.assertEqual(data["state"], "SIMULATED_ONLY")
        self.assertIsNone(data["liquidation_price"])
        self.assertTrue(data["read_only"])

    def test_service_result_passes_through(self):
        fake = FakeService(result=_status(state="DATA_OK", liquidation_price="54000", margin_ratio="0.01"))
        with patch.object(api_module, "LIQUIDATION_STATUS_SERVICE", fake):
            with self._no_credential_env():
                os.environ.pop("DCABOT_FUTURES_TESTNET_CREDENTIAL_ID", None)
                status, body = _asgi("/api/risk/liquidation-status/BTCUSDT")
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["state"], "DATA_OK")
        self.assertEqual(body["data"]["liquidation_price"], "54000")
        self.assertEqual(body["data"]["margin_ratio"], "0.01")
        self.assertEqual(fake.calls[0][0], "BTCUSDT")
        self.assertIsNone(fake.calls[0][1])

    def test_upstream_failure_is_502_with_code(self):
        fake = FakeService(error=LiquidationStatusServiceError("ALC_UPSTREAM_UNAVAILABLE", "Upstream okunamadı."))
        with patch.object(api_module, "LIQUIDATION_STATUS_SERVICE", fake):
            status, body = _asgi("/api/risk/liquidation-status/BTCUSDT")
        self.assertEqual(status, 502)
        self.assertEqual(body["code"], "ALC_UPSTREAM_UNAVAILABLE")

    def test_multi_position_is_500_with_code(self):
        fake = FakeService(error=LiquidationStatusServiceError("ALC_MULTI_POSITION_UNSUPPORTED", "Çift bacak."))
        with patch.object(api_module, "LIQUIDATION_STATUS_SERVICE", fake):
            status, body = _asgi("/api/risk/liquidation-status/BTCUSDT")
        self.assertEqual(status, 500)
        self.assertEqual(body["code"], "ALC_MULTI_POSITION_UNSUPPORTED")


if __name__ == "__main__":
    unittest.main()
