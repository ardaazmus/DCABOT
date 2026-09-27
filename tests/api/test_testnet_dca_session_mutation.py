"""Faz 17 AA.-1 (testnet-session dilimi, adım 3): /place ve /sync.

Arda'nın 2026-09-23 yazılı onayı sonrası (AGENTS.md testnet-mutation gate).
Gerçek ağa hiç çıkılmıyor -- `place_next_action`/`sync_order_fills`/
`fetch_binance_testnet_account` modül seviyesinde sahteleniyor (aynı
`test_binance_public_market.py`/`test_binance_testnet_account.py` deseni).
"""
import asyncio
import json
from pathlib import Path
import tempfile
import unittest

import dcabot.server.api as api
from dcabot.application.credential_boundary import AccountCapability, CapabilitySource
from dcabot.application.testnet_dca_session import OrderBinding
from dcabot.application.testnet_order_execution import GatedOrderResult
from dcabot.data_adapters.binance_testnet_account import BinanceTestnetAccountSnapshot
from dcabot.data_adapters.binance_testnet_order_execution import PlacedTestnetOrder


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
    asyncio.run(api.app(scope, receive, send))
    status = next(m["status"] for m in sent if m["type"] == "http.response.start")
    payload = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    return status, json.loads(payload.decode())


def _raw_config(**overrides) -> dict:
    raw = json.loads((Path(__file__).resolve().parents[2] / "config/paper.json").read_text(encoding="utf-8"))
    raw.update(overrides)
    return raw


def _account_snapshot() -> BinanceTestnetAccountSnapshot:
    return BinanceTestnetAccountSnapshot(
        credential_id="testnet-readonly",
        account_type="SPOT",
        can_trade=True,
        can_withdraw=False,
        can_deposit=True,
        permissions=("SPOT",),
        update_time_ms=1_700_000_000_000,
        balances_count=1,
        balances=(),
        capability=AccountCapability.from_evidence(
            source=CapabilitySource.SIGNED_ACCOUNT_CONTEXT,
            signed_request_verified=True,
            can_trade=True,
            trade_scope_verified=True,
        ),
        response_sha256="a" * 64,
        observed_at_us=1_700_000_000_000_000,
    )


class TestnetDcaSessionMutationApiTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        session_path = Path(self._tmp.name) / "dca-sessions.sqlite3"
        attempts_path = Path(self._tmp.name) / "dca-attempts.sqlite3"
        self._original_session_store = api.TESTNET_DCA_SESSION_STORE
        self._original_attempt_store = api.TESTNET_DCA_ATTEMPT_STORE
        self._original_fetch_account = api.fetch_binance_testnet_account
        self._original_place = api.place_next_action
        self._original_sync = api.sync_order_fills
        self._original_kill_switch = api.trading_kill_switch_enabled
        self._original_env = api.os.environ.get("DCABOT_TESTNET_CREDENTIAL_ID")
        api.TESTNET_DCA_SESSION_STORE = api.TestnetDcaSessionStore(session_path)
        api.TESTNET_DCA_ATTEMPT_STORE = api.AttemptStore(attempts_path)
        api.os.environ["DCABOT_TESTNET_CREDENTIAL_ID"] = "testnet-readonly"
        api.fetch_binance_testnet_account = lambda *a, **kw: _account_snapshot()
        api.trading_kill_switch_enabled = lambda: True

        payload = json.dumps(
            {"session_id": "s1", "symbol": "BTCUSDT", "config": _raw_config()}
        ).encode()
        _asgi("/api/testnet/dca-sessions", method="POST", body=payload)
        _asgi("/api/testnet/dca-sessions/s1/mark", method="POST", body=json.dumps({"price": "100"}).encode())

    def tearDown(self):
        api.TESTNET_DCA_SESSION_STORE.close()
        api.TESTNET_DCA_ATTEMPT_STORE.close()
        api.TESTNET_DCA_SESSION_STORE = self._original_session_store
        api.TESTNET_DCA_ATTEMPT_STORE = self._original_attempt_store
        api.fetch_binance_testnet_account = self._original_fetch_account
        api.place_next_action = self._original_place
        api.sync_order_fills = self._original_sync
        api.trading_kill_switch_enabled = self._original_kill_switch
        if self._original_env is None:
            api.os.environ.pop("DCABOT_TESTNET_CREDENTIAL_ID", None)
        else:
            api.os.environ["DCABOT_TESTNET_CREDENTIAL_ID"] = self._original_env
        self._tmp.cleanup()

    def test_place_without_confirmed_true_is_rejected(self):
        status, body = _asgi(
            "/api/testnet/dca-sessions/s1/place", method="POST",
            body=json.dumps({"role": "BASE", "qty": "1", "confirmed": False}).encode(),
        )
        self.assertEqual(status, 422)
        self.assertIn("confirmed", body["error"]["fields"])

    def test_place_with_mismatched_role_is_rejected(self):
        status, body = _asgi(
            "/api/testnet/dca-sessions/s1/place", method="POST",
            body=json.dumps({"role": "SAFETY:1", "qty": "1", "confirmed": True}).encode(),
        )
        self.assertEqual(status, 409)

    def test_place_without_credential_configured_is_409(self):
        api.os.environ.pop("DCABOT_TESTNET_CREDENTIAL_ID", None)
        status, body = _asgi(
            "/api/testnet/dca-sessions/s1/place", method="POST",
            body=json.dumps({"role": "BASE", "qty": "1", "confirmed": True}).encode(),
        )
        self.assertEqual(status, 409)
        self.assertEqual(body["code"], "TESTNET_CREDENTIAL_NOT_CONFIGURED")

    def test_place_when_kill_switch_off_is_409(self):
        api.trading_kill_switch_enabled = lambda: False
        status, body = _asgi(
            "/api/testnet/dca-sessions/s1/place", method="POST",
            body=json.dumps({"role": "BASE", "qty": "1", "confirmed": True}).encode(),
        )
        self.assertEqual(status, 409)
        self.assertEqual(body["code"], "GATE_KILL_SWITCH_OFF")

    def test_successful_place_updates_the_session(self):
        async def fake_place(session, *, role, qty, **kwargs):
            from dataclasses import replace
            from dcabot.domain.engine import apply as engine_apply

            next_state = engine_apply(
                session.state,
                {"type": "INTENT", "order_id": kwargs["attempt_id"], "role": role,
                 "qty": "1", "limit_price": "100"},
                session.config,
            )
            next_session = replace(
                session,
                state=next_state,
                bindings=(
                    *session.bindings,
                    OrderBinding(
                        local_order_id=kwargs["attempt_id"], role=role,
                        attempt_id=kwargs["attempt_id"], venue_order_id=555,
                    ),
                ),
            )
            result = GatedOrderResult(
                attempt=None,  # not inspected by the endpoint
                placed=PlacedTestnetOrder(
                    symbol=session.symbol, order_id=555, client_order_id=kwargs["attempt_id"],
                    status="NEW", transact_time_ms=1_700_000_000_001,
                ),
            )
            return next_session, result

        api.place_next_action = fake_place
        status, body = _asgi(
            "/api/testnet/dca-sessions/s1/place", method="POST",
            body=json.dumps({"role": "BASE", "qty": "1", "confirmed": True}).encode(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["venue_order_id"], 555)
        self.assertEqual(body["data"]["venue_status"], "NEW")

        # Persisted: a fresh load shows the same unsettled order.
        status, body = _asgi("/api/testnet/dca-sessions/s1")
        self.assertEqual(status, 200)
        self.assertEqual(len(body["data"]["unsettled_orders"]), 1)


class TestnetDcaSessionSyncApiTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        session_path = Path(self._tmp.name) / "dca-sessions.sqlite3"
        self._original_session_store = api.TESTNET_DCA_SESSION_STORE
        self._original_sync = api.sync_order_fills
        self._original_env = api.os.environ.get("DCABOT_TESTNET_CREDENTIAL_ID")
        api.TESTNET_DCA_SESSION_STORE = api.TestnetDcaSessionStore(session_path)
        api.os.environ["DCABOT_TESTNET_CREDENTIAL_ID"] = "testnet-readonly"
        payload = json.dumps(
            {"session_id": "s1", "symbol": "BTCUSDT", "config": _raw_config()}
        ).encode()
        _asgi("/api/testnet/dca-sessions", method="POST", body=payload)

    def tearDown(self):
        api.TESTNET_DCA_SESSION_STORE.close()
        api.TESTNET_DCA_SESSION_STORE = self._original_session_store
        api.sync_order_fills = self._original_sync
        if self._original_env is None:
            api.os.environ.pop("DCABOT_TESTNET_CREDENTIAL_ID", None)
        else:
            api.os.environ["DCABOT_TESTNET_CREDENTIAL_ID"] = self._original_env
        self._tmp.cleanup()

    def test_sync_without_credential_is_409(self):
        api.os.environ.pop("DCABOT_TESTNET_CREDENTIAL_ID", None)
        status, body = _asgi(
            "/api/testnet/dca-sessions/s1/sync", method="POST",
            body=json.dumps({"role": "BASE"}).encode(),
        )
        self.assertEqual(status, 409)

    def test_sync_missing_role_is_422(self):
        status, body = _asgi(
            "/api/testnet/dca-sessions/s1/sync", method="POST",
            body=json.dumps({}).encode(),
        )
        self.assertEqual(status, 422)

    def test_sync_calls_through_and_persists(self):
        async def fake_sync(session, role, **kwargs):
            return session  # no-op session, just proves the wiring works

        api.sync_order_fills = fake_sync
        status, body = _asgi(
            "/api/testnet/dca-sessions/s1/sync", method="POST",
            body=json.dumps({"role": "BASE"}).encode(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["session_id"], "s1")


if __name__ == "__main__":
    unittest.main()
