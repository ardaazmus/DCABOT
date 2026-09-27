"""Paper/"botUSD" design (2026-09-23, docs/KARARLAR.md): `starting_balance`
is an optional, display-only virtual balance anchor on a DCA session --
never used inside engine.py, purely a store-level convenience so the UI
can show "starting botUSD + realized net" without inventing a second place
to store it."""
import json
from pathlib import Path
import tempfile
import unittest

from dcabot.application.testnet_dca_session import new_session
from dcabot.domain.config import Config
from dcabot.persistence.testnet_dca_session_store import (
    TestnetDcaSessionStore,
    TestnetDcaSessionStoreError,
)

ROOT = Path(__file__).resolve().parents[1]


def raw_config(**updates) -> dict:
    raw = json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))
    raw.update(updates)
    return raw


class StartingBalanceTests(unittest.TestCase):
    def test_starting_balance_round_trips(self):
        config = Config.parse(raw_config())
        session = new_session(config, "BTCUSDT")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            with TestnetDcaSessionStore(path) as store:
                store.create("s1", session, raw_config(), now_us=1000, starting_balance="1000")
                self.assertEqual(store.get_starting_balance("s1"), "1000")

    def test_omitted_starting_balance_is_none(self):
        config = Config.parse(raw_config())
        session = new_session(config, "BTCUSDT")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            with TestnetDcaSessionStore(path) as store:
                store.create("s1", session, raw_config(), now_us=1000)
                self.assertIsNone(store.get_starting_balance("s1"))

    def test_non_positive_or_malformed_starting_balance_is_rejected(self):
        config = Config.parse(raw_config())
        session = new_session(config, "BTCUSDT")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            with TestnetDcaSessionStore(path) as store:
                for bad in ("0", "-10", "not-a-number", "1e5"):
                    with self.assertRaises(TestnetDcaSessionStoreError):
                        store.create(f"s-{bad}", session, raw_config(), now_us=1000, starting_balance=bad)

    def test_loaded_session_is_unaffected_by_starting_balance(self):
        config = Config.parse(raw_config())
        session = new_session(config, "BTCUSDT")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            with TestnetDcaSessionStore(path) as store:
                store.create("s1", session, raw_config(), now_us=1000, starting_balance="500")
                loaded = store.load("s1")
        self.assertEqual(loaded.symbol, "BTCUSDT")

    def test_pre_starting_balance_file_upgrades_in_place(self):
        import sqlite3

        config = Config.parse(raw_config())
        session = new_session(config, "BTCUSDT")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            old_db = sqlite3.connect(str(path))
            old_db.execute(
                """
                CREATE TABLE dca_sessions (
                    session_id TEXT PRIMARY KEY,
                    bot_id TEXT,
                    symbol TEXT NOT NULL,
                    raw_config TEXT NOT NULL,
                    state_payload TEXT NOT NULL,
                    bindings_payload TEXT NOT NULL,
                    applied_trade_ids TEXT NOT NULL,
                    created_at_us INTEGER NOT NULL,
                    updated_at_us INTEGER NOT NULL
                )
                """
            )
            old_db.execute(
                "INSERT INTO dca_sessions VALUES (?,?,?,?,?,?,?,?,?)",
                ("legacy-1", None, "BTCUSDT", "{}", "{}", "[]", "[]", 1000, 1000),
            )
            old_db.commit()
            old_db.close()

            with TestnetDcaSessionStore(path) as store:
                self.assertIn("legacy-1", store.list_ids())
                self.assertIsNone(store.get_starting_balance("legacy-1"))
                store.create("s1", session, raw_config(), now_us=2000, starting_balance="200")
                self.assertEqual(store.get_starting_balance("s1"), "200")


if __name__ == "__main__":
    unittest.main()
