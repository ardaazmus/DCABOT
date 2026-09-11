import json
from dataclasses import replace
import hashlib
from pathlib import Path
import tempfile
import unittest

from dcabot.application.historical import build_historical_run_plan
from dcabot.application.historical_run_contract import build_historical_run_capture, canonical_json
from dcabot.application.historical_simulation import simulate_historical_ohlcv
from dcabot.application.oos_lineage import new_evaluation_lineage
from dcabot.application.stress_lineage import new_stress_lineage
from dcabot.application.trial_registry import TrialRecord, TrialStatus, new_trial_study, register_trial
from dcabot.application.evaluation_run_binding import (
    EvaluationRunBinding,
    EvaluationRunBindingError,
    attach_run_binding,
    bind_historical_run,
)
from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput, HistoricalDatasetMetadata
from dcabot.domain.config import Config
from dcabot.persistence.historical_runs import HistoricalRunStore, HistoricalRunStoreError


def _capture():
    dataset = HistoricalDatasetInput(
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
    raw_config = json.loads(Path("config/paper.json").read_text(encoding="utf-8"))
    config = Config.parse(raw_config)
    config_hash = build_historical_run_plan(dataset, raw_config).config.config_hash
    result = simulate_historical_ohlcv(dataset, config, config_hash=config_hash)
    return build_historical_run_capture(dataset, raw_config, result, config_hash=config_hash)


def _trial():
    study = new_trial_study(
        "study-1",
        parameter_space_id="space-1",
        objective_id="objective-1",
        selection_rule_id="rule-1",
    )
    trial = TrialRecord("trial-1", TrialStatus.SUCCEEDED)
    study, _ = register_trial(study, trial)
    return study, trial


class EvaluationRunBindingTests(unittest.TestCase):
    def test_binding_carries_existing_run_identity_and_optional_stress_identity(self):
        capture = _capture()
        study, trial = _trial()
        oos = new_evaluation_lineage("experiment-1")
        stress = new_stress_lineage(
            capture.result_sha256,
            stress_profile_id="slippage-wide-1",
            stress_profile_hash="a" * 64,
        )

        binding = bind_historical_run(
            capture,
            study=study,
            trial=trial,
            oos_lineage=oos,
            stress_lineage=stress,
        )
        attached = attach_run_binding(capture, binding)

        self.assertEqual(binding.result_sha256, capture.result_sha256)
        self.assertEqual(binding.run_identity_sha256, capture.execution.identity_sha256)
        self.assertEqual(binding.stress_result_id, stress.stress_result_id)
        self.assertEqual(
            attached.evaluation_binding_sha256,
            binding.binding_sha256,
        )
        self.assertEqual(
            json.loads(attached.evaluation_binding_json)["trial_id"],
            "trial-1",
        )

    def test_same_inputs_produce_same_binding_and_different_stress_is_distinct(self):
        capture = _capture()
        study, trial = _trial()
        oos = new_evaluation_lineage("experiment-1")
        first = bind_historical_run(
            capture,
            study=study,
            trial=trial,
            oos_lineage=oos,
            stress_lineage=None,
        )
        repeat = bind_historical_run(
            capture,
            study=study,
            trial=trial,
            oos_lineage=oos,
            stress_lineage=None,
        )
        stress = new_stress_lineage(
            capture.result_sha256,
            stress_profile_id="ohlc-worst-1",
            stress_profile_hash="b" * 64,
        )
        stressed = bind_historical_run(
            capture,
            study=study,
            trial=trial,
            oos_lineage=oos,
            stress_lineage=stress,
        )

        self.assertEqual(first, repeat)
        self.assertNotEqual(first.binding_sha256, stressed.binding_sha256)
        self.assertIsNone(first.stress_result_id)

    def test_unregistered_trial_and_wrong_stress_base_fail_closed(self):
        capture = _capture()
        study, _ = _trial()
        unregistered = TrialRecord("trial-unknown", TrialStatus.FAILED)
        with self.assertRaisesRegex(ValueError, "TRIAL_NOT_REGISTERED"):
            bind_historical_run(
                capture,
                study=study,
                trial=unregistered,
                oos_lineage=new_evaluation_lineage("experiment-1"),
                stress_lineage=None,
            )

        wrong_stress = new_stress_lineage(
            "different-result",
            stress_profile_id="profile-1",
            stress_profile_hash="c" * 64,
        )
        _, trial = _trial()
        with self.assertRaisesRegex(ValueError, "STRESS_BASE_RESULT_MISMATCH"):
            bind_historical_run(
                capture,
                study=study,
                trial=trial,
                oos_lineage=new_evaluation_lineage("experiment-1"),
                stress_lineage=wrong_stress,
            )

    def test_binding_persists_reopens_and_conflicts_on_changed_retry(self):
        capture = _capture()
        study, trial = _trial()
        study, second_trial_outcome = register_trial(
            study, TrialRecord("trial-2", TrialStatus.FAILED)
        )
        self.assertEqual(second_trial_outcome, "ACCEPTED")
        oos = new_evaluation_lineage("experiment-1")
        stress = new_stress_lineage(
            capture.result_sha256,
            stress_profile_id="slippage-wide-1",
            stress_profile_hash="a" * 64,
        )
        binding = bind_historical_run(
            capture,
            study=study,
            trial=trial,
            oos_lineage=oos,
            stress_lineage=stress,
        )
        attached = attach_run_binding(capture, binding)

        with tempfile.TemporaryDirectory() as directory:
            store_path = Path(directory) / "historical-runs.sqlite3"
            with HistoricalRunStore(store_path) as store:
                saved = store.save(
                    attached,
                    source_execution_id="execution-binding",
                    created_at="2026-09-10T00:00:00Z",
                )
                retry = store.save(
                    attached,
                    source_execution_id="execution-binding",
                    created_at="2026-09-10T00:00:01Z",
                )
                detail = store.get(saved.run_id)

            with HistoricalRunStore(store_path) as reopened:
                reopened_detail = reopened.get(saved.run_id)
                changed_binding = bind_historical_run(
                    capture,
                    study=study,
                    trial=TrialRecord("trial-2", TrialStatus.FAILED),
                    oos_lineage=oos,
                    stress_lineage=stress,
                )
                with self.assertRaises(HistoricalRunStoreError) as conflict:
                    reopened.save(
                        attach_run_binding(capture, changed_binding),
                        source_execution_id="execution-binding",
                        created_at="2026-09-10T00:00:02Z",
                    )

            self.assertTrue(saved.created)
            self.assertFalse(retry.created)
            self.assertEqual(retry.run_id, saved.run_id)
            self.assertEqual(conflict.exception.code, "SOURCE_EXECUTION_CONFLICT")
            self.assertEqual(detail.evaluation_lineage, reopened_detail.evaluation_lineage)
            self.assertEqual(detail.evaluation_lineage["binding_sha256"], binding.binding_sha256)
            self.assertEqual(detail.evaluation_lineage["trial_id"], "trial-1")
            self.assertEqual(detail.evaluation_lineage["oos_experiment_id"], "experiment-1")
            self.assertEqual(detail.evaluation_lineage["stress_result_id"], stress.stress_result_id)

    def test_store_rejects_hash_valid_but_schema_invalid_binding(self):
        capture = _capture()
        study, trial = _trial()
        binding = bind_historical_run(
            capture,
            study=study,
            trial=trial,
            oos_lineage=new_evaluation_lineage("experiment-1"),
            stress_lineage=None,
        )
        attached = attach_run_binding(capture, binding)
        invalid_payload = json.loads(attached.evaluation_binding_json)
        invalid_payload["secret"] = "must-not-be-persisted"
        invalid_binding_hash = hashlib.sha256(
            canonical_json(
                {key: value for key, value in invalid_payload.items() if key != "binding_sha256"}
            ).encode("utf-8")
        ).hexdigest()
        invalid_payload["binding_sha256"] = invalid_binding_hash
        invalid_json = canonical_json(invalid_payload)
        invalid_capture = replace(
            attached,
            evaluation_binding_json=invalid_json,
            evaluation_binding_sha256=invalid_binding_hash,
        )

        with tempfile.TemporaryDirectory() as directory:
            with HistoricalRunStore(Path(directory) / "historical-runs.sqlite3") as store:
                with self.assertRaises(HistoricalRunStoreError) as invalid:
                    store.save(
                        invalid_capture,
                        source_execution_id="execution-invalid-binding",
                        created_at="2026-09-10T00:00:04Z",
                    )
        self.assertEqual(invalid.exception.code, "RUN_CAPTURE_INVALID")

    def test_binding_object_rejects_noncanonical_binding_hash(self):
        capture = _capture()
        study, trial = _trial()
        binding = bind_historical_run(
            capture,
            study=study,
            trial=trial,
            oos_lineage=new_evaluation_lineage("experiment-1"),
            stress_lineage=None,
        )
        with self.assertRaises(EvaluationRunBindingError) as invalid:
            replace(binding, binding_sha256="b" * 64)
        self.assertEqual(invalid.exception.code, "RUN_BINDING_HASH_MISMATCH")


if __name__ == "__main__":
    unittest.main()
