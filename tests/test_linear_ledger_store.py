import sqlite3
from pathlib import Path
import tempfile
import unittest

from dcabot.application.linear_futures_math import LinearLedgerEvent
from dcabot.persistence.linear_ledger_store import (
    LinearLedgerStore,
    LinearLedgerStoreError,
    LinearLedgerStoreOutcome,
)


def funding(event_id="funding-1", amount="-5.25", time_us=2_000):
    return LinearLedgerEvent(event_id, "FUNDING", time_us, "USDT", amount)


def fee(event_id="fee-1", amount="0.5", time_us=3_000):
    return LinearLedgerEvent(event_id, "TRADING_FEE", time_us, "USDT", amount)


class LinearLedgerStoreTests(unittest.TestCase):
    def setUp(self):
        self.path = self._temporary_path()

    def tearDown(self):
        for suffix in ("", "-wal", "-shm"):
            self.path.with_name(self.path.name + suffix).unlink(missing_ok=True)

    @staticmethod
    def _temporary_path():
        return Path(tempfile.mkdtemp()) / "ledger.sqlite"

    def test_replays_exact_ledger_after_restart(self):
        with LinearLedgerStore.create(self.path, "USDT") as store:
            self.assertEqual(store.append(funding()), LinearLedgerStoreOutcome.ACCEPTED)
            self.assertEqual(store.append(fee()), LinearLedgerStoreOutcome.ACCEPTED)
            expected = store.load()
        with LinearLedgerStore.open(self.path) as store:
            self.assertEqual(store.load(), expected)

    def test_duplicate_is_idempotent_and_conflict_is_rejected(self):
        with LinearLedgerStore.create(self.path, "USDT") as store:
            self.assertEqual(store.append(funding()), LinearLedgerStoreOutcome.ACCEPTED)
            self.assertEqual(store.append(funding()), LinearLedgerStoreOutcome.DUPLICATE)
            with self.assertRaisesRegex(LinearLedgerStoreError, "LINEAR_STORE_EVENT_CONFLICT"):
                store.append(funding(amount="5.25"))

    def test_order_and_checksum_fail_closed(self):
        with LinearLedgerStore.create(self.path, "USDT") as store:
            store.append(fee(time_us=3_000))
            with self.assertRaisesRegex(LinearLedgerStoreError, "LINEAR_LEDGER_EVENT_ORDER"):
                store.append(funding(time_us=2_000))
        db = sqlite3.connect(self.path)
        try:
            db.execute("UPDATE linear_ledger_events SET event_payload=?", ('{"amount":"999"}',))
            db.commit()
        finally:
            db.close()
        with self.assertRaisesRegex(LinearLedgerStoreError, "LINEAR_STORE_RECORD_CORRUPT"):
            LinearLedgerStore.open(self.path)

    def test_row_identity_and_metadata_tampering_fail_closed(self):
        with LinearLedgerStore.create(self.path, "USDT") as store:
            store.append(funding())
        db = sqlite3.connect(self.path)
        try:
            db.execute("UPDATE linear_ledger_events SET event_id=?", ("other-event",))
            db.commit()
        finally:
            db.close()
        with self.assertRaisesRegex(LinearLedgerStoreError, "LINEAR_STORE_RECORD_CORRUPT"):
            LinearLedgerStore.open(self.path)


if __name__ == "__main__":
    unittest.main()
