"""F10.7: local event center ring buffer (F33)."""
import sqlite3
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from dcabot.application.event_log import EventLog, EventLogError


class EventLogTests(unittest.TestCase):
    def test_append_and_list_newest_first(self):
        log = EventLog(capacity=3)
        first = log.append(kind="DEAL_CREATED", ref="deal-1", summary="created", time_us=100)
        second = log.append(kind="DEAL_EVENT", ref="deal-1", summary="START", time_us=200)
        self.assertEqual(first, 1)
        self.assertEqual(second, 2)
        entries = log.list()
        self.assertEqual([e["seq"] for e in entries], [2, 1])
        self.assertEqual(entries[0]["kind"], "DEAL_EVENT")

    def test_capacity_drops_oldest(self):
        log = EventLog(capacity=2)
        log.append(kind="A", ref="r1", summary="s", time_us=1)
        log.append(kind="B", ref="r2", summary="s", time_us=2)
        log.append(kind="C", ref="r3", summary="s", time_us=3)
        self.assertEqual([e["kind"] for e in log.list()], ["C", "B"])

    def test_limit_bounded(self):
        log = EventLog(capacity=10)
        for index in range(5):
            log.append(kind="A", ref=f"r{index}", summary="s", time_us=index)
        self.assertEqual(len(log.list(limit=2)), 2)
        with self.assertRaises(EventLogError):
            log.list(limit=0)
        with self.assertRaises(EventLogError):
            log.list(limit=201)

    def test_bad_kind_rejected(self):
        log = EventLog()
        with self.assertRaises(EventLogError) as ctx:
            log.append(kind="nope", ref="r", summary="s", time_us=1)
        self.assertEqual(ctx.exception.code, "EVENT_KIND_INVALID")

    def test_bad_time_rejected(self):
        log = EventLog()
        with self.assertRaises(EventLogError):
            log.append(kind="A", ref="r", summary="s", time_us=-1)

    def test_empty_ref_rejected(self):
        log = EventLog()
        with self.assertRaises(EventLogError):
            log.append(kind="A", ref="", summary="s", time_us=1)

    def test_list_after_replays_oldest_first(self):
        log = EventLog()
        log.append(kind="A", ref="r1", summary="s", time_us=1)
        log.append(kind="B", ref="r2", summary="s", time_us=2)
        log.append(kind="C", ref="r3", summary="s", time_us=3)
        entries = log.list_after(1)
        self.assertEqual([e["seq"] for e in entries], [2, 3])

    def test_list_after_empty_when_current(self):
        log = EventLog()
        log.append(kind="A", ref="r1", summary="s", time_us=1)
        self.assertEqual(log.list_after(1), [])
        self.assertEqual(log.list_after(99), [])

    def test_list_after_validates(self):
        log = EventLog()
        with self.assertRaises(EventLogError):
            log.list_after(-1)
        with self.assertRaises(EventLogError):
            log.list_after(0, limit=0)
        with self.assertRaises(EventLogError):
            log.list_after(0, limit=201)

    def test_wait_for_returns_true_on_append(self):
        log = EventLog()
        log.append(kind="A", ref="r1", summary="s", time_us=1)

        def _append_late():
            time.sleep(0.05)
            log.append(kind="B", ref="r2", summary="s", time_us=2)

        worker = threading.Thread(target=_append_late)
        worker.start()
        try:
            self.assertEqual(log.wait_for(1, timeout=5.0), 2)
        finally:
            worker.join(timeout=10)

    def test_wait_for_returns_current_when_already_ahead(self):
        log = EventLog()
        log.append(kind="A", ref="r1", summary="s", time_us=1)
        self.assertEqual(log.wait_for(0, timeout=5.0), 1)

    def test_wait_for_timeout_returns_last_seq(self):
        log = EventLog()
        self.assertEqual(log.wait_for(0, timeout=0.05), 0)

    def test_evicted_entries_are_skipped(self):
        log = EventLog(capacity=1)
        log.append(kind="A", ref="r1", summary="s", time_us=1)
        log.append(kind="B", ref="r2", summary="s", time_us=2)
        self.assertEqual(log.wait_for(0, timeout=1.0), 2)
        self.assertEqual([e["seq"] for e in log.list_after(0)], [2])

    def test_wait_for_validates(self):
        log = EventLog()
        with self.assertRaises(EventLogError):
            log.wait_for(-1, timeout=1.0)
        with self.assertRaises(EventLogError):
            log.wait_for(0, timeout=0)


