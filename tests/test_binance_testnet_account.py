import hashlib
import hmac
import json
from urllib.parse import parse_qsl, urlsplit
import unittest

from dcabot.application.credential_boundary import EphemeralCredentialProvider, CredentialMaterial
from dcabot.application.signed_request import ApiKeyType
from dcabot.data_adapters.binance_testnet_account import (
    BINANCE_SPOT_TESTNET_ACCOUNT_URL,
    BinanceTestnetAccountError,
    fetch_binance_testnet_account,
)


class FixedClock:
    def now_ms(self) -> int:
        return 1_700_000_000_000


class FakeResponse:
    status = 200

    def __init__(self, payload: dict[str, object]):
        self.headers = {"Content-Length": str(len(json.dumps(payload).encode("utf-8")))}
        self._body = json.dumps(payload).encode("utf-8")
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


class BinanceTestnetAccountTests(unittest.TestCase):
    def setUp(self):
        self.provider = EphemeralCredentialProvider()
        self.provider.put(
            CredentialMaterial(
                credential_id="testnet-readonly",
                api_key="dummy-api-key",
                key_type=ApiKeyType.HMAC,
                secret=b"dummy-secret",
            )
        )
        self.payload = {
            "accountType": "SPOT",
            "canTrade": True,
            "canWithdraw": False,
            "canDeposit": True,
            "updateTime": 1_700_000_000_001,
            "permissions": ["SPOT"],
            "balances": [
                {"asset": "USDT", "free": "100.00000000", "locked": "0.00000000"}
            ],
        }

    def test_signed_read_only_account_request_returns_capability_without_secret(self):
        response = FakeResponse(self.payload)
        opener = FakeOpener(response)

        result = fetch_binance_testnet_account(
            "testnet-readonly",
            provider=self.provider,
            clock=FixedClock(),
            opener=opener,
        )

        query = dict(parse_qsl(urlsplit(opener.request.full_url).query, keep_blank_values=True))
        signed_payload = "&".join(
            f"{name}={value}"
            for name, value in parse_qsl(
                urlsplit(opener.request.full_url).query, keep_blank_values=True
            )
            if name != "signature"
        )
        expected_signature = hmac.new(
            b"dummy-secret", signed_payload.encode("ascii"), hashlib.sha256
        ).hexdigest()

        self.assertEqual(result.credential_id, "testnet-readonly")
        self.assertEqual(result.account_type, "SPOT")
        self.assertTrue(result.capability.signed_request_verified)
        self.assertTrue(result.capability.can_trade)
        self.assertTrue(result.capability.trade_scope_verified)
        self.assertEqual(result.balances_count, 1)
        self.assertEqual(opener.request.full_url.split("?", 1)[0], BINANCE_SPOT_TESTNET_ACCOUNT_URL)
        self.assertEqual(opener.request.get_header("X-mbx-apikey"), "dummy-api-key")
        self.assertEqual(query["timestamp"], "1700000000000")
        self.assertEqual(query["recvWindow"], "5000")
        self.assertEqual(query["signature"], expected_signature)
        self.assertNotIn("dummy-secret", opener.request.full_url)
        self.assertNotIn("dummy-secret", repr(result))
        self.assertNotIn("100.00000000", repr(result))
        self.assertTrue(response.closed)

    def test_account_response_hash_is_deterministic_for_received_bytes(self):
        response = FakeResponse(self.payload)
        result = fetch_binance_testnet_account(
            "testnet-readonly",
            provider=self.provider,
            clock=FixedClock(),
            opener=FakeOpener(response),
        )

        self.assertEqual(
            result.response_sha256,
            hashlib.sha256(response._body).hexdigest(),
        )

    def test_malformed_account_response_fails_closed(self):
        response = FakeResponse({"accountType": "SPOT", "canTrade": True})

        with self.assertRaisesRegex(BinanceTestnetAccountError, "TESTNET_ACCOUNT_RESPONSE_INVALID"):
            fetch_binance_testnet_account(
                "testnet-readonly",
                provider=self.provider,
                clock=FixedClock(),
                opener=FakeOpener(response),
            )


if __name__ == "__main__":
    unittest.main()
