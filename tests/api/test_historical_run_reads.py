import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from starlette.responses import Response

import dcabot.server.api as api
from dcabot.application.historical import build_historical_run_plan
from dcabot.application.historical_run_contract import build_historical_run_capture
from dcabot.application.historical_simulation import simulate_historical_ohlcv
from dcabot.application.evaluation_run_binding import attach_run_binding, bind_historical_run
from dcabot.application.oos_lineage import new_evaluation_lineage
from dcabot.application.stress_lineage import new_stress_lineage
from dcabot.application.trial_registry import TrialRecord, TrialStatus, new_trial_study, register_trial
from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput, HistoricalDatasetMetadata
from dcabot.domain.config import Config
from dcabot.persistence.historical_runs import HistoricalRunStore


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


def _capture():
    dataset = _dataset()
    raw_config = json.loads(Path("config/paper.json").read_text(encoding="utf-8"))
    config = Config.parse(raw_config)
    config_hash = build_historical_run_plan(dataset, raw_config).config.config_hash
    result = simulate_historical_ohlcv(dataset, config, config_hash=config_hash)
    return build_historical_run_capture(dataset, raw_config, result, config_hash=config_hash)


class HistoricalRunReadApiTests(unittest.TestCase):
    def test_list_and_detail_reopen_an_immutable_record_without_paths(self):
        original_path = api.HISTORICAL_RUNS_PATH
        with tempfile.TemporaryDirectory() as directory:
            api.HISTORICAL_RUNS_PATH = Path(directory) / "historical-runs.sqlite3"
            try:
                with HistoricalRunStore(api.HISTORICAL_RUNS_PATH) as store:
                    saved = store.save(
                        _capture(),
                        source_execution_id="execution-list-detail",
                        created_at="2026-09-08T00:00:00Z",
                    )

                list_response = Response()
                listed = api.list_historical_runs(limit=50, response=list_response)
                self.assertEqual(list_response.headers["cache-control"], "no-store")
                self.assertEqual(listed.count, 1)
                self.assertEqual(listed.runs[0].run_id, saved.run_id)
                self.assertEqual(listed.runs[0].record_health, "OK")

                detail_response = Response()
                detail = api.get_historical_run(saved.run_id, detail_response)
                self.assertEqual(detail_response.headers["cache-control"], "no-store")
                self.assertEqual(detail.run_id, saved.run_id)
                self.assertEqual(detail.storage_state, "STORED")
                self.assertFalse(detail.result_snapshot["persisted"])
                serialized = json.dumps(detail.model_dump(mode="json"))
                self.assertNotIn('"path"', serialized)
                self.assertNotIn('"url"', serialized)
            finally:
                api.HISTORICAL_RUNS_PATH = original_path

    def test_missing_store_returns_empty_list_and_does_not_create_database(self):
        original_path = api.HISTORICAL_RUNS_PATH
        with tempfile.TemporaryDirectory() as directory:
            api.HISTORICAL_RUNS_PATH = Path(directory) / "historical-runs.sqlite3"
            try:
                result = api.list_historical_runs(limit=50, response=Response())
                self.assertEqual(result.count, 0)
                self.assertEqual(result.runs, [])
                self.assertFalse(api.HISTORICAL_RUNS_PATH.exists())
            finally:
                api.HISTORICAL_RUNS_PATH = original_path

    def test_detail_response_is_rejected_when_serialized_body_exceeds_budget(self):
        original_path = api.HISTORICAL_RUNS_PATH
        with tempfile.TemporaryDirectory() as directory:
            api.HISTORICAL_RUNS_PATH = Path(directory) / "historical-runs.sqlite3"
            try:
                with HistoricalRunStore(api.HISTORICAL_RUNS_PATH) as store:
                    saved = store.save(
                        _capture(),
                        source_execution_id="execution-detail-size",
                        created_at="2026-09-08T00:00:01Z",
                    )
                original_get = api.HistoricalRunStore.get

                def oversized_get(store, run_id):
                    detail = original_get(store, run_id)
                    detail.result_snapshot["bounded_test_padding"] = "x" * (256 * 1024)
                    return detail

                with patch.object(api.HistoricalRunStore, "get", oversized_get):
                    result = api.get_historical_run(saved.run_id, Response())
                self.assertEqual(result.status_code, 422)
                self.assertEqual(json.loads(result.body)["code"], "RUN_DETAIL_RESPONSE_TOO_LARGE")
            finally:
                api.HISTORICAL_RUNS_PATH = original_path

    def test_detail_rejects_forbidden_snapshot_keys(self):
        original_path = api.HISTORICAL_RUNS_PATH
        with tempfile.TemporaryDirectory() as directory:
            api.HISTORICAL_RUNS_PATH = Path(directory) / "historical-runs.sqlite3"
            try:
                with HistoricalRunStore(api.HISTORICAL_RUNS_PATH) as store:
                    saved = store.save(
                        _capture(),
                        source_execution_id="execution-detail-safety",
                        created_at="2026-09-08T00:00:02Z",
                    )
                original_get = api.HistoricalRunStore.get

                def unsafe_get(store, run_id):
                    detail = original_get(store, run_id)
                    detail.config["path"] = "C:/private"
                    return detail

                with patch.object(api.HistoricalRunStore, "get", unsafe_get):
                    result = api.get_historical_run(saved.run_id, Response())
                self.assertEqual(result.status_code, 409)
                self.assertEqual(json.loads(result.body)["code"], "RUN_DETAIL_UNSAFE")
            finally:
                api.HISTORICAL_RUNS_PATH = original_path

    def test_detail_exposes_safe_evaluation_lineage_binding(self):
        capture = _capture()
        study = new_trial_study(
            "study-api",
            parameter_space_id="space-api",
            objective_id="objective-api",
            selection_rule_id="rule-api",
        )
        study, _ = register_trial(study, TrialRecord("trial-api", TrialStatus.SUCCEEDED))
        oos = new_evaluation_lineage("experiment-api")
        stress = new_stress_lineage(
            capture.result_sha256,
            stress_profile_id="stress-api",
            stress_profile_hash="d" * 64,
        )
        binding = bind_historical_run(
            capture,
            study=study,
            trial=study.trials[0],
            oos_lineage=oos,
            stress_lineage=stress,
        )

        original_path = api.HISTORICAL_RUNS_PATH
        with tempfile.TemporaryDirectory() as directory:
            api.HISTORICAL_RUNS_PATH = Path(directory) / "historical-runs.sqlite3"
            try:
                with HistoricalRunStore(api.HISTORICAL_RUNS_PATH) as store:
                    saved = store.save(
                        attach_run_binding(capture, binding),
                        source_execution_id="execution-api-binding",
                        created_at="2026-09-10T00:00:03Z",
                    )
                detail = api.get_historical_run(saved.run_id, Response())
                self.assertEqual(detail.evaluation_lineage["binding_sha256"], binding.binding_sha256)
                self.assertEqual(detail.evaluation_lineage["study_id"], "study-api")
                self.assertEqual(detail.evaluation_lineage["stress_result_id"], stress.stress_result_id)
                serialized = json.dumps(detail.model_dump(mode="json"), ensure_ascii=True)
                self.assertNotIn('"token"', serialized)
                self.assertNotIn('"path"', serialized)
                self.assertNotIn('"url"', serialized)
            finally:
                api.HISTORICAL_RUNS_PATH = original_path
