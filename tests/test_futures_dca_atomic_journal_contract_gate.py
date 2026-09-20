import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class FuturesDcaAtomicJournalContractGateTests(unittest.TestCase):
    def test_failed_transaction_leaves_no_partial_economic_projection(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "journal.sqlite"
            self._initialize(path)
            db = sqlite3.connect(path, isolation_level=None)
            try:
                db.execute("BEGIN IMMEDIATE")
                db.execute(
                    "INSERT INTO journal_records(identity, kind, payload) VALUES (?, ?, ?)",
                    ("event-1", "event", "fill=100"),
                )
                db.execute(
                    "INSERT INTO journal_records(identity, kind, payload) VALUES (?, ?, ?)",
                    ("reservation-1", "reservation", "consumed=1"),
                )
                with self.assertRaisesRegex(RuntimeError, "injected failure"):
                    try:
                        raise RuntimeError("injected failure before commit")
                    except RuntimeError:
                        db.execute("ROLLBACK")
                        raise
            finally:
                db.close()

            reopened = sqlite3.connect(path)
            try:
                self.assertEqual(reopened.execute("SELECT COUNT(*) FROM journal_records").fetchone(), (0,))
            finally:
                reopened.close()

    def test_committed_projection_replays_as_one_restart_visible_unit(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "journal.sqlite"
            self._initialize(path)
            db = sqlite3.connect(path, isolation_level=None)
            try:
                db.execute("BEGIN IMMEDIATE")
                db.executemany(
                    "INSERT INTO journal_records(identity, kind, payload) VALUES (?, ?, ?)",
                    (
                        ("event-1", "event", "fill=100"),
                        ("reservation-1", "reservation", "consumed=1"),
                        ("posting-1", "posting", "cursor=1"),
                    ),
                )
                db.execute("COMMIT")
            finally:
                db.close()

            reopened = sqlite3.connect(path)
            try:
                self.assertEqual(
                    reopened.execute(
                        "SELECT identity, kind, payload FROM journal_records ORDER BY identity"
                    ).fetchall(),
                    [
                        ("event-1", "event", "fill=100"),
                        ("posting-1", "posting", "cursor=1"),
                        ("reservation-1", "reservation", "consumed=1"),
                    ],
                )
            finally:
                reopened.close()

    @staticmethod
    def _initialize(path: Path) -> None:
        db = sqlite3.connect(path, isolation_level=None)
        try:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA synchronous=FULL")
            db.execute(
                "CREATE TABLE journal_records(" 
                "identity TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL)"
            )
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
