"""F10.7: local event center ring buffer (F33)."""
import unittest

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


if __name__ == "__main__":
    unittest.main()
