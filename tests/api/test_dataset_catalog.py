from io import BytesIO
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZIP_DEFLATED, ZipFile

from starlette.responses import Response

from dcabot.data_adapters.catalog import PublicDatasetCatalog, PublicDatasetDefinition
from dcabot.data_adapters.download_jobs import DownloadJobNotFound, DownloadJobSnapshot, DownloadJobStatus
from dcabot.data_adapters.public_download import download_to_cache
from dcabot.data_adapters.public_sources import PublicDownloadRegistry, PublicSourceSpec
import dcabot.server.api as api


def _zip_payload() -> bytes:
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("BTCUSDT-1h-2025-01-01.csv", "open_time,open\n1,2\n")
    return output.getvalue()


class _FakeResponse:
    status = 200

    def __init__(self, payload: bytes):
        self.headers = {"Content-Length": str(len(payload))}
        self._payload = BytesIO(payload)

    def read(self, size: int = -1) -> bytes:
        return self._payload.read(size)

    def close(self) -> None:
        pass


class _FakeOpener:
    def __init__(self, payload: bytes):
        self.response = _FakeResponse(payload)

    def open(self, request, timeout: int):
        return self.response


class _StubDownloadJobs:
    def __init__(self):
        self.snapshot = DownloadJobSnapshot(
            job_id="job-1",
            dataset_id="fixture-source-btcusdt-1h-2025-01-01",
            status=DownloadJobStatus.RUNNING,
            attempt=1,
            max_attempts=3,
            bytes_downloaded=128,
            total_bytes=512,
            cache_hit=None,
            error_code=None,
            error_message=None,
        )

    def start(self, dataset_id, plan, cache_dir):
        return self.snapshot.job_id

    def get(self, job_id):
        if job_id != self.snapshot.job_id:
            raise DownloadJobNotFound("missing")
        return self.snapshot

    def cancel(self, job_id):
        if job_id != self.snapshot.job_id:
            raise DownloadJobNotFound("missing")
        self.snapshot = replace(self.snapshot, status=DownloadJobStatus.CANCELLED)
        return self.snapshot


class DatasetCatalogApiTests(unittest.TestCase):
    def setUp(self):
        self.payload = _zip_payload()
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
            expected_sha256=hashlib.sha256(self.payload).hexdigest(),
            expected_bytes=len(self.payload),
            max_bytes=1024,
            inner_filename="BTCUSDT-1h-2025-01-01.csv",
        )
        self.definition = PublicDatasetDefinition(
            dataset_id="fixture-source-btcusdt-1h-2025-01-01",
            plan=plan,
            symbol="BTCUSDT",
            interval="1h",
            period_start="2025-01-01",
            period_end="2025-01-02",
        )
        self.original_catalog = api.DATASET_CATALOG
        self.original_download_jobs = api.DOWNLOAD_JOBS
        self.directory = tempfile.TemporaryDirectory()
        api.DATASET_CATALOG = PublicDatasetCatalog(Path(self.directory.name), [self.definition])
        api.DOWNLOAD_JOBS = _StubDownloadJobs()

    def tearDown(self):
        api.DATASET_CATALOG = self.original_catalog
        api.DOWNLOAD_JOBS = self.original_download_jobs
        self.directory.cleanup()

    def test_list_returns_contract_without_local_paths(self):
        response = Response()

        payload = api.list_datasets(response).model_dump(mode="json")

        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["datasets"][0]["status"], "MISSING")
        self.assertIsNone(payload["datasets"][0]["artifact"])
        self.assertNotIn("path", json.dumps(payload))
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_selection_returns_verified_summary_and_known_missing_is_409(self):
        missing_response = Response()
        missing = api.select_dataset(
            api.DatasetSelectionRequest(dataset_id=self.definition.dataset_id),
            missing_response,
        )
        self.assertEqual(missing.status_code, 409)
        self.assertEqual(json.loads(missing.body)["code"], "DATASET_CACHE_MISSING")

        download_to_cache(
            self.definition.plan,
            Path(self.directory.name),
            opener=_FakeOpener(self.payload),
        )
        response = Response()

        selected = api.select_dataset(
            api.DatasetSelectionRequest(dataset_id=self.definition.dataset_id),
            response,
        ).model_dump(mode="json")

        self.assertEqual(selected["selected"]["status"], "VERIFIED")
        self.assertEqual(selected["selected"]["artifact"]["byte_size"], len(self.payload))
        self.assertNotIn("path", json.dumps(selected))
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_unknown_selection_is_404(self):
        response = Response()

        result = api.select_dataset(
            api.DatasetSelectionRequest(dataset_id="unknown-dataset"),
            response,
        )

        self.assertEqual(result.status_code, 404)
        self.assertEqual(json.loads(result.body)["code"], "DATASET_NOT_FOUND")

    def test_corrupt_selection_is_409(self):
        download_to_cache(
            self.definition.plan,
            Path(self.directory.name),
            opener=_FakeOpener(self.payload),
        )
        next(Path(self.directory.name).glob("*.zip")).write_bytes(b"tampered")
        response = Response()

        result = api.select_dataset(
            api.DatasetSelectionRequest(dataset_id=self.definition.dataset_id),
            response,
        )

        self.assertEqual(result.status_code, 409)
        self.assertEqual(json.loads(result.body)["code"], "DATASET_CACHE_CORRUPT")

    def test_download_start_status_and_cancel_never_expose_paths_or_urls(self):
        response = Response()
        started = api.start_dataset_download(
            api.DatasetSelectionRequest(dataset_id=self.definition.dataset_id),
            response,
        ).model_dump(mode="json")

        self.assertEqual(started["job"]["status"], "RUNNING")
        self.assertEqual(started["job"]["bytes_downloaded"], 128)
        self.assertNotIn("url", json.dumps(started))
        self.assertNotIn("path", json.dumps(started))

        status_response = Response()
        status = api.get_dataset_download("job-1", status_response).model_dump(mode="json")
        self.assertEqual(status["status"], "RUNNING")
        self.assertEqual(status_response.headers["cache-control"], "no-store")

        cancel_response = Response()
        cancelled = api.cancel_dataset_download("job-1", cancel_response).model_dump(mode="json")
        self.assertEqual(cancelled["status"], "CANCELLED")
        self.assertEqual(cancel_response.headers["cache-control"], "no-store")

    def test_download_start_unknown_dataset_is_404(self):
        response = Response()
        result = api.start_dataset_download(
            api.DatasetSelectionRequest(dataset_id="unknown-dataset"),
            response,
        )

        self.assertEqual(result.status_code, 404)
        self.assertEqual(json.loads(result.body)["code"], "DATASET_NOT_FOUND")
