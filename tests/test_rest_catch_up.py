import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from dcabot.application.credential_boundary import CredentialMaterial, EphemeralCredentialProvider
from dcabot.application.order_attempt import AttemptOperation, AttemptState, OrderAttempt, request_fingerprint
from dcabot.application.reconciliation import ConnectionState, ReconciliationCoordinator
from dcabot.application.rest_catch_up import RestCatchUpError, run_rest_catch_up
from dcabot.application.signed_request import ApiKeyType
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


def _attempt(*, client_order_id: str | None = "client-1") -> OrderAttempt:
    return OrderAttempt(
        attempt_id="attempt-1",
        run_id="run-1",
        venue="BINANCE_SPOT_TESTNET",
        operation=AttemptOperation.PLACE_ORDER,
        symbol="BTCUSDT",
        client_order_id=client_order_id,
        request_fingerprint_sha256=request_fingerprint({"symbol": "BTCUSDT"}),
        capability_snapshot_hash="a" * 64,
        filter_snapshot_hash="b" * 64,
        state=AttemptState.PREPARED,
        created_at_us=1_700_000_000_000_000,
        last_transition_at_us=1_700_000_000_000_000,
    )


def _order_status_response(*, order_id: int, client_order_id: str) -> str:
    return json.dumps(
        {
            "id": "diag-1",
            "status": 200,
            "result": {
                "symbol": "BTCUSDT",
                "orderId": order_id,
                "clientOrderId": client_order_id,
            },
        }
    )


def _not_found_response() -> str:
    return json.dumps(
        {"id": "diag-1", "status": 400, "error": {"code": -2013, "msg": "Order does not exist."}}
    )


class RestCatchUpTests(unittest.IsolatedAsyncioTestCase):
    async def test_sending_attempt_resolves_by_client_id_and_reaches_synced(self):
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                store.prepare(_attempt())
                store.persist("attempt-1", now_us=1_700_000_000_000_001)
                store.mark_sending("attempt-1", now_us=1_700_000_000_000_002)
                coordinator = ReconciliationCoordinator(store)
                coordinator.startup(now_us=1_700_000_000_000_003)
                socket = FakeSocket(_order_status_response(order_id=999, client_order_id="client-1"))

                final_state = await run_rest_catch_up(
                    coordinator,
                    store,
                    credential_id="testnet-readonly",
                    provider=_provider(),
                    clock=FixedClock(),
                    now_us=1_700_000_000_000_004,
                    websocket_factory=lambda _url, **_kwargs: socket,
                    request_id_factory=lambda: "diag-1",
                    snapshot_id_factory=lambda: "snapshot-1",
                )

                self.assertEqual(final_state, ConnectionState.SYNCED)
                self.assertEqual(coordinator.state, ConnectionState.SYNCED)
                self.assertEqual(store.get("attempt-1").state, AttemptState.ACKNOWLEDGED)
                self.assertEqual(store.get("attempt-1").venue_order_id, 999)
                self.assertTrue(socket.closed)

    async def test_genuinely_missing_order_becomes_unresolved_and_blocks_synced(self):
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                store.prepare(_attempt())
                store.persist("attempt-1", now_us=1_700_000_000_000_001)
                store.mark_sending("attempt-1", now_us=1_700_000_000_000_002)
                coordinator = ReconciliationCoordinator(store)
                coordinator.startup(now_us=1_700_000_000_000_003)
                socket = FakeSocket(_not_found_response())

                with self.assertRaisesRegex(RestCatchUpError, "CATCH_UP_UNRESOLVED_ATTEMPTS"):
                    await run_rest_catch_up(
                        coordinator,
                        store,
                        credential_id="testnet-readonly",
                        provider=_provider(),
                        clock=FixedClock(),
                        now_us=1_700_000_000_000_004,
                        websocket_factory=lambda _url, **_kwargs: socket,
                        request_id_factory=lambda: "diag-1",
                    )

                self.assertEqual(store.get("attempt-1").state, AttemptState.UNRESOLVED)
                self.assertEqual(coordinator.state, ConnectionState.RECONCILIATION_REQUIRED)

    async def test_transport_failure_fails_closed_without_mutating_state_further(self):
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                store.prepare(_attempt())
                store.persist("attempt-1", now_us=1_700_000_000_000_001)
                store.mark_sending("attempt-1", now_us=1_700_000_000_000_002)
                coordinator = ReconciliationCoordinator(store)
                coordinator.startup(now_us=1_700_000_000_000_003)
                socket = FakeSocket(OSError("network unreachable"))

                with self.assertRaisesRegex(RestCatchUpError, "CATCH_UP_LOOKUP_FAILED"):
                    await run_rest_catch_up(
                        coordinator,
                        store,
                        credential_id="testnet-readonly",
                        provider=_provider(),
                        clock=FixedClock(),
                        now_us=1_700_000_000_000_004,
                        websocket_factory=lambda _url, **_kwargs: socket,
                    )

                self.assertEqual(store.get("attempt-1").state, AttemptState.UNKNOWN)

    async def test_unidentifiable_attempt_fails_closed_without_inventing_identity(self):
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                store.prepare(_attempt(client_order_id=None))
                store.persist("attempt-1", now_us=1_700_000_000_000_001)
                store.mark_sending("attempt-1", now_us=1_700_000_000_000_002)
                coordinator = ReconciliationCoordinator(store)
                coordinator.startup(now_us=1_700_000_000_000_003)

                with self.assertRaisesRegex(RestCatchUpError, "CATCH_UP_ATTEMPT_UNIDENTIFIABLE"):
                    await run_rest_catch_up(
                        coordinator,
                        store,
                        credential_id="testnet-readonly",
                        provider=_provider(),
                        clock=FixedClock(),
                        now_us=1_700_000_000_000_004,
                        websocket_factory=lambda _url, **_kwargs: None,
                    )

    async def test_wrong_connection_state_is_rejected_before_any_lookup(self):
        coordinator = ReconciliationCoordinator()
        coordinator.begin_connect()
        coordinator.public_snapshot_ready()

        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                with self.assertRaisesRegex(RestCatchUpError, "CATCH_UP_STATE_INVALID"):
                    await run_rest_catch_up(
                        coordinator,
                        store,
                        credential_id="testnet-readonly",
                        provider=_provider(),
                        clock=FixedClock(),
                        now_us=1_700_000_000_000_004,
                        websocket_factory=lambda _url, **_kwargs: None,
                    )

    async def test_no_blocking_attempts_still_requires_a_matching_cursor(self):
        # No prior stream events were ever accepted, so the coordinator has no
        # hydrated cursor; the snapshot's event_cursor=None must match that.
        with TemporaryDirectory() as directory:
            with AttemptStore(Path(directory) / "attempts.sqlite") as store:
                coordinator = ReconciliationCoordinator(store)
                coordinator.state = ConnectionState.RECONCILIATION_REQUIRED

                final_state = await run_rest_catch_up(
                    coordinator,
                    store,
                    credential_id="testnet-readonly",
                    provider=_provider(),
                    clock=FixedClock(),
                    now_us=1_700_000_000_000_004,
                    websocket_factory=lambda _url, **_kwargs: None,
                    snapshot_id_factory=lambda: "snapshot-empty",
                )

                self.assertEqual(final_state, ConnectionState.SYNCED)


if __name__ == "__main__":
    unittest.main()
