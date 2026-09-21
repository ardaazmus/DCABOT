"""Faz 13: durable webhook dedup store (AttemptStore deseninde SQLite)."""
import tempfile
import unittest
from pathlib import Path

from dcabot.persistence.webhook_dedup_store import WebhookDedupStore


def _intake(**overrides):
    body = {
        "signal_id": "tv-abc123",
        "dedup_key": "tradingview|BTCUSDT|BUY|1700000000000000",
        "payload_hash": "a" * 64,
        "source": "tradingview",
        "symbol": "BTCUSDT",
        "action": "BUY",
        "event_time_us": 1_700_000_000_000_000,
        "price": "81556.10",
        "received_us": 1_700_000_000_100_000,
    }
    body.update(overrides)
    return body


class WebhookDedupStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = WebhookDedupStore(Path(self.tmp.name) / "webhook.db")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_first_record_accepts_second_is_duplicate(self):
        self.assertEqual(self.store.record_intake(**_intake()), "ACCEPTED")
        self.assertEqual(self.store.record_intake(**_intake()), "DUPLICATE")

    def test_duplicate_does_not_overwrite_original_receipt(self):
        self.store.record_intake(**_intake())
        self.store.record_intake(**_intake(price="99999", received_us=1_800_000_000_000_000))
        row = self.store.get_intake("tv-abc123")
        assert row is not None
        self.assertEqual(row["price"], "81556.10")
        self.assertEqual(row["received_us"], 1_700_000_000_100_000)
        self.assertEqual(row["status"], "ACCEPTED")

    def test_roundtrip_survives_reopen(self):
        self.store.record_intake(**_intake())
        self.store.close()
        reopened = WebhookDedupStore(Path(self.tmp.name) / "webhook.db")
        try:
            row = reopened.get_intake("tv-abc123")
            assert row is not None
            self.assertEqual(row["dedup_key"], _intake()["dedup_key"])
            self.assertEqual(row["payload_hash"], "a" * 64)
        finally:
            reopened.close()

    def test_unknown_signal_returns_none(self):
        self.assertIsNone(self.store.get_intake("tv-missing"))

    def test_mark_bound_records_candidate_once(self):
        self.store.record_intake(**_intake())
        self.store.mark_bound("tv-abc123", "cand-1")
        row = self.store.get_intake("tv-abc123")
        assert row is not None
        self.assertEqual(row["status"], "BOUND")
        self.assertEqual(row["candidate_id"], "cand-1")

    def test_different_signal_id_same_key_stays_duplicate(self):
        self.store.record_intake(**_intake())
        outcome = self.store.record_intake(**_intake(signal_id="tv-other"))
        self.assertEqual(outcome, "DUPLICATE")
        self.assertIsNone(self.store.get_intake("tv-other"))

    def test_list_returns_newest_first_bounded(self):
        self.store.record_intake(**_intake(signal_id="tv-old", dedup_key="k-old", received_us=100))
        self.store.record_intake(**_intake(signal_id="tv-new", dedup_key="k-new", received_us=200))
        rows = self.store.list_intakes(limit=10)
        self.assertEqual([row["signal_id"] for row in rows], ["tv-new", "tv-old"])
        self.assertEqual(len(self.store.list_intakes(limit=1)), 1)

    def test_list_rejects_bad_limit(self):
        from dcabot.persistence.webhook_dedup_store import WebhookDedupStoreError

        for bad in (0, -1, 101, "10"):
            with self.subTest(bad=bad):
                with self.assertRaises(WebhookDedupStoreError):
                    self.store.list_intakes(limit=bad)
