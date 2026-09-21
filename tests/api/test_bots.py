"""F8.1: bot registry API."""
import unittest

from dcabot.application.bot_registry import BotRegistry
from dcabot.server.api import (
    _bot_bind_session,
    _bot_check_pair,
    _bot_get,
    _bot_list,
    _bot_register,
    _bot_update_lists,
    _validate_bot_bind_payload,
    _validate_bot_check_payload,
    _validate_bot_lists_payload,
    _validate_bot_register_payload,
)


def _register_body(**overrides):
    body = {
        "bot_id": "bot-1",
        "name": "Grid Alpha",
        "pairs": ["BTCUSDT", "ETHUSDT"],
        "blacklist": ["LUNAUSDT"],
        "favorites": ["BTCUSDT"],
        "virtual_quote_budget": "10000",
    }
    body.update(overrides)
    return body


class BotApiTests(unittest.TestCase):
    def setUp(self):
        self.registry = BotRegistry()

    def test_register_list_get_roundtrip(self):
        validated, fields = _validate_bot_register_payload(_register_body())
        self.assertEqual(fields, {})
        created = _bot_register(self.registry, validated)
        self.assertEqual(created["result"], "CREATED")
        self.assertEqual(created["profile"]["bot_id"], "bot-1")
        listed = _bot_list(self.registry)
        self.assertEqual(listed["bot_ids"], ["bot-1"])
        fetched = _bot_get(self.registry, "bot-1")
        self.assertEqual(fetched["profile"]["name"], "Grid Alpha")
        self.assertEqual(fetched["sessions"], {})

    def test_register_minimal_body_uses_defaults(self):
        validated, fields = _validate_bot_register_payload(
            {"bot_id": "bot-1", "name": "A", "pairs": ["BTCUSDT"]}
        )
        self.assertEqual(fields, {})
        created = _bot_register(self.registry, validated)
        self.assertEqual(created["profile"]["blacklist"], [])
        self.assertEqual(created["profile"]["favorites"], [])
        self.assertEqual(created["profile"]["virtual_quote_budget"], "0")

    def test_bind_session_flow(self):
        _bot_register(self.registry, _register_body())
        validated, fields = _validate_bot_bind_payload(
            {"session_id": "sess-1", "symbol": "BTCUSDT"}
        )
        self.assertEqual(fields, {})
        bound = _bot_bind_session(self.registry, "bot-1", validated)
        self.assertEqual(bound["result"], "BOUND")
        self.assertEqual(bound["owner"], "bot-1")
        fetched = _bot_get(self.registry, "bot-1")
        self.assertEqual(fetched["sessions"], {"sess-1": "BTCUSDT"})

    def test_check_pair_verdict(self):
        _bot_register(self.registry, _register_body())
        validated, fields = _validate_bot_check_payload({"symbol": "LUNAUSDT"})
        self.assertEqual(fields, {})
        result = _bot_check_pair(self.registry, "bot-1", validated)
        self.assertEqual(result["verdict"], "BLOCKED_BLACKLIST")
        self.assertTrue(result["reason"])

    def test_update_lists_flow(self):
        _bot_register(self.registry, _register_body())
        validated, fields = _validate_bot_lists_payload(
            {"blacklist": [], "favorites": ["ETHUSDT"]}
        )
        self.assertEqual(fields, {})
        result = _bot_update_lists(self.registry, "bot-1", validated)
        self.assertEqual(result["profile"]["favorites"], ["ETHUSDT"])

    def test_bad_pairs_is_field_error(self):
        validated, fields = _validate_bot_register_payload(_register_body(pairs="BTCUSDT"))
        self.assertIsNone(validated)
        self.assertIn("pairs", fields)

    def test_unknown_field_rejected(self):
        validated, fields = _validate_bot_register_payload(
            _register_body(extra="nope")
        )
        self.assertIsNone(validated)
        self.assertIn("body", fields)

    def test_unknown_bot_raises_value_error(self):
        with self.assertRaises(ValueError):
            _bot_get(self.registry, "ghost")


if __name__ == "__main__":
    unittest.main()
