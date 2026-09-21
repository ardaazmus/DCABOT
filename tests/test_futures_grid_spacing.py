"""Faz 12.3: grid başına brüt aralık yüzdesi (fee/funding hariç, exact)."""
import unittest

from dcabot.application.futures_grid_levels import (
    FuturesGridProfile,
    project_futures_grid_levels,
    project_gross_spacing_percent,
)


def _projection(level_mode="ARITHMETIC", lower="100", upper="200", count=2):
    return project_futures_grid_levels(
        profile=FuturesGridProfile(),
        direction="NEUTRAL",
        initial_position_policy="FLAT",
        level_mode=level_mode,
        lower_price=lower,
        upper_price=upper,
        interval_count=count,
        price_tick="1",
        tick_origin="0",
    )


class GrossSpacingPercentTests(unittest.TestCase):
    def test_arithmetic_spacing_is_step_over_lower(self):
        result = project_gross_spacing_percent(_projection())
        self.assertEqual(result, {"percent": "50", "exact": True})

    def test_geometric_spacing_is_ratio_minus_one(self):
        projection = _projection(level_mode="GEOMETRIC", lower="100", upper="225", count=2)
        result = project_gross_spacing_percent(projection)
        self.assertEqual(result, {"percent": "50", "exact": True})

    def test_repeating_decimal_is_disclosed_not_silent(self):
        projection = _projection(lower="300", upper="400", count=2)
        result = project_gross_spacing_percent(projection)
        self.assertEqual(result, {"percent": "16.666666666667", "exact": False})
