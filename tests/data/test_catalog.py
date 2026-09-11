import hashlib
from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from zipfile import ZIP_DEFLATED, ZipFile

from dcabot.data_adapters.catalog import (
    CatalogError,
    PublicDatasetCatalog,
    PublicDatasetDefinition,
)
from dcabot.data_adapters.public_download import download_to_cache
from dcabot.data_adapters.public_sources import PublicDownloadRegistry, PublicSourceSpec


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


class CatalogTests(unittest.TestCase):
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

    def test_catalog_lists_missing_then_verified_cache_and_selects_path(self):
        with tempfile.TemporaryDirectory() as directory:
            catalog = PublicDatasetCatalog(Path(directory), [self.definition])
            self.assertEqual(catalog.list_entries()[0].quality_status, "MISSING")

            download_to_cache(
                self.definition.plan,
                Path(directory),
                opener=_FakeOpener(self.payload),
            )

            entry = catalog.list_entries()[0]
            selection = catalog.select(self.definition.dataset_id)
            self.assertEqual(entry.quality_status, "VERIFIED")
            self.assertEqual(entry.sha256, self.definition.plan.expected_sha256)
            self.assertEqual(entry.byte_count, len(self.payload))
            self.assertEqual(selection.path.read_bytes(), self.payload)
            self.assertEqual(selection.inner_filename, "BTCUSDT-1h-2025-01-01.csv")

    def test_catalog_does_not_select_unknown_or_corrupt_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            catalog = PublicDatasetCatalog(Path(directory), [self.definition])
            with self.assertRaises(CatalogError):
                catalog.select("unknown")

            download_to_cache(
                self.definition.plan,
                Path(directory),
                opener=_FakeOpener(self.payload),
            )
            cache_path = next(Path(directory).glob("*.zip"))
            cache_path.write_bytes(b"tampered")

            self.assertEqual(catalog.list_entries()[0].quality_status, "CORRUPT")
            with self.assertRaises(CatalogError):
                catalog.select(self.definition.dataset_id)
