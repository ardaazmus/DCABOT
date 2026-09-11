from io import BytesIO
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZIP_DEFLATED, ZipFile

from starlette.responses import Response

from dcabot.data_adapters.catalog import PublicDatasetCatalog, PublicDatasetDefinition
from dcabot.data_adapters.public_sources import PublicDownloadRegistry, PublicSourceSpec
from dcabot.data_adapters.public_download import download_to_cache
import dcabot.server.api as api


RAW_KLINES = """1735689600000000,100.00000000,101.00000000,99.00000000,100.50000000,2.50000000,1735693199999999,251.25000000,12,1.25000000,125.62500000,0
1735693200000000,100.50000000,102.00000000,100.00000000,101.50000000,3.00000000,1735696799999999,304.50000000,13,1.50000000,152.25000000,0
""".encode()


def _zip_payload() -> bytes:
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("BTCUSDT-1h-2025-01-01.csv", RAW_KLINES)
    return output.getvalue()


class _FakeResponse:
    status = 200

    def __init__(self, payload: bytes):
        self.headers = {"Content-Length": str(len(payload))}
        self._stream = BytesIO(payload)

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)

    def close(self) -> None:
        pass


class _FakeOpener:
    def __init__(self, payload: bytes):
        self.payload = payload

    def open(self, request, timeout: int):
        return _FakeResponse(self.payload)


