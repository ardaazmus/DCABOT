import hashlib
from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from zipfile import ZIP_DEFLATED, ZipFile

from dcabot.data_adapters.public_download import download_to_cache
from dcabot.data_adapters.public_sources import PublicDownloadError, PublicDownloadRegistry, PublicSourceSpec


def _zip_payload() -> bytes:
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("BTCUSDT-1h-2025-01-01.csv", "open_time,open\n1,2\n")
    return output.getvalue()


class _FakeResponse:
    def __init__(self, payload: bytes, headers: dict[str, str] | None = None):
        self.status = 200
        self.headers = headers or {}
        self._body = BytesIO(payload)
        self.closed = False

    def read(self, size: int = -1) -> bytes:
        return self._body.read(size)

    def close(self) -> None:
        self.closed = True


class _FakeOpener:
    def __init__(self, response: _FakeResponse):
        self.response = response
        self.requests = []

    def open(self, request, timeout: int):
        self.requests.append((request, timeout))
        return self.response


class PublicDownloadTests(unittest.TestCase):
    def setUp(self):
        self.registry = PublicDownloadRegistry(
            [
                PublicSourceSpec(
                    source_id="fixture-source",
                    allowed_hosts=frozenset({"public.example"}),
                    allowed_path_prefixes=("/datasets",),
                )
            ]
        )
        self.payload = _zip_payload()

    def _plan(self, expected_sha256: str | None = None, expected_bytes: int | None = None):
        return self.registry.create_plan(
            source_id="fixture-source",
            url="https://public.example/datasets/bars.zip",
            filename="bars.zip",
            expected_sha256=expected_sha256 or hashlib.sha256(self.payload).hexdigest(),
            expected_bytes=len(self.payload) if expected_bytes is None else expected_bytes,
            max_bytes=1024,
            inner_filename="BTCUSDT-1h-2025-01-01.csv",
        )

    def test_download_verifies_zip_and_publishes_atomic_cache(self):
        response = _FakeResponse(self.payload, {"Content-Length": str(len(self.payload))})
        opener = _FakeOpener(response)
        with tempfile.TemporaryDirectory() as directory:
            result = download_to_cache(self._plan(), Path(directory), opener=opener, chunk_bytes=7)

            self.assertFalse(result.cache_hit)
            self.assertEqual(result.metadata.byte_count, len(self.payload))
            self.assertEqual(result.cache_path.read_bytes(), self.payload)
            self.assertTrue(result.cache_path.with_suffix(".json").is_file())
            self.assertEqual(len(opener.requests), 1)
            self.assertEqual(opener.requests[0][1], 30)

            cached = download_to_cache(self._plan(), Path(directory), opener=opener)

            self.assertTrue(cached.cache_hit)
            self.assertEqual(len(opener.requests), 1)

    def test_checksum_mismatch_never_publishes_final_cache(self):
        response = _FakeResponse(self.payload)
        opener = _FakeOpener(response)
        plan = self._plan(expected_sha256="0" * 64)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(PublicDownloadError):
                download_to_cache(plan, Path(directory), opener=opener)

            self.assertEqual(list(Path(directory).glob("*.zip")), [])
            self.assertEqual(list(Path(directory).glob("*.json")), [])
            self.assertEqual(list(Path(directory).glob("*.part")), [])

    def test_declared_content_length_is_rejected_before_body_read(self):
        response = _FakeResponse(self.payload, {"Content-Length": "1025"})
        opener = _FakeOpener(response)
        plan = self._plan()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(PublicDownloadError):
                download_to_cache(plan, Path(directory), opener=opener)

            self.assertEqual(response._body.tell(), 0)
