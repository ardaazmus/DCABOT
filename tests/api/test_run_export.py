"""F10.1: run export route helper (F22)."""
import unittest

from dcabot.server.api import _historical_run_export_data


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


class RunExportApiTests(unittest.TestCase):
    def test_json_envelope(self):
        data = _historical_run_export_data(_detail(), "json")
        self.assertEqual(data["format"], "json")
        self.assertTrue(data["filename"].endswith(".json"))
        self.assertIn("12345678-1234-5678-1234-567812345678", data["content"])

    def test_csv_envelope(self):
        data = _historical_run_export_data(_detail(), "csv")
        self.assertEqual(data["format"], "csv")
        self.assertTrue(data["filename"].endswith(".csv"))
        self.assertTrue(data["content"].startswith("run_id,"))

    def test_unknown_format_rejected(self):
        with self.assertRaises(ValueError):
            _historical_run_export_data(_detail(), "xml")


if __name__ == "__main__":
    unittest.main()
