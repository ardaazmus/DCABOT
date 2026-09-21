"""F8.1: multi-bot registry — identity, pair scope, ownership (F05)."""
import unittest

from dcabot.application.bot_registry import (
    BotRegistry,
    BotRegistryError,
    new_bot_profile,
)


class BotRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = BotRegistry()

    def test_register_and_get_roundtrip(self):
        profile = new_bot_profile(
            bot_id="bot-1",
            name="Grid Alpha",
            pairs=["BTCUSDT", "ETHUSDT"],
            blacklist=["LUNAUSDT"],
            favorites=["BTCUSDT"],
            virtual_quote_budget="10000",
        )
        self.assertEqual(self.registry.register(profile), "CREATED")
        stored = self.registry.get("bot-1")
        self.assertEqual(stored.bot_id, "bot-1")
        self.assertEqual(stored.name, "Grid Alpha")
        self.assertEqual(stored.pairs, ("BTCUSDT", "ETHUSDT"))
        self.assertEqual(stored.blacklist, ("LUNAUSDT",))
        self.assertEqual(stored.favorites, ("BTCUSDT",))
        self.assertEqual(stored.virtual_quote_budget, "10000")

    def test_identical_reregister_is_duplicate(self):
        kwargs = dict(
            bot_id="bot-1", name="A", pairs=["BTCUSDT"],
            blacklist=[], favorites=[], virtual_quote_budget="100",
        )
        self.registry.register(new_bot_profile(**kwargs))
        self.assertEqual(self.registry.register(new_bot_profile(**kwargs)), "DUPLICATE")

    def test_conflicting_reregister_rejected(self):
        self.registry.register(new_bot_profile(
            bot_id="bot-1", name="A", pairs=["BTCUSDT"],
            blacklist=[], favorites=[], virtual_quote_budget="100",
        ))
        with self.assertRaises(BotRegistryError) as ctx:
            self.registry.register(new_bot_profile(
                bot_id="bot-1", name="B", pairs=["BTCUSDT"],
                blacklist=[], favorites=[], virtual_quote_budget="100",
            ))
        self.assertEqual(ctx.exception.code, "BOT_ID_CONFLICT")

    def test_empty_pairs_rejected(self):
        with self.assertRaises(BotRegistryError) as ctx:
            new_bot_profile(
                bot_id="bot-1", name="A", pairs=[],
                blacklist=[], favorites=[], virtual_quote_budget="100",
            )
        self.assertEqual(ctx.exception.code, "BOT_PAIRS_INVALID")

    def test_duplicate_pairs_rejected(self):
        with self.assertRaises(BotRegistryError) as ctx:
            new_bot_profile(
                bot_id="bot-1", name="A", pairs=["BTCUSDT", "BTCUSDT"],
                blacklist=[], favorites=[], virtual_quote_budget="100",
            )
        self.assertEqual(ctx.exception.code, "BOT_PAIRS_INVALID")

    def test_blacklist_overlapping_pairs_rejected(self):
        with self.assertRaises(BotRegistryError) as ctx:
            new_bot_profile(
                bot_id="bot-1", name="A", pairs=["BTCUSDT"],
                blacklist=["BTCUSDT"], favorites=[], virtual_quote_budget="100",
            )
        self.assertEqual(ctx.exception.code, "BOT_BLACKLIST_CONFLICT")

    def test_favorite_outside_pairs_rejected(self):
        with self.assertRaises(BotRegistryError) as ctx:
            new_bot_profile(
                bot_id="bot-1", name="A", pairs=["BTCUSDT"],
                blacklist=[], favorites=["ETHUSDT"], virtual_quote_budget="100",
            )
        self.assertEqual(ctx.exception.code, "BOT_FAVORITES_INVALID")

    def test_bad_budget_rejected(self):
        with self.assertRaises(BotRegistryError) as ctx:
            new_bot_profile(
                bot_id="bot-1", name="A", pairs=["BTCUSDT"],
                blacklist=[], favorites=[], virtual_quote_budget="lots",
            )
        self.assertEqual(ctx.exception.code, "BOT_BUDGET_INVALID")

    def test_check_pair_verdicts(self):
        self.registry.register(new_bot_profile(
            bot_id="bot-1", name="A", pairs=["BTCUSDT"],
            blacklist=["LUNAUSDT"], favorites=[], virtual_quote_budget="100",
        ))
        self.assertEqual(
            self.registry.check_pair("bot-1", "BTCUSDT")[0], "ALLOWED"
        )
        verdict, reason = self.registry.check_pair("bot-1", "LUNAUSDT")
        self.assertEqual(verdict, "BLOCKED_BLACKLIST")
        self.assertTrue(reason)
        verdict, _ = self.registry.check_pair("bot-1", "ETHUSDT")
        self.assertEqual(verdict, "NOT_IN_SCOPE")
        with self.assertRaises(BotRegistryError):
            self.registry.check_pair("ghost", "BTCUSDT")

    def test_bind_session_confirms_ownership(self):
        self.registry.register(new_bot_profile(
            bot_id="bot-1", name="A", pairs=["BTCUSDT"],
            blacklist=[], favorites=[], virtual_quote_budget="100",
        ))
        self.assertEqual(
            self.registry.bind_session("bot-1", "sess-1", "BTCUSDT"), "BOUND"
        )
        self.assertEqual(self.registry.owner_of("sess-1"), "bot-1")
        # idempotent rebind of the same triple
        self.assertEqual(
            self.registry.bind_session("bot-1", "sess-1", "BTCUSDT"), "DUPLICATE"
        )

    def test_bind_blocked_pair_rejected(self):
        self.registry.register(new_bot_profile(
            bot_id="bot-1", name="A", pairs=["BTCUSDT"],
            blacklist=["LUNAUSDT"], favorites=[], virtual_quote_budget="100",
        ))
        with self.assertRaises(BotRegistryError) as ctx:
            self.registry.bind_session("bot-1", "sess-1", "LUNAUSDT")
        self.assertEqual(ctx.exception.code, "BOT_PAIR_BLOCKED")
        self.assertIsNone(self.registry.owner_of("sess-1"))

    def test_session_bound_to_two_bots_rejected(self):
        for bot in ("bot-1", "bot-2"):
            self.registry.register(new_bot_profile(
                bot_id=bot, name=bot, pairs=["BTCUSDT"],
                blacklist=[], favorites=[], virtual_quote_budget="100",
            ))
        self.registry.bind_session("bot-1", "sess-1", "BTCUSDT")
        with self.assertRaises(BotRegistryError) as ctx:
            self.registry.bind_session("bot-2", "sess-1", "BTCUSDT")
        self.assertEqual(ctx.exception.code, "BOT_SESSION_OWNED")

    def test_update_lists_keeps_invariants(self):
        self.registry.register(new_bot_profile(
            bot_id="bot-1", name="A", pairs=["BTCUSDT", "ETHUSDT"],
            blacklist=[], favorites=["BTCUSDT"], virtual_quote_budget="100",
        ))
        self.registry.update_lists("bot-1", blacklist=["LUNAUSDT"], favorites=["ETHUSDT"])
        stored = self.registry.get("bot-1")
        self.assertEqual(stored.blacklist, ("LUNAUSDT",))
        self.assertEqual(stored.favorites, ("ETHUSDT",))
        with self.assertRaises(BotRegistryError):
            self.registry.update_lists("bot-1", blacklist=["BTCUSDT"], favorites=[])
        # failed update leaves the stored profile untouched
        self.assertEqual(self.registry.get("bot-1").blacklist, ("LUNAUSDT",))

    def test_unknown_bot_access_rejected(self):
        with self.assertRaises(BotRegistryError) as ctx:
            self.registry.get("ghost")
        self.assertEqual(ctx.exception.code, "BOT_UNKNOWN")


if __name__ == "__main__":
    unittest.main()
