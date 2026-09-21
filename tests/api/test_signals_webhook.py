"""Faz 13: TradingView webhook API — hızlı-ACK kabul + ayrı bind adımı."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dcabot.persistence.webhook_dedup_store import WebhookDedupStore
from dcabot.server.api import (
    _validate_tradingview_webhook_payload,
    _validate_webhook_bind_payload,
    _webhook_accept,
    _webhook_bind,
    _webhook_expected_token,
    _webhook_list,
    _webhook_status,
)


def _body(**overrides):
    body = {
        "secret": "t" * 32,
        "symbol": "BTCUSDT",
        "action": "BUY",
        "event_time_us": 1_700_000_000_000_000,
        "price": "81556.10",
    }
    body.update(overrides)
    return body


def _bind_body(**overrides):
    body = {
        "closed_bar_time_us": 1_700_000_000_000_000,
        "warmup_bars_observed": 10,
        "required_warmup_bars": 5,
        "max_staleness_us": 5_000_000,
        "action_map": [["BUY", "BUY"], ["SELL", "SELL"]],
        "qty": "0.01",
        "ttl_us": 60_000_000,
    }
    body.update(overrides)
    return body


class WebhookTokenGateTests(unittest.TestCase):
    def test_missing_env_means_not_configured(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DCABOT_TRADINGVIEW_WEBHOOK_TOKEN", None)
            self.assertIsNone(_webhook_expected_token())

    def test_blank_env_means_not_configured(self):
        with patch.dict(os.environ, {"DCABOT_TRADINGVIEW_WEBHOOK_TOKEN": "   "}):
            self.assertIsNone(_webhook_expected_token())

    def test_configured_token_is_returned_verbatim(self):
        with patch.dict(os.environ, {"DCABOT_TRADINGVIEW_WEBHOOK_TOKEN": "x" * 40}):
            self.assertEqual(_webhook_expected_token(), "x" * 40)


class WebhookAcceptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = WebhookDedupStore(Path(self.tmp.name) / "webhook.db")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_validate_accepts_minimal_tradingview_shape(self):
        validated, fields = _validate_tradingview_webhook_payload(_body())
        self.assertEqual(fields, {})
        assert validated is not None
        self.assertEqual(validated["symbol"], "BTCUSDT")

    def test_validate_rejects_unknown_and_bad_fields(self):
        _, fields = _validate_tradingview_webhook_payload(_body(nope=1))
        self.assertIn("body", fields)
        _, fields = _validate_tradingview_webhook_payload(_body(symbol=123))
        self.assertIn("symbol", fields)
        validated, fields = _validate_tradingview_webhook_payload(_body(symbol="!!!"))
        self.assertEqual(fields, {})
        assert validated is not None
        from dcabot.application.tradingview_webhook import TradingViewWebhookError

        with self.assertRaises(TradingViewWebhookError) as ctx:
            _webhook_accept(self.store, validated, 1_700_000_000_100_000)
        self.assertEqual(ctx.exception.code, "WEBHOOK_SYMBOL_INVALID")

    def test_accept_returns_hash_and_dedup_status(self):
        validated, _ = _validate_tradingview_webhook_payload(_body())
        assert validated is not None
        first = _webhook_accept(self.store, validated, 1_700_000_000_100_000)
        self.assertEqual(first["status"], "ACCEPTED")
        self.assertTrue(first["signal_id"].startswith("tv-"))
        self.assertEqual(len(first["payload_hash"]), 64)
        second = _webhook_accept(self.store, validated, 1_700_000_000_200_000)
        self.assertEqual(second["status"], "DUPLICATE")
        self.assertEqual(second["signal_id"], first["signal_id"])

    def test_accept_never_echoes_the_secret(self):
        validated, _ = _validate_tradingview_webhook_payload(_body())
        assert validated is not None
        result = _webhook_accept(self.store, validated, 1_700_000_000_100_000)
        self.assertNotIn("t" * 32, repr(result))


class WebhookBindTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = WebhookDedupStore(Path(self.tmp.name) / "webhook.db")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def _accepted_signal_id(self):
        validated, _ = _validate_tradingview_webhook_payload(_body())
        assert validated is not None
        return _webhook_accept(self.store, validated, 1_700_000_000_100_000)["signal_id"]

    def test_bind_consumes_stored_intake_into_candidate(self):
        signal_id = self._accepted_signal_id()
        validated, fields = _validate_webhook_bind_payload(_bind_body())
        self.assertEqual(fields, {})
        assert validated is not None
        result = _webhook_bind(self.store, signal_id, validated, 1_700_000_001_000_000)
        self.assertEqual(result["signal_id"], signal_id)
        self.assertEqual(result["side"], "BUY")
        self.assertEqual(result["qty"], "0.01")
        row = self.store.get_intake(signal_id)
        assert row is not None
        self.assertEqual(row["status"], "BOUND")

    def test_bind_unknown_signal_is_not_found(self):
        validated, _ = _validate_webhook_bind_payload(_bind_body())
        assert validated is not None
        with self.assertRaises(LookupError):
            _webhook_bind(self.store, "tv-missing", validated, 1_700_000_001_000_000)

    def test_bind_rejects_unmapped_action(self):
        signal_id = self._accepted_signal_id()
        validated, _ = _validate_webhook_bind_payload(_bind_body(action_map=[["SELL", "SELL"]]))
        assert validated is not None
        with self.assertRaises(ValueError):
            _webhook_bind(self.store, signal_id, validated, 1_700_000_001_000_000)


class WebhookStatusListTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = WebhookDedupStore(Path(self.tmp.name) / "webhook.db")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_status_reports_configured_without_secret(self):
        with patch.dict(os.environ, {"DCABOT_TRADINGVIEW_WEBHOOK_TOKEN": "s" * 40}):
            result = _webhook_status()
        self.assertEqual(result, {"configured": True})
        self.assertNotIn("s" * 40, repr(result))
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DCABOT_TRADINGVIEW_WEBHOOK_TOKEN", None)
            self.assertEqual(_webhook_status(), {"configured": False})

    def test_list_returns_stored_intakes_newest_first(self):
        validated, _ = _validate_tradingview_webhook_payload(_body())
        assert validated is not None
        first = _webhook_accept(self.store, validated, 100)
        validated2, _ = _validate_tradingview_webhook_payload(
            _body(action="SELL", event_time_us=1_700_000_001_000_000)
        )
        assert validated2 is not None
        second = _webhook_accept(self.store, validated2, 200)
        result = _webhook_list(self.store, 10)
        self.assertEqual(
            [row["signal_id"] for row in result["intakes"]],
            [second["signal_id"], first["signal_id"]],
        )
        self.assertNotIn("secret", repr(result))

    def test_list_clamps_limit(self):
        with self.assertRaises(ValueError):
            _webhook_list(self.store, 0)
        with self.assertRaises(ValueError):
            _webhook_list(self.store, 500)
