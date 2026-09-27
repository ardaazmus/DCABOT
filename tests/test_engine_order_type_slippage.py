"""Faz 17 G.2-motor (RG-07): per-role Market/Limit order type, a single live
`max_adverse_slippage_bps` policy bound (enforced at INTENT time against the
worst-case declared price), and `realized_slippage` as a pure post-fact
accounting output (never an input). LIMIT-only regression (all defaults) must
stay byte-for-byte identical to pre-G.2 behavior.
"""
import json
from fractions import Fraction as F
from pathlib import Path
import unittest

from dcabot.domain.config import Config
from dcabot.domain.engine import State, apply

ROOT = Path(__file__).resolve().parents[1]


def raw_config(**updates):
    raw = json.loads((ROOT / "config/paper.json").read_text(encoding="utf-8"))
    raw.update(updates)
    return raw


def _base_intent(state, config, price="100"):
    return apply(
        state,
        {"type": "INTENT", "order_id": "base", "role": "BASE", "qty": "1", "limit_price": price},
        config,
    )


def _fill(state, config, order_id, side, qty, price, fee="0"):
    return apply(
        state,
        {
            "type": "FILL",
            "execution_id": f"{order_id}-{price}-{qty}",
            "order_id": order_id,
            "side": side,
            "qty": qty,
            "price": price,
            "fee": fee,
            "fee_asset": "USDT",
        },
        config,
    )


class LimitDefaultRegressionTests(unittest.TestCase):
    def test_default_order_type_is_limit_everywhere(self):
        config = Config.parse(raw_config())
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_intent(state, config)
        self.assertEqual(state.orders["base"].order_type, "LIMIT")
        self.assertEqual(state.orders["base"].reference_price, F(100))

    def test_limit_fill_at_the_limit_has_zero_realized_slippage(self):
        config = Config.parse(raw_config())
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_intent(state, config)
        state = _fill(state, config, "base", "BUY", "1", "100")
        self.assertEqual(state.orders["base"].realized_slippage, F(0))

    def test_limit_fill_better_than_limit_has_negative_realized_slippage(self):
        config = Config.parse(raw_config(base_order_type="LIMIT"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        # BASE intent side is BUY (LONG); declaring a limit of 100 but the
        # execution reports a better (lower) price is a legitimate maker fill.
        state = _base_intent(state, config, price="100")
        state = _fill(state, config, "base", "BUY", "1", "99")
        self.assertEqual(state.orders["base"].realized_slippage, F(-1, 100))


class MarketOrderTypeTests(unittest.TestCase):
    def test_market_requires_config_bound_to_parse(self):
        with self.assertRaises(ValueError):
            Config.parse(raw_config(base_order_type="MARKET"))

    def test_market_worst_case_bound_within_policy_is_accepted(self):
        config = Config.parse(raw_config(base_order_type="MARKET", max_adverse_slippage_bps="100"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        # 100bps = 1% -> worst case buy bound = 101.
        state = _base_intent(state, config, price="101")
        self.assertEqual(state.orders["base"].order_type, "MARKET")
        self.assertEqual(state.orders["base"].reference_price, F(100))

    def test_market_worst_case_bound_exceeding_policy_is_rejected(self):
        config = Config.parse(raw_config(base_order_type="MARKET", max_adverse_slippage_bps="100"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        with self.assertRaises(ValueError):
            # 101.01 > 101 (the 100bps worst-case bound) -- rejected at INTENT.
            _base_intent(state, config, price="101.01")

    def test_market_fill_within_bound_records_positive_realized_slippage(self):
        config = Config.parse(raw_config(base_order_type="MARKET", max_adverse_slippage_bps="100"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_intent(state, config, price="101")
        state = _fill(state, config, "base", "BUY", "1", "100.5")
        self.assertEqual(state.orders["base"].realized_slippage, F(1, 200))  # (100.5-100)/100

    def test_fill_still_cannot_cross_the_declared_worst_case_bound(self):
        config = Config.parse(raw_config(base_order_type="MARKET", max_adverse_slippage_bps="100"))
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        state = _base_intent(state, config, price="101")
        with self.assertRaises(ValueError):
            _fill(state, config, "base", "BUY", "1", "101.5")

    def test_short_market_base_worst_case_bound_is_a_lower_price(self):
        config = Config.parse(
            raw_config(direction="SHORT", base_order_type="MARKET", max_adverse_slippage_bps="100")
        )
        state = apply(State(), {"type": "MARK", "price": "100"}, config)
        # SHORT base opens by SELLing; adverse = lower price. 100bps -> floor 99.
        state = _base_intent(state, config, price="99")
        self.assertEqual(state.orders["base"].side, "SELL")
        with self.assertRaises(ValueError):
            _base_intent(
                apply(State(), {"type": "MARK", "price": "100"}, config), config, price="98.99"
            )


if __name__ == "__main__":
    unittest.main()
