"""Bounded HTTPS download and atomic cache for verified public artifacts."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import os
from pathlib import PurePosixPath
from stat import S_IFLNK, S_IFMT
import tempfile
from typing import BinaryIO, Callable, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from zipfile import BadZipFile, ZipFile

from dcabot.data_adapters.public_sources import (
    PublicArtifactMetadata,
    PublicDownloadError,
    PublicDownloadPlan,
)


DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_CHUNK_BYTES = 64 * 1024


class DownloadResponse(Protocol):
    status: int
    headers: object

    def read(self, size: int = -1) -> bytes: ...

    def close(self) -> None: ...


class DownloadOpener(Protocol):
    def open(self, request: Request, timeout: int) -> DownloadResponse: ...


ProgressReporter = Callable[[int, int | None], None]
CancelCheck = Callable[[], bool]


@dataclass(frozen=True, slots=True)
class CachedPublicArtifact:
    """Verified artifact metadata and its content-addressed cache location."""

    metadata: PublicArtifactMetadata
    cache_path: Path
    cache_hit: bool


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, new):
        raise PublicDownloadError("Public kaynak yönlendirmesi reddedildi.")


class DownloadCancelled(PublicDownloadError):
    """Raised when a caller cancels a download before verification completes."""


def download_to_cache(
    plan: PublicDownloadPlan,
    cache_dir: Path,
    *,
    opener: DownloadOpener | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    chunk_bytes: int = DEFAULT_CHUNK_BYTES,
    on_progress: ProgressReporter | None = None,
    cancel_check: CancelCheck | None = None,
) -> CachedPublicArtifact:
    """Download one plan, verify it, and publish it as a content-addressed ZIP."""

    _validate_runtime_options(cache_dir, timeout_seconds, chunk_bytes)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = inspect_cached_artifact(plan, cache_dir)
    if cached is not None:
        return cached
    final_path, metadata_path = _cache_paths(plan, cache_dir)

    opener = opener or build_opener(_NoRedirectHandler())
    request = Request(
        plan.url,
        headers={
            "Accept": "application/zip,application/octet-stream;q=0.9,*/*;q=0.1",
            "Accept-Encoding": "identity",
        },
        method="GET",
    )
    staging_path: Path | None = None
    try:
        response = _open_response(opener, request, timeout_seconds)
        try:
            _validate_response_headers(response, plan)
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=cache_dir, prefix=".dcabot-", suffix=".part", delete=False
            ) as staging:
                staging_path = Path(staging.name)
                byte_count, sha256 = _stream_response(
                    response, staging, plan, chunk_bytes, on_progress, cancel_check
                )
                staging.flush()
                os.fsync(staging.fileno())
            metadata = _verify_staged_zip(plan, staging_path, byte_count, sha256)
            os.replace(staging_path, final_path)
            staging_path = None
            _write_metadata(metadata_path, metadata)
            return CachedPublicArtifact(metadata, final_path, False)
        finally:
            response.close()
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise PublicDownloadError(f"Public indirme başarısız: {exc}") from exc
    finally:
        if staging_path is not None:
            staging_path.unlink(missing_ok=True)


def inspect_cached_artifact(
    plan: PublicDownloadPlan, cache_dir: Path
) -> CachedPublicArtifact | None:
    """Return a verified local artifact without creating files or using the network."""

    _validate_runtime_options(cache_dir, DEFAULT_TIMEOUT_SECONDS, DEFAULT_CHUNK_BYTES)
    if not cache_dir.exists():
        return None
    final_path, metadata_path = _cache_paths(plan, cache_dir)
    cached = _read_verified_cache(plan, final_path, metadata_path)
    if cached is None:
        return None
    return CachedPublicArtifact(cached, final_path, True)


def _cache_paths(plan: PublicDownloadPlan, cache_dir: Path) -> tuple[Path, Path]:
    return (
        cache_dir / f"{plan.expected_sha256}.zip",
        cache_dir / f"{plan.expected_sha256}.json",
    )


def _validate_runtime_options(cache_dir: Path, timeout_seconds: int, chunk_bytes: int) -> None:
    if not isinstance(cache_dir, Path) or cache_dir.exists() and not cache_dir.is_dir():
        raise PublicDownloadError("Cache klasörü geçersiz.")
    if type(timeout_seconds) is not int or timeout_seconds <= 0:
        raise PublicDownloadError("İndirme timeout değeri geçersiz.")
    if type(chunk_bytes) is not int or not 0 < chunk_bytes <= 1024 * 1024:
        raise PublicDownloadError("İndirme chunk sınırı geçersiz.")


def _open_response(opener: DownloadOpener, request: Request, timeout_seconds: int) -> DownloadResponse:
    try:
        response = opener.open(request, timeout=timeout_seconds)
    except PublicDownloadError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise PublicDownloadError(f"Public kaynak açılamadı: {exc}") from exc
    status = getattr(response, "status", None) or response.getcode()
    if status != 200:
        response.close()
        raise PublicDownloadError(f"Public kaynak HTTP {status} döndürdü.")
    return response


def _validate_response_headers(response: DownloadResponse, plan: PublicDownloadPlan) -> None:
    headers = response.headers
    content_length = headers.get("Content-Length")
    if content_length is not None:
        try:
            declared = int(content_length)
        except (TypeError, ValueError) as exc:
            raise PublicDownloadError("Content-Length geçersiz.") from exc
        if declared < 0 or declared > plan.max_bytes:
            raise PublicDownloadError("Content-Length byte sınırını aşıyor.")
    encoding = headers.get("Content-Encoding")
    if encoding and encoding.lower() != "identity":
        raise PublicDownloadError("Beklenmeyen Content-Encoding reddedildi.")


def _stream_response(
    response: DownloadResponse,
    staging: BinaryIO,
    plan: PublicDownloadPlan,
    chunk_bytes: int,
    on_progress: ProgressReporter | None,
    cancel_check: CancelCheck | None,
) -> tuple[int, str]:
    digest = hashlib.sha256()
    byte_count = 0
    if on_progress:
        on_progress(0, plan.expected_bytes)
    while True:
        if cancel_check and cancel_check():
            raise DownloadCancelled("Public indirme iptal edildi.")
        chunk = response.read(chunk_bytes)
        if not chunk:
            break
        if not isinstance(chunk, bytes):
            raise PublicDownloadError("Public response gövdesi bytes olmalıdır.")
        byte_count += len(chunk)
        if byte_count > plan.max_bytes:
            raise PublicDownloadError("İndirilen payload byte sınırını aşıyor.")
        digest.update(chunk)
        staging.write(chunk)
        if on_progress:
            on_progress(byte_count, plan.expected_bytes)
    return byte_count, digest.hexdigest()


def _verify_staged_zip(
    plan: PublicDownloadPlan, staging_path: Path, byte_count: int, sha256: str
) -> PublicArtifactMetadata:
    if plan.expected_bytes is not None and byte_count != plan.expected_bytes:
        raise PublicDownloadError("İndirilen payload byte sayısı metadata ile eşleşmiyor.")
    if sha256 != plan.expected_sha256:
        raise PublicDownloadError("İndirilen payload SHA-256 metadata ile eşleşmiyor.")
    _validate_zip(staging_path, plan)
    return PublicArtifactMetadata(
        source_id=plan.source_id,
        url=plan.url,
        filename=plan.filename,
        byte_count=byte_count,
        sha256=sha256,
    )


def _validate_zip(path: Path, plan: PublicDownloadPlan) -> None:
    try:
        with ZipFile(path) as archive:
            members = archive.infolist()
            if not members or len(members) > plan.max_members:
                raise PublicDownloadError("ZIP üye sayısı sınırı dışında.")
            expanded_bytes = 0
            csv_names: list[str] = []
            for member in members:
                _validate_zip_member(member.filename, member.external_attr)
                expanded_bytes += member.file_size
                if expanded_bytes > plan.max_expanded_bytes:
                    raise PublicDownloadError("Açılmış ZIP byte sınırını aşıyor.")
                if member.filename.lower().endswith(".csv"):
                    csv_names.append(member.filename)
            if len(csv_names) != 1 or (
                plan.inner_filename is not None and plan.inner_filename != csv_names[0]
            ):
                raise PublicDownloadError("ZIP iç CSV dosyası beklenen adla eşleşmiyor.")
            if archive.testzip() is not None:
                raise PublicDownloadError("ZIP CRC doğrulaması başarısız.")
    except BadZipFile as exc:
        raise PublicDownloadError("İndirilen dosya geçerli ZIP değil.") from exc


def _validate_zip_member(filename: str, external_attr: int) -> None:
    path = PurePosixPath(filename)
    if (
        not filename
        or filename.startswith(("/", "\\"))
        or "\\" in filename
        or path.is_absolute()
        or ".." in path.parts
        or ":" in path.parts[0]
    ):
        raise PublicDownloadError("ZIP iç yolu güvenli değil.")
    if S_IFMT(external_attr >> 16) == S_IFLNK:
        raise PublicDownloadError("ZIP symlink üyesi reddedildi.")


def _read_verified_cache(
    plan: PublicDownloadPlan, final_path: Path, metadata_path: Path
) -> PublicArtifactMetadata | None:
    if not final_path.is_file() or final_path.is_symlink() or not metadata_path.is_file():
        return None
    try:
        payload = final_path.read_bytes()
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("sha256") != plan.expected_sha256:
            return None
        verified = _verify_staged_zip(plan, final_path, len(payload), hashlib.sha256(payload).hexdigest())
        if metadata != _metadata_dict(verified):
            return None
        return verified
    except (OSError, UnicodeError, json.JSONDecodeError, PublicDownloadError):
        return None


def _write_metadata(path: Path, metadata: PublicArtifactMetadata) -> None:
    content = json.dumps(_metadata_dict(metadata), ensure_ascii=False, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=".dcabot-", suffix=".json.part", delete=False
    ) as staging:
        staging_path = Path(staging.name)
        staging.write(content)
        staging.flush()
        os.fsync(staging.fileno())
    try:
        os.replace(staging_path, path)
    finally:
        staging_path.unlink(missing_ok=True)


def _metadata_dict(metadata: PublicArtifactMetadata) -> dict[str, object]:
    return {
        "source_id": metadata.source_id,
        "url": metadata.url,
        "filename": metadata.filename,
        "byte_count": metadata.byte_count,
        "sha256": metadata.sha256,
    }
