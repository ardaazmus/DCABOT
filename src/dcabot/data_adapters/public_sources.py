"""Network-free contracts for allowlisted public historical-data downloads."""

from dataclasses import dataclass
import hashlib
from pathlib import PurePosixPath
import re
from urllib.parse import unquote, urlsplit


MAX_PUBLIC_DOWNLOAD_BYTES = 256 * 1024 * 1024
_ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]{1,63}\Z")
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z", re.IGNORECASE)
_CHECKSUM_PATTERN = re.compile(r"([0-9a-f]{64})  ([^\r\n]+)(?:\r?\n)?\Z", re.IGNORECASE)


class PublicDownloadError(ValueError):
    """Raised when public-source metadata or a downloaded payload is unsafe."""


@dataclass(frozen=True, slots=True)
class PublicSourceSpec:
    """Describes the hosts and path roots allowed for one public source."""

    source_id: str
    allowed_hosts: frozenset[str]
    allowed_path_prefixes: tuple[str, ...]

    def __post_init__(self) -> None:
        if not _ID_PATTERN.fullmatch(self.source_id):
            raise PublicDownloadError("Public source ID geçersiz.")
        if not self.allowed_hosts or any(not host or host != host.lower() for host in self.allowed_hosts):
            raise PublicDownloadError("Public source host allowlist geçersiz.")
        if not self.allowed_path_prefixes or any(
            not prefix.startswith("/") or ".." in PurePosixPath(prefix).parts
            for prefix in self.allowed_path_prefixes
        ):
            raise PublicDownloadError("Public source path allowlist geçersiz.")


@dataclass(frozen=True, slots=True)
class PublicDownloadPlan:
    """Immutable request metadata checked before any future network download."""

    source_id: str
    url: str
    filename: str
    expected_sha256: str
    expected_bytes: int | None
    max_bytes: int = MAX_PUBLIC_DOWNLOAD_BYTES
    inner_filename: str | None = None
    max_expanded_bytes: int = 100 * 1024 * 1024
    max_members: int = 20


@dataclass(frozen=True, slots=True)
class PublicArtifactMetadata:
    """Verified identity metadata for bytes that have not been persisted yet."""

    source_id: str
    url: str
    filename: str
    byte_count: int
    sha256: str


class PublicDownloadRegistry:
    """Creates and verifies plans only for explicitly registered public sources."""

    def __init__(self, specs: list[PublicSourceSpec]) -> None:
        self._specs = {spec.source_id: spec for spec in specs}
        if len(self._specs) != len(specs):
            raise PublicDownloadError("Aynı public source ID birden fazla kez tanımlanamaz.")

    def create_plan(
        self,
        *,
        source_id: str,
        url: str,
        filename: str,
        expected_sha256: str,
        expected_bytes: int | None,
        max_bytes: int = MAX_PUBLIC_DOWNLOAD_BYTES,
        inner_filename: str | None = None,
        max_expanded_bytes: int = 100 * 1024 * 1024,
        max_members: int = 20,
    ) -> PublicDownloadPlan:
        spec = self._specs.get(source_id)
        if spec is None:
            raise PublicDownloadError("Public source allowlist içinde değil.")
        _validate_url(spec, url, filename)
        if not isinstance(expected_sha256, str) or not _SHA256_PATTERN.fullmatch(expected_sha256):
            raise PublicDownloadError("Beklenen SHA-256 değeri 64 hexadecimal karakter olmalıdır.")
        if expected_bytes is not None and (type(expected_bytes) is not int or expected_bytes <= 0):
            raise PublicDownloadError("Beklenen byte sayısı pozitif olmalıdır.")
        if type(max_bytes) is not int or not 0 < max_bytes <= MAX_PUBLIC_DOWNLOAD_BYTES:
            raise PublicDownloadError("Public byte sınırı geçersiz.")
        if expected_bytes is not None and expected_bytes > max_bytes:
            raise PublicDownloadError("Beklenen byte sayısı üst sınırı aşıyor.")
        if inner_filename is not None:
            _validate_inner_filename(inner_filename)
        if type(max_expanded_bytes) is not int or max_expanded_bytes <= 0:
            raise PublicDownloadError("Açılmış ZIP byte sınırı geçersiz.")
        if type(max_members) is not int or not 0 < max_members <= 20:
            raise PublicDownloadError("ZIP üye sınırı geçersiz.")
        return PublicDownloadPlan(
            source_id=source_id,
            url=url,
            filename=filename,
            expected_sha256=expected_sha256.lower(),
            expected_bytes=expected_bytes,
            max_bytes=max_bytes,
            inner_filename=inner_filename,
            max_expanded_bytes=max_expanded_bytes,
            max_members=max_members,
        )

    @staticmethod
    def verify_payload(plan: PublicDownloadPlan, payload: bytes) -> PublicArtifactMetadata:
        if not isinstance(payload, bytes):
            raise PublicDownloadError("Public payload bytes olmalıdır.")
        byte_count = len(payload)
        if byte_count > plan.max_bytes:
            raise PublicDownloadError("İndirilen payload byte sınırını aşıyor.")
        if plan.expected_bytes is not None and byte_count != plan.expected_bytes:
            raise PublicDownloadError("İndirilen payload byte sayısı metadata ile eşleşmiyor.")
        sha256 = hashlib.sha256(payload).hexdigest()
        if sha256 != plan.expected_sha256:
            raise PublicDownloadError("İndirilen payload SHA-256 metadata ile eşleşmiyor.")
        return PublicArtifactMetadata(
            source_id=plan.source_id,
            url=plan.url,
            filename=plan.filename,
            byte_count=byte_count,
            sha256=sha256,
        )


