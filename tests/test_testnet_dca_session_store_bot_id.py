"""Faz 17 AA.-1 (bot<->deal association, final piece): `bot_id` is a purely
associative, optional link on session creation -- no economic meaning,
CORE01's single-deal invariant is untouched."""
import json
from pathlib import Path
import sqlite3
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


class BotIdAssociationTests(unittest.TestCase):
    def test_sessions_without_bot_id_are_not_listed_for_any_bot(self):
        config = Config.parse(raw_config())
        session = new_session(config, "BTCUSDT")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            with TestnetDcaSessionStore(path) as store:
                store.create("s1", session, raw_config(), now_us=1000)
                self.assertEqual(store.list_ids_for_bot("bot-1"), [])

    def test_list_ids_for_bot_returns_only_that_bots_sessions(self):
        config = Config.parse(raw_config())
        session = new_session(config, "BTCUSDT")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            with TestnetDcaSessionStore(path) as store:
                store.create("s1", session, raw_config(), now_us=1000, bot_id="bot-1")
                store.create("s2", session, raw_config(), now_us=2000, bot_id="bot-2")
                store.create("s3", session, raw_config(), now_us=3000, bot_id="bot-1")
                self.assertEqual(store.list_ids_for_bot("bot-1"), ["s1", "s3"])
                self.assertEqual(store.list_ids_for_bot("bot-2"), ["s2"])

    def test_list_bot_ids_returns_every_session_with_its_bot_id_or_none(self):
        config = Config.parse(raw_config())
        session = new_session(config, "BTCUSDT")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            with TestnetDcaSessionStore(path) as store:
                store.create("s1", session, raw_config(), now_us=1000, bot_id="bot-1")
                store.create("s2", session, raw_config(), now_us=2000)
                self.assertEqual(store.list_bot_ids(), [("s1", "bot-1"), ("s2", None)])

    def test_empty_bot_id_is_rejected(self):
        config = Config.parse(raw_config())
        session = new_session(config, "BTCUSDT")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            with TestnetDcaSessionStore(path) as store:
                with self.assertRaises(TestnetDcaSessionStoreError):
                    store.create("s1", session, raw_config(), now_us=1000, bot_id="")
                with self.assertRaises(TestnetDcaSessionStoreError):
                    store.list_ids_for_bot("")

    def test_pre_bot_id_file_upgrades_in_place_without_losing_data(self):
        # Simulates a real deployed store created before bot_id existed.
        config = Config.parse(raw_config())
        session = new_session(config, "BTCUSDT")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            old_db = sqlite3.connect(str(path))
            old_db.execute(
                """
                CREATE TABLE dca_sessions (
                    session_id TEXT PRIMARY KEY,
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
                "INSERT INTO dca_sessions VALUES (?,?,?,?,?,?,?,?)",
                ("legacy-1", "BTCUSDT", "{}", "{}", "[]", "[]", 1000, 1000),
            )
            old_db.commit()
            old_db.close()

            with TestnetDcaSessionStore(path) as store:
                # The pre-existing row is still there, unaffected.
                self.assertIn("legacy-1", store.list_ids())
                # New writes with bot_id now work against the upgraded schema.
                store.create("s1", session, raw_config(), now_us=2000, bot_id="bot-1")
                self.assertEqual(store.list_ids_for_bot("bot-1"), ["s1"])

    def test_loaded_session_is_unaffected_by_bot_id(self):
        config = Config.parse(raw_config())
        session = new_session(config, "BTCUSDT")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            with TestnetDcaSessionStore(path) as store:
                store.create("s1", session, raw_config(), now_us=1000, bot_id="bot-1")
                loaded = store.load("s1")
        self.assertEqual(loaded.symbol, "BTCUSDT")


if __name__ == "__main__":
    unittest.main()
