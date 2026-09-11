"""Explicit local catalog and selection contract for verified public artifacts."""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dcabot.data_adapters.public_download import CachedPublicArtifact, inspect_cached_artifact
from dcabot.data_adapters.public_sources import (
    BINANCE_BTCUSDT_1H_2025_01_01_PLAN,
    PublicDownloadError,
    PublicDownloadPlan,
)


class CatalogError(ValueError):
    """Raised when a dataset definition or local selection is invalid."""


@dataclass(frozen=True, slots=True)
class PublicDatasetDefinition:
    """Stable descriptive metadata paired with one immutable download plan."""

    dataset_id: str
    plan: PublicDownloadPlan
    symbol: str
    interval: str
    period_start: str
    period_end: str

    def __post_init__(self) -> None:
        if (
            not self.dataset_id
            or len(self.dataset_id) > 160
            or any(separator in self.dataset_id for separator in ("/", "\\"))
        ):
            raise CatalogError("Dataset ID geçersiz.")
        if not self.symbol or not self.interval:
            raise CatalogError("Dataset sembol veya interval bilgisi eksik.")
        try:
            start = date.fromisoformat(self.period_start)
            end = date.fromisoformat(self.period_end)
        except (TypeError, ValueError) as exc:
            raise CatalogError("Dataset dönemi YYYY-MM-DD olmalıdır.") from exc
        if end <= start:
            raise CatalogError("Dataset dönemi [başlangıç, bitiş) olmalıdır.")


@dataclass(frozen=True, slots=True)
class PublicDatasetCatalogEntry:
    """A listable dataset status; VERIFIED means cache integrity is verified."""

    dataset_id: str
    source_id: str
    symbol: str
    interval: str
    period_start: str
    period_end: str
    sha256: str
    byte_count: int | None
    quality_status: str
    artifact_name: str


@dataclass(frozen=True, slots=True)
class PublicDatasetSelection:
    """A verified artifact path that can be passed to the parser/application port."""

    entry: PublicDatasetCatalogEntry
    path: Path
    inner_filename: str | None


class PublicDatasetCatalog:
    """Lists only explicit definitions and selects only verified local cache entries."""

    def __init__(self, cache_dir: Path, definitions: list[PublicDatasetDefinition]) -> None:
        if not isinstance(cache_dir, Path):
            raise CatalogError("Catalog cache klasörü geçersiz.")
        self._cache_dir = cache_dir
        self._definitions = {definition.dataset_id: definition for definition in definitions}
        if len(self._definitions) != len(definitions):
            raise CatalogError("Aynı dataset ID birden fazla kez tanımlanamaz.")

    def list_entries(self) -> tuple[PublicDatasetCatalogEntry, ...]:
        """List configured datasets without downloading or mutating local state."""

        return tuple(
            self._entry(definition, self._inspect(definition.plan))
            for definition in sorted(self._definitions.values(), key=lambda item: item.dataset_id)
        )

    def select(self, dataset_id: str) -> PublicDatasetSelection:
        """Select a dataset only when its expected hash and ZIP integrity are verified."""

        definition = self._definitions.get(dataset_id)
        if definition is None:
            raise CatalogError("Dataset katalogda bulunamadı.")
        artifact = self._inspect(definition.plan)
        if artifact is None:
            raise CatalogError("Dataset local doğrulanmış cache içinde hazır değil.")
        entry = self._entry(definition, artifact)
        return PublicDatasetSelection(entry, artifact.cache_path, definition.plan.inner_filename)

    def plan_for(self, dataset_id: str) -> PublicDownloadPlan:
        """Return the immutable download plan for one explicit dataset definition."""

        definition = self._definitions.get(dataset_id)
        if definition is None:
            raise CatalogError("Dataset katalogda bulunamadı.")
        return definition.plan

    def _entry(
        self, definition: PublicDatasetDefinition, artifact: CachedPublicArtifact | None
    ) -> PublicDatasetCatalogEntry:
        byte_count = None
        if artifact is not None:
            byte_count = artifact.metadata.byte_count
            quality_status = "VERIFIED"
        else:
            final_path = self._cache_dir / f"{definition.plan.expected_sha256}.zip"
            metadata_path = self._cache_dir / f"{definition.plan.expected_sha256}.json"
            quality_status = "CORRUPT" if final_path.exists() or metadata_path.exists() else "MISSING"
        return PublicDatasetCatalogEntry(
            dataset_id=definition.dataset_id,
            source_id=definition.plan.source_id,
            symbol=definition.symbol,
            interval=definition.interval,
            period_start=definition.period_start,
            period_end=definition.period_end,
            sha256=definition.plan.expected_sha256,
            byte_count=byte_count,
            quality_status=quality_status,
            artifact_name=definition.plan.filename,
        )

    def _inspect(self, plan: PublicDownloadPlan) -> CachedPublicArtifact | None:
        try:
            return inspect_cached_artifact(plan, self._cache_dir)
        except PublicDownloadError as exc:
            raise CatalogError("Catalog cache klasörü geçersiz.") from exc


BINANCE_BTCUSDT_1H_2025_01_01_DATASET = PublicDatasetDefinition(
    dataset_id="binance-spot-klines-v1-btcusdt-1h-2025-01-01",
    plan=BINANCE_BTCUSDT_1H_2025_01_01_PLAN,
    symbol="BTCUSDT",
    interval="1h",
    period_start="2025-01-01",
    period_end="2025-01-02",
)
