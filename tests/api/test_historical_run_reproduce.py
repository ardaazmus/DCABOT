import json
from datetime import date
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from starlette.responses import Response

import dcabot.server.api as api
from dcabot.application.historical import build_historical_run_plan
from dcabot.application.historical_run_contract import build_historical_run_capture
from dcabot.application.historical_simulation import simulate_historical_ohlcv
from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput, HistoricalDatasetMetadata
from dcabot.domain.config import Config
from dcabot.persistence.historical_runs import HistoricalRunStore


def _dataset(artifact_sha256: str = "a" * 64) -> HistoricalDatasetInput:
    return HistoricalDatasetInput(
        metadata=HistoricalDatasetMetadata(
            dataset_id="synthetic-btcusdt-1h",
            source_id="synthetic-source",
            symbol="BTCUSDT",
            interval="1h",
            period_start="2025-01-01",
            period_end="2025-01-02",
            artifact_sha256=artifact_sha256,
            artifact_bytes=1,
            timestamp_unit="microseconds",
            timezone="UTC",
        ),
        bars=(
            CanonicalBar(0, 3_599_999_999, "100", "100", "100", "100", "1", True),
            CanonicalBar(3_600_000_000, 7_199_999_999, "99", "100", "99", "99", "1", True),
        ),
    )


def _preflight(dataset: HistoricalDatasetInput) -> api.DatasetPreflightResponse:
    return api.DatasetPreflightResponse(
        dataset_id=dataset.metadata.dataset_id,
        artifact_status="VERIFIED",
        preflight_status="READY",
        instrument=dataset.metadata.symbol,
        interval=dataset.metadata.interval,
        period_start=date.fromisoformat(dataset.metadata.period_start),
        period_end=date.fromisoformat(dataset.metadata.period_end),
        bar_count=len(dataset.bars),
        timestamp_unit="microseconds",
        timezone="UTC",
        data_quality_status="UNKNOWN",
        data_quality_message="Bu testte kalite özeti kullanılmıyor.",
        artifact={"sha256": dataset.metadata.artifact_sha256, "byte_size": dataset.metadata.artifact_bytes},
        read_only=True,
    )


def _save_run(dataset: HistoricalDatasetInput, source_execution_id: str):
    raw_config = json.loads(Path("config/paper.json").read_text(encoding="utf-8"))
    config = Config.parse(raw_config)
    config_hash = build_historical_run_plan(dataset, raw_config).config.config_hash
    result = simulate_historical_ohlcv(dataset, config, config_hash=config_hash)
    capture = build_historical_run_capture(dataset, raw_config, result, config_hash=config_hash)
    with HistoricalRunStore(api.HISTORICAL_RUNS_PATH) as store:
        return store.save(capture, source_execution_id=source_execution_id, created_at="2026-09-20T12:00:00Z")


class HistoricalRunReproduceApiTests(unittest.TestCase):
    def setUp(self):
        self._original_path = api.HISTORICAL_RUNS_PATH
        self._directory = tempfile.TemporaryDirectory()
        api.HISTORICAL_RUNS_PATH = Path(self._directory.name) / "historical-runs.sqlite3"

    def tearDown(self):
        api.HISTORICAL_RUNS_PATH = self._original_path
        self._directory.cleanup()

    def test_reproduce_matches_stored_hashes_for_unchanged_dataset_and_config(self):
        dataset = _dataset()
        saved = _save_run(dataset, "execution-reproduce-1")

        with patch("dcabot.server.api._dataset_preflight", return_value=(dataset, _preflight(dataset))):
            result = api.reproduce_historical_run(saved.run_id, Response())

        self.assertTrue(result.reproduced)
        self.assertTrue(result.result_sha256_match)
        self.assertTrue(result.canonical_input_sha256_match)
        self.assertTrue(result.execution_identity_sha256_match)
        self.assertEqual(result.new_result_sha256, result.stored_result_sha256)
        self.assertEqual(result.new_result_sha256, saved.capture.result_sha256)

    def test_reproduce_fails_closed_when_local_artifact_changed(self):
        dataset = _dataset()
        saved = _save_run(dataset, "execution-reproduce-2")
        changed_dataset = _dataset(artifact_sha256="b" * 64)

        with patch(
            "dcabot.server.api._dataset_preflight",
            return_value=(changed_dataset, _preflight(changed_dataset)),
        ):
            result = api.reproduce_historical_run(saved.run_id, Response())

        self.assertEqual(result.status_code, 409)
        self.assertEqual(json.loads(result.body)["code"], "REPRODUCE_ARTIFACT_CHANGED")

    def test_reproduce_unknown_run_id_returns_not_found(self):
        result = api.reproduce_historical_run("00000000-0000-4000-8000-000000000000", Response())

        self.assertEqual(result.status_code, 404)
        self.assertEqual(json.loads(result.body)["code"], "RUN_NOT_FOUND")

    def test_reproduce_rejects_malformed_run_id(self):
        result = api.reproduce_historical_run("not-a-uuid", Response())

        self.assertEqual(result.status_code, 422)
        self.assertEqual(json.loads(result.body)["code"], "RUN_ID_INVALID")
