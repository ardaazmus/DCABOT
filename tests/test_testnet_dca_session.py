import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from dcabot.application.credential_boundary import CredentialMaterial, EphemeralCredentialProvider
from dcabot.application.instrument_filters import InstrumentFilterProfile
from dcabot.application.testnet_dca_session import (
    TestnetDcaSessionError,
    apply_mark,
    build_live_config,
    new_session,
    place_next_action,
    propose_next_action,
    sync_order_fills,
)
from dcabot.application.testnet_order_execution import TestnetOrderExecutionError
from dcabot.application.signed_request import ApiKeyType
from dcabot.data_adapters.binance_testnet_order_execution import TRADING_ENABLED_ENV_VAR
from dcabot.domain.numbers import number
from dcabot.persistence.attempt_store import AttemptStore
import os


class FixedClock:
    def now_ms(self) -> int:
        return 1_700_000_000_000


class FakeSocket:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.closed = False

    async def send(self, message: str) -> None:
        pass

    async def recv(self):
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response

    async def close(self) -> None:
        self.closed = True


class FakeHttpResponse:
    status = 200

    def __init__(self, payload) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.headers = {"Content-Length": str(len(body))}
        self._body = body
        self.closed = False

    def read(self, _size: int = -1) -> bytes:
        return self._body

    def close(self) -> None:
        self.closed = True


class FakeHttpOpener:
    def __init__(self, response: FakeHttpResponse) -> None:
        self.response = response

    def open(self, request, timeout: int):
        return self.response


def _provider() -> EphemeralCredentialProvider:
    result = EphemeralCredentialProvider()
    result.put(
        CredentialMaterial(
            credential_id="testnet-readonly",
            api_key="dummy-api-key",
            key_type=ApiKeyType.HMAC,
            secret=b"dummy-secret",
        )
    )
    return result


def _profile() -> InstrumentFilterProfile:
    return InstrumentFilterProfile(
        profile_id="btcusdt-dca",
        qty_step="0.001",
        price_tick="0.01",
        min_qty="0.001",
        min_notional="0.01",
    )


def _config():
    return build_live_config(
        _profile(),
        symbol="BTCUSDT",
        base_asset="BTC",
        base_qty="0.001",
        safety_qty="0.001",
        safety_count=1,
        deviation="0.05",
        take_profit="0.02",
        target_quote="0",
        initial_equity="1000",
        max_entry_notional="1000",
        minimum_equity="10",
    )


def _place_response(*, order_id, client_order_id) -> str:
    return json.dumps(
        {
            "id": "request-1",
            "status": 200,
            "result": {
                "symbol": "BTCUSDT",
                "orderId": order_id,
                "clientOrderId": client_order_id,
                "status": "NEW",
                "transactTime": 1_700_000_000_001,
            },
        }
    )


def _status_found_response(*, order_id) -> str:
    return json.dumps(
        {"id": "request-1", "status": 200, "result": {"symbol": "BTCUSDT", "orderId": order_id}}
    )


class TestnetDcaSessionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        os.environ[TRADING_ENABLED_ENV_VAR] = "true"

    def tearDown(self):
        os.environ.pop(TRADING_ENABLED_ENV_VAR, None)

    def test_build_live_config_from_real_filters_is_valid(self):
        config = _config()
        self.assertEqual(config.symbol, "BTCUSDT")
        self.assertEqual(config.tick, number("0.01"))

    async def test_fresh_session_proposes_base_first(self):
        session = new_session(_config(), "BTCUSDT")
        session = apply_mark(session, "100")

        self.assertEqual(propose_next_action(session), ("BASE", number("0.001")))

    async def test_full_arc_base_then_safety_then_exit(self):
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                session = new_session(_config(), "BTCUSDT")
                session = apply_mark(session, "100")

                # --- BASE ---
                self.assertEqual(propose_next_action(session), ("BASE", number("0.001")))
                place_socket = FakeSocket(_place_response(order_id=1, client_order_id="dca-base-1"))
                session, placed = await place_next_action(
                    session,
                    role="BASE",
                    qty=number("0.001"),
                    store=store,
                    attempt_id="dca-base-1",
                    credential_id="testnet-readonly",
                    provider=_provider(),
                    clock=FixedClock(),
                    now_us=1_700_000_000_000_000,
                    max_entry_notional=number("1000"),
                    capability_snapshot_hash="a" * 64,
                    websocket_factory=lambda _url, **_kwargs: place_socket,
                    request_id_factory=lambda: "request-1",
                )
                self.assertEqual(placed.placed.order_id, 1)

                base_trades_opener = FakeHttpOpener(
                    FakeHttpResponse(
                        [
                            {
                                "symbol": "BTCUSDT",
                                "id": 900,
                                "orderId": 1,
                                "price": "100",
                                "qty": "0.001",
                                "commission": "0.0000001",
                                "commissionAsset": "BTC",
                                "time": 1_700_000_000_002,
                                "isBuyer": True,
                            }
                        ]
                    )
                )
                session = await sync_order_fills(
                    session,
                    "BASE",
                    credential_id="testnet-readonly",
                    provider=_provider(),
                    clock=FixedClock(),
                    websocket_factory=lambda _url, **_kwargs: FakeSocket(_status_found_response(order_id=1)),
                    request_id_factory=lambda: "request-1",
                    my_trades_opener=base_trades_opener,
                )

                self.assertEqual(session.state.anchor, number("100"))
                self.assertTrue(session.state.orders["dca-base-1"].complete)
                # Mark hasn't moved: no safety trigger, no TP yet.
                self.assertIsNone(propose_next_action(session))

                # --- price drops: SAFETY:1 triggers at anchor*(1-0.05)=95 ---
                session = apply_mark(session, "94")
                self.assertEqual(propose_next_action(session), ("SAFETY:1", number("0.001")))

                place_socket_2 = FakeSocket(_place_response(order_id=2, client_order_id="dca-safety-1"))
                session, placed_2 = await place_next_action(
                    session,
                    role="SAFETY:1",
                    qty=number("0.001"),
                    store=store,
                    attempt_id="dca-safety-1",
                    credential_id="testnet-readonly",
                    provider=_provider(),
                    clock=FixedClock(),
                    now_us=1_700_000_000_000_001,
                    max_entry_notional=number("1000"),
                    capability_snapshot_hash="a" * 64,
                    websocket_factory=lambda _url, **_kwargs: place_socket_2,
                    request_id_factory=lambda: "request-1",
                )
                self.assertEqual(placed_2.placed.order_id, 2)

                safety_trades_opener = FakeHttpOpener(
                    FakeHttpResponse(
                        [
                            {
                                "symbol": "BTCUSDT",
                                "id": 901,
                                "orderId": 2,
                                "price": "95",
                                "qty": "0.001",
                                "commission": "0.0000001",
                                "commissionAsset": "BTC",
                                "time": 1_700_000_000_003,
                                "isBuyer": True,
                            }
                        ]
                    )
                )
                session = await sync_order_fills(
                    session,
                    "SAFETY:1",
                    credential_id="testnet-readonly",
                    provider=_provider(),
                    clock=FixedClock(),
                    websocket_factory=lambda _url, **_kwargs: FakeSocket(_status_found_response(order_id=2)),
                    request_id_factory=lambda: "request-1",
                    my_trades_opener=safety_trades_opener,
                )

                # average = (100*0.001 + 95*0.001) / 0.002 = 97.5; target = 97.5*1.02 = 99.45
                self.assertEqual(session.state.position.average, number("97.5"))

                # --- price rises to target: EXIT ---
                session = apply_mark(session, "100")
                action = propose_next_action(session)
                self.assertIsNotNone(action)
                self.assertEqual(action[0], "EXIT")

    async def test_sync_is_idempotent_across_repeated_calls(self):
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                session = new_session(_config(), "BTCUSDT")
                session = apply_mark(session, "100")
                place_socket = FakeSocket(_place_response(order_id=1, client_order_id="dca-base-1"))
                session, _ = await place_next_action(
                    session,
                    role="BASE",
                    qty=number("0.001"),
                    store=store,
                    attempt_id="dca-base-1",
                    credential_id="testnet-readonly",
                    provider=_provider(),
                    clock=FixedClock(),
                    now_us=1_700_000_000_000_000,
                    max_entry_notional=number("1000"),
                    capability_snapshot_hash="a" * 64,
                    websocket_factory=lambda _url, **_kwargs: place_socket,
                    request_id_factory=lambda: "request-1",
                )

                trade_list = [
                    {
                        "symbol": "BTCUSDT",
                        "id": 900,
                        "orderId": 1,
                        "price": "100",
                        "qty": "0.001",
                        "commission": "0.0000001",
                        "commissionAsset": "BTC",
                        "time": 1_700_000_000_002,
                        "isBuyer": True,
                    }
                ]
                session = await sync_order_fills(
                    session,
                    "BASE",
                    credential_id="testnet-readonly",
                    provider=_provider(),
                    clock=FixedClock(),
                    websocket_factory=lambda _url, **_kwargs: FakeSocket(_status_found_response(order_id=1)),
                    request_id_factory=lambda: "request-1",
                    my_trades_opener=FakeHttpOpener(FakeHttpResponse(trade_list)),
                )
                filled_after_first = session.state.orders["dca-base-1"].filled

                session = await sync_order_fills(
                    session,
                    "BASE",
                    credential_id="testnet-readonly",
                    provider=_provider(),
                    clock=FixedClock(),
                    websocket_factory=lambda _url, **_kwargs: FakeSocket(_status_found_response(order_id=1)),
                    request_id_factory=lambda: "request-1",
                    my_trades_opener=FakeHttpOpener(FakeHttpResponse(trade_list)),
                )

                self.assertEqual(session.state.orders["dca-base-1"].filled, filled_after_first)

    async def test_kill_switch_off_leaves_session_untouched_on_failed_send(self):
        os.environ.pop(TRADING_ENABLED_ENV_VAR, None)
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                session = new_session(_config(), "BTCUSDT")
                session = apply_mark(session, "100")

                with self.assertRaises(TestnetOrderExecutionError):
                    await place_next_action(
                        session,
                        role="BASE",
                        qty=number("0.001"),
                        store=store,
                        attempt_id="dca-base-1",
                        credential_id="testnet-readonly",
                        provider=_provider(),
                        clock=FixedClock(),
                        now_us=1_700_000_000_000_000,
                        max_entry_notional=number("1000"),
                        capability_snapshot_hash="a" * 64,
                    )

                self.assertEqual(session.bindings, ())
                self.assertEqual(store.count(), 0)


if __name__ == "__main__":
    unittest.main()
