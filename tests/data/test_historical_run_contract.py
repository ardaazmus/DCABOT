import json
from dataclasses import replace
from pathlib import Path
import unittest

from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput, HistoricalDatasetMetadata
from dcabot.domain.config import Config


def _raw_config() -> dict[str, object]:
    return json.loads(Path("config/paper.json").read_text(encoding="utf-8"))


def _dataset() -> HistoricalDatasetInput:
    return HistoricalDatasetInput(
        metadata=HistoricalDatasetMetadata(
            dataset_id="synthetic-btcusdt-1h",
            source_id="synthetic-source",
            symbol="BTCUSDT",
            interval="1h",
            period_start="2025-01-01",
            period_end="2025-01-10",
            artifact_sha256="a" * 64,
            artifact_bytes=1,
            timestamp_unit="microseconds",
            timezone="UTC",
        ),
        bars=(
            CanonicalBar(0, 3_599_999_999, "100", "100", "100", "100", "1", True),
            CanonicalBar(3_600_000_000, 7_199_999_999, "99", "100", "99", "99", "1", True),
        ),
    )


class HistoricalRunContractTests(unittest.TestCase):
    def test_capture_contains_full_safe_config_and_canonical_input(self):
        from dcabot.application.historical_run_contract import build_historical_run_capture
        from dcabot.application.historical_simulation import simulate_historical_ohlcv
        from dcabot.application.historical import build_historical_run_plan

        raw_config = _raw_config()
        dataset = _dataset()
        config = Config.parse(raw_config)
        config_hash = build_historical_run_plan(dataset, raw_config).config.config_hash
        result = simulate_historical_ohlcv(dataset, config, config_hash=config_hash)

        capture = build_historical_run_capture(dataset, raw_config, result, config_hash=config_hash)
        config_snapshot = json.loads(capture.config_json)
        input_snapshot = json.loads(capture.input_snapshot_json)

        self.assertEqual(config_snapshot, raw_config)
        self.assertEqual(input_snapshot["monetary_unit"], "USDT")
        self.assertEqual(input_snapshot["bars"][0]["open"], "100")
        self.assertEqual(input_snapshot["bars"][1]["open_time_us"], 3_600_000_000)
        self.assertEqual(capture.canonical_input_sha256, capture.canonical_input_sha256.lower())
        self.assertEqual(capture.execution.model_id, "historical_ohlcv_v1")
        self.assertEqual(capture.execution.profile_id, "paper")
        self.assertFalse(capture.execution.historical_filter_claim)
        self.assertEqual(capture.execution.seed_policy, "NOT_APPLICABLE")
        self.assertNotIn("path", capture.config_json.lower())
        self.assertNotIn("url", capture.config_json.lower())

    def test_same_capture_has_stable_identity_and_result_hashes(self):
        from dcabot.application.historical import build_historical_run_plan
        from dcabot.application.historical_run_contract import build_historical_run_capture
        from dcabot.application.historical_simulation import simulate_historical_ohlcv

        raw_config = _raw_config()
        dataset = _dataset()
        config = Config.parse(raw_config)
        config_hash = build_historical_run_plan(dataset, raw_config).config.config_hash
        first = simulate_historical_ohlcv(dataset, config, config_hash=config_hash)
        second = simulate_historical_ohlcv(dataset, config, config_hash=config_hash)

        first_capture = build_historical_run_capture(dataset, raw_config, first, config_hash=config_hash)
        second_capture = build_historical_run_capture(dataset, raw_config, second, config_hash=config_hash)

        self.assertEqual(first_capture, second_capture)
        self.assertEqual(len(first_capture.canonical_input_sha256), 64)
        self.assertEqual(len(first_capture.execution.identity_sha256), 64)
        self.assertEqual(len(first_capture.result_sha256), 64)

    def test_capture_rejects_non_numeric_action_reference(self):
        from dcabot.application.historical import build_historical_run_plan
        from dcabot.application.historical_run_contract import HistoricalRunContractError, build_historical_run_capture
        from dcabot.application.historical_simulation import simulate_historical_ohlcv

        raw_config = _raw_config()
        dataset = _dataset()
        config = Config.parse(raw_config)
        config_hash = build_historical_run_plan(dataset, raw_config).config.config_hash
        result = simulate_historical_ohlcv(dataset, config, config_hash=config_hash)
        tampered = replace(result, actions=(replace(result.actions[0], raw_reference="file:///secret"),))

        with self.assertRaises(HistoricalRunContractError) as context:
            build_historical_run_capture(dataset, raw_config, tampered, config_hash=config_hash)

        self.assertEqual(context.exception.code, "ACTION_REFERENCE_UNSAFE")
