"""Faz 17 AA.-1 (testnet-session dilimi, adım 1): durable DcaSession store.
Closes testnet_dca_session.py's own documented gap ("does not persist
State/bindings durably -- a process crash mid-deal loses the in-memory DCA
session")."""
import json
from pathlib import Path
import tempfile
import unittest

from dcabot.application.testnet_dca_session import DcaSession, OrderBinding, new_session
from dcabot.domain.config import Config
from dcabot.domain.engine import apply
from dcabot.persistence.testnet_dca_session_store import (
    TestnetDcaSessionStore,
    TestnetDcaSessionStoreError,
)

ROOT = Path(__file__).resolve().parents[1]


def raw_config(**updates) -> dict:
    raw = json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))
    raw.update(updates)
    return raw


class CreateLoadTests(unittest.TestCase):
    def test_create_then_load_round_trips_a_fresh_session(self):
        config = Config.parse(raw_config())
        session = new_session(config, "BTCUSDT")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            with TestnetDcaSessionStore(path) as store:
                store.create("s1", session, raw_config(), now_us=1000)
                loaded = store.load("s1")
        self.assertEqual(loaded.symbol, "BTCUSDT")
        self.assertEqual(loaded.state.position.qty, session.state.position.qty)
        self.assertEqual(loaded.config.symbol, config.symbol)
        self.assertEqual(loaded.bindings, ())
        self.assertEqual(loaded.applied_trade_ids, frozenset())

    def test_create_duplicate_id_is_rejected(self):
        config = Config.parse(raw_config())
        session = new_session(config, "BTCUSDT")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            with TestnetDcaSessionStore(path) as store:
                store.create("s1", session, raw_config(), now_us=1000)
                with self.assertRaises(TestnetDcaSessionStoreError) as ctx:
                    store.create("s1", session, raw_config(), now_us=2000)
                self.assertEqual(ctx.exception.code, "DCA_SESSION_ALREADY_EXISTS")

    def test_load_unknown_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            with TestnetDcaSessionStore(path) as store:
                with self.assertRaises(TestnetDcaSessionStoreError) as ctx:
                    store.load("ghost")
                self.assertEqual(ctx.exception.code, "DCA_SESSION_NOT_FOUND")


class SaveAndSurviveRestartTests(unittest.TestCase):
    def test_state_mutation_survives_a_reopened_store(self):
        config = Config.parse(raw_config())
        session = new_session(config, "BTCUSDT")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            with TestnetDcaSessionStore(path) as store:
                store.create("s1", session, raw_config(), now_us=1000)
                next_state = apply(session.state, {"type": "MARK", "price": "100"}, config)
                from dataclasses import replace as _replace

                mutated = _replace(session, state=next_state)
                store.save("s1", mutated, now_us=2000)

            # Reopen the store from a fresh connection -- simulates a restart.
            with TestnetDcaSessionStore(path) as reopened:
                loaded = reopened.load("s1")
        self.assertEqual(loaded.state.mark, next_state.mark)

    def test_save_unknown_id_is_rejected(self):
        config = Config.parse(raw_config())
        session = new_session(config, "BTCUSDT")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            with TestnetDcaSessionStore(path) as store:
                with self.assertRaises(TestnetDcaSessionStoreError) as ctx:
                    store.save("ghost", session, now_us=1000)
                self.assertEqual(ctx.exception.code, "DCA_SESSION_NOT_FOUND")

    def test_bindings_and_applied_trade_ids_survive_round_trip(self):
        config = Config.parse(raw_config())
        session = new_session(config, "BTCUSDT")
        binding = OrderBinding(
            local_order_id="local-1", role="BASE", attempt_id="attempt-1", venue_order_id=99
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            with TestnetDcaSessionStore(path) as store:
                from dataclasses import replace as _replace

                mutated = _replace(
                    session, bindings=(binding,), applied_trade_ids=frozenset({1, 2, 3})
                )
                store.create("s1", mutated, raw_config(), now_us=1000)
                loaded = store.load("s1")
        self.assertEqual(loaded.bindings, (binding,))
        self.assertEqual(loaded.applied_trade_ids, frozenset({1, 2, 3}))


class ListIdsTests(unittest.TestCase):
    def test_list_ids_returns_creation_order(self):
        config = Config.parse(raw_config())
        session = new_session(config, "BTCUSDT")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            with TestnetDcaSessionStore(path) as store:
                store.create("s1", session, raw_config(), now_us=1000)
                store.create("s2", session, raw_config(), now_us=2000)
                self.assertEqual(store.list_ids(), ["s1", "s2"])


class ValidationTests(unittest.TestCase):
    def test_invalid_session_id_is_rejected(self):
        config = Config.parse(raw_config())
        session = new_session(config, "BTCUSDT")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            with TestnetDcaSessionStore(path) as store:
                with self.assertRaises(TestnetDcaSessionStoreError):
                    store.create("", session, raw_config(), now_us=1000)
                with self.assertRaises(TestnetDcaSessionStoreError):
                    store.create("has space", session, raw_config(), now_us=1000)


if __name__ == "__main__":
    unittest.main()
