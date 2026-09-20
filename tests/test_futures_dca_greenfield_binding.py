from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from dcabot.persistence.futures_dca_journal_schema import (
    FuturesDcaEconomicPosting,
    FuturesDcaEventEnvelope,
    FuturesDcaJournalSchemaError,
    FuturesDcaProfileRevision,
    FuturesDcaReservationProjection,
    append_event_reservation_and_posting_atomic,
    append_profile_revision,
    create_futures_dca_journal_schema,
    load_journal_events,
    load_economic_postings,
    load_reservation_projections,
)


class FuturesDcaGreenfieldBindingTests(unittest.TestCase):
    def test_event_reservation_and_posting_are_one_replayable_unit(self):
        with TemporaryDirectory() as directory:
            path = create_futures_dca_journal_schema(Path(directory) / "journal.sqlite")
            profile = FuturesDcaProfileRevision(
                "profile-1", "BINANCE", "USD_M_PERPETUAL", "BTCUSDT", "USDT", "ISOLATED", "ONE_WAY", 100,
                "0.001", "fee-1", "slippage-1", "rounding-1",
            )
            event = FuturesDcaEventEnvelope(
                "event-1", 1, "execution-1", "order-1", "FILL", "profile-1", 100, 101,
                "1", "100", "100", "0", "USDT", "slippage-1", "rounding-1", '{"source":"offline"}',
            )
            reservation = FuturesDcaReservationProjection(
                "reservation-1", "deal-1", "USDT", "100", "100", "0", "release-1", "RELEASED", 1, "event-1", 1,
            )
            posting = FuturesDcaEconomicPosting(
                "posting-1", "event-1", 1, "100", "0", "0", "PROJECTED",
            )
            append_profile_revision(path, profile)

            self.assertEqual(
                append_event_reservation_and_posting_atomic(path, event, reservation, posting),
                "ACCEPTED",
            )
            self.assertEqual(
                append_event_reservation_and_posting_atomic(path, event, reservation, posting),
                "DUPLICATE",
            )
            self.assertEqual(load_economic_postings(path), (posting,))

    def test_posting_cursor_gap_rolls_back_event_and_reservation(self):
        with TemporaryDirectory() as directory:
            path = create_futures_dca_journal_schema(Path(directory) / "journal.sqlite")
            append_profile_revision(path, FuturesDcaProfileRevision(
                "profile-1", "BINANCE", "USD_M_PERPETUAL", "BTCUSDT", "USDT", "ISOLATED", "ONE_WAY", 100,
                "0.001", "fee-1", "slippage-1", "rounding-1",
            ))
            event = FuturesDcaEventEnvelope(
                "event-1", 1, "execution-1", "order-1", "FILL", "profile-1", 100, 101,
                "1", "100", "100", "0", "USDT", "slippage-1", "rounding-1", '{"source":"offline"}',
            )
            reservation = FuturesDcaReservationProjection(
                "reservation-1", "deal-1", "USDT", "100", "100", "0", "release-1", "RELEASED", 1, "event-1", 1,
            )
            with self.assertRaisesRegex(FuturesDcaJournalSchemaError, "FUTURES_DCA_POSTING_CURSOR_INVALID"):
                append_event_reservation_and_posting_atomic(
                    path,
                    event,
                    reservation,
                    FuturesDcaEconomicPosting("posting-1", "event-1", 2, "100", "0", "0", "PROJECTED"),
                )
            self.assertEqual(load_journal_events(path), ())
            self.assertEqual(load_reservation_projections(path), ())
            self.assertEqual(load_economic_postings(path), ())

    def test_unknown_event_cannot_create_economic_posting(self):
        with TemporaryDirectory() as directory:
            path = create_futures_dca_journal_schema(Path(directory) / "journal.sqlite")
            append_profile_revision(path, FuturesDcaProfileRevision(
                "profile-1", "BINANCE", "USD_M_PERPETUAL", "BTCUSDT", "USDT", "ISOLATED", "ONE_WAY", 100,
                "0.001", "fee-1", "slippage-1", "rounding-1",
            ))
            event = FuturesDcaEventEnvelope(
                "event-1", 1, "execution-1", "order-1", "FILL", "profile-1", 100, 101,
                "1", "100", "100", "0", "USDT", "slippage-1", "rounding-1", '{"source":"offline"}', "UNKNOWN",
            )
            reservation = FuturesDcaReservationProjection(
                "reservation-1", "deal-1", "USDT", "100", "0", "100", None, "OPEN", 0, "event-1",
            )
            with self.assertRaisesRegex(FuturesDcaJournalSchemaError, "FUTURES_DCA_POSTING_EVENT_NOT_ACCEPTED"):
                append_event_reservation_and_posting_atomic(
                    path,
                    event,
                    reservation,
                    FuturesDcaEconomicPosting("posting-1", "event-1", 1, "100", "0", "0", "PROJECTED"),
                )
            self.assertEqual(load_journal_events(path), ())
            self.assertEqual(load_reservation_projections(path), ())
            self.assertEqual(load_economic_postings(path), ())


if __name__ == "__main__":
    unittest.main()
