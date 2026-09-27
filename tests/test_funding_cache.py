"""G3-b: funding cache — coverage-gated reads, atomic range writes."""

import tempfile
import unittest
from pathlib import Path

from dcabot.data_adapters.binance_futures_public_transport import BinanceFuturesFundingRate
from dcabot.persistence.funding_cache import FundingCache, FundingCacheError

H8 = 8 * 3_600_000_000


def _record(time_us, rate="0.0001"):
    return BinanceFuturesFundingRate(funding_time_us=time_us, rate=rate)


class FundingCacheTest(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.cache = FundingCache(Path(self._dir.name) / "funding.sqlite3")

    def tearDown(self) -> None:
        self.cache.close()
        self._dir.cleanup()

    def test_miss_before_put_roundtrip_after(self) -> None:
        self.assertIsNone(self.cache.get_range("BTCUSDT", 0, 2 * H8))
        records = (_record(0), _record(H8))
        self.cache.put_range("BTCUSDT", records, start_us=0, end_us=2 * H8)
        self.assertEqual(self.cache.get_range("BTCUSDT", 0, 2 * H8), records)

    def test_partial_overlap_is_miss(self) -> None:
        self.cache.put_range("BTCUSDT", (_record(0),), start_us=0, end_us=H8)
        self.assertIsNone(self.cache.get_range("BTCUSDT", 0, 2 * H8))
        self.assertEqual(self.cache.get_range("BTCUSDT", 0, H8), (_record(0),))

    def test_empty_range_is_cached_data(self) -> None:
        self.cache.put_range("BTCUSDT", (), start_us=0, end_us=H8)
        self.assertEqual(self.cache.get_range("BTCUSDT", 0, H8), ())

    def test_out_of_range_record_rejected(self) -> None:
        with self.assertRaises(FundingCacheError) as ctx:
            self.cache.put_range("BTCUSDT", (_record(5 * H8),), start_us=0, end_us=2 * H8)
        self.assertEqual(ctx.exception.code, "FUNDING_CACHE_RECORDS_INVALID")
        self.assertIsNone(self.cache.get_range("BTCUSDT", 0, 2 * H8))

    def test_bad_range_rejected(self) -> None:
        with self.assertRaises(FundingCacheError) as ctx:
            self.cache.get_range("BTCUSDT", 10, 10)
        self.assertEqual(ctx.exception.code, "FUNDING_CACHE_RANGE_INVALID")

    def test_symbols_isolated(self) -> None:
        self.cache.put_range("BTCUSDT", (_record(0),), start_us=0, end_us=H8)
        self.assertIsNone(self.cache.get_range("ETHUSDT", 0, H8))


if __name__ == "__main__":
    unittest.main()
