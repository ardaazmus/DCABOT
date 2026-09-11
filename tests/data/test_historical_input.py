from dataclasses import dataclass
from io import BytesIO
import hashlib
import tempfile
import unittest
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from dcabot.application.historical import load_verified_dataset
from dcabot.data_adapters.catalog import PublicDatasetCatalog, PublicDatasetDefinition
from dcabot.data_adapters.historical import CanonicalBar, HistoricalDatasetInput, HistoricalDatasetMetadata
from dcabot.data_adapters.public_download import download_to_cache
from dcabot.data_adapters.public_sources import PublicDownloadRegistry, PublicSourceSpec


RAW_KLINES = """1735689600000000,100.00000000,101.00000000,99.00000000,100.50000000,2.50000000,1735693199999999,251.25000000,12,1.25000000,125.62500000,0
1735693200000000,100.50000000,102.00000000,100.00000000,101.50000000,3.00000000,1735696799999999,304.50000000,13,1.50000000,152.25000000,0
""".encode()


def _zip_payload() -> bytes:
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("BTCUSDT-1h-2025-01-01.csv", RAW_KLINES)
    return output.getvalue()


@dataclass
class _FakeResponse:
    payload: bytes

    status = 200

    def __post_init__(self):
        self.headers = {"Content-Length": str(len(self.payload))}
        self._stream = BytesIO(self.payload)

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)

    def close(self) -> None:
        pass


class _FakeOpener:
    def __init__(self, payload: bytes):
        self.payload = payload

    def open(self, request, timeout: int):
        return _FakeResponse(self.payload)


class HistoricalInputTests(unittest.TestCase):
    def test_verified_selection_becomes_exact_canonical_bars_with_source_time_metadata(self):
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

        with tempfile.TemporaryDirectory() as directory:
            cache_dir = Path(directory)
            download_to_cache(plan, cache_dir, opener=_FakeOpener(payload))
            selection = PublicDatasetCatalog(cache_dir, [definition]).select(definition.dataset_id)

            result = load_verified_dataset(selection)

        self.assertEqual(
            result,
            HistoricalDatasetInput(
                metadata=HistoricalDatasetMetadata(
                    dataset_id=definition.dataset_id,
                    source_id="fixture-source",
                    symbol="BTCUSDT",
                    interval="1h",
                    period_start="2025-01-01",
                    period_end="2025-01-02",
                    artifact_sha256=hashlib.sha256(payload).hexdigest(),
                    artifact_bytes=len(payload),
                    timestamp_unit="microseconds",
                    timezone="UTC",
                ),
                bars=(
                    CanonicalBar(
                        open_time_us=1735689600000000,
                        close_time_us=1735693199999999,
                        open="100",
                        high="101",
                        low="99",
                        close="100.5",
                        base_volume="2.5",
                        is_closed=True,
                    ),
                    CanonicalBar(
                        open_time_us=1735693200000000,
                        close_time_us=1735696799999999,
                        open="100.5",
                        high="102",
                        low="100",
                        close="101.5",
                        base_volume="3",
                        is_closed=True,
                    ),
                ),
            ),
        )
