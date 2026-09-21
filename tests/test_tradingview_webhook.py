"""Faz 13: TradingView webhook alım katmanı (static-token + dedup kimliği)."""
import unittest

from dcabot.application.tradingview_webhook import (
    TradingViewWebhookError,
    canonical_alert_payload,
    parse_tradingview_alert,
    verify_webhook_token,
    webhook_dedup_key,
    webhook_signal_id,
)


def _alert(**overrides):
    body = {
        "secret": "t" * 32,
        "symbol": "BTCUSDT",
        "action": "BUY",
        "event_time_us": 1_700_000_000_000_000,
        "price": "81556.10",
    }
    body.update(overrides)
    return body


class TradingViewAlertParsingTests(unittest.TestCase):
    def test_valid_alert_parses_with_microsecond_time(self):
        alert = parse_tradingview_alert(_alert())
        self.assertEqual(alert.symbol, "BTCUSDT")
        self.assertEqual(alert.action, "BUY")
        self.assertEqual(alert.event_time_us, 1_700_000_000_000_000)
        self.assertEqual(alert.price, "81556.10")
        self.assertIsNone(alert.strategy_order_id)

    def test_iso8601_utc_time_converts_to_microseconds(self):
        alert = parse_tradingview_alert(_alert(event_time_us="2026-09-21T10:00:00Z"))
        self.assertEqual(alert.event_time_us, 1_789_984_800_000_000)

    def test_strategy_order_id_accepted_as_time_reference(self):
        alert = parse_tradingview_alert(_alert(strategy_order_id="long-entry-1"))
        self.assertEqual(alert.strategy_order_id, "long-entry-1")

    def test_rejects_non_object_and_unknown_fields(self):
        with self.assertRaises(TradingViewWebhookError) as ctx:
            parse_tradingview_alert(["not-an-object"])
        self.assertEqual(ctx.exception.code, "WEBHOOK_BODY_INVALID")
        with self.assertRaises(TradingViewWebhookError) as ctx:
            parse_tradingview_alert(_alert(extra="nope"))
        self.assertEqual(ctx.exception.code, "WEBHOOK_FIELD_UNKNOWN")

    def test_rejects_bad_symbol_action_price_and_time(self):
        for field, value, code in (
            ("symbol", "btc usdt!", "WEBHOOK_SYMBOL_INVALID"),
            ("action", "", "WEBHOOK_ACTION_INVALID"),
            ("price", "12.34.56", "WEBHOOK_PRICE_INVALID"),
            ("event_time_us", -5, "WEBHOOK_TIME_INVALID"),
            ("event_time_us", "21/09/2026", "WEBHOOK_TIME_INVALID"),
            ("event_time_us", "2026-09-21T10:00:00", "WEBHOOK_TIME_INVALID"),
        ):
            with self.subTest(field=field, value=value):
                with self.assertRaises(TradingViewWebhookError) as ctx:
                    parse_tradingview_alert(_alert(**{field: value}))
                self.assertEqual(ctx.exception.code, code)

    def test_secret_is_not_part_of_the_parsed_alert(self):
        alert = parse_tradingview_alert(_alert())
        self.assertNotIn("t" * 32, repr(alert))


class WebhookTokenTests(unittest.TestCase):
    def test_matching_token_verifies(self):
        verify_webhook_token(presented="s" * 32, expected="s" * 32)

    def test_mismatch_and_missing_values_fail_closed_without_detail(self):
        for presented, expected in (
            ("s" * 32, "q" * 32),
            ("", "q" * 32),
            ("s" * 32, ""),
            (None, "q" * 32),
        ):
            with self.subTest(presented=presented):
                with self.assertRaises(TradingViewWebhookError) as ctx:
                    verify_webhook_token(presented=presented, expected=expected)
                self.assertEqual(ctx.exception.code, "WEBHOOK_TOKEN_MISMATCH")
                self.assertNotIn("q" * 8, str(ctx.exception))


class WebhookIdentityTests(unittest.TestCase):
    def test_same_alert_same_key_and_signal_id(self):
        first = parse_tradingview_alert(_alert())
        second = parse_tradingview_alert(_alert())
        self.assertEqual(webhook_dedup_key(first), webhook_dedup_key(second))
        self.assertEqual(webhook_signal_id(first), webhook_signal_id(second))
        self.assertTrue(webhook_signal_id(first).startswith("tv-"))

    def test_strategy_order_id_distinguishes_same_bar_alerts(self):
        plain = parse_tradingview_alert(_alert())
        with_id = parse_tradingview_alert(_alert(strategy_order_id="x-1"))
        self.assertNotEqual(webhook_dedup_key(plain), webhook_dedup_key(with_id))

    def test_different_price_same_bar_keeps_same_key(self):
        first = parse_tradingview_alert(_alert(price="100"))
        second = parse_tradingview_alert(_alert(price="101"))
        self.assertEqual(webhook_dedup_key(first), webhook_dedup_key(second))

    def test_canonical_payload_hashes_stably(self):
        from dcabot.application.signal_intake import hash_signal_payload

        first = parse_tradingview_alert(_alert())
        second = parse_tradingview_alert(_alert(price="999"))
        self.assertEqual(
            hash_signal_payload(canonical_alert_payload(first)),
            hash_signal_payload(canonical_alert_payload(first)),
        )
        self.assertNotEqual(
            hash_signal_payload(canonical_alert_payload(first)),
            hash_signal_payload(canonical_alert_payload(second)),
        )
