"""AA.13 sec-compare backend wiring: POST /api/presets/compare.

`preset_comparison.py` (Faz 17 B.4-motor) was already fully tested; this
only proves the thin HTTP surface -- bind two templates, run each on the
same dataset, return both sides with the same shared `performance_metrics()`
the saved-run/sweep/live-simulate surfaces already use.
"""
import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import dcabot.server.api as api
from dcabot.application.template_materialization import TemplateFileStore
from dcabot.application.strategy_template import new_strategy_template
from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput, HistoricalDatasetMetadata


def _asgi(path, method="GET", body=None):
    messages = [{"type": "http.request", "body": body or b"", "more_body": False}]
    sent = []

    async def receive():
        return messages.pop(0)

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http", "method": method, "path": path, "raw_path": path.encode(),
        "query_string": b"", "headers": [(b"content-type", b"application/json")],
        "scheme": "http", "server": ("testserver", 80), "client": ("testclient", 1),
    }
    asyncio.run(api.app(scope, receive, send))
    status = next(m["status"] for m in sent if m["type"] == "http.response.start")
    payload = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    return status, json.loads(payload.decode())


def _dataset() -> HistoricalDatasetInput:
    prices = (
        ("100", "100", "100", "100"),
        ("95", "100", "89", "90"),
        ("97", "98", "97", "97"),
        ("110", "110", "110", "110"),
    )
    metadata = HistoricalDatasetMetadata(
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
    )
    return HistoricalDatasetInput(
        metadata=metadata,
        bars=tuple(
            CanonicalBar(
                index * 3_600_000_000,
                index * 3_600_000_000 + 3_599_999_999,
                open_price, high, low, close, "1", True,
            )
            for index, (open_price, high, low, close) in enumerate(prices, start=1)
        ),
    )


def _save_template(store, template_id, payload):
    template = new_strategy_template(
        template_id=template_id,
        schema_version="strategy-template-v1",
        payload=payload,
        declared_capabilities=("DCA", "SPOT"),
    )
    store.save(template)


def _side(template_id, profile_id="paper"):
    return {
        "template_id": template_id,
        "profile_id": profile_id,
        "allowed_capabilities": ["DCA", "SPOT"],
        "approval": "APPROVED",
    }


class PresetCompareApiTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._original_store = api.TEMPLATE_STORE
        api.TEMPLATE_STORE = TemplateFileStore(Path(self._tmp.name) / "templates")
        _save_template(api.TEMPLATE_STORE, "t-a", {"deviation": "0.1"})
        _save_template(api.TEMPLATE_STORE, "t-b", {"deviation": "0.2"})

    def tearDown(self):
        api.TEMPLATE_STORE = self._original_store
        self._tmp.cleanup()

    def _compare(self, dataset, **overrides):
        preflight = api.DatasetPreflightResponse(
            dataset_id=dataset.metadata.dataset_id,
            artifact_status="VERIFIED",
            preflight_status="READY",
            instrument=dataset.metadata.symbol,
            interval=dataset.metadata.interval,
            period_start=api.date.fromisoformat(dataset.metadata.period_start),
            period_end=api.date.fromisoformat(dataset.metadata.period_end),
            bar_count=len(dataset.bars),
            timestamp_unit="microseconds",
            timezone="UTC",
            data_quality_status="UNKNOWN",
            data_quality_message="test",
            artifact={"sha256": dataset.metadata.artifact_sha256, "byte_size": dataset.metadata.artifact_bytes},
            read_only=True,
        )
        body = {
            "dataset_id": dataset.metadata.dataset_id,
            "artifact_sha256": dataset.metadata.artifact_sha256,
            "a": _side("t-a"),
            "b": _side("t-b"),
        }
        body.update(overrides)
        with patch("dcabot.server.api._dataset_preflight", return_value=(dataset, preflight)):
            return _asgi("/api/presets/compare", method="POST", body=json.dumps(body).encode())

    def test_two_different_templates_compare_side_by_side(self):
        status, body = self._compare(_dataset())
        self.assertEqual(status, 200, body)
        self.assertEqual(body["data"]["dataset_id"], "synthetic-btcusdt-1h")
        for side in ("a", "b"):
            data = body["data"][side]
            self.assertIn("realized_net_after_all_costs", data)
            self.assertIn("win_rate", data)
            self.assertIn("profit_factor", data)
            self.assertIn("roi", data)
            self.assertIn("deal_pnls", data)
        self.assertNotEqual(body["data"]["a"]["binding_id"], body["data"]["b"]["binding_id"])

    def test_unknown_template_is_422(self):
        status, body = self._compare(_dataset(), a=_side("does-not-exist"))
        self.assertEqual(status, 422)

    def test_missing_field_is_422(self):
        status, body = self._compare(_dataset())
        malformed = {"dataset_id": "x", "artifact_sha256": "a" * 64, "a": _side("t-a")}
        status, body = _asgi("/api/presets/compare", method="POST", body=json.dumps(malformed).encode())
        self.assertEqual(status, 422)
        self.assertIn("body", body["error"]["fields"])

    def test_artifact_mismatch_is_409(self):
        status, body = self._compare(_dataset(), artifact_sha256="b" * 64)
        self.assertEqual(status, 409)
        self.assertEqual(body["code"], "ARTIFACT_MISMATCH")


if __name__ == "__main__":
    unittest.main()
