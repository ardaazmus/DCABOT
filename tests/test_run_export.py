"""F10.1: historical-run CSV/JSON export serializers (F22)."""
import csv
import io
import json
import unittest

from dcabot.application.run_export import RunExportError, export_run_csv, export_run_json


def _detail():
    return {
        "run_id": "12345678-1234-5678-1234-567812345678",
        "created_at": "2026-09-21T10:00:00+00:00",
        "storage_state": "STORED",
        "execution_status": "COMPLETED",
        "dataset": {"dataset_id": "binance-btcusdt-1h", "symbol": "BTCUSDT"},
        "input_snapshot": {"profile_id": "p1"},
        "config": {"anchor": "100"},
        "instrument_risk": {"leverage": "1"},
        "execution": {"model_id": "historical_ohlcv_v1"},
        "result_snapshot": {"trades": 3},
        "result_sha256": "ab" * 32,
        "record_sha256": "cd" * 32,
        "evaluation_lineage": None,
    }


class RunExportTests(unittest.TestCase):
    def test_json_export_is_canonical_and_complete(self):
        first = export_run_json(_detail())
        second = export_run_json(_detail())
        self.assertEqual(first, second)
        parsed = json.loads(first)
        self.assertEqual(parsed["run_id"], _detail()["run_id"])
        self.assertEqual(parsed["result_snapshot"], {"trades": 3})
        self.assertEqual(parsed["record_sha256"], "cd" * 32)
        # canonical: sorted keys, compact separators
        self.assertEqual(first, json.dumps(parsed, sort_keys=True, separators=(",", ":")))

    def test_csv_export_has_header_and_summary_row(self):
        content = export_run_csv(_detail())
        rows = list(csv.reader(io.StringIO(content)))
        self.assertEqual(len(rows), 2)
        header, row = rows
        self.assertEqual(header[0], "run_id")
        self.assertIn("record_sha256", header)
        record = dict(zip(header, row))
        self.assertEqual(record["run_id"], _detail()["run_id"])
        self.assertEqual(record["execution_status"], "COMPLETED")
        self.assertEqual(record["record_sha256"], "cd" * 32)

    def test_csv_escapes_commas_and_quotes(self):
        detail = _detail()
        detail["execution_status"] = 'DONE, "quoted"'
        content = export_run_csv(detail)
        rows = list(csv.reader(io.StringIO(content)))
        self.assertEqual(len(rows), 2)
        record = dict(zip(rows[0], rows[1]))
        self.assertEqual(record["execution_status"], 'DONE, "quoted"')

    def test_missing_run_id_rejected(self):
        detail = _detail()
        del detail["run_id"]
        with self.assertRaises(RunExportError) as ctx:
            export_run_json(detail)
        self.assertEqual(ctx.exception.code, "RUN_EXPORT_DETAIL_INVALID")
        with self.assertRaises(RunExportError):
            export_run_csv(detail)

    def test_wrong_type_rejected(self):
        with self.assertRaises(RunExportError):
            export_run_json(["nope"])  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
