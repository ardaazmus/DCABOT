import json
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest

from dcabot.application.historical import build_historical_run_plan
from dcabot.application.historical_run_contract import build_historical_run_capture, canonical_json
from dcabot.application.historical_simulation import simulate_historical_ohlcv
from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput, HistoricalDatasetMetadata
from dcabot.domain.config import Config


def _capture():
    raw_config = json.loads(Path("config/paper.json").read_text(encoding="utf-8"))
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
    config = Config.parse(raw_config)
    config_hash = build_historical_run_plan(dataset, raw_config).config.config_hash
    result = simulate_historical_ohlcv(dataset, config, config_hash=config_hash)
    return build_historical_run_capture(dataset, raw_config, result, config_hash=config_hash)


class HistoricalRunStoreTests(unittest.TestCase):
    def test_save_reopen_and_list_keep_an_immutable_record(self):
        from dcabot.persistence.historical_runs import HistoricalRunStore

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "historical-runs.sqlite3"
            with HistoricalRunStore(path) as store:
                saved = store.save(_capture(), source_execution_id="execution-1", created_at="2026-09-08T10:00:00Z")
                self.assertTrue(saved.created)
                self.assertEqual(store.list_runs(), (saved.list_item,))
                detail = store.get(saved.run_id)
                self.assertEqual(detail.run_id, saved.run_id)
                self.assertEqual(detail.execution_status, "COMPLETED")
                self.assertEqual(detail.storage_state, "STORED")
                self.assertEqual(detail.dataset["monetary_unit"], "USDT")
                self.assertEqual(detail.result_snapshot["persisted"], False)
            with HistoricalRunStore(path) as reopened:
                self.assertEqual(reopened.list_runs()[0], saved.list_item)
                self.assertEqual(reopened.get(saved.run_id), detail)

    def test_same_source_retry_is_idempotent_and_different_payload_conflicts(self):
        from dcabot.persistence.historical_runs import HistoricalRunStore, HistoricalRunStoreError

        with tempfile.TemporaryDirectory() as directory, HistoricalRunStore(Path(directory) / "runs.sqlite3") as store:
            first = store.save(_capture(), source_execution_id="execution-1", created_at="2026-09-08T10:00:00Z")
            retry = store.save(_capture(), source_execution_id="execution-1", created_at="2026-09-08T10:01:00Z")
            self.assertFalse(retry.created)
            self.assertEqual(retry.run_id, first.run_id)
            with self.assertRaises(HistoricalRunStoreError) as context:
                store.save(_capture().__class__(
                    record_schema_version=first.capture.record_schema_version,
                    input_snapshot_json=first.capture.input_snapshot_json,
                    canonical_input_sha256=first.capture.canonical_input_sha256,
                    config_json=first.capture.config_json,
                    config_hash=first.capture.config_hash,
                    instrument_risk_json=first.capture.instrument_risk_json,
                    instrument_risk_snapshot_sha256=first.capture.instrument_risk_snapshot_sha256,
                    result_json=first.capture.result_json.replace('"persisted":false', '"persisted":true'),
                    result_sha256="b" * 64,
                    execution_identity_json=first.capture.execution_identity_json,
                    execution=first.capture.execution,
                ), source_execution_id="execution-1", created_at="2026-09-08T10:02:00Z")
            self.assertEqual(context.exception.code, "SOURCE_EXECUTION_CONFLICT")
            self.assertEqual(store.get(first.run_id).result_snapshot["persisted"], False)

    def test_tampered_record_is_corrupt_but_other_records_remain_listable(self):
        from dcabot.persistence.historical_runs import HistoricalRunStore, HistoricalRunStoreError

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runs.sqlite3"
            with HistoricalRunStore(path) as store:
                first = store.save(_capture(), source_execution_id="execution-1", created_at="2026-09-08T10:00:00Z")
                second = store.save(_capture(), source_execution_id="execution-2", created_at="2026-09-08T10:01:00Z")
                store.db.execute(
                    "UPDATE historical_runs SET record_json=? WHERE run_id=?",
                    ("{\"tampered\":true}", first.run_id),
                )
                items = store.list_runs()
                self.assertEqual(items[0].run_id, second.run_id)
                self.assertEqual(items[0].record_health, "OK")
                self.assertEqual(items[1].run_id, first.run_id)
                self.assertEqual(items[1].record_health, "CORRUPT")
                with self.assertRaises(HistoricalRunStoreError) as context:
                    store.get(first.run_id)
                self.assertEqual(context.exception.code, "RUN_CORRUPT")

    def test_tampered_list_metadata_is_corrupt_even_when_record_checksum_is_valid(self):
        from dcabot.persistence.historical_runs import HistoricalRunStore

        with tempfile.TemporaryDirectory() as directory, HistoricalRunStore(Path(directory) / "runs.sqlite3") as store:
            saved = store.save(_capture(), source_execution_id="execution-1", created_at="2026-09-08T10:00:00Z")
            store.db.execute(
                "UPDATE historical_runs SET symbol=? WHERE run_id=?",
                ("TAMPERED", saved.run_id),
            )

            item = store.list_runs()[0]
            self.assertEqual(item.run_id, saved.run_id)
            self.assertEqual(item.record_health, "CORRUPT")

    def test_valid_checksum_with_missing_record_fields_is_corrupt_not_an_exception(self):
        from dcabot.persistence.historical_runs import HistoricalRunStore, HistoricalRunStoreError

        with tempfile.TemporaryDirectory() as directory, HistoricalRunStore(Path(directory) / "runs.sqlite3") as store:
            saved = store.save(_capture(), source_execution_id="execution-1", created_at="2026-09-08T10:00:00Z")
            record = json.loads(
                store.db.execute(
                    "SELECT record_json FROM historical_runs WHERE run_id=?", (saved.run_id,)
                ).fetchone()[0]
            )
            record["dataset"].pop("dataset_id")
            record.pop("record_sha256")
            record["record_sha256"] = hashlib.sha256(canonical_json(record).encode("utf-8")).hexdigest()
            store.db.execute(
                "UPDATE historical_runs SET record_json=?, record_sha256=? WHERE run_id=?",
                (canonical_json(record), record["record_sha256"], saved.run_id),
            )

            self.assertEqual(store.list_runs()[0].record_health, "CORRUPT")
            with self.assertRaises(HistoricalRunStoreError) as context:
                store.get(saved.run_id)
            self.assertEqual(context.exception.code, "RUN_CORRUPT")

    def test_existing_unrelated_sqlite_file_is_not_adopted(self):
        from dcabot.persistence.historical_runs import HistoricalRunStore, HistoricalRunStoreError

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "foreign.sqlite3"
            database = sqlite3.connect(path)
            try:
                database.execute("CREATE TABLE unrelated(value TEXT)")
                database.commit()
            finally:
                database.close()
            with self.assertRaises(HistoricalRunStoreError) as context:
                HistoricalRunStore(path)
            self.assertEqual(context.exception.code, "RUN_STORE_UNSUPPORTED")