def parse_checksum_text(checksum_text: str | bytes, filename: str) -> str:
    """Parse Binance's single-record SHA-256 plus exact ZIP basename format."""

    if isinstance(checksum_text, bytes):
        try:
            checksum_text = checksum_text.decode("ascii")
        except UnicodeDecodeError as exc:
            raise PublicDownloadError("Checksum metni ASCII olmalıdır.") from exc
    if not isinstance(checksum_text, str) or not isinstance(filename, str):
        raise PublicDownloadError("Checksum metadata metin olmalıdır.")
    match = _CHECKSUM_PATTERN.fullmatch(checksum_text)
    if match is None or match.group(2) != filename:
        raise PublicDownloadError("Checksum biçimi veya dosya adı geçersiz.")
    return match.group(1).lower()


def _validate_url(spec: PublicSourceSpec, url: str, filename: str) -> None:
    if not isinstance(url, str) or len(url) > 2048:
        raise PublicDownloadError("Public URL geçersiz.")
    if not isinstance(filename, str) or not filename or len(filename) > 255 or any(
        separator in filename for separator in ("/", "\\")
    ):
        raise PublicDownloadError("Public filename geçersiz.")
    if not filename.lower().endswith((".csv", ".zip")):
        raise PublicDownloadError("Public filename CSV veya ZIP olmalıdır.")
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        parsed.port
    except ValueError as exc:
        raise PublicDownloadError("Public URL geçersiz.") from exc
    if parsed.scheme != "https" or hostname not in spec.allowed_hosts or parsed.username or parsed.password:
        raise PublicDownloadError("Public URL HTTPS ve allowlist koşullarını sağlamıyor.")
    if parsed.query or parsed.fragment or "\\" in parsed.path:
        raise PublicDownloadError("Public URL query, fragment veya backslash içeremez.")
    path = unquote(parsed.path)
    parts = PurePosixPath(path).parts
    if not path or not path.startswith("/") or any(part in {".", ".."} for part in parts):
        raise PublicDownloadError("Public URL path traversal içeriyor.")
    if PurePosixPath(path).name != filename:
        raise PublicDownloadError("URL dosya adı metadata ile eşleşmiyor.")
    if not any(path == prefix or path.startswith(prefix.rstrip("/") + "/") for prefix in spec.allowed_path_prefixes):
        raise PublicDownloadError("Public URL path allowlist içinde değil.")


def _validate_inner_filename(filename: str) -> None:
    if not filename or len(filename) > 255 or any(separator in filename for separator in ("/", "\\")):
        raise PublicDownloadError("ZIP iç dosya adı geçersiz.")
    if not filename.lower().endswith(".csv"):
        raise PublicDownloadError("ZIP iç dosya adı CSV olmalıdır.")


BINANCE_SPOT_KLINES_SOURCE = PublicSourceSpec(
    source_id="binance_spot_klines_v1",
    allowed_hosts=frozenset({"data.binance.vision"}),
    allowed_path_prefixes=("/data/spot/daily/klines/BTCUSDT/1h",),
)

BINANCE_SPOT_REGISTRY = PublicDownloadRegistry([BINANCE_SPOT_KLINES_SOURCE])

BINANCE_BTCUSDT_1H_2025_01_01_PLAN = BINANCE_SPOT_REGISTRY.create_plan(
    source_id="binance_spot_klines_v1",
    url=(
        "https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1h/"
        "BTCUSDT-1h-2025-01-01.zip"
    ),
    filename="BTCUSDT-1h-2025-01-01.zip",
    expected_sha256="8077644eb5088200969b135d7046ba777281be303fa32aceff28fe3baeaa5873",
    expected_bytes=1591,
    max_bytes=1_048_576,
    inner_filename="BTCUSDT-1h-2025-01-01.csv",
)
