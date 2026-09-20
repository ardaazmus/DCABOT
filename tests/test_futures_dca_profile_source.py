import unittest

from dcabot.application.futures_dca_plan import FuturesDcaProfile
from dcabot.application.futures_dca_profile_source import (
    FuturesDcaProfileRevisionSource,
    FuturesDcaProfileSourceError,
    build_futures_dca_profile_revision,
)
from dcabot.persistence.futures_dca_journal_schema import FuturesDcaProfileRevision


class FuturesDcaProfileSourceTests(unittest.TestCase):
    def source(self, contract_size="0.001"):
        return FuturesDcaProfileRevisionSource(
            "profile-1", "BTCUSDT", 100, contract_size, "fee-1", "slippage-1", "rounding-1"
        )

    def test_explicit_source_projects_exact_profile_revision(self):
        revision = build_futures_dca_profile_revision(FuturesDcaProfile(), self.source())

        self.assertEqual(
            revision,
            FuturesDcaProfileRevision(
                "profile-1", "BINANCE", "USD_M_PERPETUAL", "BTCUSDT", "USDT", "ISOLATED", "ONE_WAY", 100,
                "0.001", "fee-1", "slippage-1", "rounding-1",
            ),
        )

    def test_missing_or_invalid_contract_size_and_identity_fail_closed(self):
        with self.assertRaisesRegex(FuturesDcaProfileSourceError, "FUTURES_DCA_PROFILE_CONTRACT_SIZE_REQUIRED"):
            build_futures_dca_profile_revision(FuturesDcaProfile(), self.source("0"))
        with self.assertRaisesRegex(FuturesDcaProfileSourceError, "FUTURES_DCA_PROFILE_SOURCE_INVALID"):
            build_futures_dca_profile_revision(FuturesDcaProfile(), FuturesDcaProfileRevisionSource(
                "bad id", "BTCUSDT", 100, "0.001", "fee-1", "slippage-1", "rounding-1"
            ))


if __name__ == "__main__":
    unittest.main()
