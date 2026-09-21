"""Faz 13.4: iç/relay istemciler için HMAC korumalı intake (TradingView ucundan ayrı)."""
import hashlib
import hmac
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dcabot.application.signal_intake import hash_signal_payload
from dcabot.application.tradingview_webhook import canonical_alert_payload, parse_internal_alert
from dcabot.persistence.webhook_dedup_store import WebhookDedupStore
from dcabot.server.api import (
    _relay_keys,
    _validate_internal_intake_payload,
    _webhook_accept_internal,
)

KEY_ID = "relay-1"
KEY_HEX = "ab" * 32


def _sign(payload_hash: str) -> str:
    return hmac.new(bytes.fromhex(KEY_HEX), payload_hash.encode("ascii"), hashlib.sha256).hexdigest()


def _body(**overrides):
    alert = parse_internal_alert(
        {
            "symbol": "BTCUSDT",
            "action": "BUY",
            "event_time_us": 1_700_000_000_000_000,
            "price": "81556.10",
        }
    )
    payload_hash = hash_signal_payload(canonical_alert_payload(alert))
    body = {
        "symbol": "BTCUSDT",
        "action": "BUY",
        "event_time_us": 1_700_000_000_000_000,
        "price": "81556.10",
        "key_id": KEY_ID,
        "signature": _sign(payload_hash),
    }
    body.update(overrides)
    return body


class RelayKeysTests(unittest.TestCase):
    def test_missing_or_invalid_env_is_empty(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DCABOT_SIGNAL_RELAY_KEYS", None)
            self.assertEqual(_relay_keys(), {})
        with patch.dict(os.environ, {"DCABOT_SIGNAL_RELAY_KEYS": "not-json"}):
            self.assertEqual(_relay_keys(), {})

    def test_valid_json_maps_key_ids(self):
        with patch.dict(os.environ, {"DCABOT_SIGNAL_RELAY_KEYS": '{"relay-1": "ab"}'}):
            self.assertEqual(_relay_keys(), {"relay-1": "ab"})


class InternalAlertParsingTests(unittest.TestCase):
    def test_secret_free_shape_parses(self):
        alert = parse_internal_alert(
            {"symbol": "BTCUSDT", "action": "SELL", "event_time_us": 5, "strategy_order_id": "x"}
        )
        self.assertEqual(alert.source, "internal-relay")
        self.assertEqual(alert.strategy_order_id, "x")

    def test_secret_field_rejected(self):
        from dcabot.application.tradingview_webhook import TradingViewWebhookError

        with self.assertRaises(TradingViewWebhookError):
            parse_internal_alert({"symbol": "BTCUSDT", "action": "B", "event_time_us": 5, "secret": "x"})


class InternalIntakeApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = WebhookDedupStore(Path(self.tmp.name) / "webhook.db")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_valid_hmac_accepts_and_dedups(self):
        validated, fields = _validate_internal_intake_payload(_body())
        self.assertEqual(fields, {})
        assert validated is not None
        keys = {KEY_ID: KEY_HEX}
        first = _webhook_accept_internal(self.store, validated, keys, 100)
        self.assertEqual(first["status"], "ACCEPTED")
        self.assertTrue(first["signal_id"].startswith("tv-"))
        second = _webhook_accept_internal(self.store, validated, keys, 200)
        self.assertEqual(second["status"], "DUPLICATE")

    def test_bad_signature_fails_closed(self):
        from dcabot.application.signal_intake import SignalIntakeError

        validated, fields = _validate_internal_intake_payload(_body(signature="0" * 64))
        self.assertEqual(fields, {})
        assert validated is not None
        with self.assertRaises(SignalIntakeError):
            _webhook_accept_internal(self.store, validated, {KEY_ID: KEY_HEX}, 100)

    def test_unknown_key_fails_closed(self):
        from dcabot.application.signal_intake import SignalIntakeError

        validated, fields = _validate_internal_intake_payload(_body(key_id="nope"))
        self.assertEqual(fields, {})
        assert validated is not None
        with self.assertRaises(SignalIntakeError):
            _webhook_accept_internal(self.store, validated, {KEY_ID: KEY_HEX}, 100)

    def test_internal_and_tradingview_streams_do_not_collide(self):
        from dcabot.server.api import _validate_tradingview_webhook_payload, _webhook_accept

        tv, _ = _validate_tradingview_webhook_payload(
            {
                "secret": "t" * 32,
                "symbol": "BTCUSDT",
                "action": "BUY",
                "event_time_us": 1_700_000_000_000_000,
                "price": "81556.10",
            }
        )
        assert tv is not None
        internal, _ = _validate_internal_intake_payload(_body())
        assert internal is not None
        tv_result = _webhook_accept(self.store, tv, 100)
        internal_result = _webhook_accept_internal(self.store, internal, {KEY_ID: KEY_HEX}, 200)
        self.assertEqual(tv_result["status"], "ACCEPTED")
        self.assertEqual(internal_result["status"], "ACCEPTED")
        self.assertNotEqual(tv_result["signal_id"], internal_result["signal_id"])
