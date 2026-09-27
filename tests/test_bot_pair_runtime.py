"""M1: pair runtime store + deals symbol migration backfill."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from dcabot.domain.engine import State
from dcabot.domain.numbers import Q
from dcabot.persistence.bot_store import BotDeal, BotPairRuntime, BotStore


class PairRuntimeStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = BotStore(Path(self.tmp.name) / "bots.sqlite3")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def _pair(self, symbol, last_bar=0):
        return BotPairRuntime("bot_1", symbol, {"cooldown_seconds": 0}, State(), Q(0), last_bar, 7)

    def test_empty_then_round_trip(self):
        self.assertEqual(self.store.get_pair_runtimes("bot_1"), ())
        self.store.save_pair_step(
            (self._pair("BTCUSDT", 1), self._pair("ETHUSDT", 2)),
            deals=(BotDeal("bot_1", 0, 100, None, 0, None, None, 0, "BTCUSDT"),),
        )
        loaded = self.store.get_pair_runtimes("bot_1")
        self.assertEqual([(r.symbol, r.last_bar_open_us) for r in loaded], [("BTCUSDT", 1), ("ETHUSDT", 2)])
        deals = self.store.list_deals("bot_1")
        self.assertEqual([(d.deal_sequence, d.symbol) for d in deals], [(0, "BTCUSDT")])

    def test_empty_symbol_rejected(self):
        with self.assertRaisesRegex(Exception, "BOT_DEAL_SYMBOL_INVALID"):
            self.store.save_pair_step(
                (self._pair("BTCUSDT"),),
                deals=(BotDeal("bot_1", 0, 100, None, 0, None, None),),
            )

    def test_mixed_bot_ids_rejected(self):
        other = BotPairRuntime("bot_2", "BTCUSDT", {}, State(), Q(0), 0, 0)
        with self.assertRaisesRegex(Exception, "BOT_PAIR_RUNTIME_INVALID"):
            self.store.save_pair_step((self._pair("BTCUSDT"), other))

    def test_legacy_rows_backfill_symbol_from_bot(self):
        path = Path(self.tmp.name) / "legacy.sqlite3"
        db = sqlite3.connect(str(path))
        db.execute(
            "CREATE TABLE bots (bot_id TEXT PRIMARY KEY, name TEXT, strategy_type TEXT, mode TEXT, symbol TEXT,"
            " strategy_json TEXT, budget TEXT, status TEXT, status_reason TEXT, revision INTEGER,"
            " created_at_us INTEGER, updated_at_us INTEGER, archived_at_us INTEGER)"
        )
        db.execute(
            "CREATE TABLE bot_deals (bot_id TEXT, deal_sequence INTEGER, started_at_us INTEGER,"
            " closed_at_us INTEGER, safety_orders_filled INTEGER, profit TEXT, close_reason TEXT,"
            " manual_orders_filled INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (bot_id, deal_sequence))"
        )
        db.execute(
            "INSERT INTO bots VALUES ('bot_9','n','DCA','PAPER','ETHUSDT','{}','100','STOPPED',NULL,1,0,0,NULL)"
        )
        db.execute("INSERT INTO bot_deals VALUES ('bot_9',0,100,NULL,0,NULL,NULL,0)")
        db.commit()
        db.close()
        store = BotStore(path)
        try:
            deals = store.list_deals("bot_9")
        finally:
            store.close()
        self.assertEqual([(d.deal_sequence, d.symbol) for d in deals], [(0, "ETHUSDT")])


if __name__ == "__main__":
    unittest.main()
