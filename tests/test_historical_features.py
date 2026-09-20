import json
from dataclasses import replace
from pathlib import Path
import unittest

from dcabot.application.historical import build_historical_run_plan
from dcabot.application.historical import HistoricalRunPlanError
from dcabot.application.historical_features import (
    FeatureDefinition,
    HistoricalFeaturePipeline,
    LabelDefinition,
)
from dcabot.application.historical_run_contract import build_historical_run_capture
from dcabot.application.historical_simulation import simulate_historical_ohlcv
from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput, HistoricalDatasetMetadata
from dcabot.domain.config import Config


def dataset() -> HistoricalDatasetInput:
    return HistoricalDatasetInput(
        metadata=HistoricalDatasetMetadata(
            dataset_id="synthetic-features-btcusdt-1h",
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
        bars=tuple(
            CanonicalBar(
                index * 3_600_000_000,
                (index + 1) * 3_600_000_000 - 1,
                str(100 + index),
                str(101 + index),
                str(99 + index),
                str(100 + index),
                "1",
                True,
            )
            for index in range(5)
        ),
    )


def pipeline() -> HistoricalFeaturePipeline:
    return HistoricalFeaturePipeline(
        pipeline_id="close-features-v1",
        features=(FeatureDefinition("CLOSE_SMA", 3), FeatureDefinition("CLOSE_RETURN", 2)),
        label=LabelDefinition("FUTURE_CLOSE_RETURN", 1),
    )


class HistoricalFeatureTests(unittest.TestCase):
    def test_binding_computes_exact_features_and_future_label_without_lookahead(self):
        raw_config = json.loads(Path("config/paper.json").read_text(encoding="utf-8"))
        plan = build_historical_run_plan(dataset(), raw_config, feature_pipeline=pipeline())
        binding = plan.feature_binding
        self.assertIsNotNone(binding)
        assert binding is not None
        self.assertEqual(binding.required_lookback_bars, 3)
        self.assertEqual(binding.warmup_bar_count, 2)
        self.assertEqual((binding.first_eligible_bar_index, binding.last_eligible_bar_index), (3, 4))
        self.assertEqual(binding.rows[0].features, (("CLOSE_SMA", "101"), ("CLOSE_RETURN", "1/50")))
        self.assertEqual(binding.rows[0].label_value, "1/102")

    def test_feature_binding_is_bound_to_historical_runner_and_capture_identity(self):
        data = dataset()
        raw_config = json.loads(Path("config/paper.json").read_text(encoding="utf-8"))
        config = Config.parse(raw_config)
        plan = build_historical_run_plan(data, raw_config, feature_pipeline=pipeline())
        binding = plan.feature_binding
        assert binding is not None
        result = simulate_historical_ohlcv(
            data,
            config,
            config_hash=plan.config.config_hash,
            feature_binding=plan.feature_binding,
        )
        self.assertEqual(result.actions[0].bar_index, 3)
        self.assertTrue(all(action.bar_index >= binding.first_eligible_bar_index for action in result.actions))
        self.assertEqual(result.feature_binding, plan.feature_binding)
        capture = build_historical_run_capture(data, raw_config, result, config_hash=plan.config.config_hash)
        self.assertEqual(capture.execution.feature_binding_sha256, plan.feature_binding.binding_sha256)
        self.assertEqual(json.loads(capture.result_json)["feature_binding"]["row_count"], 2)

    def test_binding_rejects_dataset_without_feature_and_label_horizon(self):
        raw_config = json.loads(Path("config/paper.json").read_text(encoding="utf-8"))
        short = HistoricalDatasetInput(dataset().metadata, dataset().bars[:3])
        with self.assertRaisesRegex(HistoricalRunPlanError, "FEATURE_SCOPE_TOO_SMALL"):
            build_historical_run_plan(short, raw_config, feature_pipeline=pipeline())

    def test_runner_rejects_tampered_binding_before_economic_reducer(self):
        from dcabot.application.historical_simulation import HistoricalSimulationError

        data = dataset()
        raw_config = json.loads(Path("config/paper.json").read_text(encoding="utf-8"))
        config = Config.parse(raw_config)
        plan = build_historical_run_plan(data, raw_config, feature_pipeline=pipeline())
        assert plan.feature_binding is not None
        tampered = replace(plan.feature_binding, first_eligible_bar_index=2)
        with self.assertRaisesRegex(HistoricalSimulationError, "FEATURE_BINDING_INVALID"):
            simulate_historical_ohlcv(data, config, config_hash=plan.config.config_hash, feature_binding=tampered)


if __name__ == "__main__":
    unittest.main()
