import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from dcabot.application.credential_boundary import CredentialMaterial, EphemeralCredentialProvider
from dcabot.application.instrument_filters import InstrumentFilterProfile
from dcabot.application.order_attempt import AttemptOperation, AttemptState, OrderAttempt, request_fingerprint
from dcabot.application.signed_request import ApiKeyType
from dcabot.application.testnet_order_execution import (
    TestnetOrderExecutionError,
    cancel_gated_testnet_order,
    place_gated_testnet_limit_order,
    recover_stuck_attempts,
)
from dcabot.data_adapters.binance_testnet_order_execution import TRADING_ENABLED_ENV_VAR
from dcabot.domain.numbers import number
from dcabot.persistence.attempt_store import AttemptStore


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
        profile_id="btcusdt-1",
        qty_step="0.001",
        price_tick="0.01",
        min_qty="0.001",
        min_notional="10",
    )


def _place_response(*, order_id=999, client_order_id="attempt-1") -> str:
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


def _status_found_response(*, order_id=999, client_order_id="attempt-1") -> str:
    return json.dumps(
        {
            "id": "recover-1",
            "status": 200,
            "result": {"symbol": "BTCUSDT", "orderId": order_id, "clientOrderId": client_order_id},
        }
    )


def _status_not_found_response() -> str:
    return json.dumps(
        {"id": "recover-1", "status": 400, "error": {"code": -2013, "msg": "Order does not exist."}}
    )


def _stuck_attempt(state, *, attempt_id="attempt-1") -> OrderAttempt:
    return OrderAttempt(
        attempt_id=attempt_id,
        run_id="run-1",
        venue="BINANCE_SPOT_TESTNET",
        operation=AttemptOperation.PLACE_ORDER,
        symbol="BTCUSDT",
        client_order_id=attempt_id,
        request_fingerprint_sha256=request_fingerprint({"symbol": "BTCUSDT"}),
        capability_snapshot_hash="a" * 64,
        filter_snapshot_hash="b" * 64,
        state=state,
        created_at_us=1_700_000_000_000_000,
        last_transition_at_us=1_700_000_000_000_000,
    )


class GatedPlacementTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        os.environ.pop(TRADING_ENABLED_ENV_VAR, None)

    def tearDown(self):
        os.environ.pop(TRADING_ENABLED_ENV_VAR, None)

    async def test_unconfirmed_request_never_reaches_the_store_or_network(self):
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                with self.assertRaisesRegex(TestnetOrderExecutionError, "GATE_CONFIRMATION_REQUIRED"):
                    await place_gated_testnet_limit_order(
                        store=store,
                        run_id="run-1",
                        attempt_id="attempt-1",
                        client_order_id="attempt-1",
                        symbol="BTCUSDT",
                        side="BUY",
                        quantity="0.01",
                        price="90",
                        filter_profile=_profile(),
                        max_entry_notional=number("1000"),
                        capability_snapshot_hash="a" * 64,
                        confirmed=False,
                        credential_id="testnet-readonly",
                        provider=_provider(),
                        clock=FixedClock(),
                        now_us=1_700_000_000_000_000,
                    )
                self.assertEqual(store.count(), 0)

    async def test_kill_switch_off_blocks_after_confirmation(self):
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                with self.assertRaisesRegex(TestnetOrderExecutionError, "GATE_KILL_SWITCH_OFF"):
                    await place_gated_testnet_limit_order(
                        store=store,
                        run_id="run-1",
                        attempt_id="attempt-1",
                        client_order_id="attempt-1",
                        symbol="BTCUSDT",
                        side="BUY",
                        quantity="0.01",
                        price="90",
                        filter_profile=_profile(),
                        max_entry_notional=number("1000"),
                        capability_snapshot_hash="a" * 64,
                        confirmed=True,
                        credential_id="testnet-readonly",
                        provider=_provider(),
                        clock=FixedClock(),
                        now_us=1_700_000_000_000_000,
                    )
                self.assertEqual(store.count(), 0)

    async def test_notional_over_cap_is_rejected_before_any_attempt_is_prepared(self):
        os.environ[TRADING_ENABLED_ENV_VAR] = "true"
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                with self.assertRaisesRegex(TestnetOrderExecutionError, "GATE_NOTIONAL_CAP_EXCEEDED"):
                    await place_gated_testnet_limit_order(
                        store=store,
                        run_id="run-1",
                        attempt_id="attempt-1",
                        client_order_id="attempt-1",
                        symbol="BTCUSDT",
                        side="BUY",
                        quantity="1",
                        price="90000",
                        filter_profile=_profile(),
                        max_entry_notional=number("1000"),
                        capability_snapshot_hash="a" * 64,
                        confirmed=True,
                        credential_id="testnet-readonly",
                        provider=_provider(),
                        clock=FixedClock(),
                        now_us=1_700_000_000_000_000,
                    )
                self.assertEqual(store.count(), 0)

    async def test_successful_placement_is_durable_before_send_and_acknowledged(self):
        os.environ[TRADING_ENABLED_ENV_VAR] = "true"
        socket = FakeSocket(_place_response())
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                result = await place_gated_testnet_limit_order(
                    store=store,
                    run_id="run-1",
                    attempt_id="attempt-1",
                    client_order_id="attempt-1",
                    symbol="BTCUSDT",
                    side="BUY",
                    quantity="0.5",
                    price="90",
                    filter_profile=_profile(),
                    max_entry_notional=number("1000"),
                    capability_snapshot_hash="a" * 64,
                    confirmed=True,
                    credential_id="testnet-readonly",
                    provider=_provider(),
                    clock=FixedClock(),
                    now_us=1_700_000_000_000_000,
                    websocket_factory=lambda _url, **_kwargs: socket,
                    request_id_factory=lambda: "request-1",
                )

                self.assertEqual(result.attempt.state, AttemptState.ACKNOWLEDGED)
                self.assertEqual(result.attempt.venue_order_id, 999)
                self.assertEqual(result.placed.order_id, 999)
                self.assertEqual(store.get("attempt-1").state, AttemptState.ACKNOWLEDGED)

    async def test_second_in_flight_attempt_is_refused(self):
        os.environ[TRADING_ENABLED_ENV_VAR] = "true"
        # First attempt's socket never answers (simulates an attempt stuck at SENDING).
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                stuck = OrderAttempt(
                    attempt_id="attempt-stuck",
                    run_id="run-1",
                    venue="BINANCE_SPOT_TESTNET",
                    operation=AttemptOperation.PLACE_ORDER,
                    symbol="BTCUSDT",
                    client_order_id="attempt-stuck",
                    request_fingerprint_sha256=request_fingerprint({"a": "b"}),
                    capability_snapshot_hash="a" * 64,
                    filter_snapshot_hash="b" * 64,
                    state=AttemptState.PREPARED,
                    created_at_us=1_700_000_000_000_000,
                    last_transition_at_us=1_700_000_000_000_000,
                )
                store.prepare(stuck)

                with self.assertRaisesRegex(TestnetOrderExecutionError, "GATE_MUTATION_IN_FLIGHT"):
                    await place_gated_testnet_limit_order(
                        store=store,
                        run_id="run-1",
                        attempt_id="attempt-2",
                        client_order_id="attempt-2",
                        symbol="BTCUSDT",
                        side="BUY",
                        quantity="0.01",
                        price="90",
                        filter_profile=_profile(),
                        max_entry_notional=number("1000"),
                        capability_snapshot_hash="a" * 64,
                        confirmed=True,
                        credential_id="testnet-readonly",
                        provider=_provider(),
                        clock=FixedClock(),
                        now_us=1_700_000_000_000_001,
                    )

    async def test_transport_failure_drops_attempt_to_unknown_not_silently_lost(self):
        os.environ[TRADING_ENABLED_ENV_VAR] = "true"
        socket = FakeSocket(OSError("network unreachable"))
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                with self.assertRaisesRegex(TestnetOrderExecutionError, "GATE_SEND_FAILED"):
                    await place_gated_testnet_limit_order(
                        store=store,
                        run_id="run-1",
                        attempt_id="attempt-1",
                        client_order_id="attempt-1",
                        symbol="BTCUSDT",
                        side="BUY",
                        quantity="0.5",
                        price="90",
                        filter_profile=_profile(),
                        max_entry_notional=number("1000"),
                        capability_snapshot_hash="a" * 64,
                        confirmed=True,
                        credential_id="testnet-readonly",
                        provider=_provider(),
                        clock=FixedClock(),
                        now_us=1_700_000_000_000_000,
                        websocket_factory=lambda _url, **_kwargs: socket,
                    )

                self.assertEqual(store.get("attempt-1").state, AttemptState.UNKNOWN)

    async def test_clean_venue_rejection_becomes_rejected_not_unknown(self):
        # Found live (2026-09-21): a real order priced outside Binance's
        # PERCENT_PRICE_BY_SIDE band got a clean, synchronous 400 from the
        # venue, but the gate marked it UNKNOWN -- as if the outcome were
        # ambiguous and needed REST catch-up. It wasn't ambiguous; the venue
        # gave a definitive answer. This proves the fix.
        os.environ[TRADING_ENABLED_ENV_VAR] = "true"
        socket = FakeSocket(
            json.dumps(
                {
                    "id": "request-1",
                    "status": 400,
                    "error": {"code": -1013, "msg": "Filter failure: PERCENT_PRICE_BY_SIDE"},
                }
            )
        )
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                with self.assertRaisesRegex(TestnetOrderExecutionError, "GATE_ORDER_REJECTED"):
                    await place_gated_testnet_limit_order(
                        store=store,
                        run_id="run-1",
                        attempt_id="attempt-1",
                        client_order_id="attempt-1",
                        symbol="BTCUSDT",
                        side="BUY",
                        quantity="0.5",
                        price="90",
                        filter_profile=_profile(),
                        max_entry_notional=number("1000"),
                        capability_snapshot_hash="a" * 64,
                        confirmed=True,
                        credential_id="testnet-readonly",
                        provider=_provider(),
                        clock=FixedClock(),
                        now_us=1_700_000_000_000_000,
                        websocket_factory=lambda _url, **_kwargs: socket,
                        request_id_factory=lambda: "request-1",
                    )

                resolved = store.get("attempt-1")
                self.assertEqual(resolved.state, AttemptState.REJECTED)
                self.assertEqual(resolved.venue_error_code, -1013)
                self.assertNotEqual(resolved.state, AttemptState.UNKNOWN)


class GatedCancelTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        os.environ.pop(TRADING_ENABLED_ENV_VAR, None)

    def tearDown(self):
        os.environ.pop(TRADING_ENABLED_ENV_VAR, None)

    async def test_unconfirmed_cancel_is_refused(self):
        with self.assertRaisesRegex(TestnetOrderExecutionError, "GATE_CONFIRMATION_REQUIRED"):
            await cancel_gated_testnet_order(
                symbol="BTCUSDT",
                order_id=999,
                confirmed=False,
                credential_id="testnet-readonly",
                provider=_provider(),
                clock=FixedClock(),
            )


class RecoverStuckAttemptsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        os.environ.pop(TRADING_ENABLED_ENV_VAR, None)

    def tearDown(self):
        os.environ.pop(TRADING_ENABLED_ENV_VAR, None)

    async def _recover(self, store, socket):
        return await recover_stuck_attempts(
            store=store,
            credential_id="testnet-readonly",
            provider=_provider(),
            clock=FixedClock(),
            now_us=1_700_000_000_000_001,
            websocket_factory=lambda _url, **_kwargs: socket,
            request_id_factory=lambda: "recover-1",
        )

    async def test_crash_right_after_prepare_recovers_and_finds_the_order(self):
        # Simulates a process death between prepare() and persist() -- the
        # network was never touched, but the venue turns out to have the
        # order anyway (found live: the boundary between "definitely never
        # sent" and "sent" cannot be trusted, so this must still be checked).
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                store.prepare(_stuck_attempt(AttemptState.PREPARED))
                socket = FakeSocket(_status_found_response())

                resolved = await self._recover(store, socket)

                self.assertEqual(len(resolved), 1)
                self.assertEqual(resolved[0].state, AttemptState.ACKNOWLEDGED)
                self.assertEqual(resolved[0].venue_order_id, 999)
                self.assertEqual(store.count_in_flight_attempts(), 0)

    async def test_crash_after_persist_recovers_and_stays_unresolved_if_never_sent(self):
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                attempt = _stuck_attempt(AttemptState.PREPARED)
                store.prepare(attempt)
                store.persist(attempt.attempt_id, now_us=1_700_000_000_000_000)
                socket = FakeSocket(_status_not_found_response())

                resolved = await self._recover(store, socket)

                self.assertEqual(resolved[0].state, AttemptState.UNRESOLVED)
                self.assertEqual(store.count_in_flight_attempts(), 0)
                self.assertEqual(store.count_blocking_attempts(), 1)

    async def test_crash_during_sending_recovers_the_same_way(self):
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                attempt = _stuck_attempt(AttemptState.PREPARED)
                store.prepare(attempt)
                store.persist(attempt.attempt_id, now_us=1_700_000_000_000_000)
                store.mark_sending(attempt.attempt_id, now_us=1_700_000_000_000_000)
                socket = FakeSocket(_status_found_response())

                resolved = await self._recover(store, socket)

                self.assertEqual(resolved[0].state, AttemptState.ACKNOWLEDGED)

    async def test_recovery_unblocks_a_new_order_after_it_resolves(self):
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                store.prepare(_stuck_attempt(AttemptState.PREPARED, attempt_id="stuck-1"))
                await self._recover(store, FakeSocket(_status_not_found_response()))
                self.assertEqual(store.count_in_flight_attempts(), 0)

                os.environ[TRADING_ENABLED_ENV_VAR] = "true"
                place_socket = FakeSocket(_place_response(order_id=1000, client_order_id="new-1"))
                result = await place_gated_testnet_limit_order(
                    store=store,
                    run_id="run-1",
                    attempt_id="new-1",
                    client_order_id="new-1",
                    symbol="BTCUSDT",
                    side="BUY",
                    quantity="0.5",
                    price="90",
                    filter_profile=_profile(),
                    max_entry_notional=number("1000"),
                    capability_snapshot_hash="a" * 64,
                    confirmed=True,
                    credential_id="testnet-readonly",
                    provider=_provider(),
                    clock=FixedClock(),
                    now_us=1_700_000_000_000_002,
                    websocket_factory=lambda _url, **_kwargs: place_socket,
                    request_id_factory=lambda: "request-1",
                )

                self.assertEqual(result.attempt.state, AttemptState.ACKNOWLEDGED)
                self.assertEqual(result.placed.order_id, 1000)


if __name__ == "__main__":
    unittest.main()
