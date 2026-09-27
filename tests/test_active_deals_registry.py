"""Faz 17 I.2 (RG-12): Max Active Deals -- account/bot/pair concurrency
registry. Over any limit rejects (never queues); each limit is independent
and `None` means unlimited."""
import unittest

from dcabot.application.active_deals_registry import ActiveDealsError, ActiveDealsRegistry


def _none() -> dict:
    return {
        "max_active_deals_account": None,
        "max_active_deals_per_bot": None,
        "allowed_deals_on_same_pair": None,
    }


class BasicOpenCloseTests(unittest.TestCase):
    def test_first_open_succeeds(self):
        reg = ActiveDealsRegistry()
        reg.try_open(deal_id="d1", bot_id="bot-1", symbol="BTCUSDT", **_none())
        self.assertEqual(reg.count_account(), 1)
        self.assertEqual(reg.count_for_bot("bot-1"), 1)
        self.assertEqual(reg.count_for_symbol("BTCUSDT"), 1)

    def test_duplicate_deal_id_is_rejected(self):
        reg = ActiveDealsRegistry()
        reg.try_open(deal_id="d1", bot_id="bot-1", symbol="BTCUSDT", **_none())
        with self.assertRaises(ActiveDealsError) as ctx:
            reg.try_open(deal_id="d1", bot_id="bot-2", symbol="ETHUSDT", **_none())
        self.assertEqual(ctx.exception.code, "ACTIVE_DEALS_DUPLICATE")

    def test_close_frees_all_counters(self):
        reg = ActiveDealsRegistry()
        reg.try_open(deal_id="d1", bot_id="bot-1", symbol="BTCUSDT", **_none())
        reg.close(deal_id="d1", bot_id="bot-1", symbol="BTCUSDT")
        self.assertEqual(reg.count_account(), 0)
        self.assertEqual(reg.count_for_bot("bot-1"), 0)
        self.assertEqual(reg.count_for_symbol("BTCUSDT"), 0)

    def test_close_unopened_deal_is_rejected(self):
        reg = ActiveDealsRegistry()
        with self.assertRaises(ActiveDealsError) as ctx:
            reg.close(deal_id="ghost", bot_id="bot-1", symbol="BTCUSDT")
        self.assertEqual(ctx.exception.code, "ACTIVE_DEALS_NOT_OPEN")


class AccountLimitTests(unittest.TestCase):
    def test_account_limit_rejects_the_nth_plus_one_deal(self):
        reg = ActiveDealsRegistry()
        limits = {**_none(), "max_active_deals_account": 2}
        reg.try_open(deal_id="d1", bot_id="bot-1", symbol="BTCUSDT", **limits)
        reg.try_open(deal_id="d2", bot_id="bot-2", symbol="ETHUSDT", **limits)
        with self.assertRaises(ActiveDealsError) as ctx:
            reg.try_open(deal_id="d3", bot_id="bot-3", symbol="SOLUSDT", **limits)
        self.assertEqual(ctx.exception.code, "ACTIVE_DEALS_ACCOUNT_LIMIT")

    def test_closing_one_frees_a_slot_for_a_new_one(self):
        reg = ActiveDealsRegistry()
        limits = {**_none(), "max_active_deals_account": 1}
        reg.try_open(deal_id="d1", bot_id="bot-1", symbol="BTCUSDT", **limits)
        with self.assertRaises(ActiveDealsError):
            reg.try_open(deal_id="d2", bot_id="bot-2", symbol="ETHUSDT", **limits)
        reg.close(deal_id="d1", bot_id="bot-1", symbol="BTCUSDT")
        reg.try_open(deal_id="d2", bot_id="bot-2", symbol="ETHUSDT", **limits)
        self.assertEqual(reg.count_account(), 1)


class PerBotLimitTests(unittest.TestCase):
    def test_bot_limit_is_independent_of_other_bots(self):
        reg = ActiveDealsRegistry()
        limits = {**_none(), "max_active_deals_per_bot": 1}
        reg.try_open(deal_id="d1", bot_id="bot-1", symbol="BTCUSDT", **limits)
        # Different bot, same account -- not affected by bot-1's limit.
        reg.try_open(deal_id="d2", bot_id="bot-2", symbol="ETHUSDT", **limits)
        with self.assertRaises(ActiveDealsError) as ctx:
            reg.try_open(deal_id="d3", bot_id="bot-1", symbol="ADAUSDT", **limits)
        self.assertEqual(ctx.exception.code, "ACTIVE_DEALS_BOT_LIMIT")


class SamePairLimitTests(unittest.TestCase):
    def test_pair_limit_allows_different_symbols_freely(self):
        reg = ActiveDealsRegistry()
        limits = {**_none(), "allowed_deals_on_same_pair": 1}
        reg.try_open(deal_id="d1", bot_id="bot-1", symbol="BTCUSDT", **limits)
        reg.try_open(deal_id="d2", bot_id="bot-2", symbol="ETHUSDT", **limits)
        with self.assertRaises(ActiveDealsError) as ctx:
            reg.try_open(deal_id="d3", bot_id="bot-3", symbol="BTCUSDT", **limits)
        self.assertEqual(ctx.exception.code, "ACTIVE_DEALS_PAIR_LIMIT")


class CombinedLimitsTests(unittest.TestCase):
    def test_all_three_limits_enforced_together_most_restrictive_wins(self):
        reg = ActiveDealsRegistry()
        limits = {
            "max_active_deals_account": 5,
            "max_active_deals_per_bot": 1,
            "allowed_deals_on_same_pair": 5,
        }
        reg.try_open(deal_id="d1", bot_id="bot-1", symbol="BTCUSDT", **limits)
        with self.assertRaises(ActiveDealsError) as ctx:
            reg.try_open(deal_id="d2", bot_id="bot-1", symbol="ETHUSDT", **limits)
        self.assertEqual(ctx.exception.code, "ACTIVE_DEALS_BOT_LIMIT")


class InputValidationTests(unittest.TestCase):
    def test_invalid_limit_values_are_rejected(self):
        reg = ActiveDealsRegistry()
        with self.assertRaises(ActiveDealsError):
            reg.try_open(
                deal_id="d1", bot_id="bot-1", symbol="BTCUSDT",
                max_active_deals_account=0, max_active_deals_per_bot=None, allowed_deals_on_same_pair=None,
            )
        with self.assertRaises(ActiveDealsError):
            reg.try_open(
                deal_id="d1", bot_id="bot-1", symbol="BTCUSDT",
                max_active_deals_account=None, max_active_deals_per_bot=-1, allowed_deals_on_same_pair=None,
            )


if __name__ == "__main__":
    unittest.main()
