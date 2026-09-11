import json
from datetime import date
import unittest
from unittest.mock import patch

from starlette.responses import Response

import dcabot.server.api as api
from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput, HistoricalDatasetMetadata


def _dataset(bar_count: int) -> HistoricalDatasetInput:
    bars = tuple(
        CanonicalBar(
            open_time_us=index * 3_600_000_000,
            close_time_us=index * 3_600_000_000 + 3_599_999_999,
            open="100.00",
            high="101.00",
            low="99.00",
            close="100.50",
            base_volume="1",
            is_closed=True,
        )
        for index in range(1, bar_count + 1)
    )
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
        bars=bars,
    )


class HistoricalChartDataApiTests(unittest.TestCase):
    def test_chart_data_endpoint_returns_bounded_exact_ohlc_contract(self):
        dataset = _dataset(2)
        preflight = api.DatasetPreflightResponse(
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
        response = Response()

        with patch("dcabot.server.api._dataset_preflight", return_value=(dataset, preflight)):
            result = api.get_dataset_chart_data(dataset.metadata.dataset_id, response)

        expected = api.HistoricalChartDataResponse(
            dataset_id=dataset.metadata.dataset_id,
            artifact_sha256=dataset.metadata.artifact_sha256,
            model_id="historical_ohlcv_v1",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 10),
            processed_bar_count=2,
            bars=[
                api.HistoricalChartBarResponse(
                    bar_index=1,
                    open_time_us=3_600_000_000,
                    close_time_us=7_199_999_999,
                    open="100.00",
                    high="101.00",
                    low="99.00",
                    close="100.50",
                ),
                api.HistoricalChartBarResponse(
                    bar_index=2,
                    open_time_us=7_200_000_000,
                    close_time_us=10_799_999_999,
                    open="100.00",
                    high="101.00",
                    low="99.00",
                    close="100.50",
                ),
            ],
        )

        self.assertEqual(result, expected)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertNotIn("path", json.dumps(result.model_dump(mode="json")))

    def test_chart_data_endpoint_rejects_more_than_simulation_limit(self):
        dataset = _dataset(api.MAX_HISTORICAL_SIMULATION_BARS + 1)
        with patch("dcabot.server.api._dataset_preflight", return_value=(dataset, object())):
            result = api.get_dataset_chart_data(dataset.metadata.dataset_id, Response())

        self.assertEqual(result.status_code, 409)
        self.assertIn(b"CHART_SCOPE_NOT_ADMISSIBLE", result.body)
