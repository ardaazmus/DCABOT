import tempfile
import time
import unittest
from pathlib import Path
from threading import Event
from unittest.mock import patch

from dcabot.data_adapters.download_jobs import (
    DownloadJobConflict,
    DownloadJobManager,
    DownloadJobStatus,
)
from dcabot.data_adapters.public_download import download_to_cache
from dcabot.data_adapters.public_sources import BINANCE_BTCUSDT_1H_2025_01_01_PLAN


class _Response:
    status = 200

    def __init__(self, payload: bytes, chunk: int = 2):
        self.headers = {"Content-Length": str(len(payload)), "Content-Encoding": "identity"}
        self._payload = payload
        self._chunk = chunk
        self._offset = 0
        self.closed = False

    def read(self, size: int = -1) -> bytes:
        if self._offset >= len(self._payload):
            return b""
        end = min(self._offset + min(size, self._chunk), len(self._payload))
        chunk = self._payload[self._offset:end]
        self._offset = end
        return chunk

    def close(self) -> None:
        self.closed = True


class _Opener:
    def __init__(self, payload: bytes, started: Event | None = None):
        self.payload = payload
        self.started = started
        self.calls = 0

    def open(self, request, timeout: int):
        self.calls += 1
        if self.started:
            self.started.set()
        return _Response(self.payload)


class _BlockingOpener(_Opener):
    def __init__(self):
        super().__init__(b"not-a-zip")
        self.release = Event()

    def open(self, request, timeout: int):
        self.calls += 1
        self.release.wait(timeout=2)
        return _Response(self.payload)


class DownloadJobTests(unittest.TestCase):
    def test_cancelled_download_leaves_no_part_and_reports_cancelled(self):
        with tempfile.TemporaryDirectory() as directory:
            cancel = Event()
            started = Event()

            def on_progress(byte_count: int, _total: int | None) -> None:
                if byte_count:
                    cancel.set()

            with self.assertRaises(ValueError):
                download_to_cache(
                    BINANCE_BTCUSDT_1H_2025_01_01_PLAN,
                    Path(directory),
                    opener=_Opener(b"not-a-zip", started),
                    chunk_bytes=2,
                    cancel_check=cancel.is_set,
                    on_progress=on_progress,
                )
            self.assertEqual(list(Path(directory).glob("*.part")), [])

    def test_job_retries_then_succeeds_and_reports_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            opener = _Opener(b"not-a-zip")
            manager = DownloadJobManager(max_attempts=2, retry_delay_seconds=0)
            job_id = manager.start(
                "dataset-id",
                BINANCE_BTCUSDT_1H_2025_01_01_PLAN,
                Path(directory),
                opener=opener,
            )
            deadline = time.monotonic() + 2
            snapshot = manager.get(job_id)
            while snapshot.status in {DownloadJobStatus.QUEUED, DownloadJobStatus.RUNNING, DownloadJobStatus.RETRYING} and time.monotonic() < deadline:
                time.sleep(0.01)
                snapshot = manager.get(job_id)
            self.assertEqual(snapshot.status, DownloadJobStatus.FAILED)
            self.assertEqual(snapshot.attempt, 2)
            self.assertEqual(opener.calls, 2)
            self.assertGreater(snapshot.bytes_downloaded, 0)

    def test_active_dataset_cannot_start_two_jobs(self):
        manager = DownloadJobManager()
        with tempfile.TemporaryDirectory() as directory:
            opener = _BlockingOpener()
            job_id = manager.start(
                "dataset-id",
                BINANCE_BTCUSDT_1H_2025_01_01_PLAN,
                Path(directory),
                opener=opener,
            )
            with self.assertRaises(DownloadJobConflict):
                manager.start(
                    "dataset-id",
                    BINANCE_BTCUSDT_1H_2025_01_01_PLAN,
                    Path(directory),
                    opener=_Opener(b"not-a-zip"),
                )
            manager.cancel(job_id)
            opener.release.set()

    def test_unexpected_job_error_fails_without_retrying_as_public_download_error(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = DownloadJobManager(max_attempts=3, retry_delay_seconds=0)
            with patch(
                "dcabot.data_adapters.download_jobs.download_to_cache",
                side_effect=TypeError("programming bug"),
            ):
                job_id = manager.start(
                    "dataset-id",
                    BINANCE_BTCUSDT_1H_2025_01_01_PLAN,
                    Path(directory),
                )
                deadline = time.monotonic() + 2
                snapshot = manager.get(job_id)
                while snapshot.status in {
                    DownloadJobStatus.QUEUED,
                    DownloadJobStatus.RUNNING,
                    DownloadJobStatus.RETRYING,
                } and time.monotonic() < deadline:
                    time.sleep(0.01)
                    snapshot = manager.get(job_id)

            self.assertEqual(snapshot.status, DownloadJobStatus.FAILED)
            self.assertEqual(snapshot.attempt, 1)
            self.assertEqual(snapshot.error_code, "DOWNLOAD_INTERNAL_ERROR")
