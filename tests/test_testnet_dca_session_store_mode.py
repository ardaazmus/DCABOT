"""`mode` (TESTNET|PAPER) closes a real ambiguity the UI surfaced
(2026-09-23, docs/KARARLAR.md): neither `starting_balance`'s presence nor
`bindings` reliably told a real-order-capable session apart from a
paper-only one -- so `mode` is now explicit and required at creation."""
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


class ModeTests(unittest.TestCase):
    def test_defaults_to_testnet(self):
        config = Config.parse(raw_config())
        session = new_session(config, "BTCUSDT")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            with TestnetDcaSessionStore(path) as store:
                store.create("s1", session, raw_config(), now_us=1000)
                self.assertEqual(store.get_mode("s1"), "TESTNET")

    def test_explicit_paper_mode_round_trips(self):
        config = Config.parse(raw_config())
        session = new_session(config, "BTCUSDT")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            with TestnetDcaSessionStore(path) as store:
                store.create("s1", session, raw_config(), now_us=1000, mode="PAPER")
                self.assertEqual(store.get_mode("s1"), "PAPER")

    def test_unknown_mode_is_rejected(self):
        config = Config.parse(raw_config())
        session = new_session(config, "BTCUSDT")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dca-sessions.sqlite3"
            with TestnetDcaSessionStore(path) as store:
                with self.assertRaises(TestnetDcaSessionStoreError):
                    store.create("s1", session, raw_config(), now_us=1000, mode="LIVE")

    def test_pre_mode_file_upgrades_and_backfills_testnet(self):
        # A real deployed store predating `mode` only ever ran real /place
        # flows -- upgrade must backfill 'TESTNET', not leave NULL.
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
                    starting_balance TEXT,
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
                "INSERT INTO dca_sessions VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("legacy-1", None, None, "BTCUSDT", "{}", "{}", "[]", "[]", 1000, 1000),
            )
            old_db.commit()
            old_db.close()

            with TestnetDcaSessionStore(path) as store:
                self.assertEqual(store.get_mode("legacy-1"), "TESTNET")
                store.create("s1", session, raw_config(), now_us=2000, mode="PAPER")
                self.assertEqual(store.get_mode("s1"), "PAPER")


if __name__ == "__main__":
    unittest.main()
