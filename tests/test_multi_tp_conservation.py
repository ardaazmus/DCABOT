import unittest

from dcabot.application.multi_tp_conservation import (
    ExitCapacity,
    ExitCapacityError,
    validate_exit_capacity,
)


class MultiTpConservationTests(unittest.TestCase):
    def test_fills_and_committed_exits_leave_exact_free_capacity(self):
        result = validate_exit_capacity(
            open_qty="1",
            accepted_exit_fills=("0.2", "0.3"),
            committed_exit_qty=("0.4",),
        )

        self.assertEqual(
            result,
            ExitCapacity(
                open_qty="1",
                accepted_exit_fills="0.5",
                committed_exit_qty="0.4",
                free_exit_capacity="0.1",
            ),
        )

    def test_exit_capacity_rejects_over_close_before_any_order_authority(self):
        with self.assertRaisesRegex(
            ExitCapacityError, "EXIT_CAPACITY_EXCEEDED"
        ):
            validate_exit_capacity(
                open_qty="1",
                accepted_exit_fills=("0.6",),
                committed_exit_qty=("0.5",),
            )

    def test_split_fill_representation_is_conserved(self):
        split = validate_exit_capacity(
            open_qty="1",
            accepted_exit_fills=("0.2", "0.3"),
            committed_exit_qty=("0.4",),
        )
        combined = validate_exit_capacity(
            open_qty="1",
            accepted_exit_fills=("0.5",),
            committed_exit_qty=("0.4",),
        )

        self.assertEqual(split, combined)

    def test_zero_or_malformed_exit_quantity_fails_closed(self):
        with self.assertRaisesRegex(
            ExitCapacityError, "EXIT_CAPACITY_QTY_INVALID"
        ):
            validate_exit_capacity(
                open_qty="1",
                accepted_exit_fills=("0",),
                committed_exit_qty=(),
            )
        with self.assertRaisesRegex(
            ExitCapacityError, "EXIT_CAPACITY_QTY_INVALID"
        ):
            validate_exit_capacity(
                open_qty="1",
                accepted_exit_fills=("bad",),
                committed_exit_qty=(),
            )


if __name__ == "__main__":
    unittest.main()
