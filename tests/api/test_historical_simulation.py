import asyncio
import json
from datetime import date
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from starlette.responses import Response
from starlette.requests import Request
from fastapi.exceptions import RequestValidationError

import dcabot.server.api as api
from dcabot.application.historical import build_historical_run_plan
from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput, HistoricalDatasetMetadata
from dcabot.persistence.historical_runs import HistoricalRunStore


def _dataset(
    *bars: tuple[str, str, str, str, str, str],
    dataset_id: str = "synthetic-btcusdt-1h",
) -> HistoricalDatasetInput:
    canonical = tuple(
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
        for index, (open_price, high, low, close, _unused_a, _unused_b) in enumerate(bars, start=1)
    )
    return HistoricalDatasetInput(
        metadata=HistoricalDatasetMetadata(
            dataset_id=dataset_id,
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
        bars=canonical,
    )


class HistoricalSimulationApiTests(unittest.TestCase):
    def test_historical_profiles_endpoint_exposes_only_registered_safe_profiles(self):
        response = Response()

        result = api.list_profiles(response)

        self.assertEqual(
            [profile.profile_id for profile in result],
            [
                "paper",
                "historical_demo_btcusdt_1h_v1",
                "historical_demo_btcusdt_1h_stress_slippage_v1",
                "historical_demo_btcusdt_1h_partial_fixed_v1",
            ],
        )
        self.assertEqual(result[0].label, "Paper config (v1)")
        self.assertIsNone(result[0].expected_dataset_id)
        self.assertEqual(result[1].label, "Historical demo — BTCUSDT 1h (v1)")
        self.assertEqual(result[1].expected_dataset_id, "binance-spot-klines-v1-btcusdt-1h-2025-01-01")
        self.assertEqual(result[2].label, "Historical demo — BTCUSDT 1h, stress slippage 0.2% (v1)")
        self.assertEqual(result[2].expected_dataset_id, "binance-spot-klines-v1-btcusdt-1h-2025-01-01")
        self.assertEqual(result[3].simulation_model, "historical_ohlcv_partial_fixed_v1")
        self.assertEqual(result[3].slice_qty, "0.001")
        self.assertEqual(response.headers["cache-control"], "no-store")
        serialized = json.dumps([profile.model_dump(mode="json") for profile in result])
        self.assertNotIn("path", serialized)
        self.assertNotIn("url", serialized)

    def test_committed_prefix_authority_is_rejected_for_legacy_execution(self):
        result = api.simulate_historical_run(
            api.HistoricalSimulationRequest(
                dataset_id="synthetic-btcusdt-1h",
                profile_id="paper",
                artifact_sha256="a" * 64,
                config_hash="b" * 64,
                execution_mode="historical_ohlcv_v1",
                action_authority="COMMITTED_PREFIX",
            ),
            Response(),
        )

        self.assertEqual(result.status_code, 422)
        self.assertEqual(json.loads(result.body), {
            "type": "urn:local-api:problem:UNSUPPORTED-ACTION-AUTHORITY",
            "title": "Aksiyon yetkisi desteklenmiyor",
            "status": 422,
            "code": "UNSUPPORTED_ACTION_AUTHORITY",
            "detail": "COMMITTED_PREFIX yalnızca historical_ohlcv_partial_fixed_v1 için açıkça desteklenir.",
        })

    def test_simulate_request_validation_uses_problem_details_contract(self):
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/api/historical-runs/simulate",
                "headers": [],
                "query_string": b"",
                "server": ("test", 80),
                "client": ("test", 1),
                "scheme": "http",
            }
        )
        error = RequestValidationError(
            [{"type": "missing", "loc": ("body", "artifact_sha256"), "msg": "Field required", "input": {}}]
        )

        result = asyncio.run(api.request_validation_error(request, error))

        self.assertEqual(result.status_code, 422)
        self.assertEqual(result.media_type, "application/problem+json")

    def test_simulation_endpoint_returns_bounded_result_without_persistence(self):
        dataset = _dataset(
            ("100", "100", "100", "100", "", ""),
            ("99", "100", "99", "99", "", ""),
        )
        config_hash = build_historical_run_plan(
            dataset,
            json.loads(Path("config/paper.json").read_text(encoding="utf-8")),
        ).config.config_hash
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

        with patch("dcabot.server.api._dataset_preflight", return_value=(dataset, preflight)):
            result = api.simulate_historical_run(
                api.HistoricalSimulationRequest(
                    dataset_id=dataset.metadata.dataset_id,
                    profile_id="paper",
                    artifact_sha256=dataset.metadata.artifact_sha256,
                    config_hash=config_hash,
                    execution_mode="historical_ohlcv_v1",
                ),
                Response(),
            )

        self.assertEqual(result.execution_status, "COMPLETED")
        self.assertFalse(result.persisted)
        self.assertEqual(result.dataset.processed_bar_count, 2)
        self.assertEqual(result.actions[0].role, "BASE")
        self.assertEqual(result.summary.position_status, "OPEN_AT_END")
        serialized = json.dumps(result.model_dump(mode="json"))
        self.assertNotIn('"url"', serialized)
        self.assertNotIn('"path"', serialized)

    def test_fixed_slice_profile_requires_explicit_run_plan_opt_in(self):
        dataset = _dataset(
            ("100", "100", "100", "100", "", ""),
            dataset_id="binance-spot-klines-v1-btcusdt-1h-2025-01-01",
        )
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

        with patch("dcabot.server.api._dataset_preflight", return_value=(dataset, preflight)):
            result = api.get_dataset_run_plan(
                dataset.metadata.dataset_id,
                Response(),
                profile_id="historical_demo_btcusdt_1h_partial_fixed_v1",
            )

        self.assertEqual(result.profile.profile_id, "historical_demo_btcusdt_1h_partial_fixed_v1")
        self.assertEqual(result.profile.simulation_model, "historical_ohlcv_partial_fixed_v1")
        self.assertEqual(result.profile.slice_qty, "0.001")
        self.assertEqual(result.config.simulation_model, "historical_ohlcv_partial_fixed_v1")
        self.assertEqual(result.config.slice_qty, "0.001")
        self.assertNotEqual(
            result.config.config_hash,
            build_historical_run_plan(dataset, json.loads(Path("config/historical_demo_btcusdt_1h_v1.json").read_text(encoding="utf-8"))).config.config_hash,
        )

    def test_fixed_slice_simulation_returns_versioned_action_lifecycle_without_persistence(self):
        dataset = _dataset(
            ("100", "100", "100", "100", "", ""),
            ("100", "100", "100", "100", "", ""),
            ("100", "100", "100", "100", "", ""),
            ("100", "100", "100", "100", "", ""),
            dataset_id="binance-spot-klines-v1-btcusdt-1h-2025-01-01",
        )
        raw_config = json.loads(Path("config/historical_demo_btcusdt_1h_v1.json").read_text(encoding="utf-8"))
        profile = api.get_historical_profile("historical_demo_btcusdt_1h_partial_fixed_v1")
        plan = build_historical_run_plan(
            dataset,
            raw_config,
            simulation_model=profile.simulation_model,
            slice_qty=profile.slice_qty,
        )
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

        with patch("dcabot.server.api._dataset_preflight", return_value=(dataset, preflight)):
            result = api.simulate_historical_run(
                api.HistoricalSimulationRequest(
                    dataset_id=dataset.metadata.dataset_id,
                    profile_id=profile.profile_id,
                    artifact_sha256=dataset.metadata.artifact_sha256,
                    config_hash=plan.config.config_hash,
                    execution_mode="historical_ohlcv_partial_fixed_v1",
                ),
                Response(),
            )

        self.assertIsNone(result.execution_id)
        self.assertFalse(result.persisted)
        self.assertEqual(result.assumptions.model, "historical_ohlcv_partial_fixed_v1")
        self.assertEqual([action.action_type for action in result.actions], ["PARTIAL_FILL", "PARTIAL_FILL", "PARTIAL_FILL", "FULL_FILL"])
        self.assertEqual(result.actions[0].cumulative_filled_qty, "0.001")
        self.assertEqual(result.actions[0].leaves_qty, "0.003")
        self.assertEqual(result.actions[-1].cumulative_filled_qty, "0.004")
        self.assertEqual(result.actions[-1].leaves_qty, "0")
        self.assertEqual([action.event_sequence for action in result.actions], [1, 2, 3, 4])
        self.assertEqual(result.action_authority.mode, "FULL_RUN")
        self.assertEqual(result.action_authority.economic_state_commit_scope, "FULL_RUN")
        self.assertEqual(result.action_authority.committed_through_bar_index, 4)
        self.assertEqual(result.action_authority.committed_through_open_time_us, 14_400_000_000)
        self.assertEqual(result.action_authority.committed_through_event_sequence, 4)
        self.assertEqual(result.action_authority.action_count, 4)
        self.assertEqual(result.marker_authority, "FULL")
        self.assertEqual(result.marker_kind, "TRADE_EXECUTION")
        self.assertEqual(result.final_economic_summary.position_status, "OPEN_AT_END")
        self.assertEqual(
            [item.code for item in result.explanations],
            [
                "HISTORICAL_COMPLETED",
                "ACTION_RECORDED",
                "ACTION_RECORDED",
                "ACTION_RECORDED",
                "ACTION_RECORDED",
                "POSITION_OPEN_AT_END",
                "FUNDING_NOT_MODELED",
                "MARK_NOT_AVAILABLE",
            ],
        )
        self.assertNotIn("pnl", result.explanations[0].context)

    def test_fixed_slice_http_response_serializes_through_asgi_contract(self):
        dataset = _dataset(
            ("100", "100", "100", "100", "", ""),
            ("100", "100", "100", "100", "", ""),
            ("100", "100", "100", "100", "", ""),
            ("100", "100", "100", "100", "", ""),
            dataset_id="binance-spot-klines-v1-btcusdt-1h-2025-01-01",
        )
        raw_config = json.loads(Path("config/historical_demo_btcusdt_1h_v1.json").read_text(encoding="utf-8"))
        profile = api.get_historical_profile("historical_demo_btcusdt_1h_partial_fixed_v1")
        plan = build_historical_run_plan(
            dataset,
            raw_config,
            simulation_model=profile.simulation_model,
            slice_qty=profile.slice_qty,
        )
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

        async def request():
            payload = json.dumps(
                {
                    "dataset_id": dataset.metadata.dataset_id,
                    "profile_id": profile.profile_id,
                    "artifact_sha256": dataset.metadata.artifact_sha256,
                    "config_hash": plan.config.config_hash,
                    "execution_mode": "historical_ohlcv_partial_fixed_v1",
                }
            ).encode("utf-8")
            messages = []

            async def receive():
                return {"type": "http.request", "body": payload, "more_body": False}

            async def send(message):
                messages.append(message)

            await api.app(
                {
                    "type": "http",
                    "method": "POST",
                    "path": "/api/historical-runs/simulate",
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(payload)).encode("ascii")),
                    ],
                    "query_string": b"",
                    "server": ("test", 80),
                    "client": ("test", 1),
                    "scheme": "http",
                },
                receive,
                send,
            )
            response_body = b"".join(message.get("body", b"") for message in messages)
            response_status = next(message["status"] for message in messages if message["type"] == "http.response.start")
            return response_status, json.loads(response_body)

        with patch("dcabot.server.api._dataset_preflight", return_value=(dataset, preflight)):
            status_code, body = asyncio.run(request())

        self.assertEqual(status_code, 200)
        self.assertIsNone(body["execution_id"])
        self.assertFalse(body["persisted"])
        self.assertEqual(body["assumptions"]["model"], "historical_ohlcv_partial_fixed_v1")
        self.assertEqual(len(body["actions"]), 4)
        self.assertEqual(body["actions"][0]["action_type"], "PARTIAL_FILL")
        self.assertEqual(body["actions"][-1]["action_type"], "FULL_FILL")
        self.assertEqual(body["actions"][-1]["leaves_qty"], "0")
        self.assertEqual([action["event_sequence"] for action in body["actions"]], [1, 2, 3, 4])
        self.assertEqual(body["action_authority"]["mode"], "FULL_RUN")
        self.assertEqual(body["action_authority"]["economic_state_commit_scope"], "FULL_RUN")
        self.assertEqual(body["action_authority"]["committed_through_bar_index"], 4)
        self.assertEqual(body["action_authority"]["committed_through_open_time_us"], 14_400_000_000)
        self.assertEqual(body["action_authority"]["committed_through_event_sequence"], 4)
        self.assertEqual(body["action_authority"]["action_count"], 4)
        self.assertEqual(body["marker_authority"], "FULL")
        self.assertEqual(body["marker_kind"], "TRADE_EXECUTION")
        self.assertEqual(body["explanations"][0]["code"], "HISTORICAL_COMPLETED")
        self.assertEqual(len(body["explanations"]), 8)
        self.assertNotIn("realized_net_after_all_costs", body["explanations"][0])

    def test_fixed_slice_indeterminate_response_uses_explicit_prefix_capability(self):
        dataset = _dataset(
            ("100", "100", "100", "100", "", ""),
            ("100", "100", "100", "100", "", ""),
            ("100", "100", "100", "100", "", ""),
            ("100", "100", "100", "100", "", ""),
            ("100", "103", "89", "100", "", ""),
            dataset_id="binance-spot-klines-v1-btcusdt-1h-2025-01-01",
        )
        raw_config = json.loads(Path("config/historical_demo_btcusdt_1h_v1.json").read_text(encoding="utf-8"))
        profile = api.get_historical_profile("historical_demo_btcusdt_1h_partial_fixed_v1")
        plan = build_historical_run_plan(
            dataset,
            raw_config,
            simulation_model=profile.simulation_model,
            slice_qty=profile.slice_qty,
        )
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

        with patch("dcabot.server.api._dataset_preflight", return_value=(dataset, preflight)):
            result = api.simulate_historical_run(
                api.HistoricalSimulationRequest(
                    dataset_id=dataset.metadata.dataset_id,
                    profile_id=profile.profile_id,
                    artifact_sha256=dataset.metadata.artifact_sha256,
                    config_hash=plan.config.config_hash,
                    execution_mode="historical_ohlcv_partial_fixed_v1",
                ),
                Response(),
            )

        self.assertEqual(result.execution_status, "INDETERMINATE")
        self.assertEqual(result.application_code, "AMBIGUOUS_OHLC_PATH")
        self.assertEqual(result.ambiguity.bar_index, 5)
        self.assertEqual(result.ambiguity.open_time_us, 18_000_000_000)
        self.assertEqual(result.actions, [])
        self.assertFalse(result.complete_execution)
        self.assertEqual(result.action_authority.mode, "NONE")
        self.assertIsNone(result.action_authority.committed_through_bar_index)
        self.assertEqual(result.action_authority.ambiguity_bar_index, 5)
        self.assertFalse(result.action_authority.contains_ambiguity_bar_actions)
        self.assertFalse(result.action_authority.contains_post_ambiguity_actions)
        self.assertFalse(result.action_authority.complete_history)
        self.assertFalse(result.action_authority.economic_state_committed)
        self.assertEqual(result.marker_authority, "NONE")
        self.assertIsNone(result.final_economic_summary)
        serialized = result.model_dump(mode="json")
        self.assertNotIn("summary", serialized)
        self.assertEqual(serialized["actions"], [])

        async def request():
            payload = json.dumps(
                {
                    "dataset_id": dataset.metadata.dataset_id,
                    "profile_id": profile.profile_id,
                    "artifact_sha256": dataset.metadata.artifact_sha256,
                    "config_hash": plan.config.config_hash,
                    "execution_mode": "historical_ohlcv_partial_fixed_v1",
                    "action_authority": "COMMITTED_PREFIX",
                }
            ).encode("utf-8")
            messages = []

            async def receive():
                return {"type": "http.request", "body": payload, "more_body": False}

            async def send(message):
                messages.append(message)

            await api.app(
                {
                    "type": "http",
                    "method": "POST",
                    "path": "/api/historical-runs/simulate",
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(payload)).encode("ascii")),
                    ],
                    "query_string": b"",
                    "server": ("test", 80),
                    "client": ("test", 1),
                    "scheme": "http",
                },
                receive,
                send,
            )
            response_body = b"".join(message.get("body", b"") for message in messages)
            response_status = next(message["status"] for message in messages if message["type"] == "http.response.start")
            return response_status, json.loads(response_body)

        with patch("dcabot.server.api._dataset_preflight", return_value=(dataset, preflight)):
            status_code, body = asyncio.run(request())

        self.assertEqual(status_code, 200)
        self.assertEqual(body["execution_status"], "INDETERMINATE")
        self.assertEqual(body["ambiguity"]["open_time_us"], 18_000_000_000)
        self.assertEqual([action["event_sequence"] for action in body["actions"]], [1, 2, 3, 4])
        self.assertEqual(body["action_authority"]["mode"], "COMMITTED_PREFIX")
        self.assertEqual(body["action_authority"]["economic_state_commit_scope"], "PREFIX_ONLY")
        self.assertEqual(body["action_authority"]["committed_through_bar_index"], 4)
        self.assertEqual(body["action_authority"]["committed_through_open_time_us"], 14_400_000_000)
        self.assertEqual(body["action_authority"]["committed_through_event_sequence"], 4)
        self.assertEqual(body["action_authority"]["action_count"], 4)
        self.assertTrue(body["action_authority"]["economic_state_committed"])
        self.assertEqual(body["marker_authority"], "PREFIX_BOUNDARY_ONLY")
        self.assertEqual(body["marker_kind"], "INCOMPLETE_BOUNDARY")
        self.assertIsNone(body["final_economic_summary"])
        self.assertNotIn("summary", body)

    def test_simulation_execution_can_be_saved_once_and_retried_idempotently(self):
        dataset = _dataset(
            ("100", "100", "100", "100", "", ""),
            ("99", "100", "99", "99", "", ""),
        )
        config_hash = build_historical_run_plan(
            dataset,
            json.loads(Path("config/paper.json").read_text(encoding="utf-8")),
        ).config.config_hash
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

        with patch("dcabot.server.api._dataset_preflight", return_value=(dataset, preflight)):
            result = api.simulate_historical_run(
                api.HistoricalSimulationRequest(
                    dataset_id=dataset.metadata.dataset_id,
                    profile_id="paper",
                    artifact_sha256=dataset.metadata.artifact_sha256,
                    config_hash=config_hash,
                    execution_mode="historical_ohlcv_v1",
                ),
                Response(),
            )

        self.assertIsNotNone(result.execution_id)
        original_path = api.HISTORICAL_RUNS_PATH
        with tempfile.TemporaryDirectory() as directory:
            api.HISTORICAL_RUNS_PATH = Path(directory) / "historical-runs.sqlite3"
            try:
                first_response = Response()
                first = api.save_historical_run(
                    api.HistoricalRunSaveRequest(execution_id=result.execution_id),
                    first_response,
                )
                second_response = Response()
                second = api.save_historical_run(
                    api.HistoricalRunSaveRequest(execution_id=result.execution_id),
                    second_response,
                )
                self.assertEqual(first_response.status_code, 201)
                self.assertEqual(second_response.status_code, 200)
                self.assertTrue(first.created)
                self.assertFalse(second.created)
                self.assertEqual(first.run_id, second.run_id)
                with HistoricalRunStore(api.HISTORICAL_RUNS_PATH) as store:
                    detail = store.get(first.run_id)
                self.assertFalse(detail.result_snapshot["persisted"])
                serialized = json.dumps(detail.result_snapshot)
                self.assertNotIn('"url"', serialized)
                self.assertNotIn('"path"', serialized)
            finally:
                api.HISTORICAL_RUNS_PATH = original_path
                api.HISTORICAL_EXECUTIONS.clear()

    def test_indeterminate_simulation_can_be_saved_without_clearing_ambiguity(self):
        dataset = _dataset(
            ("100", "100", "100", "100", "", ""),
            ("100", "103", "89", "100", "", ""),
        )
        config_hash = build_historical_run_plan(
            dataset,
            json.loads(Path("config/paper.json").read_text(encoding="utf-8")),
        ).config.config_hash
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

        with patch("dcabot.server.api._dataset_preflight", return_value=(dataset, preflight)):
            result = api.simulate_historical_run(
                api.HistoricalSimulationRequest(
                    dataset_id=dataset.metadata.dataset_id,
                    profile_id="paper",
                    artifact_sha256=dataset.metadata.artifact_sha256,
                    config_hash=config_hash,
                    execution_mode="historical_ohlcv_v1",
                ),
                Response(),
            )

        self.assertEqual(result.execution_status, "INDETERMINATE")
        self.assertEqual(result.application_code, "AMBIGUOUS_OHLC_PATH")
        self.assertEqual(result.ambiguity.bar_index, 2)
        original_path = api.HISTORICAL_RUNS_PATH
        with tempfile.TemporaryDirectory() as directory:
            api.HISTORICAL_RUNS_PATH = Path(directory) / "historical-runs.sqlite3"
            try:
                response = Response()
                saved = api.save_historical_run(
                    api.HistoricalRunSaveRequest(execution_id=result.execution_id),
                    response,
                )
                self.assertEqual(response.status_code, 201)
                self.assertEqual(saved.execution_status, "INDETERMINATE")
                with HistoricalRunStore(api.HISTORICAL_RUNS_PATH) as store:
                    detail = store.get(saved.run_id)
                self.assertEqual(detail.result_snapshot["application_code"], "AMBIGUOUS_OHLC_PATH")
                self.assertEqual(detail.result_snapshot["ambiguity"]["bar_index"], 2)
                self.assertFalse(detail.result_snapshot["persisted"])
            finally:
                api.HISTORICAL_RUNS_PATH = original_path
                api.HISTORICAL_EXECUTIONS.clear()

    def test_save_rejects_unknown_execution_without_creating_a_store(self):
        original_path = api.HISTORICAL_RUNS_PATH
        with tempfile.TemporaryDirectory() as directory:
            api.HISTORICAL_RUNS_PATH = Path(directory) / "historical-runs.sqlite3"
            try:
                response = Response()
                result = api.save_historical_run(
                    api.HistoricalRunSaveRequest(execution_id="missing-execution"),
                    response,
                )
                self.assertEqual(result.status_code, 404)
                self.assertEqual(json.loads(result.body)["code"], "EXECUTION_NOT_FOUND")
                self.assertFalse(api.HISTORICAL_RUNS_PATH.exists())
            finally:
                api.HISTORICAL_RUNS_PATH = original_path
