"""F10.6: recurring-buy schedule projection (F16)."""
import unittest

from dcabot.application.recurring_schedule import (
    RecurringScheduleError,
    project_recurring_schedule,
)


class RecurringScheduleTests(unittest.TestCase):
    def test_even_slots_projected(self):
        result = project_recurring_schedule(
            symbol="BTCUSDT",
            quote_amount="100",
            start_us=1_000_000,
            interval_us=500_000,
            count=3,
        )
        self.assertEqual(result["symbol"], "BTCUSDT")
        self.assertEqual(result["quote_amount"], "100")
        self.assertEqual(
            [slot["slot_us"] for slot in result["slots"]],
            [1_000_000, 1_500_000, 2_000_000],
        )
        self.assertEqual(result["total_quote"], "300")
        self.assertEqual(result["order_authority"], "NONE")

    def test_single_slot(self):
        result = project_recurring_schedule(
            symbol="ETHUSDT",
            quote_amount="25.5",
            start_us=0,
            interval_us=1,
            count=1,
        )
        self.assertEqual(len(result["slots"]), 1)
        self.assertEqual(result["total_quote"], "25.5")

    def test_zero_count_rejected(self):
        with self.assertRaises(RecurringScheduleError) as ctx:
            project_recurring_schedule(
                symbol="BTCUSDT", quote_amount="100",
                start_us=0, interval_us=1, count=0,
            )
        self.assertEqual(ctx.exception.code, "RECURRING_COUNT_INVALID")

    def test_excessive_count_rejected(self):
        with self.assertRaises(RecurringScheduleError) as ctx:
            project_recurring_schedule(
                symbol="BTCUSDT", quote_amount="100",
                start_us=0, interval_us=1, count=366,
            )
        self.assertEqual(ctx.exception.code, "RECURRING_COUNT_INVALID")

    def test_bad_amount_rejected(self):
        with self.assertRaises(RecurringScheduleError) as ctx:
            project_recurring_schedule(
                symbol="BTCUSDT", quote_amount="0",
                start_us=0, interval_us=1, count=1,
            )
        self.assertEqual(ctx.exception.code, "RECURRING_AMOUNT_INVALID")

    def test_bad_symbol_rejected(self):
        with self.assertRaises(RecurringScheduleError) as ctx:
            project_recurring_schedule(
                symbol="btc", quote_amount="100",
                start_us=0, interval_us=1, count=1,
            )
        self.assertEqual(ctx.exception.code, "RECURRING_SYMBOL_INVALID")

    def test_non_integer_time_rejected(self):
        with self.assertRaises(RecurringScheduleError):
            project_recurring_schedule(
                symbol="BTCUSDT", quote_amount="100",
                start_us="0", interval_us=1, count=1,  # type: ignore[arg-type]
            )


if __name__ == "__main__":
    unittest.main()
