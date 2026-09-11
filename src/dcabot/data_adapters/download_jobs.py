"""Bounded in-memory orchestration for local public dataset downloads."""

from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from threading import Event, Lock, Thread
from uuid import uuid4

from dcabot.data_adapters.public_download import (
    DownloadOpener,
    PublicDownloadError,
    download_to_cache,
)
from dcabot.data_adapters.public_sources import PublicDownloadPlan


class DownloadJobStatus(str, Enum):
    """Lifecycle states exposed by the local download job contract."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    RETRYING = "RETRYING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


TERMINAL_STATUSES = frozenset(
    {DownloadJobStatus.SUCCEEDED, DownloadJobStatus.FAILED, DownloadJobStatus.CANCELLED}
)


class DownloadJobNotFound(LookupError):
    """Raised when a requested in-memory job ID does not exist."""


class DownloadJobConflict(ValueError):
    """Raised when an active download already owns the requested dataset."""


@dataclass(frozen=True, slots=True)
class DownloadJobSnapshot:
    """Safe job state with progress but without URL or local path fields."""

    job_id: str
    dataset_id: str
    status: DownloadJobStatus
    attempt: int
    max_attempts: int
    bytes_downloaded: int
    total_bytes: int | None
    cache_hit: bool | None
    error_code: str | None
    error_message: str | None


@dataclass(slots=True)
class _JobRecord:
    snapshot: DownloadJobSnapshot
    plan: PublicDownloadPlan
    cache_dir: Path
    opener: DownloadOpener | None
    cancel: Event


class DownloadJobManager:
    """Runs allowlisted downloads in daemon threads with bounded retry state."""

    def __init__(self, *, max_attempts: int = 3, retry_delay_seconds: float = 0.25) -> None:
        if type(max_attempts) is not int or not 0 < max_attempts <= 5:
            raise ValueError("Download job deneme sınırı geçersiz.")
        if type(retry_delay_seconds) not in (int, float) or not 0 <= retry_delay_seconds <= 60:
            raise ValueError("Download job retry gecikmesi geçersiz.")
        self._max_attempts = max_attempts
        self._retry_delay_seconds = float(retry_delay_seconds)
        self._lock = Lock()
        self._jobs: dict[str, _JobRecord] = {}
        self._active_by_dataset: dict[str, str] = {}

    def start(
        self,
        dataset_id: str,
        plan: PublicDownloadPlan,
        cache_dir: Path,
        *,
        opener: DownloadOpener | None = None,
    ) -> str:
        """Queue one explicit dataset download and return its opaque job ID."""

        if not dataset_id or not isinstance(cache_dir, Path):
            raise ValueError("Download job girdisi geçersiz.")
        with self._lock:
            active_id = self._active_by_dataset.get(dataset_id)
            if active_id is not None:
                active = self._jobs[active_id].snapshot
                if active.status not in TERMINAL_STATUSES:
                    raise DownloadJobConflict("Dataset için aktif download job var.")
            job_id = uuid4().hex
            snapshot = DownloadJobSnapshot(
                job_id=job_id,
                dataset_id=dataset_id,
                status=DownloadJobStatus.QUEUED,
                attempt=0,
                max_attempts=self._max_attempts,
                bytes_downloaded=0,
                total_bytes=plan.expected_bytes,
                cache_hit=None,
                error_code=None,
                error_message=None,
            )
            record = _JobRecord(snapshot, plan, cache_dir, opener, Event())
            self._jobs[job_id] = record
            self._active_by_dataset[dataset_id] = job_id
        Thread(target=self._run, args=(job_id,), daemon=True).start()
        return job_id

    def get(self, job_id: str) -> DownloadJobSnapshot:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                raise DownloadJobNotFound("Download job bulunamadı.")
            return record.snapshot

    def cancel(self, job_id: str) -> DownloadJobSnapshot:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                raise DownloadJobNotFound("Download job bulunamadı.")
            if record.snapshot.status in TERMINAL_STATUSES:
                return record.snapshot
            record.cancel.set()
            record.snapshot = replace(
                record.snapshot,
                status=DownloadJobStatus.CANCELLED,
                error_code="DOWNLOAD_CANCELLED",
                error_message="Download iptal edildi; doğrulanmış cache yayımlanmadı.",
            )
            self._active_by_dataset.pop(record.snapshot.dataset_id, None)
            return record.snapshot

    def _run(self, job_id: str) -> None:
        record = self._jobs[job_id]
        for attempt in range(1, self._max_attempts + 1):
            if record.cancel.is_set() or self._is_terminal(job_id):
                return
            self._update(
                job_id,
                status=DownloadJobStatus.RUNNING,
                attempt=attempt,
                bytes_downloaded=0,
                total_bytes=record.plan.expected_bytes,
                error_code=None,
                error_message=None,
            )
            try:
                result = download_to_cache(
                    record.plan,
                    record.cache_dir,
                    opener=record.opener,
                    on_progress=lambda byte_count, total: self._progress(job_id, byte_count, total),
                    cancel_check=record.cancel.is_set,
                )
            except PublicDownloadError:
                if record.cancel.is_set() or self._is_terminal(job_id):
                    return
                if attempt < self._max_attempts:
                    self._update(job_id, status=DownloadJobStatus.RETRYING, attempt=attempt)
                    if record.cancel.wait(self._retry_delay_seconds):
                        self.cancel(job_id)
                        return
                    continue
                self._finish(
                    job_id,
                    status=DownloadJobStatus.FAILED,
                    error_code="DOWNLOAD_FAILED",
                    error_message="Public dataset indirilemedi; doğrulanmış cache yayımlanmadı.",
                )
                return
            except Exception:
                self._finish(
                    job_id,
                    status=DownloadJobStatus.FAILED,
                    error_code="DOWNLOAD_INTERNAL_ERROR",
                    error_message="Download işleyicisinde beklenmeyen teknik hata oluştu.",
                )
                return
            self._finish(
                job_id,
                status=DownloadJobStatus.SUCCEEDED,
                bytes_downloaded=result.metadata.byte_count,
                total_bytes=result.metadata.byte_count,
                cache_hit=result.cache_hit,
            )
            return

    def _progress(self, job_id: str, byte_count: int, total_bytes: int | None) -> None:
        self._update(job_id, bytes_downloaded=byte_count, total_bytes=total_bytes)

    def _is_terminal(self, job_id: str) -> bool:
        with self._lock:
            record = self._jobs.get(job_id)
            return record is None or record.snapshot.status in TERMINAL_STATUSES

    def _update(self, job_id: str, **changes: object) -> None:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None or record.snapshot.status in TERMINAL_STATUSES:
                return
            record.snapshot = replace(record.snapshot, **changes)

    def _finish(self, job_id: str, **changes: object) -> None:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None or record.snapshot.status in TERMINAL_STATUSES:
                return
            record.snapshot = replace(record.snapshot, **changes)
            self._active_by_dataset.pop(record.snapshot.dataset_id, None)
