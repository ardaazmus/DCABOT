import asyncio
import json
from datetime import date
from pathlib import Path
import unittest
from unittest.mock import patch

from starlette.responses import Response

import dcabot.server.api as api
from dcabot.application.historical import build_historical_run_plan
from dcabot.data_adapters.historical import (
    CanonicalBar,
    HistoricalDatasetInput,
    HistoricalDatasetMetadata,
)


DATASET_ID = "binance-spot-klines-v1-btcusdt-1h-2025-01-01"
ARTIFACT_SHA256 = "a" * 64
PROFILE_ID = "historical_demo_btcusdt_1h_v1"


def _dataset(*ohlc: tuple[str, str, str, str]) -> HistoricalDatasetInput:
    bars = tuple(
        CanonicalBar(
            open_time_us=index * 3_600_000_000,
            close_time_us=index * 3_600_000_000 + 3_599_999_999,
            open=open_price,
            high=high,
            low=low,
            close=close,
            base_volume="1",
            is_closed=True,
        )
        for index, (open_price, high, low, close) in enumerate(ohlc, start=1)
    )
    return HistoricalDatasetInput(
        metadata=HistoricalDatasetMetadata(
            dataset_id=DATASET_ID,
            source_id="synthetic-source",
            symbol="BTCUSDT",
            interval="1h",
            period_start="2025-01-01",
            period_end="2025-01-10",
            artifact_sha256=ARTIFACT_SHA256,
            artifact_bytes=1,
            timestamp_unit="microseconds",
            timezone="UTC",
        ),
        bars=bars,
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
        data_quality_message="Synthetic test fixture.",
        artifact=api.ArtifactSummary(sha256=ARTIFACT_SHA256, byte_size=1),
        read_only=True,
    )


def _config_hash(dataset: HistoricalDatasetInput) -> str:
    raw = json.loads(Path("config/historical_demo_btcusdt_1h_v1.json").read_text(encoding="utf-8"))
    return build_historical_run_plan(dataset, raw).config.config_hash


def _payload(dataset: HistoricalDatasetInput, **overrides: object) -> api.HistoricalBaseLimitSimulationRequest:
    values = {
        "dataset_id": DATASET_ID,
        "profile_id": PROFILE_ID,
        "artifact_sha256": ARTIFACT_SHA256,
        "config_hash": _config_hash(dataset),
        "execution_mode": "SIMULATED",
        "simulation_model": "historical_ohlcv_base_fixed_limit_binding_v1",
        "order_id": "public-base-1",
        "limit_price": "100",
        "slice_qty": "0.001",
        "placement_bar_index": 1,
        "placement_open_time_us": 3_600_000_000,
    }
    values.update(overrides)
    return api.HistoricalBaseLimitSimulationRequest(**values)


def _post_asgi(body: bytes) -> list[dict[str, object]]:
    messages = [{"type": "http.request", "body": body, "more_body": False}]
    sent: list[dict[str, object]] = []

    async def receive():
        return messages.pop(0)

    async def send(message: dict[str, object]):
        sent.append(message)

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/historical-runs/simulate-base-limit",
        "raw_path": b"/api/historical-runs/simulate-base-limit",
        "query_string": b"",
        "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())],
        "scheme": "http",
        "server": ("testserver", 80),
        "client": ("testclient", 1),
    }
    asyncio.run(api.app(scope, receive, send))
    return sent


