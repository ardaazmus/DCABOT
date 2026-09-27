"""Faz 17 (bug fix, 2026-09-23): `spot_binding_store.py`'nin State
serileştirmesi H.1/H.2/I.1'den (ladder_start_qty, now_us,
deal_started_at_us, deal_duration_expired, sl_breach_streak,
profit_cost_recovered, retained_profit_base) önce yazılmıştı ve bu 7 alanı
her save/reload round-trip'inde sessizce düşürüyordu. Bu test dosyası bu
düzeltmeyi kanıtlıyor -- gerçek bir sessiz veri-kaybı hatasıydı."""
import json
from fractions import Fraction as F
from pathlib import Path
import tempfile
import unittest

from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply
from dcabot.persistence.spot_binding_store import _decode_state, _state_payload

ROOT = Path(__file__).resolve().parents[1]


def raw_config(**updates):
    raw = json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))
    raw.update(updates)
    return raw


class StatePayloadRoundTripTests(unittest.TestCase):
    def test_sl_breach_streak_survives_round_trip(self):
        config = Config.parse(raw_config(stop_loss_rate="0.05", stop_loss_confirmation_bars=2))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = apply(
            state,
            {"type": "INTENT", "order_id": "base", "role": "BASE", "qty": "1", "limit_price": "100"},
            config,
        )
        side = state.orders["base"].side
        state = apply(
            state,
            {"type": "FILL", "execution_id": "base-fill", "order_id": "base", "side": side,
             "qty": "1", "price": "100", "fee": "0", "fee_asset": "USDT"},
            config,
        )
        state = apply(
            state,
            {"type": "ORDER_FINAL", "order_id": "base", "status": "FILLED", "filled_qty": "1", "coverage_complete": True},
            config,
        )
        state = apply(state, {"type": "BAR_CLOSE", "close": "94"}, config)
        self.assertEqual(state.sl_breach_streak, 1)
        restored = _decode_state(_state_payload(state))
        self.assertEqual(restored.sl_breach_streak, 1)

    def test_trail_water_survives_round_trip(self):
        # F09a: armed trailing water (here 105.5 at/above the 105 TP
        # target) must survive save/reload, or a restart silently
        # disarms an in-profit deal's ratchet.
        config = Config.parse(raw_config(take_profit="0.05", trailing_take_profit_rate="0.01"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = apply(
            state,
            {"type": "INTENT", "order_id": "base", "role": "BASE", "qty": "1", "limit_price": "100"},
            config,
        )
        side = state.orders["base"].side
        state = apply(
            state,
            {"type": "FILL", "execution_id": "base-fill", "order_id": "base", "side": side,
             "qty": "1", "price": "100", "fee": "0", "fee_asset": "USDT"},
            config,
        )
        state = apply(
            state,
            {"type": "ORDER_FINAL", "order_id": "base", "status": "FILLED", "filled_qty": "1", "coverage_complete": True},
            config,
        )
        state = apply(state, {"type": "BAR_CLOSE", "close": "105.5"}, config)
        self.assertEqual(state.trail_water, F("105.5"))
        restored = _decode_state(_state_payload(state))
        self.assertEqual(restored.trail_water, F("105.5"))

    def test_clock_fields_survive_round_trip(self):
        config = Config.parse(
            raw_config(max_deal_duration_seconds=3600, max_deal_duration_action="WARN_ONLY")
        )
        state = apply(State(), {"type": "CLOCK", "now_us": 1000}, config)
        state = apply(state, {"type": "CLOCK", "now_us": 3600 * 1_000_000 + 1000}, config)
        restored = _decode_state(_state_payload(state))
        self.assertEqual(restored.now_us, state.now_us)
        self.assertEqual(restored.deal_started_at_us, state.deal_started_at_us)
        self.assertEqual(restored.deal_duration_expired, state.deal_duration_expired)

    def test_default_state_round_trips_with_new_fields_at_their_defaults(self):
        config = Config.parse(raw_config())
        state = State()
        restored = _decode_state(_state_payload(state))
        self.assertIsNone(restored.ladder_start_qty)
        self.assertIsNone(restored.now_us)
        self.assertIsNone(restored.deal_started_at_us)
        self.assertFalse(restored.deal_duration_expired)
        self.assertEqual(restored.sl_breach_streak, 0)
        self.assertIsNone(restored.trail_water)
        self.assertFalse(restored.profit_cost_recovered)
        self.assertEqual(restored.retained_profit_base, F(0))

    def test_old_payload_missing_new_fields_still_decodes_with_defaults(self):
        # Simulates a record written before H.1/H.2/I.1 existed.
        state = State()
        payload = _state_payload(state)
        for key in (
            "ladder_start_qty", "now_us", "deal_started_at_us",
            "deal_duration_expired", "sl_breach_streak", "trail_water",
            "profit_cost_recovered", "retained_profit_base",
        ):
            del payload[key]
        restored = _decode_state(payload)
        self.assertEqual(restored.sl_breach_streak, 0)
        self.assertIsNone(restored.trail_water)
        self.assertEqual(restored.retained_profit_base, F(0))

    def test_unknown_extra_field_is_still_rejected(self):
        state = State()
        payload = _state_payload(state)
        payload["not_a_real_field"] = 1
        with self.assertRaises(ValueError):
            _decode_state(payload)


if __name__ == "__main__":
    unittest.main()
