"""G3-multi (M1): symbols/max_active_deals parse + fiyat-bağımsız deal tavanı.

Elde hesap (base 100, SO 100x2, vol 1, fee 0.001, kuantum 1e-8):
siparişler [100, 100, 100], alt toplam 300, ücret tavanı
3 x ceil(0.1) = 0.3 -> spot tavan 300.3. 3x futures: marj
ceil(300/3)=100 -> 100.3. Vol 2: [100,100,200] -> 400.4 spot.
"""
import unittest
from fractions import Fraction as Q

from dcabot.application.sector_dca import (
    SectorDcaError,
    max_deal_quote_cost,
    parse_sector_dca,
)


def _raw(**overrides):
    body = dict(
        symbol="BTCUSDT", base_order="100", safety_order="100", max_safety_orders=2,
        max_active_safety_orders=None, price_deviation="10", safety_order_volume_scale="1",
        safety_order_step_scale="1", take_profit="5", stop_loss=None, direction="LONG",
        cooldown_seconds=0, min_price=None, max_price=None,
    )
    body.update(overrides)
    return body


class MultiParseTests(unittest.TestCase):
    def test_defaults_single_symbol_one_deal(self):
        params = parse_sector_dca(_raw())
        self.assertEqual(params.symbols, ("BTCUSDT",))
        self.assertEqual(params.max_active_deals, 1)

    def test_symbols_and_cap_accepted(self):
        params = parse_sector_dca(_raw(symbols=["BTCUSDT", "ETHUSDT"], max_active_deals=2))
        self.assertEqual(params.symbols, ("BTCUSDT", "ETHUSDT"))
        self.assertEqual(params.max_active_deals, 2)

    def test_symbols_rejected(self):
        for bad in (
            [],
            ["BTCUSDT"] * 2,
            ["ETHUSDT"],
            ["BTCUSDT", "ethusdt"],
            ["BTCUSDT", "X"],
            ["BTCUSDT"] + [f"SYM{i}USDT" for i in range(10)],
            "BTCUSDT",
            ["BTCUSDT", None],
        ):
            with self.assertRaises(SectorDcaError, msg=bad):
                parse_sector_dca(_raw(symbols=bad))

    def test_max_active_deals_rejected(self):
        for bad in (0, 11, True, "2", 1.5):
            with self.assertRaises(SectorDcaError, msg=bad):
                parse_sector_dca(_raw(symbols=["BTCUSDT", "ETHUSDT"], max_active_deals=bad))


class MaxDealQuoteCostTests(unittest.TestCase):
    def _cost(self, **overrides):
        params = parse_sector_dca(_raw(**overrides))
        return max_deal_quote_cost(params, fee_rate=Q(1, 1000), fee_quantum=Q(1, 10**8))

    def test_spot_flat_scale(self):
        self.assertEqual(self._cost(), Q("300.3"))

    def test_spot_volume_scale_two(self):
        self.assertEqual(self._cost(safety_order_volume_scale="2"), Q("400.4"))

    def test_futures_divides_and_ceils(self):
        params = parse_sector_dca(_raw(market_type="FUTURES", leverage=3))
        cost = max_deal_quote_cost(params, fee_rate=Q(1, 1000), fee_quantum=Q(1, 10**8))
        self.assertEqual(cost, Q("100.3"))

    def test_futures_ceil_up_not_down(self):
        params = parse_sector_dca(_raw(market_type="FUTURES", leverage=7))
        cost = max_deal_quote_cost(params, fee_rate=Q(1, 1000), fee_quantum=Q(1, 100))
        # 300/7 = 42.8571... -> 42.86 (cent up) + 0.30 fees.
        self.assertEqual(cost, Q("43.16"))

    def test_zero_safety_orders(self):
        self.assertEqual(self._cost(max_safety_orders=0), Q("100.1"))


if __name__ == "__main__":
    unittest.main()
