import unittest

from dcabot.application.trailing_exit_binding import (
    TrailingExitBinding,
    TrailingExitBindingError,
    bind_trailing_exit_candidate,
)
from dcabot.application.trailing_ratchet import (
    arm_long_trailing,
    arm_long_percentage_trailing,
    arm_short_percentage_trailing,
    arm_short_trailing,
    observe_long_trailing,
    observe_long_percentage_trailing,
    observe_short_percentage_trailing,
    observe_short_trailing,
)


def triggered_trailing():
    state = arm_long_trailing(activation_price="100", distance="10")
    state = observe_long_trailing(state, price="120")
    return observe_long_trailing(state, price="110")


def triggered_short_trailing():
    state = arm_short_trailing(activation_price="100", distance="10")
    state = observe_short_trailing(state, price="80")
    return observe_short_trailing(state, price="90")


def triggered_long_percentage_trailing():
    state = arm_long_percentage_trailing(activation_price="100", rate="0.1")
    state = observe_long_percentage_trailing(state, price="120")
    return observe_long_percentage_trailing(state, price="108")


def triggered_short_percentage_trailing():
    state = arm_short_percentage_trailing(activation_price="100", rate="0.1")
    state = observe_short_percentage_trailing(state, price="80")
    return observe_short_percentage_trailing(state, price="88")


class TrailingExitBindingTests(unittest.TestCase):
    def test_triggered_trailing_candidate_consumes_only_free_capacity(self):
        result = bind_trailing_exit_candidate(
            trailing=triggered_trailing(),
            open_qty="1",
            accepted_exit_fills=("0.2",),
            committed_exit_qty=("0.3",),
            requested_qty="0.4",
        )

        self.assertEqual(
            result,
            TrailingExitBinding(
                trigger_price="110",
                requested_qty="0.4",
                remaining_capacity="0.1",
                order_authority="NONE",
            ),
        )

    def test_untriggered_trailing_cannot_create_exit_candidate(self):
        trailing = arm_long_trailing(activation_price="100", distance="10")
        with self.assertRaisesRegex(
            TrailingExitBindingError, "TRAILING_EXIT_NOT_TRIGGERED"
        ):
            bind_trailing_exit_candidate(
                trailing=trailing,
                open_qty="1",
                accepted_exit_fills=(),
                committed_exit_qty=(),
                requested_qty="0.5",
            )

    def test_candidate_over_close_is_rejected(self):
        with self.assertRaisesRegex(
            TrailingExitBindingError, "EXIT_CAPACITY_EXCEEDED"
        ):
            bind_trailing_exit_candidate(
                trailing=triggered_trailing(),
                open_qty="1",
                accepted_exit_fills=("0.8",),
                committed_exit_qty=(),
                requested_qty="0.3",
            )

    def test_all_triggered_trailing_variants_bind_without_accepting_fill(self):
        for trailing in (
            triggered_trailing(),
            triggered_short_trailing(),
            triggered_long_percentage_trailing(),
            triggered_short_percentage_trailing(),
        ):
            with self.subTest(trailing=trailing):
                result = bind_trailing_exit_candidate(
                    trailing=trailing,
                    open_qty="1",
                    accepted_exit_fills=(),
                    committed_exit_qty=(),
                    requested_qty="0.4",
                )

                self.assertEqual(
                    result.remaining_capacity,
                    "0.6",
                )
                self.assertEqual(result.order_authority, "NONE")

    def test_percentage_untriggered_state_cannot_create_exit_candidate(self):
        trailing = arm_long_percentage_trailing(activation_price="100", rate="0.1")
        with self.assertRaisesRegex(
            TrailingExitBindingError, "TRAILING_EXIT_NOT_TRIGGERED"
        ):
            bind_trailing_exit_candidate(
                trailing=trailing,
                open_qty="1",
                accepted_exit_fills=(),
                committed_exit_qty=(),
                requested_qty="0.5",
            )


if __name__ == "__main__":
    unittest.main()