class HistoricalBaseLimitContractTests(unittest.TestCase):
    def test_public_contract_keeps_observation_separate_from_core_fill(self):
        dataset = _dataset(
            ("105", "107", "101", "104"),
            ("105", "106", "100", "100"),
            ("100", "101", "101", "100"),
        )

        with patch("dcabot.server.api._dataset_preflight", return_value=(dataset, _preflight(dataset))):
            result = api.simulate_base_limit_historical_run(_payload(dataset), Response())

        self.assertEqual(result.execution_status, "OPEN_AT_END")
        self.assertEqual(result.model, "historical_ohlcv_base_fixed_limit_binding_v1")
        self.assertEqual(len(result.binding_identity_sha256), 64)
        self.assertEqual(result.provenance.role, "BASE")
        self.assertEqual(result.reserve, api.HistoricalBaseLimitReserveResponse(
            model="NONE",
            amount="NOT_MODELED",
            asset="NOT_APPLICABLE",
        ))
        self.assertEqual(result.observations[0].kind, "EQUALITY_TOUCH")
        self.assertFalse(result.observations[0].fill_committed)
        self.assertEqual(len(result.actions), 0)
        self.assertEqual(result.state.order_status, "OPEN")
        self.assertEqual(result.state.filled_qty, "0")
        self.assertEqual(result.state.leaves_qty, "0.004")
        self.assertFalse(result.persisted)
        self.assertFalse(result.production_ready)

    def test_public_contract_identity_is_deterministic_and_not_cached(self):
        dataset = _dataset(
            ("105", "107", "101", "104"),
            ("105", "106", "99", "103"),
        )

        with patch("dcabot.server.api._dataset_preflight", return_value=(dataset, _preflight(dataset))):
            first_response = Response()
            first = api.simulate_base_limit_historical_run(_payload(dataset), first_response)
            second_response = Response()
            second = api.simulate_base_limit_historical_run(_payload(dataset), second_response)

        self.assertEqual(first.binding_identity_sha256, second.binding_identity_sha256)
        self.assertEqual(first_response.headers["cache-control"], "no-store")
        self.assertEqual(second_response.headers["cache-control"], "no-store")

    def test_public_contract_hides_indeterminate_action_prefix(self):
        from dcabot.application.historical_base_limit_binding import simulate_base_fixed_limit_binding
        from dcabot.application.historical_fixed_limit import FixedLimitOrder
        from dcabot.domain.config import Config

        dataset = _dataset(
            ("105", "107", "101", "104"),
            ("105", "106", "99", "103"),
            ("103", "106", "98", "102"),
        )
        raw_config = json.loads(Path("config/historical_demo_btcusdt_1h_v1.json").read_text(encoding="utf-8"))
        config = Config.parse(raw_config)
        plan = build_historical_run_plan(dataset, raw_config)
        order = FixedLimitOrder(
            order_id="public-base-1",
            side="BUY",
            limit_price="100",
            original_qty="0.004",
            placement_bar_index=1,
            placement_open_time_us=3_600_000_000,
        )
        internal = simulate_base_fixed_limit_binding(
            dataset,
            config,
            order,
            slice_qty="0.001",
            config_hash=plan.config.config_hash,
            ambiguous_bar_indices={2},
        )

        with patch("dcabot.server.api._dataset_preflight", return_value=(dataset, _preflight(dataset))):
            result = api._historical_base_limit_response(
                dataset,
                plan,
                internal,
                order,
                api.get_historical_profile(PROFILE_ID),
                "0.001",
            )

        self.assertEqual(result.execution_status, "INDETERMINATE")
        self.assertEqual(result.actions, [])
        self.assertEqual(result.ambiguity.bar_index, 2)

    def test_public_contract_does_not_use_placement_bar_ohlc(self):
        dataset = _dataset(
            ("105", "107", "99", "104"),
            ("105", "106", "101", "103"),
        )

        with patch("dcabot.server.api._dataset_preflight", return_value=(dataset, _preflight(dataset))):
            result = api.simulate_base_limit_historical_run(_payload(dataset), Response())

        self.assertEqual(result.execution_status, "OPEN_AT_END")
        self.assertEqual(result.actions, [])
        self.assertEqual(result.state.filled_qty, "0")

    def test_public_contract_rejects_float_financial_input(self):
        dataset = _dataset(("105", "107", "101", "104"))

        with self.assertRaises(ValueError):
            _payload(dataset, limit_price=100.0)

    def test_public_contract_normalizes_equivalent_exact_decimal_strings(self):
        dataset = _dataset(
            ("105", "107", "101", "104"),
            ("105", "106", "99", "103"),
        )

        with patch("dcabot.server.api._dataset_preflight", return_value=(dataset, _preflight(dataset))):
            result = api.simulate_base_limit_historical_run(
                _payload(dataset, limit_price="100.0", slice_qty="0.0010"),
                Response(),
            )

        self.assertEqual((result.order.limit_price, result.order.slice_qty), ("100", "0.001"))
        self.assertEqual(result.actions[0].fill_price, "100")

    def test_public_contract_rejects_profile_that_is_not_explicit_historical_fixture(self):
        dataset = _dataset(("105", "107", "101", "104"))
        payload = _payload(dataset, profile_id="paper")

        with patch("dcabot.server.api._dataset_preflight", return_value=(dataset, _preflight(dataset))):
            result = api.simulate_base_limit_historical_run(payload, Response())

        self.assertEqual(result.status_code, 409)
        self.assertEqual(json.loads(result.body)["code"], "BASE_LIMIT_PROFILE_REQUIRED")

    def test_public_contract_rejects_off_grid_slice_without_server_error(self):
        dataset = _dataset(("105", "107", "101", "104"))

        with patch("dcabot.server.api._dataset_preflight", return_value=(dataset, _preflight(dataset))):
            result = api.simulate_base_limit_historical_run(
                _payload(dataset, slice_qty="0.0001"),
                Response(),
            )

        self.assertEqual(result.status_code, 422)
        self.assertEqual(json.loads(result.body)["code"], "SLICE_QTY_OFF_GRID")

    def test_public_contract_validation_failure_uses_no_store_problem_details(self):
        dataset = _dataset(("105", "107", "101", "104"))
        raw_payload = _payload(dataset).model_dump(mode="json")
        raw_payload["limit_price"] = 100.0

        sent = _post_asgi(json.dumps(raw_payload).encode("utf-8"))

        self.assertEqual(sent[0]["status"], 422)
        headers = dict(sent[0]["headers"])
        self.assertEqual(headers[b"content-type"], b"application/problem+json")
        self.assertEqual(headers[b"cache-control"], b"no-store")
        self.assertEqual(json.loads(sent[1]["body"])["code"], "REQUEST_VALIDATION_FAILED")

    def test_public_contract_serializes_through_asgi(self):
        dataset = _dataset(
            ("105", "107", "101", "104"),
            ("105", "106", "99", "103"),
        )
        body = json.dumps(_payload(dataset).model_dump(mode="json")).encode("utf-8")
        with patch("dcabot.server.api._dataset_preflight", return_value=(dataset, _preflight(dataset))):
            sent = _post_asgi(body)

        self.assertEqual(sent[0]["status"], 200)
        payload = json.loads(sent[1]["body"])
        self.assertEqual(payload["model"], "historical_ohlcv_base_fixed_limit_binding_v1")
        self.assertEqual(len(payload["binding_identity_sha256"]), 64)
        self.assertEqual(payload["execution_status"], "OPEN_AT_END")
        self.assertEqual(payload["actions"][0]["role"], "BASE")
        self.assertEqual(payload["actions"][0]["fill_price"], "100")
        self.assertEqual(payload["reserve"]["amount"], "NOT_MODELED")
        self.assertFalse(payload["production_ready"])
        self.assertFalse(payload["persisted"])


if __name__ == "__main__":
    unittest.main()
