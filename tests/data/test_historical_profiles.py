import json
from pathlib import Path
import unittest

from dcabot.application.historical_profiles import (
    HistoricalProfileError,
    get_historical_profile,
    list_historical_profiles,
    load_historical_profile_config,
)
from dcabot.domain.config import Config


class HistoricalProfileTests(unittest.TestCase):
    def test_registry_is_bounded_and_contains_separate_demo_profile(self):
        profiles = list_historical_profiles()

        self.assertEqual(
            tuple(profile.profile_id for profile in profiles),
            (
                "paper",
                "historical_demo_btcusdt_1h_v1",
                "historical_demo_btcusdt_1h_partial_fixed_v1",
            ),
        )
        demo = get_historical_profile("historical_demo_btcusdt_1h_v1")
        self.assertEqual(demo.label, "Historical demo — BTCUSDT 1h (v1)")
        self.assertEqual(demo.expected_dataset_id, "binance-spot-klines-v1-btcusdt-1h-2025-01-01")
        self.assertEqual(demo.venue_filter_provenance, "project_fixture")
        self.assertFalse(demo.historical_filter_claim)
        fixed = get_historical_profile("historical_demo_btcusdt_1h_partial_fixed_v1")
        self.assertEqual(fixed.simulation_model, "historical_ohlcv_partial_fixed_v1")
        self.assertEqual(fixed.slice_qty, "0.001")

    def test_demo_config_is_valid_and_does_not_mutate_paper_config(self):
        root = Path.cwd()
        profile, demo_config = load_historical_profile_config(root, "historical_demo_btcusdt_1h_v1")

        Config.parse(demo_config)
        paper_config = json.loads((root / "config" / "paper.json").read_text(encoding="utf-8"))
        self.assertEqual((demo_config["base_qty"], demo_config["safety_qty"]), ("0.004", "0.003"))
        self.assertEqual((paper_config["base_qty"], paper_config["safety_qty"]), ("1", "1"))
        self.assertEqual(profile.profile_id, "historical_demo_btcusdt_1h_v1")

    def test_unknown_or_path_like_profile_is_rejected(self):
        with self.assertRaises(HistoricalProfileError) as unknown:
            get_historical_profile("unknown")
        self.assertEqual(unknown.exception.code, "PROFILE_NOT_FOUND")

        with self.assertRaises(HistoricalProfileError) as invalid:
            get_historical_profile("../paper")
        self.assertEqual(invalid.exception.code, "PROFILE_ID_INVALID")
