"""F10.7: event center list helper (F33)."""
import unittest

from dcabot.application.event_log import EventLog
from dcabot.server.api import _events_list, _record_event


class EventsApiTests(unittest.TestCase):
    def test_record_and_list_roundtrip(self):
        log = EventLog()
        _record_event(log, "DEAL_CREATED", "deal-1", "created", 100)
        _record_event(log, "DEAL_EVENT", "deal-1", "START", 200)
        data = _events_list(log, 50)
        self.assertEqual([e["seq"] for e in data["events"]], [2, 1])

    def test_bad_limit_rejected(self):
        with self.assertRaises(ValueError):
            _events_list(EventLog(), 0)

    def test_real_app_wires_landmarks_to_event_log(self):
        from dcabot.server import api as api_module

        self.assertIs(api_module.V2_BOT_DEPS.record_event, api_module._record_v2_event)
        self.assertIs(api_module.PAPER_BOT_RUNNER.deps.record_event, api_module._record_v2_event)


if __name__ == "__main__":
    unittest.main()
