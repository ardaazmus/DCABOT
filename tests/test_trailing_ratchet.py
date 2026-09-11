import unittest

from dcabot.application.trailing_ratchet import (
    TrailingLongState,
    TrailingLongPercentageState,
    TrailingShortState,
    TrailingShortPercentageState,
    TrailingRatchetError,
    arm_long_trailing,
    arm_long_percentage_trailing,
    arm_short_trailing,
    arm_short_percentage_trailing,
    observe_long_trailing,
    observe_long_percentage_trailing,
    observe_short_trailing,
    observe_short_percentage_trailing,
)


class TrailingRatchetTests(unittest.TestCase):
    def test_below_activation_remains_inactive(self):
        state = arm_long_trailing(activation_price="100", distance="10")

        self.assertEqual(
            observe_long_trailing(state, price="99"),
            TrailingLongState(
                status="INACTIVE",
                activation_price="100",
                distance="10",
                high_water=None,
                stop_price=None,
            ),
        )

    def test_activation_sets_exact_high_water_and_stop(self):
        state = arm_long_trailing(activation_price="100", distance="10")

        self.assertEqual(
            observe_long_trailing(state, price="105"),
            TrailingLongState(
                status="ACTIVE",
                activation_price="100",
                distance="10",
                high_water="105",
                stop_price="95",
            ),
        )

    def test_favorable_high_ratchets_up_and_retracement_never_lowers_stop(self):
        state = arm_long_trailing(activation_price="100", distance="10")
        state = observe_long_trailing(state, price="105")
        state = observe_long_trailing(state, price="120")

        self.assertEqual(state.stop_price, "110")
        self.assertEqual(
            observe_long_trailing(state, price="115").stop_price,
            "110",
        )

    def test_price_at_or_below_stop_transitions_to_triggered(self):
        state = arm_long_trailing(activation_price="100", distance="10")
        state = observe_long_trailing(state, price="120")

        self.assertEqual(
            observe_long_trailing(state, price="110").status,
            "TRIGGERED",
        )

    def test_invalid_activation_distance_and_post_trigger_observation_fail_closed(self):
        with self.assertRaisesRegex(
            TrailingRatchetError, "TRAILING_DISTANCE_INVALID"
        ):
            arm_long_trailing(activation_price="10", distance="10")

        state = arm_long_trailing(activation_price="100", distance="10")
        state = observe_long_trailing(state, price="120")
        state = observe_long_trailing(state, price="110")
        with self.assertRaisesRegex(
            TrailingRatchetError, "TRAILING_ALREADY_TRIGGERED"
        ):
            observe_long_trailing(state, price="105")

    def test_short_above_activation_remains_inactive(self):
        state = arm_short_trailing(activation_price="100", distance="10")

        self.assertEqual(
            observe_short_trailing(state, price="101"),
            TrailingShortState(
                status="INACTIVE",
                activation_price="100",
                distance="10",
                low_water=None,
                stop_price=None,
            ),
        )

    def test_short_activation_sets_exact_low_water_and_stop(self):
        state = arm_short_trailing(activation_price="100", distance="10")

        self.assertEqual(
            observe_short_trailing(state, price="95"),
            TrailingShortState(
                status="ACTIVE",
                activation_price="100",
                distance="10",
                low_water="95",
                stop_price="105",
            ),
        )

    def test_short_favorable_low_ratchets_down_and_retracement_never_raises_stop(self):
        state = arm_short_trailing(activation_price="100", distance="10")
        state = observe_short_trailing(state, price="95")
        state = observe_short_trailing(state, price="80")

        self.assertEqual(state.stop_price, "90")
        self.assertEqual(
            observe_short_trailing(state, price="85").stop_price,
            "90",
        )

    def test_short_price_at_or_above_stop_transitions_to_triggered(self):
        state = arm_short_trailing(activation_price="100", distance="10")
        state = observe_short_trailing(state, price="80")

        self.assertEqual(
            observe_short_trailing(state, price="90").status,
            "TRIGGERED",
        )

    def test_short_invalid_distance_and_post_trigger_observation_fail_closed(self):
        with self.assertRaisesRegex(
            TrailingRatchetError, "TRAILING_DISTANCE_INVALID"
        ):
            arm_short_trailing(activation_price="10", distance="10")

        state = arm_short_trailing(activation_price="100", distance="10")
        state = observe_short_trailing(state, price="80")
        state = observe_short_trailing(state, price="90")
        with self.assertRaisesRegex(
            TrailingRatchetError, "TRAILING_ALREADY_TRIGGERED"
        ):
            observe_short_trailing(state, price="95")

    def test_long_percentage_activation_and_exact_stop(self):
        state = arm_long_percentage_trailing(activation_price="100", rate="0.1")

        self.assertEqual(
            observe_long_percentage_trailing(state, price="110"),
            TrailingLongPercentageState(
                status="ACTIVE",
                activation_price="100",
                rate="0.1",
                high_water="110",
                stop_price="99",
            ),
        )

    def test_long_percentage_ratchets_without_lowering_stop_and_triggers(self):
        state = arm_long_percentage_trailing(activation_price="100", rate="0.1")
        state = observe_long_percentage_trailing(state, price="110")
        state = observe_long_percentage_trailing(state, price="120")

        self.assertEqual(state.stop_price, "108")
        self.assertEqual(
            observe_long_percentage_trailing(state, price="115").stop_price,
            "108",
        )
        self.assertEqual(
            observe_long_percentage_trailing(state, price="108").status,
            "TRIGGERED",
        )

    def test_short_percentage_activation_and_exact_stop(self):
        state = arm_short_percentage_trailing(activation_price="100", rate="0.1")

        self.assertEqual(
            observe_short_percentage_trailing(state, price="90"),
            TrailingShortPercentageState(
                status="ACTIVE",
                activation_price="100",
                rate="0.1",
                low_water="90",
                stop_price="99",
            ),
        )

    def test_short_percentage_ratchets_without_raising_stop_and_triggers(self):
        state = arm_short_percentage_trailing(activation_price="100", rate="0.1")
        state = observe_short_percentage_trailing(state, price="90")
        state = observe_short_percentage_trailing(state, price="80")

        self.assertEqual(state.stop_price, "88")
        self.assertEqual(
            observe_short_percentage_trailing(state, price="85").stop_price,
            "88",
        )
        self.assertEqual(
            observe_short_percentage_trailing(state, price="88").status,
            "TRIGGERED",
        )

    def test_percentage_rate_and_reobserve_validation_fail_closed(self):
        with self.assertRaisesRegex(TrailingRatchetError, "TRAILING_RATE_INVALID"):
            arm_long_percentage_trailing(activation_price="100", rate="1")

        state = arm_short_percentage_trailing(activation_price="100", rate="0.1")
        state = observe_short_percentage_trailing(state, price="90")
        state = observe_short_percentage_trailing(state, price="99")
        with self.assertRaisesRegex(
            TrailingRatchetError, "TRAILING_ALREADY_TRIGGERED"
        ):
            observe_short_percentage_trailing(state, price="100")


if __name__ == "__main__":
    unittest.main()
