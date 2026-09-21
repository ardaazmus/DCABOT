import json
import unittest
from starlette.responses import Response

import dcabot.server.api as api
from dcabot.application.credential_boundary import AccountCapability, CapabilitySource
from dcabot.data_adapters.binance_testnet_account import (
    BinanceTestnetAccountSnapshot,
    BinanceTestnetBalance,
    BinanceTestnetOpenOrder,
)


def _account_snapshot() -> BinanceTestnetAccountSnapshot:
    return BinanceTestnetAccountSnapshot(
        credential_id="testnet-readonly",
        account_type="SPOT",
        can_trade=True,
        can_withdraw=False,
        can_deposit=True,
        permissions=("SPOT",),
        update_time_ms=1_700_000_000_000,
        balances_count=2,
        balances=(BinanceTestnetBalance("USDT", "100.00000000", "0.00000000"),),
        capability=AccountCapability.from_evidence(
            source=CapabilitySource.SIGNED_ACCOUNT_CONTEXT,
            signed_request_verified=True,
            can_trade=True,
            trade_scope_verified=True,
        ),
        response_sha256="a" * 64,
        observed_at_us=1_700_000_000_000_000,
    )


def _open_order() -> BinanceTestnetOpenOrder:
    return BinanceTestnetOpenOrder(
        symbol="BTCUSDT",
        order_id=42,
        client_order_id="client-42",
        side="BUY",
        type="LIMIT",
        status="NEW",
        price="90.00000000",
        orig_qty="1.00000000",
        executed_qty="0.00000000",
        time_ms=1_700_000_000_000,
        update_time_ms=1_700_000_000_000,
    )


class BinanceTestnetAccountApiTests(unittest.TestCase):
    def setUp(self):
        self.original_env = api.os.environ.get("DCABOT_TESTNET_CREDENTIAL_ID")
        self.original_fetch_account = api.fetch_binance_testnet_account
        self.original_fetch_orders = api.fetch_binance_testnet_open_orders
        api.os.environ["DCABOT_TESTNET_CREDENTIAL_ID"] = "testnet-readonly"

    def tearDown(self):
        if self.original_env is None:
            api.os.environ.pop("DCABOT_TESTNET_CREDENTIAL_ID", None)
        else:
            api.os.environ["DCABOT_TESTNET_CREDENTIAL_ID"] = self.original_env
        api.fetch_binance_testnet_account = self.original_fetch_account
        api.fetch_binance_testnet_open_orders = self.original_fetch_orders

    def test_account_snapshot_is_read_only_and_has_no_credentials(self):
        api.fetch_binance_testnet_account = lambda credential_id, *, provider: _account_snapshot()

        result = api.get_binance_testnet_account(Response()).model_dump(mode="json")

        self.assertEqual(result["environment"], "BINANCE_SPOT_TESTNET")
        self.assertEqual(result["read_only"], True)
        self.assertEqual(result["credential_required"], True)
        self.assertEqual(result["balances_count"], 2)
        self.assertEqual(result["balances"], [{"asset": "USDT", "free": "100.00000000", "locked": "0.00000000"}])
        self.assertNotIn("credential_id", result)
        self.assertNotIn("api_key", json.dumps(result).lower())
        self.assertNotIn("secret", json.dumps(result).lower())

    def test_missing_credential_configuration_fails_closed(self):
        api.os.environ.pop("DCABOT_TESTNET_CREDENTIAL_ID", None)

        result = api.get_binance_testnet_account(Response())

        self.assertEqual(result.status_code, 409)
        self.assertEqual(json.loads(result.body)["code"], "TESTNET_CREDENTIAL_NOT_CONFIGURED")

    def test_account_upstream_failure_maps_to_sanitized_problem_details(self):
        def fail(_credential_id, *, provider):
            raise api.BinanceTestnetAccountError(
                "TESTNET_ACCOUNT_UNAVAILABLE", "secret=must-not-cross-the-api-boundary"
            )

        api.fetch_binance_testnet_account = fail

        result = api.get_binance_testnet_account(Response())

        self.assertEqual(result.status_code, 503)
        body = json.loads(result.body)
        self.assertEqual(body["code"], "TESTNET_ACCOUNT_UNAVAILABLE")
        self.assertNotIn("secret", json.dumps(body).lower())
        self.assertNotIn("must-not-cross", json.dumps(body))

    def test_open_orders_snapshot_is_read_only(self):
        api.fetch_binance_testnet_open_orders = (
            lambda credential_id, *, provider, symbol=None: (_open_order(),)
        )

        result = api.get_binance_testnet_open_orders(Response(), symbol="BTCUSDT").model_dump(mode="json")

        self.assertEqual(result["environment"], "BINANCE_SPOT_TESTNET")
        self.assertEqual(result["read_only"], True)
        self.assertEqual(result["credential_required"], True)
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["orders"][0]["symbol"], "BTCUSDT")
        self.assertEqual(result["orders"][0]["order_id"], 42)

    def test_open_orders_missing_credential_configuration_fails_closed(self):
        api.os.environ.pop("DCABOT_TESTNET_CREDENTIAL_ID", None)

        result = api.get_binance_testnet_open_orders(Response())

        self.assertEqual(result.status_code, 409)
        self.assertEqual(json.loads(result.body)["code"], "TESTNET_CREDENTIAL_NOT_CONFIGURED")

    def test_open_orders_invalid_symbol_is_a_client_error_not_an_outage(self):
        def fail(_credential_id, *, provider, symbol=None):
            raise api.BinanceTestnetAccountError(
                "TESTNET_OPEN_ORDERS_SYMBOL_INVALID", "Açık emir symbol değeri geçersiz."
            )

        api.fetch_binance_testnet_open_orders = fail

        result = api.get_binance_testnet_open_orders(Response(), symbol="not a symbol")

        self.assertEqual(result.status_code, 400)
        self.assertEqual(json.loads(result.body)["code"], "TESTNET_OPEN_ORDERS_SYMBOL_INVALID")


if __name__ == "__main__":
    unittest.main()