class SqliteEventLogTests(unittest.TestCase):
    def test_entries_survive_reopen_with_monotonic_seq(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.sqlite3"
            log = EventLog(path=path)
            log.append(kind="A", ref="r1", summary="s", time_us=1)
            log.append(kind="B", ref="r2", summary="s", time_us=2)
            log.close()
            reopened = EventLog(path=path)
            try:
                self.assertEqual([e["seq"] for e in reopened.list()], [2, 1])
                self.assertEqual(
                    reopened.append(kind="C", ref="r3", summary="s", time_us=3), 3
                )
                self.assertEqual(
                    [e["seq"] for e in reopened.list_after(1)], [2, 3]
                )
            finally:
                reopened.close()

    def test_capacity_prunes_oldest_on_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.sqlite3"
            log = EventLog(capacity=2, path=path)
            log.append(kind="A", ref="r1", summary="s", time_us=1)
            log.append(kind="B", ref="r2", summary="s", time_us=2)
            log.append(kind="C", ref="r3", summary="s", time_us=3)
            log.close()
            check = sqlite3.connect(str(path))
            try:
                rows = check.execute("SELECT seq FROM landmarks ORDER BY seq").fetchall()
            finally:
                check.close()
            self.assertEqual(rows, [(2,), (3,)])
            reopened = EventLog(capacity=2, path=path)
            try:
                self.assertEqual([e["kind"] for e in reopened.list()], ["C", "B"])
            finally:
                reopened.close()

    def test_unusable_path_fails_fast(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(EventLogError) as ctx:
                EventLog(path=Path(tmp))
            self.assertEqual(ctx.exception.code, "EVENT_LOG_STORE_INVALID")
            with self.assertRaises(EventLogError):
                EventLog(path=12345)

    def test_append_degrades_to_ram_on_storage_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = EventLog(path=Path(tmp) / "events.sqlite3")
            assert log._db is not None
            log._db.close()
            broken = mock.MagicMock()
            broken.execute.side_effect = sqlite3.OperationalError("disk")
            log._db = broken
            with self.assertLogs("dcabot.application.event_log", level="WARNING"):
                seq = log.append(kind="A", ref="r1", summary="s", time_us=1)
            self.assertEqual(seq, 1)
            self.assertEqual([e["seq"] for e in log.list()], [1])
            log.close()

    def test_ram_mode_close_is_noop(self):
        EventLog().close()


class NotificationStateTests(unittest.TestCase):
    def test_default_nothing_seen(self):
        log = EventLog()
        log.append(kind="A", ref="r1", summary="s", time_us=1)
        self.assertEqual(log.get_last_seen(), 0)
        self.assertEqual(log.unread_count(), 1)

    def test_mark_read_clears_unread(self):
        log = EventLog()
        log.append(kind="A", ref="r1", summary="s", time_us=1)
        log.append(kind="B", ref="r2", summary="s", time_us=2)
        self.assertEqual(log.set_last_seen(2), 2)
        self.assertEqual(log.get_last_seen(), 2)
        self.assertEqual(log.unread_count(), 0)
        log.append(kind="C", ref="r3", summary="s", time_us=3)
        self.assertEqual(log.unread_count(), 1)

    def test_last_seen_is_monotonic(self):
        log = EventLog()
        log.set_last_seen(5)
        self.assertEqual(log.set_last_seen(3), 5)
        self.assertEqual(log.get_last_seen(), 5)

    def test_last_seen_validates(self):
        log = EventLog()
        for bad in (-1, True, "2", 2.0, None):
            with self.subTest(bad=bad), self.assertRaises(EventLogError) as ctx:
                log.set_last_seen(bad)
            self.assertEqual(ctx.exception.code, "EVENT_SEQ_INVALID")

    def test_last_seen_survives_reopen(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.sqlite3"
            log = EventLog(path=path)
            log.append(kind="A", ref="r1", summary="s", time_us=1)
            log.append(kind="B", ref="r2", summary="s", time_us=2)
            log.set_last_seen(1)
            log.close()
            reopened = EventLog(path=path)
            try:
                self.assertEqual(reopened.get_last_seen(), 1)
                self.assertEqual(reopened.unread_count(), 1)
            finally:
                reopened.close()

    def test_unread_counts_retained_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.sqlite3"
            log = EventLog(capacity=2, path=path)
            try:
                log.append(kind="A", ref="r1", summary="s", time_us=1)
                log.append(kind="B", ref="r2", summary="s", time_us=2)
                log.append(kind="C", ref="r3", summary="s", time_us=3)
                self.assertEqual(log.unread_count(), 2)
            finally:
                log.close()


if __name__ == "__main__":
    unittest.main()
