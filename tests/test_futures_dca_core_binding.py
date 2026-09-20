from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from dcabot.persistence.futures_dca_core_binding import (
    FuturesDcaCoreBindingPreflight,
    preflight_futures_dca_core_binding,
)
from dcabot.persistence.futures_dca_journal_schema import (
    FuturesDcaEconomicPosting,
    FuturesDcaEventEnvelope,
    FuturesDcaProfileRevision,
    FuturesDcaReservationProjection,
    append_journal_event,
    append_profile_revision,
    append_reservation_projection,
    create_futures_dca_journal_schema,
)
from dcabot.persistence.futures_dca_release_store import (
    append_futures_dca_fill_release_and_posting_atomic,
)
from dcabot.persistence.futures_dca_release_transition import FuturesDcaReleaseTransition


class FuturesDcaCoreBindingTests(unittest.TestCase):
    def prepare(self):
        directory = TemporaryDirectory()
        path = create_futures_dca_journal_schema(Path(directory.name) / "journal.sqlite")
        append_profile_revision(path, FuturesDcaProfileRevision(
            "profile-1", "BINANCE", "USD_M_PERPETUAL", "BTCUSDT", "USDT", "ISOLATED", "ONE_WAY", 100,
            "0.001", "fee-1", "slippage-1", "rounding-1",
        ))
        append_journal_event(path, FuturesDcaEventEnvelope(
            "event-1", 1, "execution-1", "order-1", "FILL", "profile-1", 100, 101,
            "1", "100", "100", "0", "USDT", "slippage-1", "rounding-1", '{"source":"offline"}',
        ))
        append_reservation_projection(path, FuturesDcaReservationProjection(
            "reservation-1", "deal-1", "USDT", "100", "0", "100", None, "OPEN", 0, "event-1",
        ))
        append_futures_dca_fill_release_and_posting_atomic(
            path,
            FuturesDcaEventEnvelope(
                "event-2", 2, "execution-2", "order-1", "FILL", "profile-1", 100, 101,
                "0.4", "100", "40", "0", "USDT", "slippage-1", "rounding-1", '{"source":"offline"}',
            ),
            FuturesDcaReleaseTransition(
                "reservation-1", "event-2", "release-1", 1, 0, "PARTIAL_FILL", "40", "60",
            ),
            FuturesDcaEconomicPosting("posting-1", "event-2", 1, "40", "0", "0", "PROJECTED"),
        )
        return directory, path

    def test_replay_is_read_only_and_blocks_without_core_intent_mapping(self):
        directory, path = self.prepare()
        try:
            before = path.read_bytes()
            self.assertEqual(
                preflight_futures_dca_core_binding(path),
                (FuturesDcaCoreBindingPreflight(
                    "event-2", "posting-1", "BLOCKED",
                    ("side", "core_order_intent", "role", "limit_price"),
                    "FUTURES_DCA_CORE_INTENT_MAPPING_MISSING",
                ),),
            )
            self.assertEqual(path.read_bytes(), before)
        finally:
            directory.cleanup()

    def test_empty_durable_posting_replay_has_no_binding_decision(self):
        with TemporaryDirectory() as directory:
            path = create_futures_dca_journal_schema(Path(directory) / "journal.sqlite")
            self.assertEqual(preflight_futures_dca_core_binding(path), ())

    def test_preflight_does_not_claim_core_store_or_order_authority(self):
        directory, path = self.prepare()
        try:
            decision = preflight_futures_dca_core_binding(path)[0]
            self.assertEqual(decision.status, "BLOCKED")
            self.assertIn("core_order_intent", decision.missing_authority)
            self.assertEqual(decision.reason_code, "FUTURES_DCA_CORE_INTENT_MAPPING_MISSING")
        finally:
            directory.cleanup()


if __name__ == "__main__":
    unittest.main()
