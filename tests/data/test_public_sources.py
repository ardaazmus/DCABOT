import unittest

from dcabot.data_adapters.public_sources import (
    BINANCE_BTCUSDT_1H_2025_01_01_PLAN,
    PublicDownloadError,
    PublicDownloadRegistry,
    PublicSourceSpec,
    parse_checksum_text,
)


class PublicSourcesTests(unittest.TestCase):
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

    def test_plan_requires_allowlisted_https_url_and_metadata(self):
        plan = self.registry.create_plan(
            source_id="fixture-source",
            url="https://public.example/datasets/bars.csv",
            filename="bars.csv",
            expected_sha256="a" * 64,
            expected_bytes=12,
        )

        self.assertEqual(plan.source_id, "fixture-source")
        self.assertEqual(plan.expected_bytes, 12)
        self.assertEqual(plan.max_bytes, 256 * 1024 * 1024)

    def test_unknown_source_and_unsafe_url_are_rejected(self):
        with self.assertRaises(PublicDownloadError):
            self.registry.create_plan(
                source_id="unknown",
                url="https://public.example/datasets/bars.csv",
                filename="bars.csv",
                expected_sha256="a" * 64,
                expected_bytes=12,
            )
        with self.assertRaises(PublicDownloadError):
            self.registry.create_plan(
                source_id="fixture-source",
                url="http://public.example/datasets/bars.csv?download=1",
                filename="bars.csv",
                expected_sha256="a" * 64,
                expected_bytes=12,
            )

    def test_payload_verification_checks_size_and_checksum_without_writing(self):
        plan = self.registry.create_plan(
            source_id="fixture-source",
            url="https://public.example/datasets/bars.csv",
            filename="bars.csv",
            expected_sha256="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            expected_bytes=3,
        )

        metadata = self.registry.verify_payload(plan, b"abc")

        self.assertEqual(metadata.byte_count, 3)
        self.assertEqual(metadata.sha256, plan.expected_sha256)

    def test_verified_binance_plan_is_pinned_to_researched_fixture(self):
        self.assertEqual(BINANCE_BTCUSDT_1H_2025_01_01_PLAN.source_id, "binance_spot_klines_v1")
        self.assertEqual(BINANCE_BTCUSDT_1H_2025_01_01_PLAN.expected_bytes, 1591)
        self.assertEqual(BINANCE_BTCUSDT_1H_2025_01_01_PLAN.inner_filename, "BTCUSDT-1h-2025-01-01.csv")

    def test_checksum_parser_requires_exact_hash_and_filename(self):
        checksum = (
            "8077644eb5088200969b135d7046ba777281be303fa32aceff28fe3baeaa5873"
            "  BTCUSDT-1h-2025-01-01.zip"
        )

        self.assertEqual(
            parse_checksum_text(checksum, "BTCUSDT-1h-2025-01-01.zip"),
            BINANCE_BTCUSDT_1H_2025_01_01_PLAN.expected_sha256,
        )
        with self.assertRaises(PublicDownloadError):
            parse_checksum_text(checksum + "\nextra", "BTCUSDT-1h-2025-01-01.zip")