class DatasetPreflightApiTests(unittest.TestCase):
    def test_verified_dataset_preflight_returns_authoritative_scope_and_safe_quality_state(self):
        payload = _zip_payload()
        registry = PublicDownloadRegistry(
            [
                PublicSourceSpec(
                    source_id="fixture-source",
                    allowed_hosts=frozenset({"public.example"}),
                    allowed_path_prefixes=("/datasets",),
                )
            ]
        )
        plan = registry.create_plan(
            source_id="fixture-source",
            url="https://public.example/datasets/bars.zip",
            filename="bars.zip",
            expected_sha256=hashlib.sha256(payload).hexdigest(),
            expected_bytes=len(payload),
            max_bytes=1024 * 1024,
            inner_filename="BTCUSDT-1h-2025-01-01.csv",
        )
        definition = PublicDatasetDefinition(
            dataset_id="fixture-source-btcusdt-1h-2025-01-01",
            plan=plan,
            symbol="BTCUSDT",
            interval="1h",
            period_start="2025-01-01",
            period_end="2025-01-02",
        )
        original_catalog = api.DATASET_CATALOG
        with tempfile.TemporaryDirectory() as directory:
            try:
                api.DATASET_CATALOG = PublicDatasetCatalog(Path(directory), [definition])
                download_to_cache(plan, Path(directory), opener=_FakeOpener(payload))
                response = Response()

                result = api.get_dataset_preflight(definition.dataset_id, response).model_dump(mode="json")

                self.assertEqual(
                    result,
                    {
                        "dataset_id": definition.dataset_id,
                        "artifact_status": "VERIFIED",
                        "preflight_status": "READY",
                        "instrument": "BTCUSDT",
                        "interval": "1h",
                        "period_start": "2025-01-01",
                        "period_end": "2025-01-02",
                        "bar_count": 2,
                        "timestamp_unit": "microseconds",
                        "timezone": "UTC",
                        "data_quality_status": "UNKNOWN",
                        "data_quality_message": "Bu fazda analitik veri kalite uyarısı üretilmiyor.",
                        "artifact": {"sha256": hashlib.sha256(payload).hexdigest(), "byte_size": len(payload)},
                        "read_only": True,
                    },
                )
                self.assertNotIn("url", json.dumps(result))
                self.assertNotIn("path", json.dumps(result))
                self.assertEqual(response.headers["cache-control"], "no-store")
            finally:
                api.DATASET_CATALOG = original_catalog

    def test_verified_dataset_run_plan_binds_dataset_preflight_to_current_offline_config(self):
        payload = _zip_payload()
        registry = PublicDownloadRegistry(
            [
                PublicSourceSpec(
                    source_id="fixture-source",
                    allowed_hosts=frozenset({"public.example"}),
                    allowed_path_prefixes=("/datasets",),
                )
            ]
        )
        plan = registry.create_plan(
            source_id="fixture-source",
            url="https://public.example/datasets/bars.zip",
            filename="bars.zip",
            expected_sha256=hashlib.sha256(payload).hexdigest(),
            expected_bytes=len(payload),
            max_bytes=1024 * 1024,
            inner_filename="BTCUSDT-1h-2025-01-01.csv",
        )
        definition = PublicDatasetDefinition(
            dataset_id="fixture-source-btcusdt-1h-2025-01-01",
            plan=plan,
            symbol="BTCUSDT",
            interval="1h",
            period_start="2025-01-01",
            period_end="2025-01-02",
        )
        config = json.loads(api.CONFIG_PATH.read_text(encoding="utf-8"))
        config_hash = hashlib.sha256(
            json.dumps(config, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()
        original_catalog = api.DATASET_CATALOG
        with tempfile.TemporaryDirectory() as directory:
            try:
                api.DATASET_CATALOG = PublicDatasetCatalog(Path(directory), [definition])
                download_to_cache(plan, Path(directory), opener=_FakeOpener(payload))
                response = Response()

                result = api.get_dataset_run_plan(definition.dataset_id, response).model_dump(mode="json")

                self.assertEqual(
                    result,
                    {
                        "dataset": {
                            "dataset_id": definition.dataset_id,
                            "artifact_status": "VERIFIED",
                            "preflight_status": "READY",
                            "instrument": "BTCUSDT",
                            "interval": "1h",
                            "period_start": "2025-01-01",
                            "period_end": "2025-01-02",
                            "bar_count": 2,
                            "timestamp_unit": "microseconds",
                            "timezone": "UTC",
                            "data_quality_status": "UNKNOWN",
                            "data_quality_message": "Bu fazda analitik veri kalite uyarısı üretilmiyor.",
                            "artifact": {"sha256": hashlib.sha256(payload).hexdigest(), "byte_size": len(payload)},
                            "read_only": True,
                        },
                        "config": {
                            "schema_version": 1,
                            "config_hash": config_hash,
                            "mode": "offline",
                            "symbol": "BTCUSDT",
                            "base_asset": "BTC",
                            "quote_asset": "USDT",
                            "base_qty": "1",
                            "safety_qty": "1",
                            "safety_count": 2,
                            "deviation": "0.1",
                            "target_mode": "GROSS_PRICE_RETURN",
                            "fee_rate": "0.001",
                            "slippage": "0",
                        },
                        "profile": {
                            "profile_id": "paper",
                            "profile_version": "1",
                            "label": "Paper config (v1)",
                            "expected_dataset_id": None,
                            "venue_filter_provenance": "project_fixture",
                            "historical_filter_claim": False,
                            "anchor_source": "dataset_first_bar_open",
                        },
                        "execution_mode": "SIMULATED",
                        "run_status": "NOT_STARTED",
                        "read_only": True,
                    },
                )
                self.assertNotIn("url", json.dumps(result))
                self.assertNotIn("path", json.dumps(result))
                self.assertEqual(response.headers["cache-control"], "no-store")
            finally:
                api.DATASET_CATALOG = original_catalog

    def test_historical_run_validation_accepts_current_verified_revisions_without_execution(self):
        payload = _zip_payload()
        registry = PublicDownloadRegistry(
            [
                PublicSourceSpec(
                    source_id="fixture-source",
                    allowed_hosts=frozenset({"public.example"}),
                    allowed_path_prefixes=("/datasets",),
                )
            ]
        )
        plan = registry.create_plan(
            source_id="fixture-source",
            url="https://public.example/datasets/bars.zip",
            filename="bars.zip",
            expected_sha256=hashlib.sha256(payload).hexdigest(),
            expected_bytes=len(payload),
            max_bytes=1024 * 1024,
            inner_filename="BTCUSDT-1h-2025-01-01.csv",
        )
        definition = PublicDatasetDefinition(
            dataset_id="fixture-source-btcusdt-1h-2025-01-01",
            plan=plan,
            symbol="BTCUSDT",
            interval="1h",
            period_start="2025-01-01",
            period_end="2025-01-02",
        )
        config = json.loads(api.CONFIG_PATH.read_text(encoding="utf-8"))
        config_hash = hashlib.sha256(
            json.dumps(config, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()
        original_catalog = api.DATASET_CATALOG
        with tempfile.TemporaryDirectory() as directory:
            try:
                api.DATASET_CATALOG = PublicDatasetCatalog(Path(directory), [definition])
                download_to_cache(plan, Path(directory), opener=_FakeOpener(payload))
                result = api.validate_historical_run(
                    api.HistoricalRunValidationRequest(
                        dataset_id=definition.dataset_id,
                        profile_id="paper",
                        artifact_sha256=hashlib.sha256(payload).hexdigest(),
                        config_hash=config_hash,
                        execution_mode="SIMULATED",
                    ),
                    Response(),
                )

                self.assertEqual(result.validation_status, "READY")
                self.assertEqual(result.run_status, "NOT_STARTED")
                self.assertTrue(result.read_only)
                self.assertTrue(result.offline)
                self.assertEqual(result.execution_mode, "SIMULATED")
                self.assertEqual(result.dataset.bar_count, 2)
                self.assertEqual(result.dataset.artifact_sha256, hashlib.sha256(payload).hexdigest())
                self.assertEqual(result.config.config_hash, config_hash)
                serialized = json.dumps(result.model_dump(mode="json"))
                self.assertNotIn("url", serialized)
                self.assertNotIn("path", serialized)
            finally:
                api.DATASET_CATALOG = original_catalog

    def test_historical_run_validation_rejects_stale_revision(self):
        payload = _zip_payload()
        registry = PublicDownloadRegistry(
            [
                PublicSourceSpec(
                    source_id="fixture-source",
                    allowed_hosts=frozenset({"public.example"}),
                    allowed_path_prefixes=("/datasets",),
                )
            ]
        )
        plan = registry.create_plan(
            source_id="fixture-source",
            url="https://public.example/datasets/bars.zip",
            filename="bars.zip",
            expected_sha256=hashlib.sha256(payload).hexdigest(),
            expected_bytes=len(payload),
            max_bytes=1024 * 1024,
            inner_filename="BTCUSDT-1h-2025-01-01.csv",
        )
        definition = PublicDatasetDefinition(
            dataset_id="fixture-source-btcusdt-1h-2025-01-01",
            plan=plan,
            symbol="BTCUSDT",
            interval="1h",
            period_start="2025-01-01",
            period_end="2025-01-02",
        )
        config = json.loads(api.CONFIG_PATH.read_text(encoding="utf-8"))
        config_hash = hashlib.sha256(
            json.dumps(config, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()
        original_catalog = api.DATASET_CATALOG
        with tempfile.TemporaryDirectory() as directory:
            try:
                api.DATASET_CATALOG = PublicDatasetCatalog(Path(directory), [definition])
                download_to_cache(plan, Path(directory), opener=_FakeOpener(payload))
                result = api.validate_historical_run(
                    api.HistoricalRunValidationRequest(
                        dataset_id=definition.dataset_id,
                        profile_id="paper",
                        artifact_sha256="a" * 64,
                        config_hash=config_hash,
                        execution_mode="SIMULATED",
                    ),
                    Response(),
                )

                self.assertEqual(result.status_code, 409)
                self.assertEqual(json.loads(result.body)["code"], "ARTIFACT_REVISION_CONFLICT")
            finally:
                api.DATASET_CATALOG = original_catalog

    def test_historical_run_validation_request_forbids_free_form_fields(self):
        with self.assertRaises(ValueError):
            api.HistoricalRunValidationRequest(
                dataset_id="fixture-source-btcusdt-1h-2025-01-01",
                profile_id="paper",
                artifact_sha256="a" * 64,
                config_hash="b" * 64,
                execution_mode="SIMULATED",
                config={"base_qty": "1000000"},
            )
