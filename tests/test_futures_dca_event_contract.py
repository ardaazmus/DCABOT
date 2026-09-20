import unittest

from dcabot.application.futures_dca_event_contract import (
    FuturesDcaEventError,
    accept_futures_dca_fill_event,
    new_futures_dca_fill_event,
)
from dcabot.application.futures_dca_fill_projection import FuturesDcaFill


def event(event_id="event-1", sequence=1, execution_id="execution-1", deal_id="deal-1"):
    return new_futures_dca_fill_event(
        event_id, deal_id, "config-1", sequence, FuturesDcaFill(execution_id, 0, "0.1", "100")
    )


class FuturesDcaEventContractTests(unittest.TestCase):
    def test_same_scope_sequence_is_accepted_and_exact_duplicate_is_idempotent(self):
        first, outcome = accept_futures_dca_fill_event((), event())
        second, next_outcome = accept_futures_dca_fill_event(first, event("event-2", 2, "execution-2"))
        duplicate, duplicate_outcome = accept_futures_dca_fill_event(second, second[0])
        self.assertEqual((outcome, next_outcome, duplicate_outcome, duplicate), ("ACCEPTED", "ACCEPTED", "DUPLICATE", second))

    def test_event_id_conflict_and_execution_id_reuse_fail_closed(self):
        history, _ = accept_futures_dca_fill_event((), event())
        with self.assertRaisesRegex(FuturesDcaEventError, "FUTURES_DCA_EVENT_CONFLICT"):
            accept_futures_dca_fill_event(history, event("event-1", 2, "execution-2"))
        with self.assertRaisesRegex(FuturesDcaEventError, "FUTURES_DCA_EXECUTION_CONFLICT"):
            accept_futures_dca_fill_event(history, event("event-2", 2, "execution-1"))

    def test_scope_and_sequence_gaps_fail_closed(self):
        history, _ = accept_futures_dca_fill_event((), event())
        with self.assertRaisesRegex(FuturesDcaEventError, "FUTURES_DCA_EVENT_SCOPE_CONFLICT"):
            accept_futures_dca_fill_event(history, event("event-2", 2, "execution-2", "other-deal"))
        with self.assertRaisesRegex(FuturesDcaEventError, "FUTURES_DCA_EVENT_SEQUENCE_INVALID"):
            accept_futures_dca_fill_event(history, event("event-3", 3, "execution-3"))

    def test_first_event_must_start_at_sequence_one(self):
        with self.assertRaisesRegex(FuturesDcaEventError, "FUTURES_DCA_EVENT_SEQUENCE_INVALID"):
            accept_futures_dca_fill_event((), event(sequence=2))


if __name__ == "__main__":
    unittest.main()
