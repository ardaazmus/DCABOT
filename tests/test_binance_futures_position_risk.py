"""Faz 17 D.1: futures position-risk/account-margin adapter (fake-seam,
gerçek ağ çağrısı yok -- futures testnet credential'ı repo'da yok)."""
import json
import unittest

from dcabot.application.credential_boundary import CredentialMaterial, EphemeralCredentialProvider
from dcabot.application.signed_request import ApiKeyType
from dcabot.data_adapters.binance_futures_testnet_position_risk import (
    BINANCE_FUTURES_TESTNET_ACCOUNT_URL,
    BINANCE_FUTURES_TESTNET_POSITION_RISK_URL,
    BinanceFuturesPositionRiskError,
    fetch_binance_futures_account_margin,
    fetch_binance_futures_position_risk,
)


class FixedClock:
    def now_ms(self) -> int:
        return 1_700_000_000_000


class FakeResponse:
    status = 200

    def __init__(self, payload):
        body = json.dumps(payload).encode("utf-8")
        self.headers = {"Content-Length": str(len(body))}
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


class PositionRiskTests(unittest.TestCase):
    def setUp(self):
        self.provider = EphemeralCredentialProvider()
        self.provider.put(
            CredentialMaterial(
                credential_id="futures-readonly",
                api_key="dummy-api-key",
                key_type=ApiKeyType.HMAC,
                secret=b"dummy-secret",
            )
        )
        self.row = {
            "symbol": "BTCUSDT",
            "positionAmt": "1.000",
            "entryPrice": "60000",
            "markPrice": "60500",
            "liquidationPrice": "54000",
            "leverage": "5",
            "unRealizedProfit": "500",
            "positionSide": "LONG",
            "updateTime": 1_700_000_000_001,
        }

    def test_signed_position_risk_request_hits_v3_endpoint_and_normalizes(self):
        response = FakeResponse([self.row])
        opener = FakeOpener(response)
        rows = fetch_binance_futures_position_risk(
            "futures-readonly",
            "BTCUSDT",
            provider=self.provider,
            clock=FixedClock(),
            opener=opener,
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].liquidation_price, "54000")
        self.assertTrue(opener.request.full_url.startswith(BINANCE_FUTURES_TESTNET_POSITION_RISK_URL))
        self.assertIn("X-mbx-apikey", opener.request.headers)
        self.assertNotIn(b"dummy-secret", opener.request.full_url.encode())

    def test_symbol_mismatch_fails_closed(self):
        row = dict(self.row, symbol="ETHUSDT")
        opener = FakeOpener(FakeResponse([row]))
        with self.assertRaises(BinanceFuturesPositionRiskError) as ctx:
            fetch_binance_futures_position_risk(
                "futures-readonly", "BTCUSDT", provider=self.provider, clock=FixedClock(), opener=opener
            )
        self.assertEqual(ctx.exception.code, "FUTURES_POSITION_RISK_RESPONSE_INVALID")

    def test_negative_liquidation_price_fails_closed(self):
        row = dict(self.row, liquidationPrice="-1")
        opener = FakeOpener(FakeResponse([row]))
        with self.assertRaises(BinanceFuturesPositionRiskError):
            fetch_binance_futures_position_risk(
                "futures-readonly", "BTCUSDT", provider=self.provider, clock=FixedClock(), opener=opener
            )

    def test_zero_liquidation_price_is_accepted_as_meaningless_marker(self):
        row = dict(self.row, liquidationPrice="0")
        opener = FakeOpener(FakeResponse([row]))
        rows = fetch_binance_futures_position_risk(
            "futures-readonly", "BTCUSDT", provider=self.provider, clock=FixedClock(), opener=opener
        )
        self.assertEqual(rows[0].liquidation_price, "0")

    def test_negative_position_amt_is_accepted_for_short_exposure(self):
        row = dict(self.row, positionAmt="-1.000", positionSide="SHORT")
        opener = FakeOpener(FakeResponse([row]))
        rows = fetch_binance_futures_position_risk(
            "futures-readonly", "BTCUSDT", provider=self.provider, clock=FixedClock(), opener=opener
        )
        self.assertEqual(rows[0].position_amt, "-1.000")

    def test_oversized_response_fails_closed(self):
        opener = FakeOpener(FakeResponse([self.row] * 600))
        with self.assertRaises(BinanceFuturesPositionRiskError) as ctx:
            fetch_binance_futures_position_risk(
                "futures-readonly", "BTCUSDT", provider=self.provider, clock=FixedClock(), opener=opener
            )
        self.assertEqual(ctx.exception.code, "FUTURES_POSITION_RISK_RESPONSE_INVALID")


class AccountMarginTests(unittest.TestCase):
    def setUp(self):
        self.provider = EphemeralCredentialProvider()
        self.provider.put(
            CredentialMaterial(
                credential_id="futures-readonly",
                api_key="dummy-api-key",
                key_type=ApiKeyType.HMAC,
                secret=b"dummy-secret",
            )
        )
        self.payload = {
            "totalMaintMargin": "120",
            "totalMarginBalance": "10000",
            "updateTime": 1_700_000_000_001,
        }

    def test_signed_account_margin_request_hits_v3_endpoint(self):
        opener = FakeOpener(FakeResponse(self.payload))
        margin = fetch_binance_futures_account_margin(
            "futures-readonly", provider=self.provider, clock=FixedClock(), opener=opener
        )
        self.assertEqual(margin.total_maint_margin, "120")
        self.assertEqual(margin.total_margin_balance, "10000")
        self.assertTrue(opener.request.full_url.startswith(BINANCE_FUTURES_TESTNET_ACCOUNT_URL))

    def test_missing_field_fails_closed(self):
        payload = dict(self.payload)
        del payload["totalMarginBalance"]
        opener = FakeOpener(FakeResponse(payload))
        with self.assertRaises(BinanceFuturesPositionRiskError) as ctx:
            fetch_binance_futures_account_margin(
                "futures-readonly", provider=self.provider, clock=FixedClock(), opener=opener
            )
        self.assertEqual(ctx.exception.code, "FUTURES_ACCOUNT_MARGIN_RESPONSE_INVALID")

    def test_non_decimal_margin_fails_closed(self):
        payload = dict(self.payload, totalMaintMargin="abc")
        opener = FakeOpener(FakeResponse(payload))
        with self.assertRaises(BinanceFuturesPositionRiskError):
            fetch_binance_futures_account_margin(
                "futures-readonly", provider=self.provider, clock=FixedClock(), opener=opener
            )


if __name__ == "__main__":
    unittest.main()
